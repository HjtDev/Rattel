"""
Orphaned-media scanner backing the admin sweep (media_cleanup.admin).

Two sets are compared:
  - "referenced": every relative media path currently stored in any FileField
    (or subclass, e.g. ImageField / django_resized's ResizedImageField) across
    every installed model, discovered dynamically so new file fields never
    need to be registered here by hand.
  - "on disk": every file actually present under MEDIA_ROOT.

Anything on disk but not referenced, outside the excluded prefixes, and older
than the configured age guard, is reported as an orphan. Deletion only ever
happens via delete_orphans(), called from the admin after a fresh re-scan.
"""
import os
import time
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from django.apps import apps
from django.conf import settings
from django.core.files.storage import default_storage
from django.db import models


@dataclass(frozen=True)
class OrphanFile:
    path: str
    size: int
    mtime: float


@dataclass(frozen=True)
class MissingFile:
    """A DB row whose FileField points at a path absent from disk. Read-only —
    surfaced for a human to investigate, never auto-fixed."""
    model_label: str
    object_id: str
    field_name: str
    path: str


@dataclass(frozen=True)
class SweepReport:
    orphans: list[OrphanFile]
    missing: list[MissingFile]
    total_bytes: int


def _normalize(path: str) -> str:
    return str(PurePosixPath(path.replace('\\', '/')))


def _iter_file_fields():
    """Yield (model, field_name) for every concrete FileField on every installed model."""
    for model in apps.get_models():
        for f in model._meta.get_fields():
            if isinstance(f, models.FileField):
                yield model, f.name


def _referenced_paths() -> set[str]:
    referenced = set()
    for model, field_name in _iter_file_fields():
        values = (
            model._default_manager
            .exclude(**{field_name: ''})
            .exclude(**{f'{field_name}__isnull': True})
            .values_list(field_name, flat=True)
            .iterator()
        )
        for value in values:
            if value:
                referenced.add(_normalize(str(value)))
    return referenced


def _missing_files(on_disk: set[str]) -> list[MissingFile]:
    missing = []
    for model, field_name in _iter_file_fields():
        rows = (
            model._default_manager
            .exclude(**{field_name: ''})
            .exclude(**{f'{field_name}__isnull': True})
            .values_list('pk', field_name)
            .iterator()
        )
        for pk, value in rows:
            if not value:
                continue
            path = _normalize(str(value))
            if path not in on_disk:
                missing.append(MissingFile(
                    model_label=f'{model._meta.app_label}.{model.__name__}',
                    object_id=str(pk),
                    field_name=field_name,
                    path=path,
                ))
    return missing


def _walk_media_root():
    """Yield (relpath, size, mtime) for every file under MEDIA_ROOT."""
    media_root = Path(settings.MEDIA_ROOT)
    for dirpath, _dirnames, filenames in os.walk(media_root):
        for filename in filenames:
            abspath = Path(dirpath) / filename
            try:
                stat = abspath.stat()
            except OSError:
                continue
            relpath = _normalize(str(abspath.relative_to(media_root)))
            yield relpath, stat.st_size, stat.st_mtime


def _is_excluded(path: str) -> bool:
    prefixes = getattr(settings, 'MEDIA_CLEANUP_EXCLUDE_PREFIXES', ())
    return any(path.startswith(prefix) for prefix in prefixes)


def find_orphans() -> SweepReport:
    referenced = _referenced_paths()
    min_age_seconds = getattr(settings, 'MEDIA_CLEANUP_MIN_AGE_HOURS', 24) * 3600
    cutoff = time.time() - min_age_seconds

    on_disk = set()
    orphans = []
    for relpath, size, mtime in _walk_media_root():
        on_disk.add(relpath)
        if relpath in referenced or _is_excluded(relpath) or mtime > cutoff:
            continue
        orphans.append(OrphanFile(path=relpath, size=size, mtime=mtime))

    orphans.sort(key=lambda o: o.size, reverse=True)
    missing = _missing_files(on_disk)
    total_bytes = sum(o.size for o in orphans)

    return SweepReport(orphans=orphans, missing=missing, total_bytes=total_bytes)


def delete_orphans(paths) -> tuple[int, int, list[str]]:
    """
    Delete the given relative media paths via default_storage. Each deletion is
    isolated in its own try/except so one failure doesn't abort the batch.
    Returns (files_deleted, bytes_freed, error_messages).
    """
    files_deleted = 0
    bytes_freed = 0
    errors = []
    for path in paths:
        try:
            size = default_storage.size(path)
            default_storage.delete(path)
        except OSError as exc:
            errors.append(f'{path}: {exc}')
            continue
        files_deleted += 1
        bytes_freed += size
    return files_deleted, bytes_freed, errors

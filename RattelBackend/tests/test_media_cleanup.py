import os
import time
import uuid

import pytest
from django.core.files.storage import default_storage, storages
from django.test import override_settings
from django.utils.functional import empty

from media_cleanup.services import delete_orphans, find_orphans
from subscriptions.models import Plan


def _reset_default_storage():
    """
    default_storage / storages['default'] cache a FileSystemStorage instance whose
    `.location` is resolved from settings.MEDIA_ROOT lazily and then cached for the
    life of the process. override_settings(MEDIA_ROOT=...) does not reset this cache
    (Django only wires that up for STORAGES/STATIC_ROOT/STATIC_URL), so without this,
    model FileField saves/deletes would silently keep hitting the real media/ dir.
    This mirrors what Django's own `storages_changed` test signal handler does.
    """
    storages._backends = None
    storages._storages = {}
    try:
        del storages.backends
    except AttributeError:
        pass
    default_storage._wrapped = empty


@pytest.fixture
def media_root(tmp_path):
    with override_settings(MEDIA_ROOT=str(tmp_path)):
        _reset_default_storage()
        try:
            yield tmp_path
        finally:
            _reset_default_storage()


def _make_plan(picture=None):
    return Plan.objects.create(
        id=uuid.uuid4(),
        name='Test Plan',
        description='<p>desc</p>',
        picture=picture,
        price=1000,
    )


def _write(media_root, relpath, content=b'x', age_hours=None):
    abspath = media_root / relpath
    abspath.parent.mkdir(parents=True, exist_ok=True)
    abspath.write_bytes(content)
    if age_hours is not None:
        old_time = time.time() - age_hours * 3600
        os.utime(abspath, (old_time, old_time))
    return abspath


@pytest.mark.django_db
def test_find_orphans_returns_only_unreferenced_files(media_root):
    _make_plan(picture='subscriptions/pictures/referenced.jpg')
    _write(media_root, 'subscriptions/pictures/referenced.jpg', age_hours=48)
    _write(media_root, 'subscriptions/pictures/orphan.jpg', age_hours=48)

    report = find_orphans()

    orphan_paths = {o.path for o in report.orphans}
    assert orphan_paths == {'subscriptions/pictures/orphan.jpg'}


@pytest.mark.django_db
def test_editor_prefix_is_excluded(media_root):
    _write(media_root, 'editor/embedded.png', age_hours=48)

    report = find_orphans()

    assert report.orphans == []


@pytest.mark.django_db
def test_age_guard_skips_recently_written_files(media_root):
    _write(media_root, 'subscriptions/pictures/fresh.jpg', age_hours=1)

    report = find_orphans()
    assert report.orphans == []

    _write(media_root, 'subscriptions/pictures/fresh.jpg', age_hours=48)
    report = find_orphans()
    assert [o.path for o in report.orphans] == ['subscriptions/pictures/fresh.jpg']


@pytest.mark.django_db
def test_missing_files_reports_db_rows_without_a_file_on_disk(media_root):
    _make_plan(picture='subscriptions/pictures/gone.jpg')

    report = find_orphans()

    assert len(report.missing) == 1
    assert report.missing[0].path == 'subscriptions/pictures/gone.jpg'
    assert report.missing[0].model_label == 'subscriptions.Plan'


@pytest.mark.django_db
def test_delete_orphans_removes_files_and_reports_size(media_root):
    _write(media_root, 'subscriptions/pictures/a.jpg', content=b'12345')

    files_deleted, bytes_freed, errors = delete_orphans(['subscriptions/pictures/a.jpg'])

    assert files_deleted == 1
    assert bytes_freed == 5
    assert errors == []
    assert not (media_root / 'subscriptions/pictures/a.jpg').exists()


@pytest.mark.django_db(transaction=True)
def test_replacing_a_file_field_deletes_the_old_file_after_commit(media_root):
    _write(media_root, 'subscriptions/pictures/old.jpg')
    plan = _make_plan(picture='subscriptions/pictures/old.jpg')

    _write(media_root, 'subscriptions/pictures/new.jpg')
    plan.picture = 'subscriptions/pictures/new.jpg'
    plan.save(update_fields=['picture'])

    assert not (media_root / 'subscriptions/pictures/old.jpg').exists()
    assert (media_root / 'subscriptions/pictures/new.jpg').exists()


@pytest.mark.django_db(transaction=True)
def test_deleting_a_row_removes_its_file_after_commit(media_root):
    _write(media_root, 'subscriptions/pictures/to_delete.jpg')
    plan = _make_plan(picture='subscriptions/pictures/to_delete.jpg')

    plan.delete()

    assert not (media_root / 'subscriptions/pictures/to_delete.jpg').exists()


@pytest.mark.django_db(transaction=True)
def test_rolled_back_transaction_never_loses_the_old_file(media_root):
    from django.db import transaction

    _write(media_root, 'subscriptions/pictures/kept.jpg')
    plan = _make_plan(picture='subscriptions/pictures/kept.jpg')

    _write(media_root, 'subscriptions/pictures/replacement.jpg')

    class Boom(Exception):
        pass

    with pytest.raises(Boom):
        with transaction.atomic():
            plan.picture = 'subscriptions/pictures/replacement.jpg'
            plan.save(update_fields=['picture'])
            raise Boom

    assert (media_root / 'subscriptions/pictures/kept.jpg').exists()

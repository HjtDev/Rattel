from datetime import datetime, timezone as dt_timezone

from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied
from django.db import models
from django.shortcuts import redirect
from django.template.defaultfilters import filesizeformat
from django.template.response import TemplateResponse
from django.urls import path
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from jalali_date import datetime2jalali
from jalali_date.fields import JalaliDateField, SplitJalaliDateTimeField
from jalali_date.widgets import AdminJalaliDateWidget, AdminSplitJalaliDateTime

from .models import MediaSweepRun
from .services import delete_orphans, find_orphans

_JALALI_FORMFIELD_OVERRIDES = {
    models.DateField: {'form_class': JalaliDateField, 'widget': AdminJalaliDateWidget},
    models.DateTimeField: {'form_class': SplitJalaliDateTimeField, 'widget': AdminSplitJalaliDateTime},
}


@admin.register(MediaSweepRun)
class MediaSweepRunAdmin(admin.ModelAdmin):
    formfield_overrides = _JALALI_FORMFIELD_OVERRIDES
    list_display = (
        'created_at_jalali',
        'run_by',
        'files_deleted',
        'bytes_freed_display',
        'error_count',
    )
    list_filter = ('run_by',)
    ordering = ('-created_at',)
    list_per_page = 50

    readonly_fields = ('id', 'created_at', 'run_by', 'files_deleted', 'bytes_freed', 'errors')

    @admin.display(description=_('Run At'))
    def created_at_jalali(self, obj):
        return datetime2jalali(timezone.localtime(obj.created_at)).strftime('%Y/%m/%d %H:%M')

    @admin.display(description=_('Freed'))
    def bytes_freed_display(self, obj):
        return filesizeformat(obj.bytes_freed)

    @admin.display(description=_('Errors'))
    def error_count(self, obj):
        return len(obj.errors)

    # This is an audit log, not user-editable data — it should only ever be
    # written by scan_view() below.
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def get_urls(self):
        custom_urls = [
            path(
                'scan/',
                self.admin_site.admin_view(self.scan_view),
                name='media_cleanup_mediasweeprun_scan',
            ),
        ]
        return custom_urls + super().get_urls()

    def scan_view(self, request):
        # Destructive, project-wide action — restrict beyond the usual staff/model
        # permission checks that admin_view() already applies.
        if not request.user.is_superuser:
            raise PermissionDenied

        if request.method == 'POST':
            return self._delete_confirmed(request)

        report = find_orphans()
        context = {
            **self.admin_site.each_context(request),
            'title': _('Media Sweep'),
            'opts': self.model._meta,
            'orphans': [self._orphan_display(o) for o in report.orphans],
            'missing': report.missing,
            'total_bytes_display': filesizeformat(report.total_bytes),
        }
        return TemplateResponse(request, 'admin/media_cleanup/scan.html', context)

    @staticmethod
    def _orphan_display(orphan):
        modified = datetime.fromtimestamp(orphan.mtime, tz=dt_timezone.utc)
        return {
            'path': orphan.path,
            'size_display': filesizeformat(orphan.size),
            'modified_jalali': datetime2jalali(timezone.localtime(modified)).strftime('%Y/%m/%d %H:%M'),
        }

    def _delete_confirmed(self, request):
        submitted_paths = set(request.POST.getlist('path'))

        # Re-scan rather than trust the submitted list — closes the window where a
        # file becomes referenced (or is re-uploaded) between the report render and
        # this confirm click.
        fresh_report = find_orphans()
        fresh_orphan_paths = {orphan.path for orphan in fresh_report.orphans}
        to_delete = submitted_paths & fresh_orphan_paths
        skipped = len(submitted_paths - fresh_orphan_paths)

        files_deleted, bytes_freed, errors = delete_orphans(to_delete)

        MediaSweepRun.objects.create(
            run_by=request.user,
            files_deleted=files_deleted,
            bytes_freed=bytes_freed,
            errors=errors,
        )

        if skipped:
            messages.warning(
                request,
                _('%(count)d file(s) were skipped because they were no longer orphaned.') % {'count': skipped},
            )
        if errors:
            messages.error(
                request,
                _('%(count)d file(s) could not be deleted.') % {'count': len(errors)},
            )
        messages.success(
            request,
            _('Deleted %(count)d file(s), freeing %(size)s.') % {
                'count': files_deleted,
                'size': filesizeformat(bytes_freed),
            },
        )
        return redirect('admin:media_cleanup_mediasweeprun_changelist')

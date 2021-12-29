from django.contrib import admin

from notifications.models.models import Notification


class NotificationAdmin(admin.ModelAdmin):
    raw_id_fields = ('recipient', )
    list_display = (
        'recipient', 'actor', 'level', 
        'category', 'target', 'unread'
    )
    list_filter = ('level', 'unread', 'timestamp', )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('actor')


admin.site.register(Notification, NotificationAdmin)

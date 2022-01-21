from django.contrib import admin

from notifications.models.models import Notification


class NotificationAdmin(admin.ModelAdmin):
    raw_id_fields = ('recipient', )
    list_display = (
        'recipient', 'actor', 'verb', 'level', 
        'category', 'target', 'unread'
    )
    list_filter = ('level', 'unread', 'timestamp', )
    # For django-grappelli
    related_lookup_fields = {
        'generic': [
            ['actor_content_type', 'actor_object_id'],
            ['target_content_type', 'target_object_id'],
            ['action_object_content_type', 'action_object_object_id']
        ]
    }

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('actor')


admin.site.register(Notification, NotificationAdmin)

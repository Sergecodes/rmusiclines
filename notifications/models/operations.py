from django.utils.timesince import timesince as timesince_


class NotificationOperations:
    """Mixin to be used with the Notification model"""
   
    def mark_as_read(self):
        if not self.read:
            self.read = True
            self.save(update_fields=['read'])

    def mark_as_unread(self):
        if self.read:
            self.read = False
            self.save(update_fields=['read'])

    def timesince(self, now=None):
        """
        Shortcut for the ``django.utils.timesince.timesince`` function of the
        current timestamp.
        """

        return timesince_(self.timestamp, now)


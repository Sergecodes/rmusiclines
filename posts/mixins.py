from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class PostMediaMixin:
    """Mixin used on post photo and video models."""

    @property
    def filename(self):
        """Get name of associated file with extension"""

        if hasattr(self, 'photo'):
            file_field = self.photo
        elif hasattr(self, 'video'):
            file_field = self.video
        else:
            raise ValidationError(
                _("Corresponding file field should be a photo or video"),
                code='invalid'
            )

        # Returns path such as 'artist_posts_photos/filename.jpg' 
        # (`upload_to/filename.extension`)
        file_sub_path = file_field.name

        return file_sub_path.split('/')[-1]

    
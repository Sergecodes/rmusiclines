from django.db.models import Manager


class PostRepostManager(Manager):
    def get_queryset(self):
        # Returns only posts that are reposts
        return super().get_queryset().filter(is_simple_repost__isnull=False)


class ParentPostManager(Manager):
    def get_queryset(self):
        # Returns only parent posts
        return super().get_queryset().filter(is_simple_repost__isnull=True)

    def create(self, **kwargs):
        return super().create(**kwargs)


class ArtistPostRepostManager(PostRepostManager):
    pass


class ArtistParentPostManager(ParentPostManager):
    pass


class NonArtistPostRepostManager(PostRepostManager):
    pass


class NonArtistParentPostManager(ParentPostManager):
    pass


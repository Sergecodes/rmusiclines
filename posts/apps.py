from django.apps import AppConfig


class PostsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'posts'

    def ready(self):
        import posts.signals.artist_posts
        import posts.signals.non_artist_posts
        from actstream import registry

        ## Register models for use with activities
        # (via django-activity-stream)
        # Artist post models
        registry.register(self.get_model('ArtistPost'))
        registry.register(self.get_model('ArtistPostRating'))
        registry.register(self.get_model('ArtistPostComment'))
        registry.register(self.get_model('ArtistParentPost'))
        registry.register(self.get_model('ArtistPostRepost'))
        # registry.register(self.get_model('ArtistPostMention'))
        # registry.register(self.get_model('ArtistPostCommentLike'))

        # Non artist post models
        registry.register(self.get_model('NonArtistPost'))
        registry.register(self.get_model('NonArtistPostRating'))
        registry.register(self.get_model('NonArtistPostComment'))
        registry.register(self.get_model('NonArtistParentPost'))
        registry.register(self.get_model('NonArtistPostRepost'))
        # registry.register(self.get_model('NonArtistPostMention'))
        # registry.register(self.get_model('NonArtistPostBookmark'))
        # registry.register(self.get_model('NonArtistPostDownload'))
        # registry.register(self.get_model('NonArtistPostCommentLike'))

        

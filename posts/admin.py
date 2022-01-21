from django.contrib import admin

from .models.artist_posts.models import (
    ArtistPost, ArtistPostBookmark, ArtistPostComment,
    ArtistPostCommentLike, ArtistPostCommentMention,
    ArtistPostDownload, ArtistPostPhoto, ArtistPostVideo,
    ArtistPostRepost, ArtistPostRating, ArtistPostMention, 
)
from .models.common.models import PostHashtag
from .models.non_artist_posts.models import (
    NonArtistPost, NonArtistPostBookmark, NonArtistPostComment,
    NonArtistPostCommentLike, NonArtistPostCommentMention,
    NonArtistPostDownload, NonArtistPostPhoto, NonArtistPostVideo,
    NonArtistPostRepost, NonArtistPostRating, NonArtistPostMention, 
)


class PostAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_on'
    # To add a model property, it needs to be added to BOTH readonly_fields
    # and fieldsets .
    #
    # Add non-editable fields here so that they are displayed in the
    # admin panel
    readonly_fields = [
        'num_reposts', 'num_parent_comments', 
        'num_stars', 'created_on', 
    ]

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('hashtags')

    def hashtag_list(self, obj):
        return ', '.join([o.name for o in obj.hashtags.all()])


class PostHashTagAdmin(admin.ModelAdmin):
    pass


admin.site.register(PostHashtag, PostHashTagAdmin)


## Artist-related models admins
class ArtistPostAdmin(PostAdmin):  
    fieldsets = (
        ('', {
            'fields': (
                'body', 'language', 'artist', 
            ), 
        }),
        ('Tags', {
            'classes': ('grp-collapse grp-open', ),
            'fields': ('hashtags', ),
        }),
    )
    # list_display = 'hashtag_list'
    # For django-grappelli
    raw_id_fields = ('poster', 'artist', 'users_mentioned', )
    related_lookup_fields = {
        'fk': ['poster', 'artist', ],
        'm2m': ['users_mentioned', ]
    }


class ArtistPostBookmarkAdmin(admin.ModelAdmin):
    pass


class ArtistPostCommentAdmin(admin.ModelAdmin):
    pass


class ArtistPostCommentLikeAdmin(admin.ModelAdmin):
    pass


class ArtistPostCommentMentionAdmin(admin.ModelAdmin):
    pass


class ArtistPostDownloadAdmin(admin.ModelAdmin):
    pass


class ArtistPostPhotoAdmin(admin.ModelAdmin):
    pass


class ArtistPostVideoAdmin(admin.ModelAdmin):
    pass


class ArtistPostRepostAdmin(admin.ModelAdmin):
    pass


class ArtistPostRatingAdmin(admin.ModelAdmin):
    pass


class ArtistPostMentionAdmin(admin.ModelAdmin):
    pass


admin.site.register(ArtistPost, ArtistPostAdmin)
admin.site.register(ArtistPostBookmark, ArtistPostBookmarkAdmin)
admin.site.register(ArtistPostComment, ArtistPostCommentAdmin)
admin.site.register(ArtistPostCommentLike, ArtistPostCommentLikeAdmin)
admin.site.register(ArtistPostCommentMention, ArtistPostCommentMentionAdmin)
admin.site.register(ArtistPostDownload, ArtistPostDownloadAdmin)
admin.site.register(ArtistPostPhoto, ArtistPostPhotoAdmin)
admin.site.register(ArtistPostVideo, ArtistPostVideoAdmin)
admin.site.register(ArtistPostRepost, ArtistPostRepostAdmin)
admin.site.register(ArtistPostRating, ArtistPostRatingAdmin)
admin.site.register(ArtistPostMention, ArtistPostMentionAdmin)


## Non-artist related models admins
class NonArtistPostAdmin(PostAdmin):
    fieldsets = (
        ('', {
            'fields': (
                'body', 'language',
            ), 
        }),
        ('Tags', {
            'classes': ('grp-collapse grp-open', ),
            'fields': ('hashtags', ),
        }),
    )
    # For django-grappelli
    raw_id_fields = ('poster', 'users_mentioned', )
    related_lookup_fields = {
        'fk': ['poster', ],
        'm2m': ['users_mentioned', ]
    }


class NonArtistPostBookmarkAdmin(admin.ModelAdmin):
    pass


class NonArtistPostCommentAdmin(admin.ModelAdmin):
    pass


class NonArtistPostCommentLikeAdmin(admin.ModelAdmin):
    pass


class NonArtistPostCommentMentionAdmin(admin.ModelAdmin):
    pass


class NonArtistPostDownloadAdmin(admin.ModelAdmin):
    pass


class NonArtistPostPhotoAdmin(admin.ModelAdmin):
    pass


class NonArtistPostVideoAdmin(admin.ModelAdmin):
    pass


class NonArtistPostRepostAdmin(admin.ModelAdmin):
    pass


class NonArtistPostRatingAdmin(admin.ModelAdmin):
    pass


class NonArtistPostMentionAdmin(admin.ModelAdmin):
    pass


admin.site.register(NonArtistPost, NonArtistPostAdmin)
admin.site.register(NonArtistPostBookmark, NonArtistPostBookmarkAdmin)
admin.site.register(NonArtistPostComment, NonArtistPostCommentAdmin)
admin.site.register(NonArtistPostCommentLike, NonArtistPostCommentLikeAdmin)
admin.site.register(NonArtistPostCommentMention, NonArtistPostCommentMentionAdmin)
admin.site.register(NonArtistPostDownload, NonArtistPostDownloadAdmin)
admin.site.register(NonArtistPostPhoto, NonArtistPostPhotoAdmin)
admin.site.register(NonArtistPostVideo, NonArtistPostVideoAdmin)
admin.site.register(NonArtistPostRepost, NonArtistPostRepostAdmin)
admin.site.register(NonArtistPostRating, NonArtistPostRatingAdmin)
admin.site.register(NonArtistPostMention, NonArtistPostMentionAdmin)
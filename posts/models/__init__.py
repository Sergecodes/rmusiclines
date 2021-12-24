# See https://docs.djangoproject.com/en/3.2/topics/db/models/#organizing-models-in-a-package

from .artist_posts.models import (
    ArtistPost, ArtistPostDownload, ArtistPostPhoto,
    ArtistPostBookmark, ArtistPostMention, ArtistPostRating,
    ArtistPostCommentLike, ArtistPostComment, HashtaggedArtistPost,
    ArtistPostRepost, ArtistPostVideo, 
)
from .non_artist_posts.models import (
    NonArtistPost, NonArtistPostDownload, NonArtistPostPhoto,
    NonArtistPostBookmark, NonArtistPostMention, NonArtistPostRating,
    NonArtistPostCommentLike, NonArtistPostComment, HashtaggedNonArtistPost,
    NonArtistPostRepost, NonArtistPostVideo, 
)

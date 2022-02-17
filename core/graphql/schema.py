import graphene
from graphene_django.debug import DjangoDebug
from graphql_auth.schema import UserQuery, MeQuery

from accounts.graphql.artists.mutations import (
    CreateArtist, PatchArtist, DeleteArtist, FilterUpdateArtist,
    FollowArtist, UnfollowArtist, 
)
from accounts.graphql.artists.queries import ArtistQuery
from accounts.graphql.users.mutations import (
    AuthRelayMutation, PatchUser, FollowUser, UnfollowUser,
    ChangeUsername, ChangeEmail, BlockUser, UnblockUser,
    VerifyNewEmail, SuspendUser, FlagUser, Subscribe, 
    DeactivateAccount, ReactivateAccount, UserLogout
)
from posts.graphql.artist_posts.mutations import (
    CreateArtistPost, PatchArtistPost, DeleteArtistPost, RepostArtistPost, 
    RecordArtistPostDownload, BookmarkArtistPost, RemoveArtistPostBookmark, 
    RateArtistPost, RemoveArtistPostRating, CreateArtistPostAncestorComment,
    PatchArtistPostComment, DeleteArtistPostComment, ReplyToArtistPostComment,
    LikeArtistPostComment, RemoveArtistPostCommentLike, FlagArtistPost,
    UnflagArtistPost, FlagArtistPostComment, UnflagArtistPostComment,
    AbsolveArtistPost, AbsolveArtistPostComment, PinArtistPost,
    PinArtistPostComment, UnpinPinnedArtistPost, UnpinPinnedArtistPostComment,
    DeleteFlaggedArtistPost, DeleteFlaggedArtistPostComment
)
from posts.graphql.artist_posts.queries import (
    ArtistPostQuery, ArtistPostCommentQuery
)
from posts.graphql.common.mutations import (
    DeleteImageMutation, SingleImageUploadMutation, 
    MultipleImageUploadMutation
)
from posts.graphql.non_artist_posts.queries import (
    NonArtistPostQuery, 
)


# All Queries will be imported here
class Query(
    UserQuery, MeQuery, ArtistQuery, 
    ArtistPostQuery, ArtistPostCommentQuery,
    NonArtistPostQuery, 
    graphene.ObjectType
):
    debug = graphene.Field(DjangoDebug, name='_debug')


# All Mutations will be imported here
class Mutation(AuthRelayMutation, graphene.ObjectType):
    debug = graphene.Field(DjangoDebug, name='_debug')
    
    ## Post Upload mutations
    single_image_upload = SingleImageUploadMutation.Field()
    multiple_image_upload = MultipleImageUploadMutation.Field()
    delete_image = DeleteImageMutation.Field()

    ## Extra user mutations
    patch_user = PatchUser.Field()
    logout_user = UserLogout.Field()
    change_username = ChangeUsername.Field()
    change_email = ChangeEmail.Field()
    verify_new_email = VerifyNewEmail.Field()
    follow_user = FollowUser.Field()
    unfollow_user = UnfollowUser.Field()
    block_user = BlockUser.Field()
    unblock_user = UnblockUser.Field()
    flag_account = FlagUser.Field()
    suspend_user = SuspendUser.Field()
    deactivate_account = DeactivateAccount.Field()
    reactivate_account = ReactivateAccount.Field()
    subscribe = Subscribe.Field()

    ## Artist mutations
    create_artist = CreateArtist.Field()
    patch_artist = PatchArtist.Field()
    delete_artist = DeleteArtist.Field()
    filter_update_artist = FilterUpdateArtist.Field()
    follow_artist = FollowArtist.Field()
    unfollow_artist = UnfollowArtist.Field()

    ## Artist Post mutations
    create_artist_post = CreateArtistPost.Field()
    patch_artist_post = PatchArtistPost.Field()
    delete_artist_post = DeleteArtistPost.Field()
    repost_artist_post = RepostArtistPost.Field()
    record_artist_post_download = RecordArtistPostDownload.Field()
    bookmark_artist_post = BookmarkArtistPost.Field()
    remove_artist_post_bookmark = RemoveArtistPostBookmark.Field()
    rate_artist_post = RateArtistPost.Field()
    remove_artist_post_rating = RemoveArtistPostRating.Field()
    flag_artist_post = FlagArtistPost.Field()
    unflag_artist_post = UnflagArtistPost.Field()
    absolve_artist_post = AbsolveArtistPost.Field()
    pin_artist_post = PinArtistPost.Field()
    unpin_pinned_artist_post = UnpinPinnedArtistPost.Field()
    delete_flagged_artist_post = DeleteFlaggedArtistPost.Field()
    
    ## Artist post comment mutations
    create_artist_post_ancestor_comment = CreateArtistPostAncestorComment.Field()
    patch_artist_post_comment = PatchArtistPostComment.Field()
    delete_artist_post_comment = DeleteArtistPostComment.Field()
    reply_to_artist_post_comment = ReplyToArtistPostComment.Field()
    like_artist_post_comment = LikeArtistPostComment.Field()
    remove_artist_post_comment_like = RemoveArtistPostCommentLike.Field()
    flag_artist_post_comment = FlagArtistPostComment.Field()
    unflag_artist_post_comment = UnflagArtistPostComment.Field()
    absolve_artist_post_comment = AbsolveArtistPostComment.Field()
    pin_artist_post_comment = PinArtistPostComment.Field()
    unpin_pinned_artist_post_comment = UnpinPinnedArtistPostComment.Field()
    delete_flagged_artist_post_comment = DeleteFlaggedArtistPostComment.Field()


schema = graphene.Schema(query=Query, mutation=Mutation)



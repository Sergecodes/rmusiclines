
# TODO
- UPDATE googlemail to gmail conversion. (perhaps use custom field that automatically does the convertion) .
eg. email.replace(@googlemail.com, @gmail.com)
(see https://stackoverflow.com/questions/44117619/why-django-lowercases-only-the-domain-part-of-email-addresses-in-normalize-email)
- update pre delete User signal ; see
 https://stackoverflow.com/questions/59603139/how-to-use-a-pre-delete-signal-to-universally-prevent-delete
In conlusion, don't use pre delete signal.

- update non artist post graphql stuffs
- setup social authentication (django graphql social auth...)
- test media upload via AWS



then:
- setup memcached for storing sessions and for general caching !! (performance reasons)
- go through all TODOs and resolve those possible.
- payment mutations

- db constraint; artist post and repost should have same artist_id
- db constraint; If new post is simple repost, ensure poster has just one simple repost on given post parent
- db constraint; if post is parent, it should have content (at least body or photo or video)


# 
# THIS !! TODO
# To improve download_count query, during each new month, reset the download_count of all users
# to zero, then increment normally when user downloads a post. If we wish, we can create another
# table(model) to store the user's download count per month in each year so as to keep track of
# user's past number of downloads.


# add to site specification:
- users can't edit post. however, b4 their post is published, they should be shown a render of their
post. If they validate it, then their post is posted.
The reason they shouldn't be able to edit is because when a user posts, all his followers for instance
will be updated. If later he edits(even within a brief 3 minutes span), new users will be seeing another
version of his post; which isn't very good. Same with comments lol; imagine if user is prestigious/important... 
...
- remove avatar images 
- save post content/images in cache if user doesn't post it.
- posts/comments can be edited if they haven't lasted up to 3 minutes
- moderator can notify admin to delete a post
- specify site and notification settings
- preview post before posting (or preview post during creation)
- post can be private
- users can be mentioned in comments..
- ratings for posts are now 1, 3 or 5 stars
- remove music_title field.
- user can change username but after changing username, they have to wait until
after 15 days before they can change it again. 
- possibility for poster of post to pin comment(parent) under post.
- language of post should be auto detected
- update max post length to 500chars. imagine that a user wants to post facts about a given artist... ...
and other stuff... ...
- max length of comments should be 2000chars, just so user doesnt abuse the length
- for artist posts, before adding a post to following users' timeline, verify posts level of 
"politeness" such as using google's natural language api. If post is like "artist sucks" with a low 
"score", then only poster's followers will see the post.
- users can post audio that will be transformed to a video with a given static image / cool wavy background with the site's logo ... . they can also select areas of the audio they wish to use... Audio can be perhaps max 1 minute.
- user can upload audio or video of any length, buth with the obligations that:
 (if the video is from a url, it should be may be at most 2 minutes??? eg. youtube video.. else they
 can upload a video irrespective of duration but when posting the post, the video check should be made).
 This is becoz there will be a possibility to resize the uploaded video(iff it isn't from a url) b4 posting.
 ** Same with audio.  should we permit audio via url ?



# add to database specification 
- table indexes
- pinned_artist_post or non_artist_post; not both.
- constraints on database fields(birth_date, num_stars, ) and field types 
(this can be done on a table : field | type | constraints | extra(or misc)
- ArtistFollow table
- unique email if user is active


# other proposals
- possibility to filter posts for profanity? or this depends on users followers...
- place button near post (like Youtube) for translation to user's
  language(perhaps his current language); 
  then in user's settings, there will be option to view all posts or posts by countries...
- separate section on site for videos(like facebook). Better still, there can be a section 
for videos where only posts with videos(and photos/gifs ?) will be displayed. 
Then on the home page all kinds of posts are displayed, or perhaps only non video posts..?.
- We should have a verified account on the site, that by default all users will follow.
This account will choose a random post and repost daily. xD 


ADDITIONS:
- trending posts, artists and users
- paid advertisements for companies; and these ads will be shown to all users,
view only sponsored ads (ads where companies contacted us...)


# source /home/sergeman/.virtualenvs/musicsite-env/bin/activate





## Not very useful


# After this number of minutes, comment/post can't be edited
# COMMENT_CAN_EDIT_TIME_LIMIT = timedelta(minutes=3)
# POST_CAN_EDIT_TIME_LIMIT = timedelta(minutes=3)



# class PatchArtistPost(Output, DjangoPatchMutation):
#     class Meta:
#         model = ArtistPost
#         only_fields = ('body', )

#     @classmethod
#     def check_permissions(cls, root, info, input, id, obj: ArtistPost):
#         """Only poster of post can edit the post and post should be editable"""

#         # Only poster can edit post
#         print(info.context.user)
#         print(obj.poster)
#         if info.context.user.id != obj.poster_id:
#             raise GraphQLError(
#                 _("Only poster can edit post"),
#                 extensions={'code': 'not_permitted'}
#             )

#         # Post should be editable
#         if not obj.can_be_edited:
#             err = _("You can no longer edit a post after %(can_edit_minutes)d minutes of its creation") \
#                 % {'can_edit_minutes': POST_CAN_EDIT_TIME_LIMIT.seconds // 60}

#             raise GraphQLError(err, extensions={'code': 'not_editable'})

#     @classmethod
#     @login_required
#     def mutate(cls, root, info, input, id):
#         # This method was overriden just to use the login_required decorator so as to have a 
#         # consistent authentication api.
#         return super().mutate(cls, root, info, input, id)

#     @classmethod
#     def after_mutate(cls, root, info, id, input, obj: ArtistPost, return_data):
#         # Save photos or video to updated object
#         user_cache_keys = get_user_cache_keys(info.context.user.username)
#         cache_photos_key, cache_video_key = user_cache_keys['photos'], user_cache_keys['video']
        

	# @property
	# def can_be_edited(self):
	# 	"""Verify if post is within edit time frame"""
	# 	if timezone.now() - self.created_on > POST_CAN_EDIT_TIME_LIMIT:
	# 		return False
	# 	return True


# class PatchArtistPostComment(Output, DjangoPatchMutation):
#     class Meta:
#         model = ArtistPostComment
#         login_required = True
#         only_fields = ('body', )

#     @classmethod
#     def check_permissions(cls, root, info, input, id, obj: ArtistPostComment):
#         """Only poster of comment can edit the comment and comment should be editable"""

#         # Only poster can edit comment
#         print(info.context.user)
#         print(obj.poster)
#         if info.context.user.id != obj.poster_id:
#             raise GraphQLError(
#                 _("Only poster can edit comment"),
#                 extensions={'code': 'not_permitted'}
#             )

#         # Comment should be editable
#         if not obj.can_be_edited:
#             err = _("You can no longer edit a comment after %(can_edit_minutes)d minutes of its creation") \
#                 % {'can_edit_minutes': COMMENT_CAN_EDIT_TIME_LIMIT.seconds // 60}

#             raise GraphQLError(err, extensions={'code': 'not_editable'})


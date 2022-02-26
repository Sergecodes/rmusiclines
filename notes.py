
# TODO
- update post, repost, mark_user_verified, toggle_user_premium, toggle user is moderator mutations 
- db constraint; artist post and repost should have same artist_id
- enable profile pic and cover photo uploads
- setup social authentication (django graphql social auth...)

then:
- test media upload via AWS
- setup memcached for storing sessions and for general caching !! (performance reasons)
- go through all TODOs and resolve those possible.


# 
# THIS !! TODO
# To improve download_count query, during each new month, reset the download_count of all users
# to zero, then increment normally when user downloads a post. If we wish, we can create another
# table(model) to store the user's download count per month in each year so as to keep track of
# user's past number of downloads.


# add to site specification:
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
- max length of comments should be 2000chars, just so user doesnt abuse the length; and
for posts should be 350 chars.
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

# class SingleImageUploadMutation(Output, graphene.Mutation):
#     """Upload an image"""

#     class Arguments:
#         file = Upload(required=True)
#         # form_for = PostFormFor(required=True)

#     filename = graphene.String()
#     base64_str = graphene.String()
#     mimetype = graphene.String()
     
#     @classmethod
#     @login_required
#     def mutate(cls, root, info, file: InMemoryUploadedFile, **kwargs):
#         # print(info.context.FILES)
#         # form = ArtistPhotoForm({'photo': file})
#         # print(form.data)
#         # print(form.is_valid())

#         user_cache_keys = get_user_cache_keys(info.context.user.username)
#         cache_photos_key, cache_video_key = user_cache_keys['photos'], user_cache_keys['video']

#         # Validate cache content
#         validate_cache_media(file, cache_photos_key, cache_video_key)

#         try:
#             validate_post_photo_file(file)
#         except ValidationError as err:
#             raise GraphQLError(
#                 err.message % (err.params or {}),
#                 extensions={'code': err.code}
#             )

#         # Use None so this value stays in the cache indefinitely, till explicitly deleted
#         # (or server restarts xD)
#         cache_key = cache_photos_key
#         user_photos_list = cache.get_or_set(cache_key, [], None)

#         ## Save file to cache
#         # Get name without extension
#         # valid_filename = STORAGE.get_valid_name(file.name).split('.')[0]

#         # Get file extension and type to use with PIL
#         file_extension, ftype = get_image_file_thumbnail_extension_and_type(file)

#         # Save thumbnail to in-memory file as StringIO
#         image = Image.open(file)
#         # image = image.convert('RGB')
#         image.thumbnail(THUMBNAIL_ALIASES['']['sm_thumb']['size'], Image.ANTIALIAS)
#         thumb_file = BytesIO()
#         image.save(thumb_file, format=ftype)

#         # Use random uuid as filename so as to protect user privacy; and besides we don't
#         # really need the original file name.
#         use_filename = str(uuid.uuid4()) + '.' + file_extension
#         # thumb_file.seek(0)

#         # Will be used with ContentFile to regenerate the file so as to save to
#         # model object when posting a post
#             # from django.core.files.base import ContentFile
#             # img_file = ContentFile(img_io.getvalue())
#             # saved_file_name = STORAGE.save(save_dir + valid_name, img_file)

#         file_bytes = thumb_file.getvalue()
#         base64_bytes = base64.b64encode(file_bytes)
#         base64_str = base64_bytes.decode('utf-8')
#         mimetype = file.content_type
#         # save_dir = FORM_AND_UPLOAD_DIR[form_for]
#         # saved_filename = STORAGE.save(save_dir + use_filename, file)

#         print(file.size, thumb_file.tell())
#         user_photos_list.append({
#             'file_bytes': file_bytes,
#             'filename': use_filename,
#             'mimetype': mimetype
#         })
#         cache.set(cache_key, user_photos_list)
#         thumb_file.close()

#         return SingleImageUploadMutation(
#             base64_str=base64_str,
#             filename=use_filename,
#             mimetype=mimetype
#         )
       
    

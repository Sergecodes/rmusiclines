
# TODO
- create other models mutations(for post create/update mutations, read photos in cache and 
store them in database(post's photos) after the post has been validated)
- enable pfp and cover photo upload for user profile
(appropriate size validators for pfp & cover photo, use params in post.validators file)
- setup social authentication (django graphql social auth...)
- test image upload via AWS
- setup memcached for storing sessions and for general caching !! (performance reasons)
- save post content/images in cache if user doesn't post it.
# how to optimize/compress base64 strings...

# add to site specification:
(- remove avatar images ? )
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


ADDITIONS:
- trending posts, artists and users
- paid advertisements for companies; and these ads will be shown to all users,
view only sponsored ads (ads where companies contacted us...)


# source /home/sergeman/.virtualenvs/musicsite-env/bin/activate

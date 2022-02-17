
# TODO
- post, update post, repost mutations (handle photos, gifs and videos plus caching)
- db constraint; artist post and repost should have same artist_id
- enable profile pic and cover photo uploads
- setup social authentication (django graphql social auth...)

then:
- test image upload via AWS
- setup memcached for storing sessions and for general caching !! (performance reasons)


# 
# THIS !!
# To improve download_count query, during each new month, reset the download_count of all users
# to zero, then increment normally when user downloads a post. If we wish, we can create another
# table(model) to store the user's download count per month in each year so as to keep track of
# user's past number of downloads.


# add to site specification:
(- remove avatar images ? )
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
- 


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


# TODO
- create "change email address mutation" (use ResendActivationEmail...)
(what if a user registers with someone's email, but does not confirm the email.
Can the rightful owner of the email register using the email; or an `email already exists`
error is raises ?? TEST THIS !)
- create other models mutations
- enable pfp and cover photo upload for user profile
- setup social authentication (use firebase and django graphql social auth...)



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
after 15 days before they can change this. 
- possibility for poster of post to pin comment(parent) under post.


# add to database specification 
- table indexes
- pinned_artist_post or non_artist_post; not both.
- constraints on database fields(birth_date, num_stars, ) and field types 
(this can be done on a table : field | type | constraints | extra(or misc)
- ArtistFollow table


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

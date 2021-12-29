ADDITIONS:
- trending posts, artists and users
- paid advertisements for companies


    # TODO
# add to site specification:
- posts/comments can be edited if they haven't stayed for up to 3 minutes
- moderator can notify admin to delete a post
- specify site and notification settings

# add to database specification 
- table indexes
- pinned_artist_post or non_artist_post; not both.
- constraints on database fields(birth_date, num_stars, ) and field types 
(this can be done on a table : field | type | constraints | extra(or misc)

# coding 
# - parse hashtags and mentions(@) 
(validate other unicode chars - chinese, etc...; with tags and hashtags)
(makemigrations nd migrate flagging/notifications)
- implement payment
- setup activity streams
- configure project settings (images storage -- image and file fields, static files, media path and urls, emails, )

- install/setup django extensions; admin site and django-grappelli
- setup social authentication gateways
(# validate email (googlemail vs gmail) in allauth. (adapter... ?)
- create django rest framework serializers 
- test models

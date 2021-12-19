
# validate email (googlemail vs gmail) in allauth. (adapter... ?)

    # TODO
# add to site specification:
- add artist photos to uml diagram and database models
- user can block other users
- user can post either max 4 photos or 1 video or 1 gif per post.
- specify site and notification settings
- toonified dp/cover photo for premium users
- view reposts 

# add to database specification 
- change unique_str to uuid
- put artist and co in accounts schema
- rename hashtag table to post_hashtag
- table indexes
- max hashtags per post to 5 and max length of hashtag to 50
- rename star_count to num_stars
- constraints on database fields and field types
* this can be done on a table : field | type | contraints | extra(or misc)

# coding 
- complete other apps models
- setup django-allauth
- implement methods
- implement payment
- configure project settings (static files, media path and urls, emails, )
- setup stream api (use env var for api keys !)
- install/setup admin site and django-grappelli

start: 17:23
stop: 
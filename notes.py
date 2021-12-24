
# validate email (googlemail vs gmail) in allauth. (adapter... ?)

    # TODO
# add to site specification:
- add artist photos to uml diagram and database models
- specify site and notification settings

# add to database specification 
- table indexes
- constraints on database fields and field types (this can be done on a table : field | type | contraints | extra(or misc)

# coding 
- implement methods
- arrange flagging 
- implement payment
- configure project settings (images storage -- image and file fields, static files, media path and urls, emails, )
- setup stream api (use env var for api keys !)
- install/setup django extensions; admin site and django-grappelli
- setup social authentication gateways
- test models


DATABASE_COLLATIONS:
    ## https://docs.djangoproject.com/en/3.2/ref/contrib/postgres/operations
    # /#managing-colations-using-migrations
    #
    ## https://stackoverflow.com/questions/18807276/
    # how-to-make-my-postgresql-database-use-a-case-insensitive-colation
    #
    ## https://gist.github.com/hleroy/2f3c6b00f284180da10ed9d20bf9240a
    # how to use Django 3.2 CreateCollation and db_collation to implement a 
    # case-insensitive Chaffield with Postgres > 1
    #
    ## https://www.postgresql.org/docs/current/citext.html
    #
    ## https://www.postgresql.org/docs/current/collation.html#COLLATION-NONDETERMINISTIC
# """This file contains functions using this app(posts) that access the database"""

# from accounts.models import User, Artist


# # User = get_user_model()

# class UserDAO:
#     """Data Access Object between User and database"""

#     def create_user(self, username, email, password, **extra_fields):
#         return User.objects.create_user(username, email, password, **extra_fields)

#     def get_users(self, limit=None, **filters):
#         # list[:None] will return the entire list
#         return User.objects.filter(**filters)[:limit]

#     def get_user(self, **filters):
#         try:
#             return User.objects.get(**filters)
#         except User.DoesNotExist:
#             return False

#     def update_user(self, user, new_props: dict):
#         for key, value in new_props.items():
#             setattr(user, key, value)
#         user.save(update_fields=list(new_props.keys()))

#     def delete_user(self, user, really_delete=False):
#         if really_delete:
#             user.delete()
#         user.deactivate()


# class ArtistDAO:
#     """Data Access Object between Artist and database"""

#     def create_artist(self, name, country, date_of_birth, gender='M'):
#         artist = Artist.objects.create(
#             name=name, 
#             country=country, 
#             gender=gender,
#             date_of_birth=date_of_birth
#         )
#         artist.tags.add(country)
#         return artist

#     def get_artist(self, **filters):
#         try:
#             return Artist.objects.get(**filters)
#         except Artist.DoesNotExist:
#             return False

#     def get_artists(self, limit=None, **filters):
#         # list[:None] will return the entire list
#         return Artist.objects.filter(**filters)[:limit]

#     def update_artist(self, artist, new_props: dict):
#         for key, value in new_props.items():
#             setattr(artist, key, value)
#         artist.save(update_fields=list(new_props.keys()))

#     def delete_artist(self, artist):
#         artist.delete() 



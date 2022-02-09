"""Contains project-wide utilities"""
from django.contrib.contenttypes.models import ContentType


def get_content_type(model_obj):
    """Return the content type of a given model"""
    
    return ContentType.objects.get_for_model(model_obj)




# Problem: The country field is a choices field; graphene parses it into an Enum.
# Multiple fields have the country field, so this gives the same Enum name; => Error.
# So we have to use a different enum name.
# To this this, we neet to manually create out enum.
# CountryEnum = convert_choices_to_named_enum_with_descriptions('country', countries)
# GenderEnum = convert_choices_to_named_enum_with_descriptions('gender', GENDERS)


# def graphene_enum_naming(field):
#     """Generate unique enum name for graphene choices field"""
#     # Problem: The country field is a choices field; graphene parses it into an Enum.
#     # Multiple fields have the country field, so this gives the same Enum name; => Error.
#     # So we have to use a different enum name.

#     # Directly importing the module doesn't work since field.model is a string.
#     # So get a string representation of the model's path
#     NonArtistPost = import_string('posts.models.non_artist_posts.models.NonArtistPost')
#     ArtistPost = import_string('posts.models.artist_posts.models.ArtistPost')
#     User = import_string('accounts.models.users.models.User')
#     Artist = import_string('accounts.models.artists.models.Artist')

#     if field.model == User:
#         return f'User{field.name.title()}Enum'
#     elif field.model == Artist:
#         return f'Artist{field.name.title()}Enum'
#     elif field.model == ArtistPost:
#         return f'ArtistPost{field.name.title()}Enum'
#     elif field.model == NonArtistPost:
#         return f'NonArtistPost{field.name.title()}Enum'
    
#     print(field.model, type(field.model))
#     return f'{field.name.title()}Enum'


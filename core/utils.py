"""Contains project-wide utilities"""
import ffmpeg
import os
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _
from graphene_django_cud.util import disambiguate_id
from graphql import GraphQLError


def get_content_type(model_obj):
    """Return the content type of a given model"""
    
    return ContentType.objects.get_for_model(model_obj)


def get_int_id_or_none(id):
    """
    Parse disambiguated id to int or None. `id` should be a graphene.ID \n
    Basically this function should be used when the id can be None.
    """
    # If id is None, return None coz disambiguate_id(None) would be None 
    # and int(None) would raise TypeError
    if id is None:
        return None

    return int(disambiguate_id(id))


def get_image_file_thumbnail_extension_and_type(file):
    """
    Get and validate image file thumbnail extension.
    Used in image upload mutations.
    """
    
    thumb_name, thumb_extension = os.path.splitext(file.name)
    thumb_extension = thumb_extension.lower()

    # Yes, the file types returned should be in uppercase
    if thumb_extension in ['.jpg', '.jpeg']:
        FTYPE = 'JPEG'
    elif thumb_extension == '.gif':
        FTYPE = 'GIF'
    elif thumb_extension == '.png':
        FTYPE = 'PNG'
    else:
        raise GraphQLError(
            _('Weird, unrecognized file type'),
            extensions={'code': 'invalid_image'}
        )

    return thumb_extension, FTYPE


def get_user_cache_keys(username: str):
    """
    Return the cache keys corresponding to the `username`.
    Update list of possible keys in the file `core.constants.py`
    """
    cache_photos_key = f'{username}-unposted-photos'
    cache_video_key = f'{username}-unposted-video'
    
    return {
        'photos': cache_photos_key,
        'video': cache_video_key
    }


def compress_video(video_full_path, size_upper_bound, two_pass=True, filename_suffix='1'):
    """
    Compress video file to max-supported size.
    :param video_full_path: the video you want to compress.
    :param size_upper_bound: Max video size in KB.
    :param two_pass: Set to True to enable two-pass calculation.
    :param filename_suffix: Add a suffix for new video.
    :return: out_put_name or error
    """
    filename, extension = os.path.splitext(video_full_path)
    extension = '.mp4'
    output_file_name = filename + filename_suffix + extension

    total_bitrate_lower_bound = 11000
    min_audio_bitrate = 32000
    max_audio_bitrate = 256000
    min_video_bitrate = 100000

    try:
        # Bitrate reference: https://en.wikipedia.org/wiki/Bit_rate#Encoding_bit_rate
        probe = ffmpeg.probe(video_full_path)

        # Video duration, in s.
        duration = float(probe['format']['duration'])

        # Audio bitrate, in bps.
        audio_bitrate = float(next((s for s in probe['streams'] if s['codec_type'] == 'audio'), None)['bit_rate'])
       
        # Target total bitrate, in bps.
        target_total_bitrate = (size_upper_bound * 1024 * 8) / (1.073741824 * duration)
        if target_total_bitrate < total_bitrate_lower_bound:
            print('Bitrate is extremely low! Stop compress!')
            return False

        # Best min size, in kB.
        best_min_size = (min_audio_bitrate + min_video_bitrate) * (1.073741824 * duration) / (8 * 1024)
        if size_upper_bound < best_min_size:
            print('Quality not good! Recommended minimum size:', '{:,}'.format(int(best_min_size)), 'KB.')
            # return False

        # Target audio bitrate, in bps.
        audio_bitrate = audio_bitrate

        # target audio bitrate, in bps
        if 10 * audio_bitrate > target_total_bitrate:
            audio_bitrate = target_total_bitrate / 10
            if audio_bitrate < min_audio_bitrate < target_total_bitrate:
                audio_bitrate = min_audio_bitrate
            elif audio_bitrate > max_audio_bitrate:
                audio_bitrate = max_audio_bitrate

        # Target video bitrate, in bps.
        video_bitrate = target_total_bitrate - audio_bitrate
        if video_bitrate < 1000:
            print('Bitrate {} is extremely low! Stop compress.'.format(video_bitrate))
            return False

        i = ffmpeg.input(video_full_path)
        if two_pass:
            ffmpeg.output(i, '/dev/null' if os.path.exists('/dev/null') else 'NUL',
                          **{'c:v': 'libx264', 'b:v': video_bitrate, 'pass': 1, 'f': 'mp4'}
                          ).overwrite_output().run()
            ffmpeg.output(i, output_file_name,
                          **{'c:v': 'libx264', 'b:v': video_bitrate, 'pass': 2, 'c:a': 'aac', 'b:a': audio_bitrate}
                          ).overwrite_output().run()
        else:
            ffmpeg.output(i, output_file_name,
                          **{'c:v': 'libx264', 'b:v': video_bitrate, 'c:a': 'aac', 'b:a': audio_bitrate}
                          ).overwrite_output().run()

        if os.path.getsize(output_file_name) <= size_upper_bound * 1024:
            return output_file_name
        elif os.path.getsize(output_file_name) < os.path.getsize(video_full_path):  # Do it again
            return compress_video(output_file_name, size_upper_bound)
        else:
            return False

    except FileNotFoundError as e:
        print('You do not have ffmpeg installed!', e)
        # sudo apt install ffmpeg
        print('You can install ffmpeg by reading https://github.com/kkroening/ffmpeg-python/issues/251')
        return False



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


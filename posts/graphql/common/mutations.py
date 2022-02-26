import base64
import graphene
import os
import shortuuid
from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from graphene_file_upload.scalars import Upload
from graphql import GraphQLError
from graphql_auth.bases import Output
from graphql_auth.decorators import login_required
from io import BytesIO
from PIL import Image
from pydub import AudioSegment
import subprocess

from core.constants import FILE_STORAGE_CLASS
from core.utils import (
	get_file_extension, get_user_cache_keys,
	get_image_file_thumbnail_extension_and_type, get_file_path
)
from posts.constants import MAX_NUM_PHOTOS, TEMP_FILES_UPLOAD_DIR, POST_COVER_IMG_DIR
from posts.validators import (
	validate_post_photo_file, validate_cache_media,
	validate_post_video_file, validate_post_audio_file
)

STORAGE = FILE_STORAGE_CLASS()
USE_S3 = settings.USE_S3
MEDIA_ROOT = settings.MEDIA_ROOT
THUMBNAIL_ALIASES = settings.THUMBNAIL_ALIASES

		
class MultipleImageUploadMutation(Output, graphene.Mutation):
	"""Upload multiple images at once"""

	class Arguments:
		files = graphene.List(Upload, required=True)

	filenames = graphene.List(graphene.String)
	base64_strs = graphene.List(graphene.String)
	mimetypes = graphene.List(graphene.String)
	 
	@classmethod
	@login_required
	def mutate(cls, root, info, files: list, **kwargs):
		user_cache_keys = get_user_cache_keys(info.context.user.username)
		cache_photos_key, cache_video_key = user_cache_keys['photos'], user_cache_keys['video']

		# Validate cache content and uploaded file
		for file in files:
			validate_cache_media(cache_photos_key, cache_video_key)

			try:
				validate_post_photo_file(file)
			except ValidationError as err:
				raise GraphQLError(
					err.message % (err.params or {}),
					extensions={'code': err.code}
				)

		# Use None so this value stays in the cache indefinitely, till explicitly deleted
		# (or server restarts xD)
		cache_key = cache_photos_key
		user_photos_list = cache.get_or_set(cache_key, [], None)

		# Validate photos length(if number of photos uploaded plus previous ones will be
		# more than the limit)
		if len(files) + len(user_photos_list) > MAX_NUM_PHOTOS:
			raise GraphQLError(
				_('Maximum number of photos attained'),
				extensions={'code': 'max_photos_attained'}
			)

		# Get thumbnails of files and saved to cache
		base64_strs, filenames, mimetypes = [], [], []
		for file in files:
			# Get file extension and type to use with PIL
			file_extension, ftype = get_image_file_thumbnail_extension_and_type(file)

			image = Image.open(file)
			# image = image.convert('RGB')
			image.thumbnail(THUMBNAIL_ALIASES['']['sm_thumb']['size'], Image.ANTIALIAS)
			thumb_file = BytesIO()
			image.save(thumb_file, format=ftype)
			
			use_filename = shortuuid.uuid() + '.' + file_extension
			mimetype = file.content_type
			file_bytes = thumb_file.getvalue()
			base64_bytes = base64.b64encode(file_bytes)
			base64_str = base64_bytes.decode('utf-8')

			base64_strs.append(base64_str)
			filenames.append(use_filename)
			mimetypes.append(mimetype)
			thumb_file.close()

			user_photos_list.append({
				'file_bytes': file_bytes,
				'filename': use_filename,
				'mimetype': mimetype
			})
		
		cache.set(cache_key, user_photos_list)

		return MultipleImageUploadMutation(
			filenames=filenames,
			base64_strs=base64_strs,
			mimetypes=mimetypes
		)
	   

class DeleteImageMutation(Output, graphene.Mutation):
	"""Delete an uploaded image via its filename"""

	class Arguments:
		filename = graphene.String()

	@classmethod
	@login_required
	def mutate(cls, root, info, filename, **kwargs):
		user_cache_keys = get_user_cache_keys(info.context.user.username)
		cache_key = user_cache_keys['photos']

		user_photos_list = cache.get_or_set(cache_key, [], None)

		# Find file name in cache
		for i in range(len(user_photos_list)):
			photo_dict = user_photos_list[i]

			if photo_dict['filename'] == filename:
				del_index = i
				break
		else:
			# If the for loop is not broken(break-ed) - (if the filename is not found)
			# this will be executed.
			# 
			# In other words, this statement will be executed only if the loop completes.
			raise GraphQLError(
				_('No such file found'),
				extensions={'code': 'not_found'}
			)

		del user_photos_list[del_index]
		cache.set(cache_key, user_photos_list)

		return DeleteImageMutation(success=True)


class VideoUploadMutation(Output, graphene.Mutation):
	"""
	Upload a video.
	Flow:
		- Video is uploaded to backend. 
		- Store filename, mimetype and filepath in cache and return them.
	"""

	class Arguments:
		file = Upload(required=True)

	filename = graphene.String()
	filepath = graphene.String()
	mimetype = graphene.String()
	was_audio = graphene.Boolean(default_value=False)
	 
	@classmethod
	@login_required
	def mutate(cls, root, info, file, **kwargs):
		## Note that InMemoryUploaded files will be saved during validation,
		# while TemporaryUploaded files won't be

		user = info.context.user
		user_cache_keys = get_user_cache_keys(user.username)
		cache_photos_key, cache_video_key = user_cache_keys['photos'], user_cache_keys['video']

		# Validate cache content
		validate_cache_media(cache_photos_key, cache_video_key)

		# Validate video file.
		try:
			validate_post_video_file(file)
		except ValidationError as err:
			raise GraphQLError(
				err.message % (err.params or {}),
				extensions={'code': err.code}
			)

		# Use None so this value stays in the cache indefinitely, till explicitly deleted
		# (or server restarts xD)
		cache_key = cache_video_key
		# cache_video_dict = cache.get_or_set(cache_key, {}, None)

		use_filename = shortuuid.uuid() + '.' + get_file_extension(file)
		mimetype = file.content_type
		root_save_path = os.path.join(MEDIA_ROOT, TEMP_FILES_UPLOAD_DIR, file.name)
		save_path = TEMP_FILES_UPLOAD_DIR + use_filename

		# If file is not in disk, save it. This is the case for TemporaryUploadedFiles.
		if not STORAGE.exists(save_path):
			print('not in storage')
			# Print something like "tmp/filename.ext"
			saved_filename = STORAGE.save(save_path, file)

			# AWS can construct urls to the file when given the filename. 
			# In our case, we need to be able to attach the file to a post when saving, so
			# we need the path in storage without MEDIA_ROOT
			path = STORAGE.url(saved_filename) if USE_S3 else save_path

		# Else if file is already in disk, rename it with custom name. 
		# This is the case for InMemoryUploadedFiles coz during validation, they need to be
		# saved to get duration, resolution, etc...
		else:
			print('in storage')
			new_root_save_path = os.path.join(MEDIA_ROOT, TEMP_FILES_UPLOAD_DIR, use_filename)
			os.rename(root_save_path, new_root_save_path)
			path = STORAGE.url(use_filename) if USE_S3 else save_path

		file_dict = {
			'filename': use_filename, 'mimetype': mimetype,
			'filepath': path, 'was_audio': False
		}
		cache.set(cache_key, file_dict, None)

		return VideoUploadMutation(**file_dict)
	   

class AudioUploadMutation(Output, graphene.Mutation):
	"""
	Upload an audio.
	Flow:
		- Audio is uploaded to backend. 
		- Compress audio(perhaps use bitrate 96k) then convert to video using custom image/images
		- Store filename, mimetype and filepath in cache and return them.
	"""

	class Arguments:
		file = Upload(required=True)

	filename = graphene.String()
	filepath = graphene.String()
	mimetype = graphene.String()
	was_audio = graphene.Boolean(default_value=True)
	 
	@classmethod
	@login_required
	def mutate(cls, root, info, file, **kwargs):
		user = info.context.user
		user_cache_keys = get_user_cache_keys(user.username)
		cache_photos_key, cache_video_key = user_cache_keys['photos'], user_cache_keys['video']

		# Validate cache content
		validate_cache_media(cache_photos_key, cache_video_key)

		# Validate audio file
		try:
			validate_post_audio_file(file)
		except ValidationError as err:
			raise GraphQLError(
				err.message % (err.params or {}),
				extensions={'code': err.code}
			)

		# Use None so this value stays in the cache indefinitely, till explicitly deleted
		# (or server restarts xD)
		cache_key = cache_video_key
	
		# Compress audio 
		# file.name also include extension
		audio_save_path = os.path.join(MEDIA_ROOT, TEMP_FILES_UPLOAD_DIR, file.name)
		audio = AudioSegment.from_mp3(get_file_path(file))
		audio.export(audio_save_path, bitrate='92k')
		# print(type(audio.export output)) # Prints '_io.BufferedRandom

		# Convert to video
		audio_path = audio_save_path
		cover_image_path = POST_COVER_IMG_DIR
		# /.../.../foo.mp4
		video_name = file.name.split('.')[0] + '.mp4'
		root_output_video_path = os.path.join(MEDIA_ROOT, TEMP_FILES_UPLOAD_DIR, video_name)

		# ['ffmpeg', '-loop', '1', '-i', cover_image_path, '-i', audio_path, '-c:a', 'copy', '-c:v', 'libx264', '-shortest', root_output_video_path]
		command = [
			'ffmpeg', '-loop', '1', '-i', cover_image_path, 
			'-i', audio_path, '-c:a', 'copy', '-c:v', 
			'libx264', '-shortest', root_output_video_path
		]

		# When using this method rather than the other ones (subprocess.call, run, etc..),
		# process execution isn't logged on the console.
		process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		process.communicate()

		# Rename file and store file info in cache
		use_filename = shortuuid.uuid() + '.mp4'
		save_path = TEMP_FILES_UPLOAD_DIR + use_filename
		new_root_save_path = os.path.join(MEDIA_ROOT, TEMP_FILES_UPLOAD_DIR, use_filename)
		os.rename(root_output_video_path, new_root_save_path)

		mimetype = file.content_type
		path = STORAGE.url(use_filename) if USE_S3 else save_path

		file_dict = {
			'filename': use_filename, 'mimetype': mimetype,
			'filepath': path, 'was_audio': True
		}
		cache.set(cache_key, file_dict, None)

		return AudioUploadMutation(**file_dict)
	   

class DeleteUploadedVideoMutation(Output, graphene.Mutation):
	"""Delete uploaded video(remove it from cache)"""

	@classmethod
	@login_required
	def mutate(cls, root, info, **kwargs):
		user_cache_keys = get_user_cache_keys(info.context.user.username)
		cache.delete(user_cache_keys['video'])

		return DeleteUploadedVideoMutation(success=True)


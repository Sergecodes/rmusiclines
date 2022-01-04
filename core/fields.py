"""All custom defined fields are placed here"""

from django.db import models
from django.db.models.fields.files import FieldFile, ImageFieldFile
from django.utils.translation import gettext_lazy as _

from .constants import FILE_STORAGE_CLASS


class DynamicStorageFieldFile(FieldFile):
	def __init__(self, instance, field, name):
		super().__init__(instance, field, name)
		self.storage = FILE_STORAGE_CLASS()


class DynamicStorageImageFieldFile(ImageFieldFile):
	def __init__(self, instance, field, name):
		super().__init__(instance, field, name)
		self.storage = FILE_STORAGE_CLASS()


class DynamicStorageFileField(models.FileField):
	"""
	Enable dynamically changing storage backend, 
	such as switching between AWS S3 and local storage.
	The model using this field should have a file or video field.
	"""
	attr_class = DynamicStorageFieldFile

	def pre_save(self, model_instance, add):
		self.storage = FILE_STORAGE_CLASS()
		
		if hasattr(model_instance, 'video'):
			model_instance.video.storage = self.storage
		else:
			model_instance.file.storage = self.storage

		file = super().pre_save(model_instance, add)
		return file


class DynamicStorageImageField(models.ImageField):
	"""
	Enable dynamically changing storage backend, 
	such as switching between AWS S3 and local storage
	"""
	attr_class = DynamicStorageImageFieldFile

	def pre_save(self, model_instance, add):
		self.storage = FILE_STORAGE_CLASS()
		model_instance.file.storage = self.storage

		file = super().pre_save(model_instance, add)
		return file
	


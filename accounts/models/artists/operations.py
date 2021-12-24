"""
Contains operations of the models in the artists module.
These classes will be used as mixins in the models.
"""

	
class ArtistOperations:
	"""Mixin for operations on the Artist model"""

	def get_photos(self, limit=None, **filters):
		# list[:None] will return the entire list
		return self.photos.filter(**filters)[:limit]


class ArtistTagOperations:
	"""Mixin for operations on the ArtistTag model"""

	def get_photos(self, limit=None, **filters):
		# list[:None] will return the entire list
		pass





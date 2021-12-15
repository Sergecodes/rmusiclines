from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Post(models.Model):
	# use all languages as choices here
	# active_language = models.CharField(choices=...)


	class Meta:
		abstract = True


class NonMusicianPost(Post):
	poster = models.ForeignKey
	# ...

	class Meta:
		# db_table = 
		pass


class MusicianPost(Post):
	pass

	class Meta:
		pass


class Comment(models.Model):
	poster = models.ForeignKey(
		User, 
		on_delete=models.CASCADE,
		related_name='comments',
		related_query_name='comment'
	)
	# ...

	class Meta:
		pass


class NonMusicianPostComment(Comment):
	pass

	class Meta: 
		pass


class MusicianPostComment(Comment):
	pass

	class Meta: 
		pass



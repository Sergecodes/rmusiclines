import datetime
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def get_age(birth_date: datetime.date):
    """Return age given date of birth"""
    # def age(self):
	# 	# Extract date from current time so as to . 
	# 	# Using just timezone.now() raises TypeError:
	# 	# unsupported operand type(s) for -: 'datetime.date' and 'datetime.datetime'
	# 	return (timezone.now().date() - self.birth_date) // datetime.timedelta(days=365)


    # see https://stackoverflow.com/q/2217488/age-from-birthdate-in-python/
    # see https://stackoverflow.com/q/5292303/how-does-tuple-comparison-work-in-python/
    # Recall: int(True) = 1, int(False) = 0
    today, born = datetime.date.today(), birth_date
    return today.year - born.year - (
        (today.month, today.day) < (born.month, born.day)
    )


def get_artist(artist_or_id):
    """If an id is passed, return corresponding artist, else return artist object"""
    from accounts.models.artists.models import Artist

    if isinstance(artist_or_id, int):
        id = artist_or_id
        return Artist.objects.get(id=id)
    elif isinstance(artist_or_id, Artist):
        artist = artist_or_id
        return artist
    else:
        raise ValidationError(
            _('Invalid type'),
            code='invalid'
        )


def get_user(user_or_id):
    """If an id is passed, return corresponding user, else return user object"""
    from django.contrib.auth import get_user_model

    User = get_user_model()

    if isinstance(user_or_id, int):
        id = user_or_id
        return User.objects.get(id=id)
    elif isinstance(user_or_id, User):
        user = user_or_id
        return user
    else:
        raise ValidationError(
            _('Invalid type'),
            code='invalid'
        )



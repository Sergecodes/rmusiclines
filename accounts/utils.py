import datetime


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


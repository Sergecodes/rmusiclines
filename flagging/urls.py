from django.urls import path

from .views import SetFlag


app_name = 'flagging'

urlpatterns = [
    path('', SetFlag.as_view(), name='flag'),
]

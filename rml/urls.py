from django.contrib import admin
from django.urls import path, include
from django.utils.translation import gettext_lazy as _

urlpatterns = [
    path('admin/', admin.site.urls),
    path(_('accounts/'), include('allauth.urls')),

]

# -*- coding: utf-8 -*-
from accounts.socialaccount.providers.auth0.provider import Auth0Provider
from accounts.socialaccount.providers.oauth2.urls import default_urlpatterns


urlpatterns = default_urlpatterns(Auth0Provider)

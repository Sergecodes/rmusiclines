from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.urls import path, include
from django.utils.translation import gettext_lazy as _


urlpatterns = [
	path('i18n/', include('django.conf.urls.i18n')),
	path('activity', include('actstream.urls')),
]

urlpatterns += i18n_patterns(
    path('admin/', admin.site.urls),
    path(_('accounts/'), include('allauth.urls')),

)


if not settings.USE_S3:
	from django.conf.urls.static import static

	urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


if settings.DEBUG:
	# import debug_toolbar

	# urlpatterns = [
	# 				  path('__debug__/', include(debug_toolbar.urls)),
	# 			  ] + urlpatterns
    pass

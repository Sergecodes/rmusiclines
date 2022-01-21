from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models.artists.models import (
    Artist, ArtistFollow, 
    ArtistTag, ArtistPhoto, 
)
from .models.users.models import (
    UserBlocking, UserFollow,
    Suspension, Settings, 
)

User = get_user_model()


## User-related models
class UserAdmin(BaseUserAdmin):
    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference specific fields on auth.User.
    list_display = (
        'id', 'username', 'display_name', 'email', 'num_followers', 'num_following', 
        'country', 'bio', 'birth_date', 'profile_picture', 'cover_photo', 'gender', 
        'joined_on', 'last_login', 'is_active', 'is_mod', 'is_staff', 'is_superuser',
        'is_verified', 'verified_on', 'is_premium', 'deactivated_on'
    )
    list_filter = (
        'username', 'country', 'gender', 
        'is_mod', 'is_verified', 'is_premium',
    )
    fieldsets = (
        (None, {'fields': (
                'username', 'email', 'display_name', 'country', 'gender', 
            )
        }),
        ('Permissions', {'fields': (
                'is_active', 'is_mod', 'is_staff', 
            )
        }),
    )
    # add_fieldsets is not a standard ModelAdmin attribute. UserAdmin
    # overrides get_fieldsets to use this attribute when creating a user.
    # add_fieldsets = (
    #     ('Personal information', {
    #         'classes': ('wide',),
    #         'fields': (
    #             'username', 'display_name', 'email', 
    #             'password1', 'password2', 'gender', 
    #         )}
    #     ),
    #     ('Site information', {
    #         'classes': ('wide', ),
    #         'fields': ('is_mod', 'is_staff', )
    #         }
    #     ),
    # )
    search_fields = (
        'email', 'display_name', 'first_language', 
        'gender', 'is_premium', 
    )
    ordering = ('username', 'country', 'joined_on', )
    date_hierarchy = 'joined_on'


class UserBlockingAdmin(admin.ModelAdmin):
    pass


class UserFollowAdmin(admin.ModelAdmin):
    pass


class SuspensionAdmin(admin.ModelAdmin):
    pass


class SettingsAdmin(admin.ModelAdmin):
    pass


admin.site.register(User, UserAdmin)
admin.site.register(UserBlocking, UserBlockingAdmin)
admin.site.register(UserFollow, UserFollowAdmin)
admin.site.register(Suspension, SuspensionAdmin)
admin.site.register(Settings, SettingsAdmin)


## Artist-related models
class ArtistAdmin(admin.ModelAdmin):
    readonly_fields = ['num_followers', 'num_posts', 'added_on', ]
    fieldsets = (
        ('', {
            'fields': (
                'name', 'country', 'gender', 'birth_date', 
            ), 
        }),
        ('Tags', {
            'classes': ('grp-collapse grp-open', ),
            'fields': ('tags', ),
        }),
    )
    # list_display = ['tag_list']
    date_hierarchy = 'added_on'
    ordering = ('name', 'num_followers', 'added_on', )

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('tags')

    def tag_list(self, obj):
        return ', '.join([o.name for o in obj.tags.all()])


class ArtistFollowAdmin(admin.ModelAdmin):
    pass


class ArtistPhotoAdmin(admin.ModelAdmin):
    pass


class ArtistTagAdmin(admin.ModelAdmin):
    pass


admin.site.register(Artist, ArtistAdmin)
admin.site.register(ArtistFollow, ArtistFollowAdmin)
admin.site.register(ArtistPhoto, ArtistPhotoAdmin)
admin.site.register(ArtistTag, ArtistTagAdmin)

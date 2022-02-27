from django.contrib.auth.models import (
    Permission, 
    UserManager as BaseUserManager
)
from django.db.models.query import QuerySet
from django.utils import timezone

from accounts.models.artists.models import Artist, ArtistPhoto
from core.utils import get_content_type


class UserQuerySet(QuerySet):
    def delete(self, really_delete=False):
        if really_delete:
            return super().delete()
        else:
            self.deactivate()

    def deactivate(self):
        self.update(is_active=False, deactivated_on=timezone.now())


class UserManager(BaseUserManager):
    def get_queryset(self):
        return UserQuerySet(self.model, using=self._db)

    def create_user(
        self, username, email, password, 
        display_name, birth_date, country,  
        **extra_fields
    ):  
        from accounts.models.users.models import UserType

        user = self.model(
            username=username, 
            email=email, 
            display_name=display_name,
            birth_date=birth_date,
            country=country,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)

        # Save corresponding type
        UserType.objects.create(user=user)
            
        return user

    def create_staff_user(
        self, username, email, password, display_name, 
        birth_date, country, **extra_fields
    ):
        from accounts.models.users.models import UserType

        extra_fields.setdefault('is_staff', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Staff must have is_staff=True.')

        staff_user = self.create_user(
            username, email, password, 
            display_name, birth_date, country, 
            **extra_fields
        )

        # Mark staff as moderator
        UserType.objects.create(user=staff_user, is_mod=True)
        
        # Get and set CUD(Create-Update-Delete) artist & artist photo operations permissions
        cud_artist_permissions = Permission.objects.filter(
            content_type=get_content_type(Artist)
        ).exclude(codename='view_artist')

        cud_artist_photo_permissions = Permission.objects.filter(
            content_type=get_content_type(ArtistPhoto)
        ).exclude(codename='view_artistphoto')

        perms = [cud_artist_permissions, cud_artist_photo_permissions]
        staff_user.user_permissions.set(perms)


    def create_superuser(
        self, username, email, password, display_name, 
        birth_date, country, **extra_fields
    ):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_staff_user(
            username, email, password, 
            display_name, birth_date, country, 
            **extra_fields
        )


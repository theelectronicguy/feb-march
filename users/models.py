import uuid
from datetime import timedelta

from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.translation import ugettext_lazy as _

from jellyfish_ams.utilities.model_mixins import Timestampable
from users.managers import UserManager


class User(PermissionsMixin, AbstractBaseUser, Timestampable):
    USERNAME_FIELD = 'email'
    # For the createsuperuser command only.
    objects = UserManager()

    uuid = models.UUIDField(
        default=uuid.uuid4,
        unique=True
    )

    first_name = models.CharField(
        _('first name'),
        max_length=255)

    last_name = models.CharField(
        _('last name'),
        max_length=255)

    email = models.EmailField(
        _('email address'), unique=True, null=False, blank=False)

    # ['DEVELOPER', 'QA', 'CEO', 'DESIGNER', 'PROJECT MANAGER', 'HR']
    designation = models.CharField(null=True, blank=True,
                                   max_length=255)
    technologies = models.CharField(null=True, blank=True,
                                    max_length=255)
    # ['EMPLOYEE', 'MANAGER', 'ADMIN']
    type = models.CharField(null=True, blank=True,
                            max_length=255)

    # SETTINGS

    is_staff = models.BooleanField(
        _('is staff'),
        default=False
    )

    is_active = models.BooleanField(
        _('is active'),
        default=False
    )

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return f"{self.first_name} – {self.email}"

    # pylint: disable=arguments-differ
    def save(self, *args, **kwargs):
        # print("hello")
        super().save(*args, **kwargs)

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"


class PasswordResetToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    token = models.CharField(max_length=255, unique=True, blank=True)

    created_at = models.DateTimeField(default=timezone.now)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if not self.id:
            self.token = get_random_string(length=50)
        super(PasswordResetToken, self).save(
            force_insert, force_update, using, update_fields
        )
        pass

    def is_expired(self):
        delta = timezone.now() - self.created_at
        return delta > timedelta(hours=48)

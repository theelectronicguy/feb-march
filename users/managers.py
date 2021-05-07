from django.contrib.auth.base_user import BaseUserManager
# from django.contrib.auth.models import Group
# from django.contrib.postgres.search import TrigramSimilarity


class UserManager(BaseUserManager):
    def create_user(self, email, password, **extra_fields):
        """
        Creates and saves a User with the given username, email and password.
        """
        if not email:
            raise ValueError('Users must have email')

        user = self.model.objects.create(
            email=self.normalize_email(email),
            **extra_fields
        )

        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        """
        Creates and saves a superuser with the given username, email and password.
        """
        user = self.create_user(
            email, password, **extra_fields
        )
        user.is_superuser = True
        user.is_staff = True
        user.is_active = True
        user.save()
        # group = Group.objects.annotate(similarity=TrigramSimilarity('name', 'super')).get(similarity__gt=0.3)
        # user.groups.add(group)
        return user

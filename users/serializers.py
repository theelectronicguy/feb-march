from django.db import IntegrityError
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from users.models import User


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Add custom claims
        # token['username'] = user.email
        return token


class BulkCreateUserImportListSerializer(serializers.ListSerializer):
    def create(self, validated_data):
        result = [self.child.create(attrs) for attrs in validated_data]

        try:
            self.child.Meta.model.objects.bulk_create(result)
        except:
            raise ValidationError()
        return result


class UserImportSerializer(serializers.ModelSerializer):
    password = serializers.CharField(required=False)

    def create(self, validated_data):
        instance = User(**validated_data)

        if isinstance(self._kwargs["data"], dict):
            instance.save()

        return instance

    def update(self, instance, validated_data):
        pass

    class Meta:
        model = User
        fields = '__all__'
        list_serializer_class = BulkCreateUserImportListSerializer

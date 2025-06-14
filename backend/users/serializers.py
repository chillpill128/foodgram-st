from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _
from rest_framework.serializers import ModelSerializer, Serializer
from rest_framework.validators import UniqueValidator
from rest_framework import serializers

from .models import User
from common.utils import Base64ImageField, RegexValidator
from recipes.serializers_short import RecipeShortenSerializer


class UserViewSerializer(ModelSerializer):
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'avatar']

    def get_avatar(self, obj):
        if obj.avatar:
            return self.context['request'].build_absolute_uri(obj.avatar.url)
        return None




class UserAddSerializer(ModelSerializer):
    username = serializers.CharField(max_length=150, required=True,
                                     validators=[RegexValidator,
                                                 UniqueValidator(
                                         queryset=User.objects.all()
                                     )])
    email = serializers.EmailField(max_length=254, required=True,
                                   validators=[UniqueValidator(
                                       queryset=User.objects.all()
                                   )])
    first_name = serializers.CharField(max_length=150, required=True)
    last_name = serializers.CharField(max_length=150, required=True)
    password = serializers.CharField(max_length=128, write_only=True)

    class Meta:
        model = User
        fields = ['email', 'id', 'username', 'first_name',
                  'last_name', 'password']
        read_only_fields = ['id']

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = super().create(validated_data)
        user.set_password(password)
        user.save()
        return user


class UserWithRecipesSerializer(ModelSerializer):
    recipes = RecipeShortenSerializer(many=True)
    # recipes_count = serializers.IntegerField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'recipes', 'avatar']

    def get_avatar(self, obj):
        if obj.avatar:
            return self.context['request'].build_absolute_uri(obj.avatar.url)
        return None



class PasswordChangeSerializer(Serializer):
    new_password = serializers.CharField(max_length=128)
    current_password = serializers.CharField(max_length=128)


# Изменённая версия rest_framework.authtoken.serializers.AuthTokenSerializer
# Вместо username используем email
class GetTokenSerializer(Serializer):
    password = serializers.CharField(max_length=128, write_only=True)
    email = serializers.EmailField(max_length=150, write_only=True)
    auth_token = serializers.CharField(source='key', read_only=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = authenticate(request=self.context.get('request'),
                                email=email, password=password)
            if not user:
                msg = _('Unable to log in with provided credentials.')
                raise serializers.ValidationError(msg, code='authorization')
        else:
            msg = _('Must include "username" and "password".')
            raise serializers.ValidationError(msg, code='authorization')

        attrs['user'] = user
        return attrs


class AvatarUploadSerializer(ModelSerializer):
    avatar = Base64ImageField(required=True)

    class Meta:
        model = User
        fields = ['avatar']


class AvatarViewSerializer(ModelSerializer):
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['avatar']

    def get_avatar(self, obj):
        if obj.avatar:
            return self.context['request'].build_absolute_uri(obj.avatar.url)
        return None

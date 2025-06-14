from rest_framework.serializers import ModelSerializer
from rest_framework import serializers

from .models import Recipe


class RecipeShortenSerializer(ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ['id', 'name', 'image', 'cooking_time']

    def get_image(self, obj):
        if obj.image:
            return self.context['request'].build_absolute_uri(obj.image.url)
        return None


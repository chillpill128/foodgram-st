from rest_framework.serializers import ModelSerializer
from rest_framework import serializers

from users.serializers import UserViewSerializer
from common.utils import Base64ImageField
from .models import Ingredient, Recipe, RecipeIngredients


class IngredientSerializer(ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'


class RecipeIngredientSerializer(ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredients
        fields = ['id', 'name', 'measurement_unit', 'amount']


class RecipeViewSerializer(ModelSerializer):
    author = UserViewSerializer()
    ingredients = RecipeIngredientSerializer(
        source='recipeingredients', many=True, read_only=True
    )
    image = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields =  ['id', 'author', 'ingredients', 'is_favorited',
                   'is_in_shopping_cart', 'name', 'image', 'text',
                   'cooking_time']

    def get_image(self, obj):
        if obj.image:
            return self.context['request'].build_absolute_uri(obj.image.url)
        return None

    def get_is_favorited(self, obj):
        return hasattr(obj, 'is_favorited') and obj.is_favorited

    def get_is_in_shopping_cart(self, obj):
        return hasattr(obj, 'is_in_shopping_cart') and obj.is_in_shopping_cart


class RecipeIngredientAddSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    amount = serializers.IntegerField(min_value=1)


class RecipeChangeSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientAddSerializer(many=True, source='recipeingredients',
                                                required=True)
    image = Base64ImageField(required=True)

    class Meta:
        model = Recipe
        fields = ('ingredients', 'image', 'name', 'text', 'cooking_time')
        extra_kwargs = {
            'name': {'required': True},
            'text': {'required': True},
            'ingredients': {'required': True},
            'cooking_time': {'required': True, 'min_value': 1}
        }

    def create(self, validated_data):
        ingredients_data = validated_data.pop('recipeingredients', None)
        author = self.context['request'].user
        recipe = Recipe.objects.create(author=author, **validated_data)

        for ingredient in ingredients_data:
            RecipeIngredients.objects.create(
                recipe=recipe,
                ingredient_id=ingredient['id'],
                amount=ingredient['amount']
            )
        return recipe


class RecipeShortLinkSerializer(ModelSerializer):
    short_link = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ['short_link']

    def get_short_link(self, obj):
        return self.context['request'].build_absolute_uri(f'/s/{obj.short_link}')

from rest_framework.serializers import ModelSerializer
from rest_framework import serializers

from recipes.models import Ingredient, Recipe, RecipeIngredients
from .fields import Base64ImageField
from .users import UserSerializer


class IngredientSerializer(ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'


class RecipeIngredientViewSerializer(ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredients
        fields = ['id', 'name', 'measurement_unit', 'amount']
        read_only_fields = fields


class RecipeViewSerializer(ModelSerializer):
    author = UserSerializer()
    ingredients = RecipeIngredientViewSerializer(
        source='recipeingredients', many=True, read_only=True
    )
    image = serializers.ImageField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields =  ['id', 'author', 'ingredients', 'is_favorited',
                   'is_in_shopping_cart', 'name', 'image', 'text',
                   'cooking_time']
        read_only_fields = fields

    def get_is_favorited(self, obj):
        return bool(hasattr(obj, 'is_favorited') and obj.is_favorited)

    def get_is_in_shopping_cart(self, obj):
        return bool(hasattr(obj, 'is_in_shopping_cart') and obj.is_in_shopping_cart)


class RecipeIngredientAddSerializer(RecipeIngredientViewSerializer):
    id = serializers.PrimaryKeyRelatedField(source='ingredient.id',
                                            queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(min_value=1)

    class Meta:
        model = RecipeIngredients
        fields = ['id', 'name', 'measurement_unit', 'amount']
        read_only_fields = ['name', 'measurement_unit']


class RecipeChangeSerializer(RecipeViewSerializer):
    author = UserSerializer(read_only=True)
    ingredients = RecipeIngredientAddSerializer(
        many=True, source='recipeingredients', required=True
    )
    image = Base64ImageField(required=True)

    class Meta:
        model = Recipe
        fields =  ['id', 'author', 'ingredients', 'is_favorited',
                   'is_in_shopping_cart', 'name', 'image', 'text',
                   'cooking_time']
        read_only_fields = ['id', 'author', 'is_favorited', 'is_in_shopping_cart']

    def validate_ingredients(self, value):
        ids = [item['ingredient']['id'].id for item in value]
        if len(ids) != len(set(ids)):
            raise serializers.ValidationError('Ингредиенты не должны повторяться.')
        return value

    def validate(self, attrs):
        recipeingredients = attrs.get('recipeingredients', None)
        if not recipeingredients:
            raise serializers.ValidationError('Отсутствуют ингредиенты')
        self.validate_ingredients(recipeingredients)
        return attrs

    def create(self, validated_data):
        recipeingredients = validated_data.pop('recipeingredients', None)
        validated_data['author'] = self.context['request'].user
        recipe = super().create(validated_data)
        self.set_recipe_ingredients(recipe, recipeingredients)
        return recipe

    def update(self, instance, validated_data):
        recipeingredients = validated_data.pop('recipeingredients', [])
        instance = super().update(instance, validated_data)
        self.set_recipe_ingredients(instance, recipeingredients)
        return instance

    def set_recipe_ingredients(self, recipe, recipeingredients):
        recipe.recipeingredients.all().delete()
        ingredients = [RecipeIngredients(
            recipe=recipe,
            ingredient=recipe_ingredient['ingredient']['id'],
            amount=recipe_ingredient['amount']
        ) for recipe_ingredient in recipeingredients]
        RecipeIngredients.objects.bulk_create(ingredients)

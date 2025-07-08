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
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields =  ['id', 'author', 'ingredients', 'is_favorited',
                   'is_in_shopping_cart', 'name', 'image', 'text',
                   'cooking_time']
        read_only_fields = fields

    def get_is_favorited(self, obj):
        return hasattr(obj, 'is_favorited') and obj.is_favorited

    def get_is_in_shopping_cart(self, obj):
        return hasattr(obj, 'is_in_shopping_cart') and obj.is_in_shopping_cart


class RecipeIngredientAddSerializer(ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(source='ingredient.id',
                                            queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(min_value=1)

    # Поля name и measurement_unit требуются для отображения ингредиента
    # В списке рецептов в ответе после его добавления/изменения.
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredients
        fields = ['id', 'name', 'measurement_unit', 'amount']
        read_only_fields = ['name', 'measurement_unit']


class RecipeChangeSerializer(ModelSerializer):
    ingredients = RecipeIngredientAddSerializer(
        many=True, source='recipeingredients', required=True
    )
    image = Base64ImageField(required=True)
    cooking_time = serializers.IntegerField(min_value=1, required=True)

    # Поля требуются для ответа после добавления/изменения рецепта.
    # Раньше были переопределены методы create/update у RecipeView, сейчас
    # используются стандартные от DRF.
    # https://github.com/yandex-praktikum/foodgram-st/blob/main/docs/openapi-schema.yml
    # стр. 153
    # responses: ...
    # schema:
    # $ref: '#/components/schemas/RecipeList'
    # стр. 799 (сокращено)
    # RecipeList:
    #     id: type: integer
    #     author: $ref: '#/components/schemas/User'
    #     ingredients: type: array $ref: '#/components/schemas/IngredientInRecipe'
    #     is_favorited: type: boolean
    #     is_in_shopping_cart: type: boolean
    #     name: type: string maxLength: 256
    #     image: type: string format: uri
    #     text: type: string
    #     cooking_time: type: integer minimum: 1
    # стр. 888 (сокращено)
    # IngredientInRecipe:
    #     id:  type: integer
    #     name:  type: string  maxLength: 128
    #     measurement_unit:  type: string  maxLength: 64
    #     amount:  type: integer  minimum: 1
    author = UserSerializer(read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields =  ['id', 'author', 'ingredients', 'is_favorited',
                   'is_in_shopping_cart', 'name', 'image', 'text',
                   'cooking_time']
        read_only_fields = ['id', 'author', 'is_favorited', 'is_in_shopping_cart']

    def get_is_favorited(self, obj):
        return hasattr(obj, 'is_favorited') and obj.is_favorited

    def get_is_in_shopping_cart(self, obj):
        return hasattr(obj, 'is_in_shopping_cart') and obj.is_in_shopping_cart

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
        self.set_recipe_ingredients(instance, recipeingredients)
        return super().update(instance, validated_data)

    def set_recipe_ingredients(self, recipe, recipeingredients):
        recipe.recipeingredients.all().delete()
        RecipeIngredients.objects.bulk_create([RecipeIngredients(
            recipe=recipe,
            ingredient=recipe_ingredient['ingredient']['id'],
            amount=recipe_ingredient['amount']
        ) for recipe_ingredient in recipeingredients])

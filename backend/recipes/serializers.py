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
        return bool(hasattr(obj, 'is_favorited') and obj.is_favorited)

    def get_is_in_shopping_cart(self, obj):
        return bool(hasattr(obj, 'is_in_shopping_cart') and obj.is_in_shopping_cart)


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

    def validate_recipeingredients(self, value):
        ids = [item['id'] for item in value]
        if len(ids) != len(set(ids)):
            raise serializers.ValidationError('Ингредиенты не должны повторяться.')
        ids_from_db = set(Ingredient.objects.filter(id__in=ids)
                          .values_list('id', flat=True))
        if set(ids) != ids_from_db:
            raise serializers.ValidationError('Ингредиенты должны существовать.')
        return value

    def validate(self, attrs):
        recipeingredients = attrs.get('recipeingredients', None)
        if not recipeingredients:
            raise serializers.ValidationError('Отсутствуют ингредиенты')
        self.validate_recipeingredients(recipeingredients)
        return attrs

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

    def update(self, instance, validated_data):
        recipeingredients_data = validated_data.pop('recipeingredients', [])

        instance = super().update(instance, validated_data)

        recipeingredients_db = RecipeIngredients.objects.filter(recipe=instance)

        ids_data = set(item['id'] for item in recipeingredients_data)
        ids_db = set(item.ingredient_id for item in recipeingredients_db)

        ids_to_add = ids_data - ids_db
        ids_to_del = ids_db - ids_data
        ids_to_check = ids_data & ids_db

        ids_amounts = {item['id']: item['amount']
                      for item in recipeingredients_data}

        # Добавляем в БД записи, которых там ещё нет:
        recipeingredients = []
        for id in ids_to_add:
            amount = ids_amounts[id]
            item = RecipeIngredients(
                recipe=instance, ingredient_id=id, amount=amount
            )
            recipeingredients.append(item)
        RecipeIngredients.objects.bulk_create(recipeingredients)

        # Разбираемся с удалением и изменением имеющихся в бд записей:
        recipeingredients = []
        for item in recipeingredients_db:
            if item.ingredient_id in ids_to_del:
                item.delete()
            if (item.ingredient_id in ids_to_check and
                    item.amount != ids_amounts[item.ingredient_id]):
                item.amount = ids_amounts[item.ingredient_id]
                recipeingredients.append(item)
        RecipeIngredients.objects.bulk_update(recipeingredients, ['amount'])

        return instance


class RecipeShortLinkSerializer(ModelSerializer):
    short_link = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ['short_link']

    def get_short_link(self, obj):
        return self.context['request'].build_absolute_uri(f'/s/{obj.short_link}')

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if 'short_link' in data:
            data['short-link'] = data.pop('short_link')
        return data

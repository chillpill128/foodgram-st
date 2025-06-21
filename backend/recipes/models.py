from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator


# from common.utils import generate_short_link, generate_random_short_link


class Ingredient(models.Model):
    name = models.CharField('Название')
    measurement_unit = models.CharField('единица измерения')

    class Meta:
        verbose_name = 'Ингридиент'
        verbose_name_plural = 'Ингридиенты'


class Recipe(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL,
                               on_delete=models.CASCADE,
                               verbose_name='Автор')
    ingredients = models.ManyToManyField(Ingredient,
                                         verbose_name='Ингридиенты',
                                         through='RecipeIngredients')
    name = models.CharField('Название', max_length=256)
    image = models.ImageField('Картинка')
    text = models.TextField('Описание')
    cooking_time = models.PositiveIntegerField('Время приготовления',
                                               validators=[MinValueValidator(1)])
    # short_link = models.CharField('Короткая ссылка', max_length=10,
    #                               unique=True)
    created_at = models.DateTimeField('Создан', auto_now_add=True)
    updated_at = models.DateTimeField('Изменён', auto_now=True)

    class Meta:
        default_related_name = 'recipes'
        indexes = [
            models.Index(fields=['created_at']),
        ]
        ordering = ['-created_at']
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    # def _generate_short_link(self):
    #     for num in range(3, 10):
    #         short_link = generate_short_link(self.pk, num)
    #         if not Recipe.objects.filter(short_link=short_link).exists():
    #             return short_link
    #     while True:
    #         short_link = generate_random_short_link(10)
    #         if not Recipe.objects.filter(short_link=short_link).exists():
    #             return short_link
    #
    # def save(self, force_insert=False, force_update=False,
    #          using=None, update_fields=None):
    #     if not self.short_link:
    #         self.short_link = self._generate_short_link()
    #     super().save(force_insert=force_insert, force_update=force_update,
    #                  using=using, update_fields=update_fields)


class RecipeIngredients(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    amount = models.PositiveIntegerField('Количество', default=1)

    class Meta:
        constraints = [models.UniqueConstraint(
            fields=['recipe', 'ingredient'],
            name='unique_recipe_ingredient_in_recipeingredients'
        )]
        default_related_name = 'recipeingredients'
        verbose_name = 'Ингридиент в рецепте'
        verbose_name_plural = 'Ингридиенты в рецептах'


class ShoppingCart(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)

    class Meta:
        constraints = [models.UniqueConstraint(
            fields=['user', 'recipe'],
            name='unique_user_recipe_in_shopping_cart'
        )]
        default_related_name = 'shopping_carts'
        verbose_name = 'Рецепт в корзине'
        verbose_name_plural = 'Рецепты в корзине'


class FavoriteRecipe(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='favorite',
                             on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe,
                               on_delete=models.CASCADE)

    class Meta:
        constraints = [models.UniqueConstraint(
            fields=['user', 'recipe'],
            name='unique_user_recipe_in_shopping_cart'
        )]
        default_related_name = 'favorites'
        verbose_name = 'Рецепт в избранном'
        verbose_name_plural = 'Рецепты в избранном'

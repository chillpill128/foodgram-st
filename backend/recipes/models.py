from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from .utils import generate_short_link


class Ingredient(models.Model):
    name = models.CharField(_('Название'))
    measurement_unit = models.CharField(_('единица измерения'))

    class Meta:
        verbose_name = _('Ингридиент')
        verbose_name_plural = _('Ингридиенты')


class Recipe(models.Model):
    author = models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    ingredients = models.ManyToManyField(to=Ingredient,
                                         related_name='recipes',
                                         verbose_name=_('Ингридиенты'),
                                         through='RecipeIngredients')
    is_favorited = models.BooleanField(_('В избранном'), default=False)
    is_in_shopping_cart = models.BooleanField(_('В корзине'), default=False)
    name = models.CharField(_('Название'), max_length=256)
    image = models.ImageField(_('Картинка'))
    text = models.TextField(_('Описание'))
    cooking_time = models.PositiveIntegerField(_('Время приготовления'))
    short_link = models.CharField(_('Короткая ссылка'), max_length=10,
                                  unique=True)

    def _generate_short_link(self):
        for num in range(3, 10):
            short_link = generate_hash_part(self.pk, num)
            if not Recipe.objects.filter(short_link=short_link).exists():
                return short_link

    def save(self, force_insert=False, force_update=False,
             using=None, update_fields=None):
        if not self.short_link:
            self.short_link = self._generate_short_link()
        super().save(force_insert=force_insert, force_update=force_update,
                     using=using, update_fields=update_fields)

    class Meta:
        verbose_name = _('Рецепт')
        verbose_name_plural = _('Рецепты')


class RecipeIngredients(models.Model):
    recipe = models.ForeignKey(Recipe, related_name='recipeingredients',
                               on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, related_name='recipeingredients',
                                   on_delete=models.CASCADE)
    amount = models.PositiveIntegerField(_('Количество'), default=1)

    class Meta:
        unique_together = ['recipe', 'ingredient']
        verbose_name = _('Ингридиент в рецепте')
        verbose_name_plural = _('Ингридиенты в рецептах')


class ShoppingCart(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             related_name='shopping_cart',
                             on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, related_name='shopping_cart',
                               on_delete=models.CASCADE)

    class Meta:
        unique_together = ['user', 'recipe']
        verbose_name = _('Рецепт в корзине')
        verbose_name_plural = _('Рецепты в корзине')


class FavoriteRecipe(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='favorite',
                             on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, related_name='favorite',
                               on_delete=models.CASCADE)

    class Meta:
        unique_together = ['user', 'recipe']
        verbose_name = _('Рецепт в избранном')
        verbose_name_plural = _('Рецепты в избранном')

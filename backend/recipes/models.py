from django.db import models
from django.core.validators import MinValueValidator, RegexValidator
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    username = models.CharField(
        max_length=150, unique=True,
        validators=[RegexValidator(regex=r'^[\w+-.@]+$')]
    )
    email = models.EmailField('Электронная почта', max_length=254,
                              unique=True)
    first_name = models.CharField('Имя', max_length=150)
    last_name = models.CharField('Фамилия', max_length=150)
    avatar = models.ImageField('Аватар', default=None, null=True,
                               upload_to='avatars')

    class Meta:
        ordering = ['email']
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return f'{self.first_name} {self.last_name} ({self.email})'


class Subscription(models.Model):
    author = models.ForeignKey(User, verbose_name='Автор',
                               on_delete=models.CASCADE,
                               related_name='subscriptions_author')
    follower = models.ForeignKey(User, verbose_name='Подписчик',
                                 on_delete=models.CASCADE,
                                 related_name='subscriptions_follower')
    class Meta:
        constraints = [models.UniqueConstraint(
            fields=['author', 'follower'],
            name='unique_author__follower'
        )]
        ordering = ['author', 'follower']
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        return f'{self.follower.username} подписан на {self.author.username}'



class Ingredient(models.Model):
    name = models.CharField('Название', max_length=128)
    measurement_unit = models.CharField('единица измерения', max_length=64)

    class Meta:
        constraints = [models.UniqueConstraint(
            fields=['name', 'measurement_unit'],
            name='unique_name__measurement_unit'
        )]
        ordering = ['name']
        verbose_name = 'Ингридиент'
        verbose_name_plural = 'Ингридиенты'

    def __str__(self):
        return f'{self.name} ({self.measurement_unit})'


class Recipe(models.Model):
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               verbose_name='Автор')
    ingredients = models.ManyToManyField(Ingredient,
                                         verbose_name='Ингридиенты',
                                         through='RecipeIngredients')
    name = models.CharField('Название', max_length=256)
    image = models.ImageField('Картинка', upload_to='images')
    text = models.TextField('Описание')
    cooking_time = models.PositiveIntegerField('Время приготовления',
                                               validators=[MinValueValidator(1)])
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

    def __str__(self):
        return f'{self.name} (автор: {self.author})'


class RecipeIngredients(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    amount = models.PositiveIntegerField('Количество', default=1,
                                         validators=[MinValueValidator(1)])

    class Meta:
        constraints = [models.UniqueConstraint(
            fields=['recipe', 'ingredient'],
            name='unique_recipe__ingredient'
        )]
        default_related_name = 'recipeingredients'
        ordering = ['recipe', 'ingredient']
        verbose_name = 'Ингридиент в рецепте'
        verbose_name_plural = 'Ингридиенты в рецептах'

    def __str__(self):
        return f'{self.recipe.name} {self.ingredient.name}' + \
               f' ({self.amount} {self.ingredient.measurement_unit})'


class UserRecipeBase(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             verbose_name='Пользователь')
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE,
                               verbose_name='Рецепт')

    class Meta:
        abstract = True

    def __str__(self):
        return f'{self.user.first_name} {self.user.last_name} - {self.recipe.name}'


class ShoppingCart(UserRecipeBase):
    class Meta:
        ordering = ['user', 'recipe']
        constraints = [models.UniqueConstraint(
            fields=['user', 'recipe'],
            name='unique_user__recipe__in__shopping_cart'
        )]
        default_related_name = 'shopping_carts'
        verbose_name = 'Рецепт в корзине'
        verbose_name_plural = 'Рецепты в корзине'


class FavoriteRecipe(UserRecipeBase):
    class Meta:
        ordering = ['user', 'recipe']
        constraints = [models.UniqueConstraint(
            fields=['user', 'recipe'],
            name='unique_user__recipe__in_favorite_recipe'
        )]
        default_related_name = 'favorites'
        verbose_name = 'Рецепт в избранном'
        verbose_name_plural = 'Рецепты в избранном'

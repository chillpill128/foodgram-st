# Generated by Django 5.2.3 on 2025-07-01 12:33

import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0009_subscription_alter_favoriterecipe_options_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='favoriterecipe',
            options={'default_related_name': 'favorites', 'ordering': ['user', 'recipe'], 'verbose_name': 'Рецепт в избранном', 'verbose_name_plural': 'Рецепты в избранном'},
        ),
        migrations.AlterModelOptions(
            name='shoppingcart',
            options={'default_related_name': 'shopping_carts', 'ordering': ['user', 'recipe'], 'verbose_name': 'Рецепт в корзине', 'verbose_name_plural': 'Рецепты в корзине'},
        ),
        migrations.RemoveField(
            model_name='user',
            name='authors',
        ),
        migrations.AlterField(
            model_name='subscription',
            name='author',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='followers', to=settings.AUTH_USER_MODEL, verbose_name='Автор'),
        ),
        migrations.AlterField(
            model_name='subscription',
            name='follower',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='authors', to=settings.AUTH_USER_MODEL, verbose_name='Подписчик'),
        ),
        migrations.AlterField(
            model_name='user',
            name='email',
            field=models.EmailField(max_length=254, unique=True, verbose_name='Электронная почта'),
        ),
        migrations.AlterField(
            model_name='user',
            name='username',
            field=models.CharField(max_length=150, unique=True, validators=[django.core.validators.RegexValidator(regex='^[\\w+-.@]+$')]),
        ),
        migrations.AddConstraint(
            model_name='favoriterecipe',
            constraint=models.UniqueConstraint(fields=('user', 'recipe'), name='unique_user__recipe__in_favorite_recipe'),
        ),
        migrations.AddConstraint(
            model_name='shoppingcart',
            constraint=models.UniqueConstraint(fields=('user', 'recipe'), name='unique_user__recipe__in__shopping_cart'),
        ),
    ]

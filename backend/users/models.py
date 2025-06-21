from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    email = models.EmailField('Электронная почта', max_length=255,
                              unique=True)
    avatar = models.ImageField('Аватар', default=None, null=True,
                               upload_to='avatars')

    authors = models.ManyToManyField('self', verbose_name='Авторы',
                                     related_name='followers',
                                     through='Subscription',
                                     through_fields='follower')
    followers = models.ManyToManyField('self', verbose_name='Подписчики',
                                       related_name='authors',
                                       through='Subscription',
                                       through_fields='author')

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'


class Subscription(models.Model):
    author = models.ForeignKey(User, verbose_name='Автор',
                               on_delete=models.CASCADE,
                               related_name='subscriptions_on_me')
    follower = models.ForeignKey(User, verbose_name='Подписчик',
                                 on_delete=models.CASCADE,
                                 related_name='subscriptions_my')

    class Meta:
        constraints = [models.UniqueConstraint(
            fields=['author', 'follower'],
            name='unique_author_follower_in_subscriptions'
        )]
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

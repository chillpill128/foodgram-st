from django.db import models
from django.utils.translation import gettext_lazy as _

from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    email = models.EmailField(max_length=255, unique=True)
    is_subscribed = models.BooleanField(_('Подписан'), default=False)
    avatar = models.ImageField(_('Аватар'), default=None, null=True, upload_to='avatars')

    class Meta:
        verbose_name = _('Пользователь')
        verbose_name_plural = _('Пользователи')


class Subscription(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions_on_me')
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions_my')

    class Meta:
        unique_together = ['author', 'follower']
        verbose_name = _('Подписка')
        verbose_name_plural = _('Подписки')

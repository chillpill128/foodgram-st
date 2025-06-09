from django.db import models
from django.utils.translation import gettext_lazy as _

from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    is_subscribed = models.BooleanField(_('Подписан'), default=False)
    avatar = models.ImageField(_('Аватар'), default=None, null=True)

    class Meta:
        verbose_name = _('Пользователь')
        verbose_name_plural = _('Пользователи')


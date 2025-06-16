import base64
import hashlib
import random
import re
import string
from django.core.files.base import ContentFile
from rest_framework import serializers


def generate_short_link(value, letters=3):
    value = str(value).encode()
    hash_bytes = hashlib.sha256(value).digest()
    return (base64.urlsafe_b64encode(hash_bytes)
            .decode()
            .replace('=', '')
            .replace('_', ''))[:letters]


def generate_random_short_link(letters=6):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(letters))


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            # Извлекаем расширение файла и декодируем base64
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            filename = generate_random_short_link(30)
            filename = f"{filename}.{ext}"
            decoded_file = base64.b64decode(imgstr)
            data = ContentFile(decoded_file, name=filename)

        return super().to_internal_value(data)


class RegexValidator:
    def __init__(self, pattern=r'^[\w\S]+$', flags=re.IGNORECASE):
        self.regex = re.compile(pattern, flags)

    def __call__(self, value):
        if not isinstance(value, str) or not (self.regex.fullmatch(value)):
            message = f'Недопустимое значение: {value}'
            raise serializers.ValidationError(message)


import base64
import hashlib
from django.core.files.base import ContentFile
from rest_framework import serializers


def generate_short_link(value, letters_number):
    value = str(value).encode()
    hash_bytes = hashlib.sha256(value).digest()[:letters_number]
    return (base64.urlsafe_b64encode(hash_bytes)
            .decode()
            .replace('=', '')
            .replace('_', ''))


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(
                base64.b64decode(imgstr),
                name=f'temp.{ext}'
            )
        return super().to_internal_value(data)

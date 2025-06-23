import base64
from django.core.files.base import ContentFile
from rest_framework import serializers

from recipes.utils import generate_random_string


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            filename = generate_random_string(30)
            filename = f"{filename}.{ext}"
            decoded_file = base64.b64decode(imgstr)
            data = ContentFile(decoded_file, name=filename)

        return super().to_internal_value(data)


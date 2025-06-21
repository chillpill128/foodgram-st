import random
import string
# import base64
# import hashlib
# from django.core.files.base import ContentFile
# from rest_framework import serializers


# def generate_short_link(value, letters=3):
#     value = str(value).encode()
#     hash_bytes = hashlib.sha256(value).digest()
#     return (base64.urlsafe_b64encode(hash_bytes)
#             .decode()
#             .replace('=', '')
#             .replace('_', ''))[:letters]


def generate_random_string(letters=6):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(letters))





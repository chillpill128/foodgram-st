import random
import string


def generate_random_string(letters=6):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(letters))


# Алфавит для Base62 (0-9, A-Z, a-z)
BASE62 = string.digits + string.ascii_letters
BASE = len(BASE62)


def encode_base62(num: int) -> str:
    """Кодирует число в Base62."""
    if num == 0:
        return BASE62[0]
    encoded = []
    while num > 0:
        num, rem = divmod(num, BASE)
        encoded.append(BASE62[rem])
    return ''.join(reversed(encoded))


def decode_base62(s: str) -> int:
    """Декодирует Base62 в число."""
    num = 0
    for ch in s:
        num = num * BASE + BASE62.index(ch)
    return num


def shorten_url(object_id, short_url_base):
    """Создаёт короткую ссылку из id объекта"""
    short_code = encode_base62(object_id)
    short_url_base = short_url_base.rstrip('/')
    return f'{short_url_base}/{short_code}/'


def restore_url(short_url, full_url_base):
    """Восстанавливает полный URL из короткой ссылки."""
    short_code = short_url.split('/')[-1]
    object_id = decode_base62(short_code)
    full_url_base = full_url_base.rstrip('/')
    return f'{full_url_base}/{object_id}/'


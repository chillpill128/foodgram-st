import random
import string


def generate_random_string(letters=6):
    # Используется для генерации имени файла при загрузке картинки
    # Используется в старой миграции.
    # Не могу удалить.
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(letters))

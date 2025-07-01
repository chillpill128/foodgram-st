import json
from django.core.management.base import BaseCommand
from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Загружает в базу ингредиенты из JSON-файла'

    def add_arguments(self, parser):
        parser.add_argument(
            'file_path', type=str,
            help='Путь к файлу с ингредиентами (в формате JSON)'
        )

    def handle(self, *args, **options):
        try:
            with open(options['file_path'], 'r', encoding='utf-8') as file:
                data = json.load(file)
        except (FileNotFoundError, PermissionError, json.JSONDecodeError) as err:
            print(f'Невозможно считать файл {options["file_path"]}. Ошибка: {err}')
            return
        except Exception as err:
            print(f'Ошибка: {err}')
            return

        new_ingredients = [
            Ingredient(name=item['name'], measurement_unit=item['measurement_unit'])
            for item in data
        ]
        created_ingredients = Ingredient.objects.bulk_create(
            new_ingredients,
            ignore_conflicts=True,
            unique_fields=('name', 'measurement_unit')
        )
        print(f'В базу добавлено {len(created_ingredients)} шт. новых ингредиентов')

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
            created_ingredients = Ingredient.objects.bulk_create(
                [Ingredient(**item) for item in data],
                ignore_conflicts=True,
            )
            print(f'В базу добавлено {len(created_ingredients)} шт. новых ингредиентов')
        except Exception as err:
            print(f'При обработке файла {options["file_path"]} возникла ошибка: {err}')

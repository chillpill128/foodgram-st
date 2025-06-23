import json
import csv
from django.core.management.base import BaseCommand
from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Load ingredients data from JSON or CSV file into the database'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str,
                            help='Путь к файлу с ингредиентами (в формате JSON или CSV)')

    def handle(self, *args, **options):
        file_path = options['file_path']

        new_data = set(self.read_file(file_path))
        existing = set(Ingredient.objects.values_list('name', 'measurement_unit'))
        to_upload = list(new_data - existing)
        if not to_upload:
            print('Нет новых ингредиентов для добавления в базу')
            return

        new_ingredients = [Ingredient(name=item[0], measurement_unit=item[1])
                           for item in to_upload]
        Ingredient.objects.bulk_create(new_ingredients, batch_size=1000)
        print(f'В базу добавлено {len(new_ingredients)} шт. новых ингредиентов')

    @staticmethod
    def read_file(file_path):
        file_format = file_path.lower().split('.')[-1]

        data = []
        with open(file_path, 'r', encoding='utf-8') as file:
            if file_format == 'csv':
                reader = csv.reader(file)
                data = [(row[0], row[1])
                        for row in reader if row]
            elif file_format == 'json':
                data = json.load(file)
                data = [(item['name'], item['measurement_unit']) for item in data]
            else:
                raise ValueError('Невозможно определить формат файла')

        return data

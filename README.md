
### Фронтенд:
- Собирается и стартует автоматически при запуске docker через команду docker-compose:
```bash
git clone https://github.com/chillpill128/foodgram-st
cd foodgram-st/infra
docker-compose up
```
- При выполнении этой команды контейнер frontend, описанный в docker-compose.yml, подготовит файлы, необходимые для работы фронтенд-приложения, а затем прекратит свою работу.
- Фронтенд будет доступен по адресу [localhost](http://localhost)


### Бэкенд.

**Автор**: [Андрей Ляшенко](https://github.com/chillpill128)

**Технологии**: Django · DRF · PostgreSQL · Docker · Nginx

### Переменные окружения
В папке backend создайте файл .env (или скопируйте .env.example в .env) и измените параметры на актуальные.

### Развертывание
Скопируйте содержимое репозитория в локальную папку:
```bash
git clone https://github.com/chillpill128/foodgram-st
```

#### Запуск через Docker (production):
Для запуска docker-compose нужно перейти в папку infra и выполнить команду:
```bash
cd ./infra
docker-compose up
```

#### Запуск локально (development):
Перейти в папку backend
```bash
# (выйти из папки infra при необходимости:)
cd ..
cd ./backend
```
В папке backend выполнить команды:
```bash
# Виртуальное окружение:
python -m venv venv && source venv/bin/activate
# Зависимости:
pip install -r requirements-dev.txt
# Миграции:
python manage.py migrate
# Запуск сервера для разработки:
python manage.py runserver
```
#### Доступные команды
```bash
# Создать администратора:
python manage.py createsuperuser

# Загрузить список ингредиентов:
python manage.py load_ingredients ../data/ingredients.json
```

### Ссылки, ведущие на бэкенд:
- **Админка**: [http://localhost:8000/admin/](http://localhost:8000/admin/)
- **API**: [http://localhost:8000/api/](http://localhost:8000/api/)

#### При запуске через docker-compose:
- **Админка**: [http://localhost/admin/](http://localhost/admin/)
- **API**: [http://localhost/api/](http://localhost/api/)

#### Спецификация API
- [localhost/api/docs](
http://localhost/api/docs/)

**Для остановки Docker**: `docker-compose down`*


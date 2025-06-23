Находясь в папке infra, выполните команду docker-compose up. При выполнении этой команды контейнер frontend, описанный в docker-compose.yml, подготовит файлы, необходимые для работы фронтенд-приложения, а затем прекратит свою работу.

По адресу http://localhost изучите фронтенд веб-приложения, а по адресу http://localhost/api/docs/ — спецификацию API.


### Бэкенд.

**Автор**: [Андрей Ляшенко](https://github.com/chillpill128)

**Технологии**: Django · DRF · PostgreSQL · Docker · Nginx

### Переменные окружения
В папке backend создайте файл .env (или скопируйте .env.example в .env) и измените параметры на актуальные.

### Развертывание

#### Запуск через Docker (production):
```bash
docker-compose up
```
#### Запуск локально (development):
```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements-dev.txt
python manage.py migrate
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
- **API**: [http://localhost:8000/](http://localhost:8000/api/)

#### При запуске через docker-compose:
- **Админка**: [http://localhost/admin/](http://localhost/admin/)
- **API**: [http://localhost/](http://localhost/api/)


**Для остановки Docker**: `docker-compose down`*


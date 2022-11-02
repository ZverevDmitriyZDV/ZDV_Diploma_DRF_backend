Steps for turning on:

to turn on google and facbook make steps:
steps in photo for help

pip install -r requirements.txt

python manage.py makemigrations
python manage.py migrate
python manage.py runserver

redis-server
redis-cli

python -m celery -A diploma  worker


Для корректной работы тестов необходимо проделать следующие шаги
 
sudo -u posgress sql <db_name_in_settings>
после соединения с БД введите команду ниже
ALTER USER <db_user_in_settings> CREATEDB;

для запуска тестов:
python manage.py test backend

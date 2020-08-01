# templater

Из папки репозитория:

Запуск:

    docker-compose build
    docker-compose up

Запуск тестов (когда докер работает и прослушивает адрес localhost:5000):

    pytest ./app/templater/tests.py -s

или

    python -m unittest app/templater/tests.py

или запустите тестовую конфигурацию докера:

    docker-compose -f ./docker-compose.test.yml build
    docker-compose -f ./docker-compose.test.yml up
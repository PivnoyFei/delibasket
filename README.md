[![Build Status](https://github.com/PivnoyFei/delibasket/actions/workflows/main.yml/badge.svg?branch=main)](https://github.com/PivnoyFei/delibasket/actions/workflows/main.yml)

<h1 align="center"><a target="_blank" href="">Электронная продуктовая корзина</a></h1>

## Описание
Проект Delibasket, «Электронная продуктовая корзина». На этом сервисе пользователи смогут публиковать рецепты, подписываться на публикации других пользователей, добавлять понравившиеся рецепты в список «Избранное», а перед походом в магазин скачивать сводный список продуктов, необходимых для приготовления одного или нескольких выбранных блюд.

### Что могут делать неавторизованные пользователи
- Создать аккаунт.
- Просматривать рецепты на главной.
- Просматривать отдельные страницы рецептов.
- Просматривать страницы пользователей.
- Фильтровать рецепты по тегам.
### Что могут делать авторизованные пользователи
- Входить в систему под своим логином и паролем.
- Выходить из системы (разлогиниваться).
- Менять свой пароль.
- Создавать/редактировать/удалять собственные рецепты
- Просматривать рецепты на главной.
- Просматривать страницы пользователей.
- Просматривать отдельные страницы рецептов.
- Фильтровать рецепты по тегам.
- Работать с персональным списком избранного: добавлять в него рецепты или удалять их, просматривать свою страницу избранных рецептов.
- Работать с персональным списком покупок: добавлять/удалять любые рецепты, выгружать файл со количеством необходимых ингридиентов для рецептов из списка покупок.
- Подписываться на публикации авторов рецептов и отменять подписку, просматривать свою страницу подписок.
### Что может делать администратор
Администратор обладает всеми правами авторизованного пользователя.
Плюс к этому он может:
- изменять пароль любого пользователя,
- создавать/блокировать/удалять аккаунты пользователей,
- редактировать/удалять **любые** рецепты,
- добавлять/удалять/редактировать ингредиенты.
- добавлять/удалять/редактировать теги.


### Стек: 
![Python](https://img.shields.io/badge/Python-171515?style=flat-square&logo=Python)![3.11](https://img.shields.io/badge/3.11-blue?style=flat-square&logo=3.11)
![FastAPI](https://img.shields.io/badge/FastAPI-171515?style=flat-square&logo=FastAPI)![0.85.0](https://img.shields.io/badge/0.85.0-blue?style=flat-square&logo=0.85.0)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-171515?style=flat-square&logo=PostgreSQL)![13.0](https://img.shields.io/badge/13.0-blue?style=flat-square&logo=13.0)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-171515?style=flat-square&logo=SQLAlchemy)
![Alembic](https://img.shields.io/badge/Alembic-171515?style=flat-square&logo=Alembic)
![Docker](https://img.shields.io/badge/Docker-171515?style=flat-square&logo=Docker)
![Docker-compose](https://img.shields.io/badge/Docker--compose-171515?style=flat-square&logo=Docker)
![Nginx](https://img.shields.io/badge/Nginx-171515?style=flat-square&logo=Nginx)
![GitHub](https://img.shields.io/badge/GitHub-171515?style=flat-square&logo=GitHub)


### Запуск проекта
Клонируем репозиторий и переходим в него:
```bash
git clone https://github.com/PivnoyFei/delibasket.git
cd delibasket
```

### Перед запуском сервера, в папке infra необходимо создать .env файл со своими данными.
```bash
POSTGRES_DB='postgres' # имя БД
POSTGRES_USER='postgres' # логин для подключения к БД
POSTGRES_PASSWORD='postgres' # пароль для подключения к БД
POSTGRES_SERVER='delibasket-db' # название контейнера
POSTGRES_PORT='5432' # порт для подключения к БД
```

#### Переходим в папку с файлом docker-compose.yaml:
```bash
cd infra
```

### Запуск проекта
```bash
docker-compose up -d --build
```

#### Миграции базы данных:
```bash
docker-compose exec delibasket-backend alembic revision --message="Initial" --autogenerate
docker-compose exec delibasket-backend alembic upgrade head
```

#### Останавливаем контейнеры:
```bash
docker-compose down -v
```

#### Создание суперпользователя:
```bash
docker-compose exec delibasket-backend python application/commands/createsuperuser.py
```

#### Загрузка ингредиентов и тегов в бд после запуска контейнера, выберите то что нужно без `<>`, по умолчанию попробует загрузить оба файла:
```bash
docker-compose exec delibasket-backend python application/commands/load_json.py <ingredients.json / tags.json>
```

#### Автор
[Смелов Илья](https://github.com/PivnoyFei)

<h1 align="center"><a target="_blank" href="">Проект Продуктовый помошник</a></h1>

![FoodgramFastAPI workflow](https://github.com/PivnoyFei/foodgram_fasapi/actions/workflows/main.yml/badge.svg)


## Прогрес
- ```/api/users/``` get: Список пользователей ✔️
- ```/api/users/{id}/``` get: Профиль пользователя ✔️
- ```/api/users/me/``` get: Текущий пользователь ✔️
- ```/api/users/subscriptions/``` get: Мои подписки ✔️
- ```/api/users/{id}/subscribe/``` post: Подписаться на пользователя ✔️
- ```/api/users/{id}/subscribe/``` delete: Отписаться от пользователя ✔️
- ```/api/auth/token/login/``` post: Получить токен авторизации ✔️
- ```/api/auth/token/logout/``` post: Удаление токена ✔️
- ```/api/users/set_password/``` post: Изменение пароля ✔️

- ```/api/tags/``` get: Cписок тегов ✔️
- ```/api/tags/``` post: Создание тега ✔️
- ```/api/tags/{id}/``` get: Получение тега ✔️
- ```/api/recipes/``` get: Список рецептов ✔️
- ```/api/recipes/``` post: Создание рецепта ✔️
- ```/api/recipes/``` delete: Удаление рецепта ✔️
- ```/api/recipes/download_shopping_cart/``` get: Скачать список покупок
- ```/api/recipes/{id}/``` get: Получение рецепта ✔️
- ```/api/recipes/{id}/favorite/``` post: Добавить рецепт в избранное
- ```/api/recipes/{id}/shopping_cart/``` post:  Добавить рецепт в список покупок
- ```/api/ingredients/``` get: Список ингредиентов ✔️
- ```/api/ingredients/``` post: Создание ингредиента ✔️
- ```/api/ingredients/{id}/``` get: Получение ингредиента ✔️


## Описание
Проект Foodgram, «Продуктовый помощник». На этом сервисе пользователи смогут публиковать рецепты, подписываться на публикации других пользователей, добавлять понравившиеся рецепты в список «Избранное», а перед походом в магазин скачивать сводный список продуктов, необходимых для приготовления одного или нескольких выбранных блюд.


### Стек: 
![Python](https://img.shields.io/badge/Python-171515?style=flat-square&logo=Python)![3.11](https://img.shields.io/badge/3.11-blue?style=flat-square&logo=3.11)
![FastAPI](https://img.shields.io/badge/FastAPI-171515?style=flat-square&logo=FastAPI)![0.85.0](https://img.shields.io/badge/0.85.0-blue?style=flat-square&logo=0.85.0)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-171515?style=flat-square&logo=PostgreSQL)![13.0](https://img.shields.io/badge/13.0-blue?style=flat-square&logo=13.0)
![Docker](https://img.shields.io/badge/Docker-171515?style=flat-square&logo=Docker)
![Docker-compose](https://img.shields.io/badge/Docker--compose-171515?style=flat-square&logo=Docker)
![Nginx](https://img.shields.io/badge/Nginx-171515?style=flat-square&logo=Nginx)
![GitHub](https://img.shields.io/badge/GitHub-171515?style=flat-square&logo=GitHub)
![GitHub-Actions](https://img.shields.io/badge/GitHub--Actions-171515?style=flat-square&logo=GitHub-Actions)

### Запуск проекта
Клонируем репозиторий и переходим в него:
```bash
git clone https://github.com/PivnoyFei/foodgram_fasapi.git
cd frames_fastapi
```
#### Создаем и активируем виртуальное окружение:
```bash
python3 -m venv venv
source venv/bin/activate
```
#### для Windows
```bash
python -m venv venv
source venv/Scripts/activate
```
#### Обновиляем pip и ставим зависимости из req.txt:
```bash
python -m pip install --upgrade pip && pip install -r backend/req.txt
```

### Перед запуском сервера, в папке infra необходимо создать .env файл со своими данными.
```bash
POSTGRES_DB='postgres' # имя БД
POSTGRES_USER='postgres' # логин для подключения к БД
POSTGRES_PASSWORD='postgres' # пароль для подключения к БД
POSTGRES_SERVER='db' # название контейнера
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

#### Останавливаем контейнеры:
```bash
docker-compose down -v
```

#### Загрузка ингредиентов и тегов в бд после первого запускаЖ
```bash
python load_json.py
```

#### Автор
[Смелов Илья](https://github.com/PivnoyFei)
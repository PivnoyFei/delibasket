<h1 align="center"><a target="_blank" href="">Проект Продуктовый помошник</a></h1>

![FoodgramFastAPI workflow](https://github.com/PivnoyFei/ ... /actions/workflows/main.yml/badge.svg)

## Описание
Проект Foodgram, «Продуктовый помощник». На этом сервисе пользователи смогут публиковать рецепты, подписываться на публикации других пользователей, добавлять понравившиеся рецепты в список «Избранное», а перед походом в магазин скачивать сводный список продуктов, необходимых для приготовления одного или нескольких выбранных блюд.


### Стек: 
```Python 3.10, fastapi 0.85.0, PostgreSQL  13.0, Docker, Nginx, GitHub Actions```

### Запуск проекта
Клонируем репозиторий и переходим в него:
```bash
git clone https://github.com/PivnoyFei/
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
ALGORITHM = "HS256"
JWT_SECRET_KEY = "key"
JWT_REFRESH_SECRET_KEY = "key"
```
#### Чтобы сгенерировать безопасный случайный секретный ключ, используйте команду ```openssl rand -hex 32```:

#### Переходим в папку с файлом docker-compose.yaml:
```bash
cd infra
```

### Запуск проекта
```bash
docker-compose up -d backend
```

#### Останавливаем контейнеры:
```bash
docker-compose down -v
```

#### Запуск проекта без Docker на SQLite
```bash
uvicorn main:app --reload
```

#### Автор
[Смелов Илья](https://github.com/PivnoyFei)
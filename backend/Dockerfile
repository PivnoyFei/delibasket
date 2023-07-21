FROM python:3.11.0-slim

WORKDIR /srv/www/app

COPY . .

COPY pyproject.toml poetry.lock ./
COPY . ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir poetry \
    && poetry config virtualenvs.create false \
    && poetry install -n --no-interaction --no-ansi --no-dev

# CMD gunicorn application.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind=0.0.0.0:8000
# CMD ["uvicorn", "application.main:app", "--reload", "--host", "0.0.0.0"]
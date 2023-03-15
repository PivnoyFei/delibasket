FROM python:3.10.7-slim

WORKDIR /backend

COPY . .

RUN apt-get update && apt-get install gcc libpq-dev -y
RUN python3 -m pip install --upgrade pip
RUN pip install -r requirements.txt

CMD gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind=0.0.0.0:8000
# CMD ["uvicorn", "main:app", "--reload", "--host", "0.0.0.0"]
FROM python:3.10.7-slim

WORKDIR /backend

COPY . .

RUN apt-get update && apt-get install gcc libpq-dev -y
RUN python3 -m pip install --upgrade pip
RUN pip install -r requirements.txt

CMD ["uvicorn", "main:app", "--reload", "--host", "0.0.0.0"]
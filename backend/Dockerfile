FROM python:3.10.7-slim
WORKDIR /frames
COPY . .
RUN apt-get update && apt-get install gcc libpq-dev -y
RUN python3 -m pip install --upgrade pip
RUN pip install -r req.txt
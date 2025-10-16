FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /code

RUN apt-get update && apt-get install -y build-essential libpq-dev gcc

COPY requirements.txt /code/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY . /code/

RUN addgroup --system app && adduser --system --ingroup app app
USER app

ENTRYPOINT ["/code/entrypoint.sh"]

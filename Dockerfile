FROM python:3.13

ENV APP_HOME=/app

WORKDIR /app

ENV PYTHONPATH=/app

RUN pip install poetry

COPY pyproject.toml poetry.lock ./

RUN poetry config virtualenvs.create false

RUN poetry install --only=main --no-root

COPY . .

EXPOSE 8000

CMD [ "poetry", "run", "python", "src/main.py"]
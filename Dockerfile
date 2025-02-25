FROM python:3.12-slim

WORKDIR /code

ENV POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1

# Install Poetry
RUN pip install --no-cache-dir poetry

# Copy project files
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry install --no-root --without dev,test \
    && rm -rf $(poetry config cache-dir)/{cache,artifacts}

# Copy application code
COPY slasher_proxy /code/slasher_proxy

# Run the application
CMD ["poetry", "run", "uvicorn", "slasher_proxy.main:app", "--host", "0.0.0.0", "--port", "80"]

FROM python:3.14-slim

WORKDIR /app

COPY requirements-lock.txt .

RUN pip install --no-cache-dir -r requirements-lock.txt

COPY . .

# Create an unprivileged user and group
RUN groupadd --system appgroup \
    && useradd --system --gid appgroup --create-home appuser
# Run the application as a non-root user
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

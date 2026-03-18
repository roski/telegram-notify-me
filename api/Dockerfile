FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY api/requirements.txt /app/api/requirements.txt
RUN pip install --no-cache-dir -r /app/api/requirements.txt

# Copy bot package (shared models + i18n)
COPY bot /app/bot

# Copy API source
COPY api /app/api

ENV PYTHONPATH=/app

CMD ["python", "-m", "flask", "--app", "api/app", "run", "--host", "0.0.0.0", "--port", "5000"]

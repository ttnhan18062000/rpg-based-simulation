FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ /app/src/
COPY data/ /app/data/

# Expose port
EXPOSE 8000

# Command to run the application
CMD ["python", "-m", "uvicorn", "src.api.app:create_app", "--host", "0.0.0.0", "--port", "8000"]

FROM python:3.11-slim

WORKDIR /app

# Install Python dependencies from pyproject.toml
COPY pyproject.toml .
RUN pip install --no-cache-dir .

# Copy source code & data
COPY src/ /app/src/
COPY data/ /app/data/

# Expose port
EXPOSE 8000

# Command to run the application
CMD ["python", "-m", "src", "serve", "--host", "0.0.0.0", "--port", "8000"]

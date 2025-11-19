<<<<<<< HEAD
# Dockerfile for the Supervisor
FROM python:3.11-slim

WORKDIR /app

# Copy shared files and install dependencies first
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Command to run the supervisor is in docker-compose.yml
CMD ["python", "-m", "uvicorn", "supervisor.main:app", "--host", "0.0.0.0", "--port", "8000"]
=======
# Dockerfile for the Supervisor
FROM python:3.11-slim

WORKDIR /app

# Copy shared files and install dependencies first
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Command to run the supervisor is in docker-compose.yml
CMD ["python", "-m", "uvicorn", "supervisor.main:app", "--host", "0.0.0.0", "--port", "8000"]
>>>>>>> upstream/main

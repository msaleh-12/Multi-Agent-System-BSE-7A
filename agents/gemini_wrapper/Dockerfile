<<<<<<< HEAD
# Dockerfile for the Gemini Wrapper Agent
FROM python:3.11-slim

WORKDIR /app

# Copy shared files and install dependencies first
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Command to run the agent is in docker-compose.yml
CMD ["python", "-m", "uvicorn", "agents.gemini_wrapper.app:app", "--host", "0.0.0.0", "--port", "5010"]
=======
# Dockerfile for the Gemini Wrapper Agent
FROM python:3.11-slim

WORKDIR /app

# Copy shared files and install dependencies first
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Command to run the agent is in docker-compose.yml
CMD ["python", "-m", "uvicorn", "agents.gemini_wrapper.app:app", "--host", "0.0.0.0", "--port", "5010"]
>>>>>>> upstream/main

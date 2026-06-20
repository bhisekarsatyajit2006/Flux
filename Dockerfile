# Use Python 3.11 slim as the base image
FROM python:3.11-slim

# Set work directory
WORKDIR /app

# Copy requirements and install dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire backend and frontend directories
# Maintaining the structure:
# /app/backend/
# /app/frontend/
COPY backend/ ./backend/
COPY frontend/ ./frontend/

# Set environment variables
ENV PYTHONPATH=/app/backend
ENV PORT=8000

# Expose the port
EXPOSE 8000

# Run the application
WORKDIR /app/backend
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

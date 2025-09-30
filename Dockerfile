# Base image
FROM python:3.12-slim

# Create a non-root user
RUN useradd -m myuser
USER myuser

# Set work directory
WORKDIR /app

# Copy project files
COPY --chown=myuser:myuser . .

# Upgrade pip & install dependencies
RUN python -m pip install --upgrade pip
RUN pip install -r requirements.txt

# Make necessary directories
RUN mkdir -p uploads/packages

# Expose port
EXPOSE 8000

# Run app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]


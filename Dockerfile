FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies as root
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Create non-root user
RUN useradd -m -u 1000 myuser && \
    chown -R myuser:myuser /app

# Copy application files
COPY --chown=myuser:myuser . .

# Create necessary directories
RUN mkdir -p uploads/packages && \
    chown -R myuser:myuser uploads

# Switch to non-root user
USER myuser

# Add user bin to PATH
ENV PATH="/home/myuser/.local/bin:${PATH}"

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Start command
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
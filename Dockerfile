# Dockerfile for WSQ Courseware Generator (Streamlit)
# Compatible with Hugging Face Spaces (Docker SDK)
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user (required for HF Spaces)
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

WORKDIR /home/user/app

# Copy requirements first for better caching
COPY --chown=user requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=user . .

# Expose port (HF Spaces uses 7860)
EXPOSE 7860

# Run Streamlit with HF Spaces compatibility
CMD ["streamlit", "run", "app.py", "--server.port", "7860", "--server.address", "0.0.0.0"]

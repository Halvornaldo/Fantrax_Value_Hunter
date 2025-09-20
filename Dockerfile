# Fantrax Value Hunter - Docker Deployment
# Multi-stage build for cache-proof React + Flask deployment

# Stage 1: Build React frontend with cache-busting
FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy package files first for better layer caching
COPY frontend/package.json ./
COPY frontend/package-lock.json* ./

# Install dependencies (fallback to npm install if package-lock.json missing)
RUN if [ -f package-lock.json ]; then \
        echo "Using npm ci with package-lock.json"; \
        npm ci --no-audit --no-fund; \
    else \
        echo "package-lock.json not found, using npm install"; \
        npm install --no-audit --no-fund; \
    fi

# Copy frontend source code
COPY frontend/ ./

# Build with cache-busting via build arg
ARG CACHEBUST=1
ENV REACT_APP_CACHEBUST=$CACHEBUST

# Build React application
RUN CI=false npm run build

# Verify build output for debugging
RUN echo "✅ React build complete - Generated files:" && \
    ls -la build/static/js/*.js | head -5 && \
    echo "Build timestamp: $(date)"

# Stage 2: Python Flask application
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for PostgreSQL
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Clean any existing React build and copy fresh one from builder stage
RUN rm -rf src/static/react-build
COPY --from=frontend-builder /app/frontend/build ./src/static/react-build

# Verify the React files were properly copied
RUN echo "📦 Final React build verification in Flask static directory:" && \
    ls -la src/static/react-build/static/js/*.js | head -3 && \
    echo "Deployment ready at: $(date)"

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Expose port
EXPOSE 8080

# Start command using the Railway-compatible startup script
CMD ["python", "startup_with_db_init.py"]
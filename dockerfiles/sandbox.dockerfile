# Use lightweight Alpine image
FROM alpine:latest

# Install Node.js, Python, and dependencies
RUN apk add --no-cache python3 py3-pip nodejs npm

# Set working directory
WORKDIR /app

# Copy agent code
COPY . .

RUN python3 -m venv venv

RUN venv/bin/python3 -m pip install -e .

# Expose port 6060
EXPOSE 6060

# Run the AI agent
CMD ["venv/bin/python3", "src/main.py"]


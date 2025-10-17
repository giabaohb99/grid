# syntax=docker/dockerfile:1

# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies needed for PostgreSQL, Pillow and other packages
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    libjpeg-dev \
    zlib1g-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libwebp-dev \
    libharfbuzz-dev \
    libfribidi-dev \
    libxcb1-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container at /app
# We do this separately to leverage Docker's layer caching.
COPY ./requirements.txt /app/requirements.txt

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Copy the rest of the application's code into the container
COPY . /app

# Expose the port the app runs on
EXPOSE 8000

# Run the application
# The command will be something like: uvicorn core.users.main:app --host 0.0.0.0 --port 8000
# We will set the final command in docker-compose.yml 
# Use an official Python runtime as the base image
FROM python:3.9-slim

# Install git
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . .

# Set the PYTHONUNBUFFERED environment variable
ENV PYTHONUNBUFFERED=1

# Run main.py when the container launches
CMD ["python", "main.py"]
# Use the base image of Python
FROM python:3

# Set the time zone to Chicago
ENV TZ=America/Chicago

# Define the working directory
WORKDIR /app

# Copy only the requirements file to take advantage of the cache
COPY requirements.txt .

# Install necessary packages, Chromium, chromedriver, libffi-dev, curl, pkg-config, and libssl-dev
RUN apt-get update -qqy \
    && apt-get install -qqy curl chromium chromium-driver libffi-dev pkg-config libssl-dev \
    libx11-6 libx11-xcb1 libfontconfig1 libfreetype6 libxext6 libxrender1 libxtst6 libnss3 libnspr4 libasound2 \
    && rm -rf /var/lib/apt/lists/* /var/cache/apt/*

# Install Python project dependencies
RUN pip install -r requirements.txt

# Copy the remaining project files into the working directory
COPY . .

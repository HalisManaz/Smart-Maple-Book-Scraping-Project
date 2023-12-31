# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the timezone to Istanbul
ENV TZ=Europe/Istanbul

WORKDIR /app

COPY requirements.txt ./

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

# Run the command on container startup
CMD ["python3" , "main.py"]
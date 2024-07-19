# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy the current directory contents into the container at /app
ADD . /app

# Install any needed packages specified in requirements.txt
RUN pip install pymongo

# Make port 3000 and 5000 available to the world outside this container
EXPOSE 3000 5000

# Run main.py when the container launches
CMD ["python", "main.py"]

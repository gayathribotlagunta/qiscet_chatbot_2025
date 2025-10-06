# Use the official Python image from the Docker Hub
FROM python:3.9-slim

# Set the working directory to /app
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install any required packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy all the remaining project files into the container
COPY . .

# Expose port 8080 to the outside world
EXPOSE 8080

# Run the bot.py file when the container is started
CMD ["python", "bot.py"]
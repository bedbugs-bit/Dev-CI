# Dockerfile for containerizing the CI system.

FROM python:3.10-slim

WORKDIR /app

# Copy all project files into the container.
COPY . /app

# Install required Python packages.
RUN pip install -r requirements.txt

# Expose ports:
# - 8888 for the dispatcher
# - 5000 for the web reporter
EXPOSE 8888 5000

# Set the default command to run the deploy script.
CMD ["python", "deploy.py"]

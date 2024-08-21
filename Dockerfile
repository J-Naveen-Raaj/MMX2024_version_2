# Use a base image with required dependencies
FROM python:3.10.13

# Set working directory
WORKDIR /app

# Copy the training script and any other necessary files
COPY . /app/

# Create a virtual environment
RUN python -m venv venv

# Activate the virtual environment
SHELL ["/bin/bash", "-c"]
RUN source venv/bin/activate

# Install required packages
RUN pip install -r requirements.txt

# Set environment variable for the port
ENV PORT 8083

CMD ["python", "server.py","runserver"]
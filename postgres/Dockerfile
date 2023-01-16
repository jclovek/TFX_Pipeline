FROM python:3.8

# Set the working directory
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Install the required Python packages
RUN /usr/local/bin/python -m pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy the API code
COPY postgres_import_api.py .

# Expose port 5020
EXPOSE 5020

# Run the API
CMD ["python", "postgres_import_api.py"]

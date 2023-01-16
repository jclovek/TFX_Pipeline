FROM python:3.8

# Set the working directory
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Install the required Python packages
RUN /usr/local/bin/python -m pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy the API code
COPY ensembl_api.py .

# Expose port 5010
EXPOSE 5010

# Run the API
CMD ["python", "ensembl_api.py"]

FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

RUN mkdir -p /app/data

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Python script to the container
COPY . .

CMD ["python", "echo_dataset_downloader.py"]

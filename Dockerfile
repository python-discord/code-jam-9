FROM python:latest

LABEL maintainer="zesty zombies"

# Set the working directory
WORKDIR /app

# Install project requirements
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy project to working directory
COPY . .

CMD ["python", "./backend/server.py"]

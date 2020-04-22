# Image
FROM python:3.8-slim-buster

# Project setup
EXPOSE 8501
WORKDIR /app
COPY requirements.txt ./requirements.txt
RUN pip install -r requirements.txt
COPY . .

# Run app
CMD ./start.sh
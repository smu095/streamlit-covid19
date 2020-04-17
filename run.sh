docker build -f Dockerfile -t app:latest .
docker run --rm -it -p 8501:8501 app:latest
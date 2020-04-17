# Image
FROM python:3.8-buster
EXPOSE 8501

# Project setup
WORKDIR /app
COPY requirements.txt ./requirements.txt
RUN pip install -r requirements.txt
COPY . .

# Run app
CMD streamlit run app.py

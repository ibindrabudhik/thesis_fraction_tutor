FROM python:3.11-slim

EXPOSE 8080
WORKDIR /app

COPY . ./

RUN pip install --no-cache-dir -r requirements.txt

ENTRYPOINT ["streamlit", "run", "app/main.py", "--server.port=8080", "--server.address=0.0.0.0"]

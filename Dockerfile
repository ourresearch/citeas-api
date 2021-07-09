FROM python:3.8-slim-buster
WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["gunicorn" , "--bind", "0.0.0.0:8000", "views:app", "-w", "3"]
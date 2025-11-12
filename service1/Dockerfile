# client docker file
FROM python:3.9-slim
WORKDIR /app
COPY client.py /app/
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir gunicorn
EXPOSE 5000
CMD ["gunicorn","--workers=4","--threads=2","--bind","0.0.0.0:5000","client:app"]

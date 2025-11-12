# resource docker file
FROM python:3.9-slim
WORKDIR /app
COPY resource.py /app/
RUN pip install flask gunicorn
EXPOSE 5001
CMD ["gunicorn", "-w", "2", "--threads", "4", "-k", "gthread", "-b", "0.0.0.0:5001", "resource:app"]


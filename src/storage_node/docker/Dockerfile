FROM python:3.10-slim
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ../app.py .
COPY ../common_utils.py .

# Each storage node will run on a different port.
EXPOSE 5000

CMD ["python", "app.py"]
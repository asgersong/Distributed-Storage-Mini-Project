FROM python:3.10-slim
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY file_handler.py .
COPY node_selection.py .
COPY config.py .
COPY storage_node_client.py .
# any shared logic

EXPOSE 4000

CMD ["python", "app.py"]
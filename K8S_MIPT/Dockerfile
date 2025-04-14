FROM python:3.9-slim

RUN apt-get update && \
    apt-get install -y curl tar && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /application

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p /application/journal

COPY server.py .

EXPOSE 5000

CMD ["python", "server.py"]

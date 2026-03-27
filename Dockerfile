FROM python:3.13-slim

RUN apt-get update && apt-get install -y --no-install-recommends git ssh && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY docli/ docli/

COPY entrypoint.sh entrypoint.sh

CMD ["./entrypoint.sh"]

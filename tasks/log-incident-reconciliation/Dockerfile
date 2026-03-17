FROM python:3.11-slim

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir pytest
RUN chmod +x run.sh

CMD ["./run.sh"]
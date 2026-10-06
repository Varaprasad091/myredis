FROM python:3.14-slim

WORKDIR /app

COPY . .

ENV PYTHONUNBUFFERED=1
ENV MYREDIS_AOF_FILE=/data/appendonly.aof
ENV MYREDIS_RDB_FILE=/data/dump.rdb

EXPOSE 6379

CMD ["python", "main.py"]
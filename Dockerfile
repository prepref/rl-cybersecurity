# Используем образ Python 3.8.8 в качестве базового
FROM python:3.8.8-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы проекта в контейнер
COPY ./utils/server.py .

# Устанавливаем зависимости
RUN pip install --no-cache-dir prometheus_client==0.12.0 psutil==5.8.0

# Запускаем сервер
CMD ["python", "server.py"]
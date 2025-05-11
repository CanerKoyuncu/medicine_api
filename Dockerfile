FROM python:3.11-slim

WORKDIR /app

# Sistem bağımlılıklarını yükle
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Önce sadece requirements.txt'yi kopyala
COPY requirements.txt .

# Bağımlılıkları yükle
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Uygulama kodunu kopyala
COPY . .

# Servis için port aç
EXPOSE 8001

# Uygulamayı çalıştır
CMD ["python", "main.py"]
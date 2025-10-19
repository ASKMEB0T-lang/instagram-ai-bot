FROM python:3.9.18-slim-bullseye

WORKDIR /app

# نسخ المتطلبات أولاً
COPY requirements.txt .

# تثبيت المتطلبات
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# نسخ باقي الملفات
COPY . .

# تشغيل التطبيق
CMD ["python", "app.py"]

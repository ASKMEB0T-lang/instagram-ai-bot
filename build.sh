#!/bin/bash
echo "🚀 بدء بناء التطبيق..."

# تحديث pip وإعداد البيئة
pip install --upgrade pip setuptools wheel

# تثبيت المتطلبات
pip install -r requirements.txt

echo "✅ اكتمل البناء بنجاح!"

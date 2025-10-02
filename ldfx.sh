#!/bin/bash
set -e

echo "🐱 Настройка Ubuntu 24.04 ARM proot и установка Python 3.10..."

# --- 1. Чистим старые PPA plucky ---
echo "🧹 Удаляем старые PPA plucky..."
rm -f /etc/apt/sources.list.d/mozillateam-ubuntu-*-plucky.* || true

# --- 2. Обновляем sources.list на noble (24.04) ---
echo "📝 Обновляю sources.list..."
cat > /etc/apt/sources.list <<EOL
deb http://ports.ubuntu.com/ubuntu-ports/ noble main universe restricted multiverse
deb http://ports.ubuntu.com/ubuntu-ports/ noble-updates main universe restricted multiverse
deb http://ports.ubuntu.com/ubuntu-ports/ noble-security main universe restricted multiverse
EOL

# --- 3. Modernize sources ---
apt update -y
apt modernize-sources -y

# --- 4. Минимальные пакеты для сборки Python (только wget и tar) ---
echo "🔧 Устанавливаем минимальные пакеты для сборки..."
apt install -y wget tar

# --- 5. Скачиваем и собираем Python 3.10 ---
PYTHON_VER=3.10.14
echo "🐍 Скачиваем Python $PYTHON_VER..."
wget https://www.python.org/ftp/python/$PYTHON_VER/Python-$PYTHON_VER.tgz
tar -xf Python-$PYTHON_VER.tgz
cd Python-$PYTHON_VER

echo "⚡ Собираем Python $PYTHON_VER..."
./configure --enable-optimizations
make -j$(nproc)
make altinstall  # altinstall, чтобы не трогать системный python3

cd ..
rm -rf Python-$PYTHON_VER Python-$PYTHON_VER.tgz

# --- 6. Настраиваем python3 по умолчанию на python3.10 ---
echo "🛠 Переключаем python3 на python3.10 по умолчанию..."
update-alternatives --install /usr/bin/python3 python3 /usr/local/bin/python3.10 2
update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 1
update-alternatives --set python3 /usr/local/bin/python3.10

# --- 7. Финальные сообщения ---
echo "✅ Python 3.10 успешно установлен и установлен по умолчанию для python3!"
echo "Версия python3: $(python3 --version)"
echo "Команда python3.10 тоже доступна: $(python3.10 --version)"
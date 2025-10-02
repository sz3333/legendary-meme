#!/bin/bash
set -e

echo "🐱 Обновляем sources.list и устанавливаем Python 3.10 из исходников на Ubuntu 24.04 ARM (proot)..."

# --- 1. Чистим старые PPA plucky ---
echo "🧹 Удаляем старые PPA plucky..."
rm -f /etc/apt/sources.list.d/mozillateam-ubuntu-*-plucky.* || true

# --- 2. Обновляем sources.list на noble (24.04) ---
echo "📝 Обновляю sources.list для noble..."
cat > /etc/apt/sources.list <<EOL
deb http://ports.ubuntu.com/ubuntu-ports/ noble main universe restricted multiverse
deb http://ports.ubuntu.com/ubuntu-ports/ noble-updates main universe restricted multiverse
deb http://ports.ubuntu.com/ubuntu-ports/ noble-security main universe restricted multiverse
EOL

# --- 3. Modernize sources, чтобы apt не ругался ---
echo "⚡ Modernizing sources..."
apt update -y
apt modernize-sources -y

# --- 4. Обновляем систему и ставим зависимости для сборки Python ---
apt upgrade -y
apt install -y build-essential curl wget gnupg lsb-release \
    libssl-dev zlib1g-dev libncurses5-dev libncursesw5-dev \
    libreadline-dev libffi-dev libsqlite3-dev tar

# --- 5. Скачиваем и собираем Python 3.10 из исходников ---
echo "🐍 Скачиваем Python 3.10.14..."
wget https://www.python.org/ftp/python/3.10.14/Python-3.10.14.tgz
tar -xf Python-3.10.14.tgz
cd Python-3.10.14

echo "🔧 Собираем Python 3.10..."
./configure --enable-optimizations
make -j$(nproc)
make altinstall  # altinstall чтобы не трогать системный python3

cd ..
rm -rf Python-3.10.14 Python-3.10.14.tgz

# --- 6. Настраиваем update-alternatives ---
update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 1
update-alternatives --install /usr/bin/python3 python3 /usr/local/bin/python3.10 2

# --- 7. Финальные сообщения ---
echo "✅ Python 3.10 успешно установлен!"
echo "Доступные версии python3:"
update-alternatives --config python3 || true
echo "Текущая версия python3 по умолчанию: $(python3 --version)"
echo "Команда python3.10 тоже доступна: $(python3.10 --version)"
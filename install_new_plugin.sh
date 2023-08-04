#!/bin/bash

# Проверяем версию ОС
echo "Проверяем архитектуру"
os_name=$(uname -s)

if [[ "$os_name" == "Linux" && "$(uname -m)" == "arm"* ]]; then
    echo "Операционная система поддерживается."
elif [[ "$os_name" == "Linux" && "$(uname -m)" == "aarch"* ]]; then
    echo "Операционная система поддерживается."
else
    echo "Операционная система не поддерживается"
    exit 1
fi

# Проверяем версию ОС
echo "Проверяем версию ОС"
required_debian_version="10.0"
current_debian_version=$(cat /etc/debian_version)

if [[ $required_debian_version == $current_debian_version || $current_debian_version > $required_debian_version ]]; then
    echo "Версия Debian ($required_debian_version) подходит для установки. Текущая версия ($current_debian_version)"
else
    echo "Ошибка: Версия Debian ($required_debian_version) не совпадает с текущей версией ($current_debian_version)"
    exit 1
fi

# Проверяем установлен ли pip
echo "Проверяем установлен ли pip?"
if which pip >/dev/null 2>&1; then
    current_pip_version=$(pip --version | awk '{print $2}')
    echo "Версия pip ($current_pip_version)."
else
    echo "Установка pip"
    apt-get install python3-pip
fi



# Проверяем версию Python
echo "Проверяем версию Python"
required_python_version="3.9"
current_python_version=$(python3 -V 2>&1 | awk '{print $2}')

if [[ $current_python_version == $required_python_version || $current_python_version > $required_python_version  ]]; then
    echo "Версия Python ($current_python_version) походит для установки. Требуемая версия должна быть не ниже ($required_python_version)"
else
    echo "Ошибка: Версия Python ($required_python_version) не походит для установки. Ваша версия ($required_python_version)"
    exit 1
fi


# Устанавливаем новый плагин в папку /home/sh2/exe
echo "Устанавливаем плагин API"
wget https://github.com/MimiSmart/new_api_plugin/archive/refs/heads/main.zip -O /home/sh2/exe/new_api_plugin.zip
unzip /home/sh2/exe/new_api_plugin.zip -d /home/sh2/exe/
mv /home/sh2/exe/new_api_plugin-main /home/sh2/exe/new_api_plugin

# Разрешам выполнение файла
chmod +x /home/sh2/exe/new_api_plugin/main.py



# Проверяем успешно ли установлен плагин
if [ -d "/home/sh2/exe/new_api_plugin" ]; then
  echo "Плагин успешно установлен"
  rm /home/sh2/exe/new_api_plugin.zip
else
  echo "Ошибка установки плагина. Выход."
  exit 1
fi

# Меняем порт сервера
echo "Устанавливаем зависимости"
pip install -r /home/sh2/exe/new_api_plugin/setup_tools/requirements.txt

# Меняем порт сервера
echo "Меняю порт сервера для приложения на 22522"
wget https://raw.githubusercontent.com/MimiSmart/new_api_plugin/main/def-args.txt?raw=true -O /home/sh2/def-args.txt


# Обноляем файл настроек MimiSetup. 
echo "Обновляю файл настроект MimiSetup"
wget https://raw.githubusercontent.com/MimiSmart/new_api_plugin/main/settings.php -O /home/html/MimiSetup/settings.php

# Restart mimismart service in screen
echo "Пытаюсь перезапустить сервер Mimiserver"
screen -S mimiserver -X stuff "qu$(printf \\r)"

if [ $? -eq 0 ]; then
    echo "Перезапуск сервера успешно выполнен."
else
    echo "Перезапуск сервера не выполенен, выполните вручную."
    exit 1
fi

# Создаём службу сервер 3.0
echo "Создаю службу new_api_plugin"
cat <<EOF >/etc/systemd/system/new_api_plugin.service
[Unit]
Description=New REST and WebSocket API plugin

After=multi-user.target

[Service]
Type=idle
# Nice=1
ExecStart=/home/sh2/exe/new_api_plugin/main.py
Environment=PYTHONUNBUFFERED=1

[Install]

WantedBy=multi-user.target
EOF

# Перезапускаем системный демон и запускаем слуюбу
systemctl daemon-reload
systemctl enable new_api_plugin.service
systemctl start new_api_plugin.service

# Проверяем, что служба запущена
if systemctl is-active --quiet new_api_plugin.service; then
  echo "Служба запущена."
else
  echo "Не удалось запустить службу. Выход."
  exit 1
fi


echo "Обновление сервера успешно ввыполнено. Мои поздравления1"


# Активируем IPTABLES
read -p "Вы хотите активировать таблицу IPTABLES? (y/n): " choice
if [[ $choice == "y" || $choice == "Y" ]]; then
    wget -O tablesOn.sh "https://raw.githubusercontent.com/MimiSmart/mimi-server/main/tablesOn.sh?raw=true" && chmod +x tablesOn.sh && ./tablesOn
else
    exit 1
fi

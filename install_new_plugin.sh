#!/bin/bash

required_python_version="3.9"
current_python_version=$(python3 -V 2>&1 | awk '{print $2}')

if [[ $current_python_version == $required_python_version ]]; then
    echo "Версия Python ($required_python_version) совпадает с текущей версией ($current_python_version)"
    # Ваш код или команда, которые должны выполняться при совпадении версий
else
    echo "Ошибка: Версия Python ($required_python_version) не совпадает с текущей версией ($current_python_version)"
    # Ваш код или команда, которые должны выполняться при несовпадении версий
fi

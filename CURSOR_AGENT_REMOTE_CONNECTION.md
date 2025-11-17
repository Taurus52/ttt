# Подключение Cursor агента к удаленному серверу для тестирования и диагностики

## Содержание
1. [Введение](#введение)
2. [Способы подключения](#способы-подключения)
3. [Настройка SSH подключения](#настройка-ssh-подключения)
4. [Тестирование удаленного сервера](#тестирование-удаленного-сервера)
5. [Диагностика проблем](#диагностика-проблем)
6. [Безопасность](#безопасность)
7. [Примеры использования](#примеры-использования)

## Введение

Cursor агент может подключаться к удаленным серверам для выполнения различных задач: тестирования приложений, диагностики проблем, мониторинга системы и выполнения команд в удаленной среде. Это позволяет разработчикам работать с продакшн-окружением, тестовыми серверами или удаленными машинами без необходимости прямого физического доступа.

## Способы подключения

### 1. SSH (Secure Shell)

SSH является основным и наиболее безопасным способом подключения к удаленному серверу. Cursor агент может использовать SSH для:

- Выполнения команд на удаленном сервере
- Передачи файлов (SCP/SFTP)
- Порт-форвардинга для доступа к удаленным сервисам
- Удаленной отладки приложений

### 2. Docker Remote API

Для работы с контейнеризованными приложениями Cursor агент может подключаться к Docker daemon через:

- Docker Remote API (TCP/Unix socket)
- SSH туннель к Docker daemon
- Docker Context для переключения между локальными и удаленными окружениями

### 3. Kubernetes API

При работе с Kubernetes кластерами агент может использовать:

- kubectl с настройкой kubeconfig
- Прямое подключение к Kubernetes API
- Port-forwarding для доступа к подам и сервисам

## Настройка SSH подключения

### Базовая настройка

1. **Генерация SSH ключей** (если еще не созданы):
```bash
ssh-keygen -t ed25519 -C "cursor-agent@example.com"
```

2. **Копирование публичного ключа на сервер**:
```bash
ssh-copy-id user@remote-server.com
```

3. **Настройка SSH config** (`~/.ssh/config`):
```
Host remote-server
    HostName remote-server.com
    User deploy
    Port 22
    IdentityFile ~/.ssh/id_ed25519
    ServerAliveInterval 60
    ServerAliveCountMax 3
```

### Использование в Cursor агенте

Cursor агент может использовать SSH подключение через:

- Прямое выполнение команд через SSH
- Настройку remote workspace через SSH
- Автоматическое подключение при необходимости выполнения удаленных операций

## Тестирование удаленного сервера

### Проверка доступности

```bash
# Проверка доступности сервера
ssh remote-server "echo 'Server is reachable'"

# Проверка сетевого подключения
ping -c 4 remote-server.com

# Проверка портов
nc -zv remote-server.com 22 80 443
```

### Проверка системных ресурсов

```bash
# Информация о системе
ssh remote-server "uname -a && uptime"

# Использование дискового пространства
ssh remote-server "df -h"

# Использование памяти
ssh remote-server "free -h"

# Загрузка процессора
ssh remote-server "top -bn1 | head -20"
```

### Тестирование приложений

```bash
# Проверка статуса сервисов
ssh remote-server "systemctl status nginx postgresql"

# Проверка логов приложения
ssh remote-server "tail -n 100 /var/log/app/application.log"

# Проверка доступности веб-приложения
curl -I https://remote-server.com/api/health

# Тестирование через SSH туннель
ssh -L 8080:localhost:8080 remote-server
```

## Диагностика проблем

### Сбор информации о системе

Cursor агент может автоматически собирать диагностическую информацию:

```bash
# Сбор системной информации
ssh remote-server << 'EOF'
echo "=== System Information ===" > diagnostics.txt
uname -a >> diagnostics.txt
uptime >> diagnostics.txt
echo "" >> diagnostics.txt
echo "=== Disk Usage ===" >> diagnostics.txt
df -h >> diagnostics.txt
echo "" >> diagnostics.txt
echo "=== Memory Usage ===" >> diagnostics.txt
free -h >> diagnostics.txt
echo "" >> diagnostics.txt
echo "=== Network Connections ===" >> diagnostics.txt
netstat -tuln >> diagnostics.txt
echo "" >> diagnostics.txt
echo "=== Running Processes ===" >> diagnostics.txt
ps aux | head -20 >> diagnostics.txt
cat diagnostics.txt
EOF
```

### Анализ логов

```bash
# Поиск ошибок в логах
ssh remote-server "grep -i error /var/log/app/*.log | tail -50"

# Мониторинг логов в реальном времени
ssh remote-server "tail -f /var/log/app/application.log"

# Анализ логов по времени
ssh remote-server "journalctl --since '1 hour ago' --until 'now' -u app.service"
```

### Проверка сетевых подключений

```bash
# Проверка открытых портов
ssh remote-server "ss -tuln"

# Проверка активных соединений
ssh remote-server "netstat -an | grep ESTABLISHED"

# Тестирование подключения к внешним сервисам
ssh remote-server "curl -v https://api.example.com/health"
```

### Диагностика производительности

```bash
# Анализ использования CPU
ssh remote-server "top -bn1 | grep 'Cpu(s)'"

# Анализ использования памяти процессами
ssh remote-server "ps aux --sort=-%mem | head -10"

# Проверка I/O операций
ssh remote-server "iostat -x 1 5"

# Анализ сетевого трафика
ssh remote-server "iftop -t -s 10"
```

## Безопасность

### Рекомендации по безопасности

1. **Использование ключей вместо паролей**:
   - Всегда используйте SSH ключи для аутентификации
   - Защищайте приватные ключи паролем (passphrase)
   - Регулярно ротируйте ключи

2. **Ограничение доступа**:
   - Используйте принцип наименьших привилегий
   - Настройте firewall для ограничения доступа
   - Используйте VPN для дополнительной защиты

3. **Мониторинг подключений**:
   ```bash
   # Просмотр активных SSH сессий
   ssh remote-server "who"
   
   # Просмотр истории подключений
   ssh remote-server "last | head -20"
   ```

4. **Шифрование данных**:
   - Всегда используйте SSH для передачи данных
   - Используйте TLS/SSL для веб-сервисов
   - Шифруйте чувствительные данные перед передачей

### Настройка SSH для повышенной безопасности

В файле `/etc/ssh/sshd_config` на удаленном сервере:

```
# Отключение входа по паролю
PasswordAuthentication no

# Отключение root входа
PermitRootLogin no

# Ограничение пользователей
AllowUsers deploy admin

# Таймаут неактивных сессий
ClientAliveInterval 300
ClientAliveCountMax 2
```

## Примеры использования

### Пример 1: Проверка статуса приложения

```bash
#!/bin/bash
# Скрипт для проверки статуса приложения на удаленном сервере

REMOTE_SERVER="remote-server.com"
REMOTE_USER="deploy"

ssh ${REMOTE_USER}@${REMOTE_SERVER} << 'EOF'
    echo "Checking application status..."
    
    # Проверка процесса
    if pgrep -f "app.py" > /dev/null; then
        echo "✓ Application process is running"
    else
        echo "✗ Application process is NOT running"
        exit 1
    fi
    
    # Проверка HTTP endpoint
    if curl -f http://localhost:8080/health > /dev/null 2>&1; then
        echo "✓ Health endpoint is responding"
    else
        echo "✗ Health endpoint is NOT responding"
        exit 1
    fi
    
    # Проверка базы данных
    if pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
        echo "✓ Database is accessible"
    else
        echo "✗ Database is NOT accessible"
        exit 1
    fi
EOF
```

### Пример 2: Развертывание и тестирование

```bash
#!/bin/bash
# Скрипт для развертывания и тестирования на удаленном сервере

REMOTE_SERVER="remote-server.com"
REMOTE_USER="deploy"
APP_DIR="/opt/app"

# Развертывание
scp -r ./dist/* ${REMOTE_USER}@${REMOTE_SERVER}:${APP_DIR}/

# Перезапуск сервиса
ssh ${REMOTE_USER}@${REMOTE_SERVER} "sudo systemctl restart app.service"

# Ожидание запуска
sleep 5

# Тестирование
ssh ${REMOTE_USER}@${REMOTE_SERVER} << 'EOF'
    # Проверка статуса
    systemctl status app.service --no-pager
    
    # Проверка логов на ошибки
    if journalctl -u app.service --since "1 minute ago" | grep -i error; then
        echo "Errors found in logs!"
        exit 1
    fi
    
    # Проверка HTTP ответа
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/health)
    if [ "$HTTP_CODE" -eq 200 ]; then
        echo "Application is healthy"
    else
        echo "Application health check failed: HTTP $HTTP_CODE"
        exit 1
    fi
EOF
```

### Пример 3: Сбор диагностической информации

```bash
#!/bin/bash
# Скрипт для сбора диагностической информации

REMOTE_SERVER="remote-server.com"
REMOTE_USER="deploy"
OUTPUT_FILE="diagnostics_$(date +%Y%m%d_%H%M%S).txt"

ssh ${REMOTE_USER}@${REMOTE_SERVER} << 'EOF' > ${OUTPUT_FILE}
    echo "=== System Information ==="
    uname -a
    cat /etc/os-release
    uptime
    
    echo -e "\n=== Resource Usage ==="
    free -h
    df -h
    top -bn1 | head -20
    
    echo -e "\n=== Network Information ==="
    ip addr show
    ss -tuln
    
    echo -e "\n=== Service Status ==="
    systemctl list-units --type=service --state=running | head -20
    
    echo -e "\n=== Recent Logs ==="
    journalctl --since "1 hour ago" | tail -50
EOF

echo "Diagnostics saved to ${OUTPUT_FILE}"
```

### Пример 4: Удаленная отладка через порт-форвардинг

```bash
# Создание SSH туннеля для доступа к удаленному сервису
ssh -L 8080:localhost:8080 \
    -L 5432:localhost:5432 \
    -L 9229:localhost:9229 \
    remote-server.com

# Теперь можно обращаться к:
# - Веб-приложению: http://localhost:8080
# - Базе данных: localhost:5432
# - Node.js debugger: localhost:9229
```

## Интеграция с Cursor агентом

Cursor агент может автоматически использовать удаленные подключения для:

1. **Автоматическое тестирование**:
   - Запуск тестов на удаленном сервере после деплоя
   - Проверка работоспособности после изменений
   - Мониторинг производительности

2. **Диагностика в реальном времени**:
   - Автоматический сбор логов при ошибках
   - Анализ метрик производительности
   - Отслеживание изменений в системе

3. **Удаленная разработка**:
   - Редактирование файлов на удаленном сервере
   - Запуск команд в удаленной среде
   - Отладка приложений через SSH туннель

## Заключение

Подключение Cursor агента к удаленному серверу открывает широкие возможности для автоматизации тестирования, диагностики и разработки. Правильная настройка SSH, соблюдение принципов безопасности и использование автоматизированных скриптов позволяют эффективно работать с удаленными окружениями.

При работе с удаленными серверами всегда помните о безопасности, логируйте все действия и используйте принцип наименьших привилегий для минимизации рисков.

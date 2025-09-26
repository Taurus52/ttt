# Инструкция по развертыванию CodeReview Bot

## 📋 Предварительные требования

- Сервер с Ubuntu 22.04 LTS
- Минимум 1 GB RAM
- 10 GB свободного места на диске
- Доступ к серверу по SSH с правами root

## 🚀 Пошаговая инструкция развертывания

### Шаг 1: Подготовка Telegram бота

1. Откройте Telegram и найдите @BotFather
2. Отправьте команду `/newbot`
3. Следуйте инструкциям:
   - Придумайте имя для бота (например: CodeReview Bot)
   - Придумайте username (должен заканчиваться на 'bot', например: codereview_company_bot)
4. Сохраните полученный токен - он понадобится для конфигурации

### Шаг 2: Получение вашего Telegram ID

1. Найдите в Telegram бота @userinfobot
2. Отправьте ему команду `/start`
3. Бот покажет ваш ID - сохраните его

### Шаг 3: Копирование файлов на сервер

На вашем локальном компьютере выполните:

```bash
# Создайте архив с проектом
cd /workspace
tar -czf codereview-bot.tar.gz codereview-bot/

# Скопируйте на сервер
scp codereview-bot.tar.gz root@85.198.83.158:/tmp/

# Подключитесь к серверу
ssh root@85.198.83.158
```

### Шаг 4: Установка на сервере

На сервере выполните:

```bash
# Распакуйте архив
cd /opt
tar -xzf /tmp/codereview-bot.tar.gz
cd codereview-bot

# Запустите скрипт установки
./scripts/server_setup.sh
```

### Шаг 5: Настройка конфигурации

```bash
# Создайте файл конфигурации
cp .env.example .env

# Отредактируйте конфигурацию
nano .env
```

Измените следующие параметры:

```env
BOT_TOKEN=ВСТАВЬТЕ_ТОКЕН_ОТ_BOTFATHER
ADMIN_TG_ID=ВСТАВЬТЕ_ВАШ_TELEGRAM_ID
DB_PASSWORD=ПРИДУМАЙТЕ_СЛОЖНЫЙ_ПАРОЛЬ
```

Сохраните файл (Ctrl+X, затем Y, затем Enter).

### Шаг 6: Запуск бота

```bash
# Запустите развертывание
./scripts/deploy.sh
```

### Шаг 7: Проверка работы

1. Проверьте статус контейнеров:
   ```bash
   docker-compose ps
   ```

2. Посмотрите логи бота:
   ```bash
   docker-compose logs -f bot
   ```

3. Откройте Telegram и найдите вашего бота по username
4. Отправьте команду `/start`

### Шаг 8: Настройка автозапуска

```bash
# Включите автозапуск при перезагрузке сервера
systemctl enable codereview-bot
```

## 🔧 Управление ботом

### Остановка бота

```bash
docker-compose down
# или
systemctl stop codereview-bot
```

### Запуск бота

```bash
docker-compose up -d
# или
systemctl start codereview-bot
```

### Перезапуск бота

```bash
docker-compose restart
# или
systemctl restart codereview-bot
```

### Обновление бота

```bash
# Остановите бота
docker-compose down

# Обновите код (если используете git)
git pull

# Пересоберите и запустите
docker-compose build
docker-compose up -d
```

## 📊 Мониторинг и обслуживание

### Просмотр логов

```bash
# Последние 100 строк логов
docker-compose logs --tail=100 bot

# Следить за логами в реальном времени
docker-compose logs -f bot

# Логи за определенный период
docker-compose logs --since="2024-01-01" bot
```

### Резервное копирование базы данных

```bash
# Создать резервную копию
docker-compose exec postgres pg_dump -U postgres codereview_bot > backup_$(date +%Y%m%d_%H%M%S).sql

# Восстановить из резервной копии
docker-compose exec -T postgres psql -U postgres codereview_bot < backup_20240101_120000.sql
```

### Доступ к базе данных через Adminer

1. Откройте в браузере: http://85.198.83.158:8080
2. Введите:
   - Система: PostgreSQL
   - Сервер: postgres
   - Пользователь: postgres
   - Пароль: (из .env файла)
   - База данных: codereview_bot

## 🔒 Рекомендации по безопасности

1. **Смените пароль root на сервере:**
   ```bash
   passwd
   ```

2. **Настройте firewall:**
   ```bash
   # Разрешите только необходимые порты
   ufw allow 22/tcp    # SSH
   ufw deny 8080/tcp   # Закройте Adminer извне
   ufw enable
   ```

3. **Создайте отдельного пользователя для управления:**
   ```bash
   adduser botadmin
   usermod -aG docker botadmin
   ```

4. **Настройте SSH ключи вместо паролей**

5. **Регулярно обновляйте систему:**
   ```bash
   apt update && apt upgrade -y
   ```

## ❓ Частые проблемы

### Бот не отвечает на команды

1. Проверьте правильность токена в .env
2. Убедитесь, что бот запущен: `docker-compose ps`
3. Проверьте логи на наличие ошибок

### Ошибка "Пользователь не найден"

Пользователь должен сначала написать боту `/start`

### База данных не запускается

1. Проверьте свободное место на диске: `df -h`
2. Проверьте логи PostgreSQL: `docker-compose logs postgres`
3. Попробуйте пересоздать volume: 
   ```bash
   docker-compose down -v
   docker-compose up -d
   ```

## 📞 Контакты для поддержки

При возникновении проблем обращайтесь к администратору системы.
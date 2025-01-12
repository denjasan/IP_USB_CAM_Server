# IP_USB_CAM_Server

## Project structure
```commandline
IP_USB_CAM_Server/
├── static/                     # Статические файлы (CSS, JS, изображения, HTML)
│   ├── main_page.html
│   ├── video_player.html
│   └── videos.html
├── media/                     # Записи видео
│   └── 172_32_0_93
│       └── <date>_<time>_<id in DB>.mp4
├── docs/                       # Документация проекта
├── requirements.txt            # Список зависимостей Python
├── README.md                   # Описание проекта
├── db_functions                # Функции для работы с Базой Данных
├── config.json                 # Параметры для конфигурации сервера
└── server.py                   # Сам сервер
```

## Описание
Сервер для работы с видеорегистратором на базе миниатюрного одноплатного компьютера Luckfox Pico. Сервер обрабатывает видеопотоки с USB-камер, сохраняет записи, обеспечивает возможность воспроизведения видео через веб-интерфейс и отправляет уведомления о сбоях системы. Проект может быть использован для систем безопасности и видеонаблюдения в различных областях.

## Основные функции:
- **Непрерывная запись видео** при обнаружении движения.
- **Сохранение видео** с метаданными, включая дату, время и описание.
- **Обработчик уведомлений о сбоях** (питание, температура, сбой в системе).
- **Воспроизведение видео** через веб-интерфейс.
- **Перезапись видео** на накопителе при нехватке места.
  
## Запуск сервера:
1. Убедитесь, что у вас установлен Python 3.8+ и все зависимости:
   ```bash
   pip install -r requirements.txt
   ```
2. Отредактируйте файл `config.json` для указания конфигурации сервера, например, IP-адреса хоста и пути для хранения видео.
3. Запустите сервер:
   ```bash
   python server.py
   ```
4. Откройте браузер и перейдите по следующему адресу для просмотра доступных видео:
   ```
   http://<your-server-ip>:8080/videos
   ```

## Конфигурация
Конфигурация сервера хранится в файле `config.json`. Пример:
```json
{
    "ip_cameras": [
        "172.32.0.93"
    ]
}
```

## Примечания:
- Видео сохраняются в формате `.mp4`, `.mkv`, `.avi` и могут быть проиграны через веб-интерфейс.
- Веб-интерфейс доступен на `http://<server-ip>:8080/videos`.


## Работа с БД:
Инициализация БД и создание тестовых метаданных для видео media/172_32_0_93/2025_01_11_15_50_id1.mp4
```commandline
python db_functions.py
```
После запуска создастся metadata.db, где все будет

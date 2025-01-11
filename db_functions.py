import sqlite3

from datetime import datetime

def test_data():
    # Соединение с базой данных
    conn = sqlite3.connect('metadata.db')
    cursor = conn.cursor()

    # Вставка данных в таблицу MetaData
    video_path = "videos/172_32_0_93/2025_01_11_15_50_id1.mp4"
    start_time = "15:50:00"

    cursor.execute('''
        INSERT INTO MetaData (video_path, start_time)
        VALUES (?, ?)
    ''', (video_path, start_time))

    # Вставка данных в таблицу Actions
    action = "появился человек"
    action_time = "15:50:12"
    cursor.execute('''
        INSERT INTO Actions (video_id, action, action_time)
        VALUES (?, ?, ?)
    ''', (1, action, action_time))

    action = "рука закрывает камеру"
    action_time = "15:50:15"
    cursor.execute('''
            INSERT INTO Actions (video_id, action, action_time)
            VALUES (?, ?, ?)
        ''', (1, action, action_time))

    # Сохраняем изменения в базе данных и закрываем соединение
    conn.commit()
    conn.close()

    print("Test data inserted successfully.")

def initialize_database():
    # Создаем подключение к базе данных
    conn = sqlite3.connect('metadata.db')
    cursor = conn.cursor()

    # Создание таблицы MetaData
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS MetaData (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        video_path TEXT,
        start_time TEXT
    )
    ''')

    # Создание таблицы Actions
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Actions (
        video_id INTEGER,
        action TEXT,
        action_time TEXT,
        FOREIGN KEY (video_id) REFERENCES MetaData(id)
    )
    ''')

    # Создание таблицы Masks
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Masks (
        ip_cam_address TEXT,
        mask1 TEXT,
        mask2 TEXT
    )
    ''')

    # Сохранение изменений и закрытие подключения
    conn.commit()
    conn.close()
    print("Database initialized successfully.")

def get_actions_for_video(video_id):
    """Получаем все действия для конкретного видео."""
    conn = sqlite3.connect('metadata.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT action, action_time FROM Actions
        WHERE video_id = ?
    ''', (video_id,))

    actions = cursor.fetchall()
    conn.close()

    return actions

def search_actions(query):
    conn = sqlite3.connect('metadata.db')
    cursor = conn.cursor()

    # Выполняем поиск по действиям
    cursor.execute('''
    SELECT a.action, a.action_time, m.video_path
    FROM Actions a
    JOIN MetaData m ON a.video_id = m.id
    WHERE a.action LIKE ?
    ''', ('%' + query + '%',))

    actions = cursor.fetchall()

    conn.close()

    return actions

if __name__ == "__main__":
    # Вызов функции для инициализации базы данных
    initialize_database()
    test_data()

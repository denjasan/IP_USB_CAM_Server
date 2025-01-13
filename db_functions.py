import sqlite3
from datetime import datetime
import json


def delete_masks_by_ip(ip_cam_address):
    """
    Удаляет все маски для указанного IP-адреса камеры.
    """
    conn = sqlite3.connect('metadata.db')
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM Masks WHERE ip_cam_address = ?", (ip_cam_address,))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Ошибка удаления масок: {e}")
        return False
    finally:
        conn.close()
    return True


def db_save_masks(ip_cam_address, masks):
    conn = sqlite3.connect('metadata.db')
    cursor = conn.cursor()
    try:
        print(masks)
        cursor.execute('DELETE FROM Masks WHERE ip_cam_address = ?', (ip_cam_address,))
        data = [(ip_cam_address, json.dumps(mask)) for mask in masks]
        cursor.executemany('INSERT INTO Masks (ip_cam_address, mask) VALUES (?, ?)', data)
        conn.commit()
        print(f"Сохранено {len(masks)} масок для {ip_cam_address}")
    except sqlite3.Error as e:
        print(f"Ошибка сохранения масок: {e}")
    finally:
        conn.close()


def get_masks(ip_cam_address):
    conn = sqlite3.connect('metadata.db')
    cursor = conn.cursor()
    cursor.execute('SELECT mask FROM Masks WHERE ip_cam_address = ?', (ip_cam_address,))
    rows = cursor.fetchall()
    conn.close()

    # Преобразуем список строк JSON в список объектов
    return [json.loads(row[0]) for row in rows] if rows else []

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
    action = "humAn detected".lower()
    action_time = "15:50:12"
    cursor.execute('''
        INSERT INTO Actions (video_id, action, action_time)
        VALUES (?, ?, ?)
    ''', (1, action, action_time))

    action = "HanD close the caMera".lower()
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
        mask TEXT
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
    ''', ('%' + query.lower() + '%',))

    actions = cursor.fetchall()

    conn.close()

    return actions

if __name__ == "__main__":
    # Вызов функции для инициализации базы данных
    initialize_database()
    test_data()

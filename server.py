import os
import json
from http.server import HTTPServer, SimpleHTTPRequestHandler
from jinja2 import Environment, FileSystemLoader
import sqlite3

from db_functions import search_actions, get_actions_for_video, get_masks, db_save_masks, delete_masks_by_ip


class CustomHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        with open("config.json", 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        # Правильная инициализация Jinja2 для загрузки шаблонов
        self.env = Environment(loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), 'static')))
        super().__init__(*args, **kwargs)

    def do_GET(self):
        """Обработка GET-запросов."""
        if self.path == '/':
            self.render_main_page()
        elif self.path == '/videos':
            self.render_videos_page()
        elif self.path.startswith('/videos/') and len(self.path.split('/')) >= 4:
            self.render_video_player()
        elif self.path.startswith('/masks/'):
            self.render_masks_page(self.path.split('/')[-1])
        elif self.path.startswith('/search'):
            self.search_for_actions()
        else:
            super().do_GET()

    def do_POST(self):
        if self.path.startswith('/save_masks/'):
            self.save_masks()
        elif self.path.startswith('/clear_masks/'):
            self.clear_masks()
        elif self.path.startswith('/trans_data/'):
            self.take_data()

    def take_data(self):
        data = {
            'pir': True,  # Движение обнаружено
            'temperature': 29.2,  # Пример температуры
            'humidity': 88,  # Пример влажности
            'action': "door open",  # Пример действия
        }
        # ToDo: добавляем запись 30 секунд по 16 кадров, получаемых по rtsp, удаляем первую, если приходит action.None,
        #  если не будет пакета, то камера выключена, температуру и влажность передаем на главную страницу

    def clear_masks(self):
        ip_cam_address = self.path[len('/clear_masks/'):]
        success = delete_masks_by_ip(ip_cam_address)

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        if success:
            self.wfile.write(json.dumps({"message": "Masks saved successfully!"}).encode("utf-8"))
        else:
            self.wfile.write(json.dumps({"message": "Error!"}).encode("utf-8"))

    def save_masks(self):
        ip_cam_address = self.path.split('/')[-1]
        content_length = int(self.headers['Content-Length'])
        post_data = json.loads(self.rfile.read(content_length).decode('utf-8'))

        # Получение масок из запроса
        masks = post_data.get('masks', [])

        # Проверяем, что маски есть
        if not masks:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'No masks provided')
            return

        # Сохраняем маски
        db_save_masks(ip_cam_address, masks)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(json.dumps({'message': 'Masks updated successfully'}).encode('utf-8'))

    def render_masks_page(self, ip_cam_address):
        """Отображение страницы для настройки масок."""
        static_dir = os.path.join(".", "static")
        masks_template = os.path.join(static_dir, "masks.html")
        image_path = os.path.join(static_dir, "images", f"{ip_cam_address}.jpg")

        if not os.path.exists(masks_template):
            self.send_error(404, "masks.html not found")
            return

        if not os.path.exists(image_path):
            image_url = "/static/images/1.jpg"  # Путь к заглушке
        else:
            image_url = f"/static/images/{ip_cam_address}.jpg"

        masks = get_masks(ip_cam_address) or []
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()

        with open(masks_template, "r", encoding="utf-8") as file:
            template = self.env.from_string(file.read())  # Используем from_string для рендеринга
            rendered_content = template.render(
                ip_cam_address=ip_cam_address,
                old_masks=masks,
                image_url=image_url
            )
            self.wfile.write(rendered_content.encode("utf-8"))

    def render_video_player(self):
        """Отображение страницы видео с действиями."""
        # Получаем название видео из URL
        video_name = self.path[len('/videos/'):]
        video_path = os.path.join("videos", video_name)

        # Проверяем, существует ли видеофайл
        if not os.path.exists(f"./media/{video_name}"):
            self.send_error(404, "Video file not found")
            return

        # Извлекаем ID видео из базы данных
        conn = sqlite3.connect('metadata.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id FROM MetaData WHERE video_path = ?
        ''', (video_path,))
        video_id_row = cursor.fetchone()

        if video_id_row is None:
            self.send_error(404, "MetaData not found for this video")
            conn.close()
            return

        video_id = video_id_row[0]

        # Получаем действия для этого видео
        actions = get_actions_for_video(video_id)
        conn.close()

        # Генерируем HTML для страницы видео с использованием шаблона
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()

        template = self.env.get_template('video_player.html')  # Загружаем шаблон
        rendered_content = template.render(
            video_name=video_name,
            video_url=f"/media/{video_name}",  # Путь для браузера
            actions=actions
        )
        self.wfile.write(rendered_content.encode("utf-8"))

    def render_main_page(self):
        """Отображение главной страницы."""
        static_dir = os.path.join(".", "static")
        index_file = os.path.join(static_dir, "main_page.html")

        if not os.path.exists(index_file):
            self.send_error(404, "main_page.html file not found")
            return

        # Получаем список камер и их прямых трансляций
        cameras = self.get_camera_stream_urls()

        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()

        with open(index_file, "r", encoding="utf-8") as file:
            template = self.env.from_string(file.read())  # Используем from_string для рендеринга
            rendered_content = template.render(cameras=cameras)
            self.wfile.write(rendered_content.encode("utf-8"))

    def render_videos_page(self):
        """Отображение страницы с видео и поиском."""
        static_dir = os.path.join(".", "static")
        videos_file = os.path.join(static_dir, "videos.html")

        if not os.path.exists(videos_file):
            self.send_error(404, "videos.html file not found")
            return

        # Получаем список видео для всех камер
        videos = self.get_videos_for_cameras()

        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()

        with open(videos_file, "r", encoding="utf-8") as file:
            template = self.env.from_string(file.read())  # Используем from_string для рендеринга
            rendered_content = template.render(videos=videos, actions=[])
            self.wfile.write(rendered_content.encode("utf-8"))

    def search_for_actions(self):
        # Получаем поисковый запрос
        query = self.path.split('?')[1].split('=')[1]
        # Ищем действия в базе данных
        actions = search_actions(query)
        formatted_actions = [
            {
                'action_name': action[0].lower(),  # Приводим к нижнему регистру
                'timestamp': action[1],
                'video_url': action[2]
            }
            for action in actions
        ]

        # Отображаем страницу с результатами поиска
        static_dir = os.path.join(".", "static")
        videos_file = os.path.join(static_dir, "videos.html")

        if not os.path.exists(videos_file):
            self.send_error(404, "videos.html file not found")
            return

        # Получаем список видео для всех камер
        videos = self.get_videos_for_cameras()

        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()

        with open(videos_file, "r", encoding="utf-8") as file:
            template = self.env.from_string(file.read())  # Используем from_string для рендеринга
            rendered_content = template.render(videos=videos, actions=formatted_actions)
            self.wfile.write(rendered_content.encode("utf-8"))

    def get_videos_for_cameras(self):
        """Возвращает список видео для всех камер."""
        videos = []
        video_base_dir = self.config.get("video_directory", "./media")

        # Проходим по каждой камере
        for ip in self.config.get("ip_cameras", []):
            camera_video_dir = os.path.join(video_base_dir, ip.replace(".", "_"))
            if os.path.exists(camera_video_dir):
                # Получаем все видеофайлы из папки камеры
                video_files = [
                    f for f in os.listdir(camera_video_dir)
                    if
                    os.path.isfile(os.path.join(camera_video_dir, f)) and f.lower().endswith(('.mp4', '.mkv', '.avi'))
                ]
                for video in video_files:
                    videos.append({
                        "ip": ip,
                        "video_path": os.path.join("/media", ip.replace(".", "_"), video),
                        "video_name": video,
                        "video_url": os.path.join("/videos", ip.replace(".", "_"), video)
                    })
        return videos

    def get_camera_stream_urls(self):
        """Возвращает список камер и их URL для прямой трансляции."""
        cameras = []
        ip_cameras = self.config.get("ip_cameras", [])
        for ip in ip_cameras:
            cameras.append({
                "ip": ip,
                "stream_url": f"rtsp://{ip}/stream",
                "is_active": True
            })
        return cameras


def run(server_class=HTTPServer, handler_class=CustomHandler, port=8080):
    server_address = ('192.168.1.12', port) # 192.168.0.3
    httpd = server_class(server_address, handler_class)
    print(f"Server running http://{server_address[0]}:{server_address[1]}/...")
    httpd.serve_forever()

if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        print("\nServer stopped.")

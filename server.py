import os
import json
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import unquote
from jinja2 import Template  # Для рендеринга HTML-шаблонов
import sqlite3
import mimetypes

from db_functions import search_actions, get_actions_for_video


class CustomHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, config=None, **kwargs):
        self.config = config
        super().__init__(*args, **kwargs)

    def do_GET(self):
        """Обработка GET-запросов."""
        if self.path == '/':
            self.render_main_page()
        elif self.path == '/videos':
            self.render_videos_page()
        elif self.path.startswith('/videos/') and len(self.path.split('/')) >= 4:
            self.show_video_page()
        else:
            super().do_GET()

    def show_video_page(self):
        """Отображение страницы видео с действиями."""
        # Получаем название видео из URL
        video_name = self.path[len('/videos/'):]
        video_path = os.path.join("videos", video_name)

        # Проверяем, существует ли видеофайл
        # if not os.path.exists(video_path):
        #     self.send_error(404, "Video file not found")
        #     return

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

        # Загружаем шаблон
        static_dir = os.path.join(".", "static")
        video_template_file = os.path.join(static_dir, "video_player.html")

        if not os.path.exists(video_template_file):
            self.send_error(404, "Template file not found")
            return

        with open(video_template_file, "r", encoding="utf-8") as file:
            template = Template(file.read())
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
            template = Template(file.read())
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
            template = Template(file.read())
            rendered_content = template.render(videos=videos)
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
                "stream_url": f"rtsp://{ip}/live/0"  # Формируем ссылку для rtsp потока
            })
        return cameras


def load_config(config_path="config.json"):
    """Загрузка конфигурации из JSON."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file '{config_path}' not found!")
    with open(config_path, "r") as file:
        return json.load(file)


def run(server_class=HTTPServer, handler_class=CustomHandler, config_path="config.json"):
    """Запуск сервера."""
    config = load_config(config_path)

    server_host = config.get("server_host", "localhost")
    server_port = config.get("server_port", 8080)
    server_address = (server_host, server_port)

    httpd = server_class(server_address, lambda *args, **kwargs: handler_class(*args, config=config, **kwargs))
    print(f"Server running on http://{server_host}:{server_port}/")
    print(f"Videos available at http://{server_host}:{server_port}/videos")
    httpd.serve_forever()


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        print("\nServer stopped.")

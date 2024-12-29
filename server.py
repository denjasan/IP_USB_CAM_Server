import os
import json
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import unquote


class CustomHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, config=None, **kwargs):
        self.config = config
        super().__init__(*args, **kwargs)

    def do_GET(self):
        """Обработка GET-запросов."""
        if self.path == '/videos':
            self.list_videos()
        elif self.path.startswith('/videos/'):
            self.stream_video()
        else:
            super().do_GET()

    def list_videos(self):
        """Отображение списка доступных видео."""
        video_dir = self.config.get("video_directory", "./videos")
        if not os.path.exists(video_dir):
            self.send_error(404, "Video directory not found")
            return

        video_files = [
            f for f in os.listdir(video_dir)
            if os.path.isfile(os.path.join(video_dir, f)) and f.lower().endswith(('.mp4', '.mkv', '.avi'))
        ]

        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()

        # Генерация HTML
        self.wfile.write(b"<html><body><h1>Available Videos</h1><ul>")
        for video in video_files:
            video_path = f"/videos/{video}"
            self.wfile.write(f'<li><a href="{video_path}">{video}</a></li>'.encode('utf-8'))
        self.wfile.write(b"</ul></body></html>")

    def stream_video(self):
        """Стриминг видеофайла."""
        video_dir = self.config.get("video_directory", "./videos")
        video_name = unquote(self.path[len('/videos/'):])  # Убираем префикс `/videos/`
        video_path = os.path.join(video_dir, video_name)

        if not os.path.exists(video_path):
            self.send_error(404, "Video file not found")
            return

        self.send_response(200)
        self.send_header("Content-type", "video/mp4")  # Предполагаем формат mp4
        self.send_header("Content-Length", str(os.path.getsize(video_path)))
        self.end_headers()

        # Читаем файл блоками для отправки клиенту
        with open(video_path, "rb") as f:
            while chunk := f.read(8192):
                self.wfile.write(chunk)


def load_config(config_path="config.json"):
    """Загрузка конфигурации из JSON."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file '{config_path}' not found!")
    with open(config_path, "r") as file:
        return json.load(file)


def prepare_directories(config):
    """Подготовка директорий на основе конфигурации."""
    video_dir = config.get("video_directory", "./videos")
    if not os.path.exists(video_dir):
        os.makedirs(video_dir)
        print(f"Created video directory: {video_dir}")


def run(server_class=HTTPServer, handler_class=CustomHandler, config_path="config.json"):
    """Запуск сервера."""
    config = load_config(config_path)
    prepare_directories(config)

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

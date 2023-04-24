from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import pathlib
import mimetypes
import socket
import threading
from os import path, mkdir, getcwd
from datetime import datetime
import json


UDP_IP = "127.0.0.1"
UDP_PORT = 5000


class HttpHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path)
        if pr_url.path == "/":
            self.send_html_file("index.html")
        elif pr_url.path == "/message":
            self.send_html_file("contact.html")
        else:
            if pathlib.Path().joinpath(pr_url.path[1:]).exists():
                self.send_static()
            else:
                self.send_html_file("error.html", 404)

    def do_POST(self):
        data = self.rfile.read(int(self.headers["Content-Length"]))
        print(data)
        run_client(UDP_IP, UDP_PORT, data)
        self.send_response(302)
        self.send_header("Location", "/")
        self.end_headers()

    def send_html_file(self, filename, status=200):
        self.send_response(status)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        with open(filename, "rb") as fd:
            self.wfile.write(fd.read())

    def send_static(self):
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        if mt:
            self.send_header("Content-type", mt[0])
        else:
            self.send_header("Content-type", "text/plain")
        self.end_headers()
        with open(f".{self.path}", "rb") as file:
            self.wfile.write(file.read())


def run_http(server_class=HTTPServer, handler_class=HttpHandler):
    server_address = ("", 3000)
    http = server_class(server_address, handler_class)
    try:
        http.serve_forever()
    except KeyboardInterrupt:
        http.server_close()


def run_client(ip, port, raw_data):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server = ip, port
    sock.sendto(raw_data, server)
    print(f"Send data: {raw_data.decode()} to server: {server}")
    response, address = sock.recvfrom(1024)
    print(f"Response data: {response.decode()} from address: {address}")
    sock.close()


def run_socket(ip, port):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        server = ip, port
        sock.bind(server)
        print("We are in socket")
        try:
            while True:
                data, address = sock.recvfrom(1024)
                print(f"Received data: {data.decode()} from: {address}")
                data_parse = urllib.parse.unquote_plus(data.decode())
                message = {
                    key: value
                    for key, value in [el.split("=") for el in data_parse.split("&")]
                }
                data_dict = {}
                if path.exists(r".\storage\data.json"):
                    with open(r"storage\data.json", "r") as read_file:
                        data_dict = json.load(read_file)
                with open(r"storage\data.json", "w") as write_file:
                    data_dict[str(datetime.now())] = message
                    json.dump(data_dict, write_file, indent=2)
                sock.sendto(b"Mission completed", address)
                print(f"Send data: {data.decode()} to: {address}")
        except KeyboardInterrupt:
            print(f"Destroy server")
        finally:
            sock.close()


def creating_folder():
    if not path.exists(r".\storage"):
        file_path = getcwd() + r"\storage"
        mkdir(file_path)


if __name__ == "__main__":
    creating_folder()
    server = threading.Thread(target=run_http, args=())
    client = threading.Thread(target=run_socket, args=(UDP_IP, UDP_PORT))
    server.start()
    client.start()
    server.join()
    client.join()
    print("Done!")

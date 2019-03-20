from signal import signal, SIGINT, SIGTERM
from socket import socket, AF_INET, SOCK_STREAM, SHUT_RDWR
from multiprocessing import JoinableQueue, Pool
import datetime
import time
import os.path
N_WORKERS = 8
PORT = 8080

MIME_TYPES = {
    ".js": "text/javascript",
    ".ico": "image/x-icon",
    ".jpg": "image/jpeg",
    ".gif": "image/gif",
    ".png": "image/png",
    ".svg": "image/svg+xml",
    ".eot": "application/vnd.ms-fontobject",
    ".css": "text/css",
    ".webm": "video/webm",
    ".webp": "image/webp",
    ".wasm": "application/wasm",
    ".json": "application/json",
    ".html": "text/html",
    ".woff": "font/woff",
    ".woff2": "font/woff2",
}


class Request:
    def _parse_headers(self, lines):
        headers = {}
        for l in lines:
            l = l.split(": ")
            try:
                headers[l[0]] = l[1]
            except IndexError as _:
                pass
        return headers

    def __init__(self, buffer):
        split_point = buffer.find(b"\r\n\r\n")
        text = buffer[:split_point].decode("UTF-8")
        lines = text.split("\r\n")
        request = lines[0].split(" ")
        self.verb = request[0].upper()
        self.path = request[1]
        self.headers = self._parse_headers(lines[1:])
        self.body = buffer[split_point+4:]  # +4 to account for \r\n\r\n

    def __str__(self):
        return "{} {} HTTP/1.0 -- {}".format(self.verb, self.path, self.headers)


def worker_proc(conn, _addr):
    conn.setblocking(True)  # for sendfile
    request = Request(conn.recv(8192))
    print(request)
    if request.verb == 'GET':
        if request.path[0] != "/":
            conn.send(b"HTTP/1.0 400 Illegal\r\n\r\nPaths must start with '/'")
        else:
            if request.path[-1] == "/":
                request.path += "index.html"
            relative_filename = request.path[1:]
            if os.path.isfile(relative_filename):
                file_extension = os.path.splitext(relative_filename)[1]
                response = "HTTP/1.0 200 OK\r\nDate: {}\r\nContent-Type: {}\r\n\r\n".format(
                    datetime.datetime.now().isoformat(), MIME_TYPES.get(file_extension) or "text/plain")
                conn.send(response.encode('UTF-8'))
                with open(relative_filename, "rb") as bytestream:
                    conn.sendfile(bytestream)
            else:
                conn.send(b"HTTP/1.0 404 Not Found\r\n\r\n404 Not Found")
    else:
        conn.send(b'HTTP/1.0 500 Budget Exceeded\r\n\r\nPlease provide additional funding to motivate the implementation of non-GET methods')
    conn.shutdown(SHUT_RDWR)
    conn.close()


if __name__ == "__main__":
    with socket(AF_INET, SOCK_STREAM) as sock:
        sock.setblocking(False)
        sock.bind(("0.0.0.0", PORT))
        sock.listen(N_WORKERS)
        proc_pool = Pool(N_WORKERS)

        def exit_gracefully(signum, frame):
            print("Got request to terminate")
            try:
                sock.shutdown(SHUT_RDWR)
            except:
                print("Someone was still trying to use the socket. Hope they don't mind")
            finally:
                sock.close()
                proc_pool.close()
                print("Goodbye")
                exit(0)
        signal(SIGINT, exit_gracefully)
        signal(SIGTERM, exit_gracefully)

        while True:
            try:
                conn, addr = sock.accept()
            except (BlockingIOError, OSError) as _:
                # 100ms is pretty responsive, but doesn't kill my CPU
                time.sleep(0.1)
            else:
                proc_pool.apply_async(worker_proc, (conn, addr)).get()

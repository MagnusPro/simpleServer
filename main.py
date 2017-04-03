import socket
import os
import mimetypes
from contextlib import closing
from sys import argv

class server:
    def __init__(self, port=8000):
        self.port = port

    def run(self):
        """
        Start server
        """
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
            sock.bind(("localhost", self.port))
            sock.listen(10)
            while 1:
                conn, addr = sock.accept()
                try:
                    self._handle_client(conn)
                except Exception as e:
                    print(e)
                    self._send_error(conn, "500 Internal Server Error", message="Server error")
                finally:
                    conn.close()

    def _handle_client(self,conn):
        """
        Handle one client request
        """
        request = self._get_request(conn)
        if request is not None:
            request_header = request.split("\r\n", 1)[0]
            method, address, protocol = request_header.split(" ", 2)

            if method != "GET":
                self._send_error(conn, "404 Not Found", message="I cant handle Post request")
                return
            else:
                self._get_method(conn, address)

    def _get_method(self, conn, address):
        """
        Handle GET request
        """
        address = "." + address
        if os.path.isdir(address):
            index = os.path.join(address, "index.html")
            if os.path.isfile(index):
                self._send_file(conn, index)
            else:
                self._send_dir(conn, address)
        elif os.path.isfile(address):
            self._send_file(conn, address)
        else:
            self._send_error(conn, "404 Not Found", message="I cant handle Post request")

    def _http_header(self, conn, length, status="200 OK", typ="text/plain; charset=utf-8"):
        """
        Send request line and headers
        """
        conn.send(b"HTTP/1.1 " + status.encode("utf-8") + b"\r\n")
        conn.send(b"Server: simplehttp\r\n")
        conn.send(b"Connection: close\r\n")
        conn.send(b"Content-Type: " + typ.encode("utf-8") + b"\r\n")
        conn.send(b"Content-Length: " + str(length).encode("utf-8") + b"\r\n")
        conn.send(b"\r\n")

    def _get_request(self, conn):
        """
        Get client request
        """
        data = b""
        while not b"\r\n" in data:
            tmp = conn.recv(1024)
            if not tmp:
                break
            else:
                data += tmp

        if not data:
            return
        return data.decode("utf-8")

    def _send_file(self, conn, address):
        """
        Send file to client
        """
        send_type, encoding = mimetypes.guess_type(address)
        if send_type is None:
            send_type = "application/octet-stream"
        self._http_header(conn, os.path.getsize(address), typ=send_type)
        with open(address, "rb") as file:
            data = file.read(1024)
            while data:
                conn.send(data)
                data = file.read(1024)

    def _send_dir(self, conn, address):
        """
        Send dir structure to client
        """
        data = "<!DOCTYPE html>"
        data += "<html><head><title>Dir</title></head><body><h1>" + address[1:] + "</h1><ul>"
        for name in sorted(os.listdir(address)):
            link = os.path.join(address, name)
            if os.path.isdir(link):
                link += "/"
                name += "/"
            data += "<li><a href=" + link[1:] + ">" + name + "</a></li>"
        data += "</ul></body></html>"
        data = data.encode("utf-8")
        send_type = "text/html; charset=utf-8"
        self._http_header(conn, length=len(data), typ=send_type)
        conn.send(data)

    def _send_error(self, conn, status, message):
        """
        Send error to client
        """
        self._http_header(conn, len(message.encode("utf-8")), status)
        conn.send(message.encode("utf-8"))

if __name__ == "__main__":
    serv_port = 8000
    if len(argv) == 2:
        port = int(argv[1])
        if port in range(1, 65535):
            serv_port = port
    s = server(serv_port)
    s.run()
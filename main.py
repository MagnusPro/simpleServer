import socket
import os
import mimetypes
from contextlib import closing

class server:
    def __init__(self, port=8000):
        self.port = port

    def run(self):
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
            sock.bind(("localhost", self.port))
            sock.listen(10)
            while 1:
                conn, addr = sock.accept()
                print("New connection from ", addr)
                try:
                    self._handle_client(conn)
                except Exception as e:
                    print(e)
                    self._http_response(conn, "500 Internal Server Error", data=b"Server error")
                finally:
                    conn.close()

    def _handle_client(self,conn):

        request = self._get_request(conn)
        if request is not None:
            request_header = request.split("\r\n", 1)[0]
            method, address, protocol = request_header.split(" ", 2)

            if method != "GET":
                self._http_response(conn, "404 Not Found", data=b"I cant handle Post request")
                return
            else:
                self._get_method(conn, address)

    def _get_method(self, conn, address):
        send_type = "text/html; charset=utf-8"
        address = "." + address
        if os.path.isdir(address):
            index = os.path.join(address, "index.html")
            if os.path.isfile(index):
                answer, send_type = self._read_file(index) #(prepare_page(index)).encode("utf-8")
            else:
                answer = (self._show_dir(address)).encode("utf-8")
        elif os.path.isfile(address):
            answer, send_type = self._read_file(address)
        else:
            self._http_response(conn, "404 Not Found", data=b"I cant handle Post request")
            return

        self._http_response(conn, typ=send_type, data=answer)

    def _http_response(self, conn, status="200 OK", typ="text/plain; charset=utf-8", data=b""):
        # строка состояния
        conn.send(b"HTTP/1.1 " + status.encode("utf-8") + b"\r\n")
        # заголовки
        conn.send(b"Server: simplehttp\r\n")
        #conn.send(b"Connection: keep-alive\r\n")
        conn.send(b"Content-Type: " + typ.encode("utf-8") + b"\r\n")
        conn.send(b"Content-Length: " + str(len(data)).encode("utf-8") + b"\r\n")
        conn.send(b"\r\n")
        # тело
        conn.send(data)

    def _get_request(self, conn):
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

    def _read_file(self, address):
        send_type, encoding = mimetypes.guess_type(address)
        print(encoding)
        if send_type is None:
            send_type = "application/octet-stream"
        with open(address, "rb") as file:
            data = file.read()
        return data, send_type

    def _show_dir(self, address):
        data = "<!DOCTYPE html>"
        data += "<html><head><title>Dir</title></head><body><h1>" + address[1:] + "</h1><ul>"
        for name in os.listdir(address):
            link = os.path.join(address, name)
            if os.path.isdir(link):
                link += "/"
                name += "/"
            data += "<li><a href=" + link[1:] + ">" + name + "</a></li>"
        data += "</ul></body></html>"
        return data

if __name__ == "__main__":
    s = server()
    s.run()
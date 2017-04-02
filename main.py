import socket
import functools
import os
import mimetypes
from contextlib import closing

def http(func=None, *, status="200 OK", typ="text/plain; charset=utf-8"):
    if func is None:
        return lambda func: http(func,status=status, typ=typ)


    @functools.wraps(func)
    def inner(*args, **kwargs):
        data = func(*args, **kwargs)
        data = data.encode("utf-8")
        # строка состояния
        response = (b"HTTP/1.1 " + status.encode("utf-8") + b"\r\n")
        # заголовки
        response += b"Server: simplehttp\r\n"
        response += b"Connection: close\r\n"
        response += b"Content-Type: " + typ.encode("utf-8") + b"\r\n"
        response += b"Content-Length: " + bytes(len(data)) + b"\r\n"
        response += b"\r\n"
        # тело
        response += data
        return response


def prepare_page(page):
    with open(page) as file:
        data = file.read()
    return data

def show_dir(address):
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


def read_file(address):
    send_type,encoding = mimetypes.guess_type(address)
    print(encoding)
    if send_type is None:
        send_type = "application/octet-stream"
    with open(address, "rb") as file:
        data = file.read()
    return data, send_type


def get_request(conn):
    data = b""

    while not b"\r\n" in data:  # ждём первую строку
        tmp = conn.recv(1024)
        if not tmp:  # сокет закрыли, пустой объект
            break
        else:
            data += tmp

    if not data:  # данные не пришли
        return  # не обрабатываем

    return data.decode("utf-8")


def http_response(conn, status="200 OK", typ="text/plain; charset=utf-8", data=b""):
        # строка состояния
        conn.send(b"HTTP/1.1 " + status.encode("utf-8") + b"\r\n")
        #заголовки
        conn.send(b"Server: simplehttp\r\n")
        #conn.send(b"Connection: close\r\n")
        conn.send(b"Content-Type: " + typ.encode("utf-8") + b"\r\n")
        conn.send(b"Content-Length: " + str(len(data)).encode("utf-8") + b"\r\n")
        conn.send(b"\r\n")
        #тело
        conn.sendall(data)


def get_method(conn, address):

    #if(os.path.exists(address)):
    #    answer = read_file(address)
    send_type = "text/html; charset=utf-8"
    address = "." + address
    if os.path.isdir(address):
        index = os.path.join(address, "index.html")
        if os.path.isfile(index):
            answer = (prepare_page(index)).encode("utf-8")
        else:
            answer = (show_dir(address)).encode("utf-8")
    elif os.path.isfile(address):
        answer, send_type = read_file(address)
    else:
        http_response(conn, "404 Not Found", data=b"I cant handle Post request")
        return

    http_response(conn, typ=send_type, data=answer)


def handle_client(conn):

    request = get_request(conn)
    if request is not None:
        print(request)

        request_header = request.split("\r\n", 1)[0]
        method, address, protocol = request_header.split(" ", 2)

        if method != "GET":
            http_response(conn, "404 Not Found", data=b"I cant handle Post request")
            return
        else:
            get_method(conn, address)


def server():
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.bind(("localhost", 8080))
        sock.listen(10)
        while 1:  # работаем постоянно
            conn, addr = sock.accept()
            print("New connection from ", addr)
            try:
                handle_client(conn)
            except Exception as e:
                print(e)
                http_response(conn, "500 Internal Server Error", data=b"Server error")
            finally:
                # так при любой ошибке
                # сокет закроем корректно
                conn.close()

if __name__ == "__main__":
    server()
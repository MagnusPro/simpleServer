from http.server import BaseHTTPRequestHandler, HTTPServer
import os

class MyHandler(BaseHTTPRequestHandler):
    def list_files(self, startpath):
        for root, dirs, files in os.walk(startpath):
            level = root.replace(startpath, '').count(os.sep)
            indent = ' ' * 4 * (level)
            print('{}{}/'.format(indent, os.path.basename(root)))
            subindent = ' ' * 4 * (level + 1)
            for f in files:
                print('{}{}'.format(subindent, f))


    def do_GET(self):
        self.send_response(200)
        self.send_header('content-type','text/html')
        self.end_headers()
        '''
        if os.path.exists(name):
            with open(name) as file:
                message = file.read()
                self.wfile.write(bytes(message, "utf8"))
        '''
        if os.path.isdir(self.path):
            index = os.path.join(self.path,"index.html")
            


serv = HTTPServer(("127.0.0.1",8080), MyHandler)
serv.serve_forever()

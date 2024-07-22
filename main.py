import os
import socket
import datetime
import http.server
import socketserver
import multiprocessing
import urllib.parse
from pymongo import MongoClient

HOST, PORT = '', 3000
SOCKET_PORT = 5000

# MongoDB setup
client = MongoClient('mongodb://mongo:27017/')
db = client['message_db']
collection = db['messages']

class MyHttpRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.path = '/templates/index.html'
        elif self.path == '/message':
            self.path = '/templates/message.html'
        elif self.path.startswith('/static/'):
            self.path = self.path
        else:
            self.path = '/templates/error.html'
        
        return http.server.SimpleHTTPRequestHandler.do_GET(self)
    
    def do_POST(self):
        if self.path == '/submit':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            post_data = urllib.parse.parse_qs(post_data.decode('utf-8'))
            
            username = post_data['username'][0]
            message = post_data['message'][0]
            
            data = {
                'username': username,
                'message': message,
                'date': datetime.datetime.now().isoformat()
            }
            
            # Send data to socket server
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((HOST, SOCKET_PORT))
                s.sendall(str(data).encode('utf-8'))
            
            self.send_response(301)
            self.send_header('Location', '/')
            self.end_headers()

def run_http_server():
    handler = MyHttpRequestHandler
    with socketserver.TCPServer((HOST, PORT), handler) as httpd:
        print(f"Serving HTTP on port {PORT}")
        httpd.serve_forever()

def run_socket_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, SOCKET_PORT))
        s.listen()
        print(f"Socket server listening on port {SOCKET_PORT}")
        while True:
            conn, addr = s.accept()
            with conn:
                data = conn.recv(1024)
                if data:
                    message_data = eval(data.decode('utf-8'))
                    collection.insert_one(message_data)
                    print(f"Received and stored: {message_data}")

if __name__ == "__main__":
    p1 = multiprocessing.Process(target=run_http_server)
    p2 = multiprocessing.Process(target=run_socket_server)

    p1.start()
    p2.start()

    p1.join()
    p2.join()

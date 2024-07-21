import asyncio
import os
import socket
import threading
import json
from aiohttp import web
from pymongo import MongoClient
from datetime import datetime

# Налаштування MongoDB
mongo_client = MongoClient('mongodb://mongo:27017/')
db = mongo_client['message_db']
collection = db['messages']

# Функція для збереження повідомлень в MongoDB
def save_message_to_db(username, message):
    document = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"),
        "username": username,
        "message": message
    }
    collection.insert_one(document)

# Функція для обробки отриманих даних через сокет
def handle_socket_connection(conn):
    with conn:
        data = conn.recv(1024).decode('utf-8')
        if data:
            message_data = json.loads(data)
            save_message_to_db(message_data['username'], message_data['message'])
        conn.close()

# Функція для запуску Socket-сервера
def run_socket_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('0.0.0.0', 5000))
        s.listen()
        while True:
            conn, addr = s.accept()
            threading.Thread(target=handle_socket_connection, args=(conn,)).start()

# Обробка статичних файлів
async def handle_static(request):
    file_path = os.path.join('static', request.match_info['filename'])
    if os.path.isfile(file_path):
        return web.FileResponse(file_path)
    else:
        return web.Response(text='File not found', status=404)

# Обробка запиту на index.html
async def handle_index(request):
    return web.FileResponse(os.path.join('templates', 'index.html'))

# Обробка запиту на message.html
async def handle_message(request):
    return web.FileResponse(os.path.join('templates', 'message.html'))

# Обробка POST запиту з форми
async def handle_form(request):
    data = await request.post()
    username = data.get('username', '')
    message = data.get('message', '')
    
    # Відправлення даних на сокет сервер
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(('localhost', 5000))
            message_data = json.dumps({'username': username, 'message': message})
            s.sendall(message_data.encode('utf-8'))
    except Exception as e:
        print(f"Socket error: {e}")
    
    return web.HTTPFound('/')

# Обробка помилки 404
async def handle_404(request):
    return web.FileResponse(os.path.join('templates', 'error.html'), status=404)

# Налаштування маршрутизації
app = web.Application()
app.router.add_get('/', handle_index)
app.router.add_get('/message.html', handle_message)
app.router.add_post('/form', handle_form)
app.router.add_get('/static/{filename}', handle_static)
app.router.add_get('/error.html', handle_404)

# Запуск веб-сервера
if __name__ == '__main__':
    # Запуск Socket-сервера в окремому потоці
    socket_server_thread = threading.Thread(target=run_socket_server, daemon=True)
    socket_server_thread.start()

    # Запуск HTTP-сервера
    web.run_app(app, port=3000)

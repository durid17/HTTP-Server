import json
from threading import Thread
from time import sleep
import socket
import sys
import re
import time
import mimetypes
import magic

hosts = {}

def handle_request(request , client_sock , pair):
    keep_alive = False
    get = False
    head = False
    host = ""
    body = ""
    range = ""
    if 'keep-alive' in request: keep_alive = True
    l = request.split('\r\n')
    for elem in l:
        list = elem.split()
        if(len(list) == 0): continue
        if(list[0] == 'GET'): 
            get = True
            body = list[1]
        if(list[0] == 'HEAD'): 
            head = True
            body = list[1]            
        if(list[0] == 'Host:'): host = list[1].split(':')[0]
        if(list[0] == 'Range:'): 
            range = list[1][6:]
            print(range)
    # if head: print('head')
    # if head: print('get')

    body = host + body

    # if get: print('get')
    # if head: print('head')
    # if keep_alive: print('keep-alive')
    # print(body)
    if (not (host , host) in hosts[pair]):
        client_sock.sendall('HTTP/1.1 404 NOT FOUND\r\n'.encode())
        client_sock.sendall('Content-Type: text/html\r\n\r\n'.encode())
        client_sock.sendall('<html><head></head><body><h1>REQUESTED DOMAIN NOT FOUND</h1></body></html>'.encode())
        client_sock.close()
        return
    
    body = body.replace("%20" , ' ')
    with open(body, "rb") as f:
        f.seek(0, 0)
        data = f.read(-1)

    start = 0
    end = len(data)
    # print(range)
    if(range != ""):
        index = range.index("-")
        if index != 0: start = int(range[0: index])
        if index + 1 != len(range): end = int(range[index + 1: len(range)]) + 1

    # HTTP/1.1 200 OK
    # Date: Mon, 27 Jul 2009 12:28:53 GMT
    # Server: Apache/2.2.14 (Win32)
    # Last-Modified: Wed, 22 Jul 2009 19:15:56 GMT
    # Content-Length: 88
    # Content-Type: text/html

    # Connection: Closed
    client_sock.sendall('HTTP/1.1 200 OK\r\n'.encode())
    client_sock.sendall('Date: 13/32/32321\r\n'.encode())
    client_sock.sendall('etag: 321312\r\n'.encode())
    client_sock.sendall('server: 321312\r\n'.encode())
    length = 'content-length: ' + str(end - start) + '\r\n'
    client_sock.sendall(length.encode())
    s = 'Accept-Ranges: bytes\r\n'
    client_sock.sendall(s.encode())
    if keep_alive:
        client_sock.sendall('Connection: keep-alive\r\n'.encode())
        client_sock.sendall('Keep-Alive: timeout=5\r\n'.encode())
    if(body.find('jpg') > 0):
        client_sock.sendall("Content-Type: image/jpeg\r\n".encode())
        client_sock.send('\r\n'.encode())
    else: 
        type = 'Content-Type: ' + magic.from_buffer(data, mime = True)  + '\r\n'
        client_sock.sendall(type.encode())
        client_sock.send('\r\n'.encode())


    if get : client_sock.sendall(data[start:end])
    client_sock.close()


def client_thread(client_sock , pair):
    data = client_sock.recv(1024)
    newdata = data 
    while(len(newdata) == 1024):
        newdata = client_sock(1024)
        data = newdata + data
    request = data.decode()
    # print(request)
    handle_request(request , client_sock , pair)
    # client_sock.send('HTTP/1.1 200 OK\r\n'.encode())


def socket_thread(arg):
    # print("socket" )
    server_sock = socket.socket(socket.AF_INET , socket.SOCK_STREAM , 0)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind(arg)
    server_sock.listen()
    while True:
        client_sock , addr = server_sock.accept()
        thread = Thread(target =  client_thread, args = (client_sock, arg)) 
        thread.start()

       
if __name__ == "__main__":
    all_pairs = set()
    with open("config.json") as json_file:
        data = json.load(json_file)
        for p in data["server"]:
            if not (p["ip"] , p["port"]) in  hosts:
                hosts[(p["ip"] , p["port"])] = set()
            hosts[(p["ip"] , p["port"])].add((p["vhost"] , p["documentroot"]))
            all_pairs.add((p["ip"] , p["port"]))
    threads = []
    for pair in all_pairs:
        thread = Thread(target = socket_thread , args = (pair, )) 
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

import socket
import threading

def handle_client(client_socket):
    while True:
        data = client_socket.recv(4096)
        if not data:
            break
        # Process the received audio/video data
        # For example, call your emotion analysis here
        result = b"emotion:happy"  # Dummy result
        client_socket.sendall(result)
    client_socket.close()

def start_server(host='0.0.0.0', port=50007):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen(5)
    print(f"Listening on {host}:{port}")
    while True:
        client_sock, addr = server.accept()
        print(f"Accepted connection from {addr}")
        client_thread = threading.Thread(target=handle_client, args=(client_sock,))
        client_thread.start()

if __name__ == "__main__":
    start_server()
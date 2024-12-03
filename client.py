import socket

HOST = 'localhost'
PORT = 4670

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    client_socket.connect((HOST, PORT))
    print(f"Conectado al servidor {HOST}:{PORT}...")

    while True:
        message = input("Cliente dice: ")
        client_socket.sendall(message.encode())
        print(f"Cliente dice: {message}")

        data = client_socket.recv(1024)
        print(f"Servidor responde: {data.decode()}")

except ConnectionRefusedError:
    print(f"No se pudo conectar al servidor en {HOST}:{PORT}")
except KeyboardInterrupt:
    print("\nCliente cerrado manualmente.")
finally:
    client_socket.close()

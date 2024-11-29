import socket


HOST = '0.0.0.0'  
PORT = 4670 


server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST, PORT))
server_socket.listen(1) 

print(f"Servidor escuchando en {HOST}:{PORT}...")

try:
    conn, addr = server_socket.accept() 
    print(f"Conexión establecida con {addr}")
    
    while True:
        data = conn.recv(1024) 
        if not data:
            break
        print(f"Cliente dice: {data.decode()}")

        conn.sendall(b"Mensaje recibido")
        
except KeyboardInterrupt:
    print("\nServidor cerrado manualmente.")
finally:
    conn.close()
    server_socket.close()

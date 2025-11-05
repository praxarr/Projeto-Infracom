import socket
import sys
import os

BUFFER_SIZE = 1024

def main():
    if len(sys.argv) < 4:
        print("Entradas incorretas")
        sys.exit(1)

    SERVER_IP = sys.argv[1]
    SERVER_PORT = int(sys.argv[2])
    FILE_PATH = sys.argv[3]

    if not os.path.exists(FILE_PATH):
        print("Arquivo não encontrado:", FILE_PATH)
        sys.exit(1)

    filename = os.path.basename(FILE_PATH)
    filesize = os.path.getsize(FILE_PATH)

    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    end_servidor = (SERVER_IP, SERVER_PORT)

    udp.sendto(filename.encode('utf-8'), end_servidor)
    tamanho = str(filesize)
    udp.sendto(tamanho.encode('utf-8'), end_servidor)
    print(f"Enviando {filename} ({filesize} bytes) para {end_servidor}")

    with open(FILE_PATH, 'rb') as f:
        while True:
            chunk = f.read(BUFFER_SIZE)
            if not chunk:
                break
            udp.sendto(chunk, end_servidor)

    print("Envio completo. Aguardando devolução do servidor...")

    nome_bin, _ = udp.recvfrom(1024)
    nome_ret = nome_bin.decode('utf-8')
    tamanho_bin, _ = udp.recvfrom(1024)
    tamanho_ret = int(tamanho_bin.decode('utf-8'))
    print(f"Servidor devolverá: {nome_ret} ({tamanho_ret} bytes)")

    os.makedirs('downloads', exist_ok=True)
    end_final = os.path.join('downloads', nome_ret)

    received = 0
    n = 25
    with open(end_final, 'wb') as f:
        while received < tamanho_ret:
            chunk, _ = udp.recvfrom(BUFFER_SIZE)
            f.write(chunk)
            received += len(chunk)
            if received >= (n * (filesize // 100)) and n <= 100:
                print(f" -> %{n} do arquivo foi recebido")
                n += 25

    print("Arquivo devolvido salvo em:", end_final)
    udp.close()


main()
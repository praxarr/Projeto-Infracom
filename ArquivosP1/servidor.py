import socket
import os

BUFFER_SIZE = 1024
LISTEN_IP = '0.0.0.0'
LISTEN_PORT = 5012

def recv_file(udp):
    nome_bin, end_cliente =  udp.recvfrom(1024)
    filename = nome_bin.decode('utf-8')
    tamanho_bin, _ = udp.recvfrom(1024)
    filesize = int(tamanho_bin.decode('utf-8'))
    print(f"[{end_cliente}] Arquivo que será recebido: {filename} ({filesize} bytes)")

    os.makedirs('recebidos', exist_ok=True)
    saved_path = os.path.join('recebidos', filename)

    received = 0
    n = 25
    with open(saved_path, 'wb') as f:
        while received < filesize:
            chunk, _ = udp.recvfrom(BUFFER_SIZE)
            f.write(chunk)
            received += len(chunk)
            if received >= (n *(filesize // 100)) and n <= 100:
                 print(f" -> %{n} do arquivo foi recebido")
                 n += 25
    print(f"Arquivo salvo como: {saved_path}")

    nome_retorno = f"ret_{filename}"
    end_retorno = os.path.join('returned', nome_retorno)

    os.makedirs('returned', exist_ok=True)

    with open(saved_path, 'rb') as src, open(end_retorno, 'wb') as dst:
        dst.write(src.read())

    tamanho_ret = str(os.path.getsize(end_retorno))
    udp.sendto(nome_retorno.encode('utf-8'), end_cliente)
    udp.sendto(tamanho_ret.encode('utf-8'), end_cliente)
    with open(end_retorno, 'rb') as f:
        while True:
            chunk = f.read(BUFFER_SIZE)
            if not chunk:
                break
            udp.sendto(chunk, end_cliente)
    print(f"Arquivo retornado'{nome_retorno}' para {end_cliente}")

def main():
    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp.bind((LISTEN_IP, LISTEN_PORT))
    print(f"Servidor UDP escutando em {LISTEN_IP}:{LISTEN_PORT}")
    try:
        while True:
            recv_file(udp)
    except KeyboardInterrupt:
        print("Desligando servidor")
    finally:
        udp.close()

main()

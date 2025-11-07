import socket
import os

# Ip 0.0.0.0 indica que o servidor recebe arquivos de qualquer IP, incluindo IPs publicos

BUFFER_SIZE = 1024
LISTEN_IP = '0.0.0.0'
LISTEN_PORT = 5015



def recebe_arquivo(udp):
    # servidor inicialmente recebe o nome do arquivo a ser enviado pelo cliente e o endereco do remetente
    nome_bin, end_cliente =  udp.recvfrom(1024)
    # datagrama inicialmente em binario deve ser decodificado para str
    filename = nome_bin.decode('utf-8')
    # o segundo datagrama recebido pelo servidor se refere ao tamanho do arquivo
    tamanho_bin, _ = udp.recvfrom(1024)
    # datagrama precisa ser decodificado para str e depois castado para Int
    filesize = int(tamanho_bin.decode('utf-8'))
    print(f"[{end_cliente}] Arquivo que será recebido: {filename} ({filesize} bytes)")

    # Diretorio criado para escrever o arquivo enviado pelo cliente

    os.makedirs('recebidos', exist_ok=True)
    end_recebidos = os.path.join('recebidos', filename)

    received = 0
    n = 25
    
    # loop para realizar a escrita do arquivo apontado pelo diretorio a partir de cada datagrama que compoe o arquivo. 
    # escrita binaria eh utilizada para compatibilidade com diferentes tipos de arquivos
    with open(end_recebidos, 'wb') as f:
        while received < filesize:
            chunk, _ = udp.recvfrom(BUFFER_SIZE)
            f.write(chunk)
            received += len(chunk)
            # progresso do recebimento do arquivo printado no terminal durante execucao 
            if received >= (filesize * (n / 100)) and n <= 100:
                print(f" -> %{n} do arquivo foi recebido")
                n += 25
    print(f"Arquivo salvo como: {end_recebidos}")

    # Alteracao do nome do arquivo para envia-lo para o cliente
    nome_retorno = f"ret_{filename}"
    end_retorno = os.path.join('retornados', nome_retorno)

    # Criando um diretorio para arquivos retornados pelo servidor ao cliente
    os.makedirs('retornados', exist_ok=True)

    # copiando o arquivo original para a pasta de retornados
    with open(end_recebidos, 'rb') as src, open(end_retorno, 'wb') as dst:
        dst.write(src.read())

    # enviando o nome do arquivo atualizado e o seu tamanho
    tamanho_ret = str(os.path.getsize(end_retorno))
    udp.sendto(nome_retorno.encode('utf-8'), end_cliente)
    udp.sendto(tamanho_ret.encode('utf-8'), end_cliente)

    # loop para o envio de cada datagrama que compoe o arquivo retornado
    with open(end_retorno, 'rb') as f:
        while True:
            chunk = f.read(BUFFER_SIZE)
            if not chunk:
                break
            udp.sendto(chunk, end_cliente)
    print(f"Arquivo retornado'{nome_retorno}' para {end_cliente}")

def main():
    # criacao do socket que sera utilizado para recebimento e envio de datagramas
    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp.bind((LISTEN_IP, LISTEN_PORT))
    print(f"Servidor UDP escutando em {LISTEN_IP}:{LISTEN_PORT}")
    # servidor sempre ligado para receber os arquivos
    try:
        while True:
            recebe_arquivo(udp)
    except KeyboardInterrupt:
        print("Desligando servidor")
    finally:
        udp.close()

main()
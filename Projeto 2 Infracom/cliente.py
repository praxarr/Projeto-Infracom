import socket
import sys
import os

BUFFER_SIZE = 1024
HEADER_TAM = 2
NUM_TENTATIVAS = 10
def verifica_segmento(segmento:bytes):
    if len(segmento) < HEADER_TAM:
        return None
    num_seq = int(segmento[0])
    flag = int(segmento[1])
    payload = segmento[2:]
    return num_seq, flag, payload

def criar_pacote(seq: int, flag: int, payload) :
    header = seq.to_bytes(1, 'big') + flag.to_bytes(1, 'big')
    if isinstance(payload, str):
        payload = payload.encode('utf-8')
    return header + payload

def enviar_arquivo(udp,endereco, segmento:bytes, num_seq):
    tentativas = 0
    while tentativas < NUM_TENTATIVAS:
        udp.settimeout(0.5)
        udp.sendto(segmento, endereco)
        _, _, payload = verifica_segmento(segmento)

        try:
            cabecalho, _ = udp.recvfrom(20)
            ack_num, ack_flag, _ = verifica_segmento(cabecalho)

            if ack_flag == 1 and ack_num == num_seq:
                udp.settimeout(None)
                return True

            else: 
                print(f"[{endereco}] Recebido algo que não é ACK correto (aseq={ack_num}, aflag={ack_flag}). Ignorando.")

        except socket.timeout:
            tentativas += 1
            print(f"[{endereco}] Timeout aguardando ACK do cliente. Retransmitindo...")
    udp.settimeout(None)
    return False



def main():
    # se a quantidade de argumentos passados for incorreta, o datagrama nao eh enviado
    if len(sys.argv) < 4:
        print("Entradas incorretas")
        sys.exit(1)

    # ordem de cada argumento utilizado pelo programa

    SERVER_IP = sys.argv[1]
    SERVER_PORT = int(sys.argv[2])
    FILE_PATH = sys.argv[3]

    if not os.path.exists(FILE_PATH):
        print("Arquivo não encontrado:", FILE_PATH)
        sys.exit(1)
    
    # coletando o nome e o tamanho do arquivo a ser enviado
    filename = os.path.basename(FILE_PATH)
    filesize = os.path.getsize(FILE_PATH)

    # criacao do socket que sera utilizado para o envio e o recebimento dos arquivos
    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    end_servidor = (SERVER_IP, SERVER_PORT)
    num_seq = 0
    expected_seq = 0
    payload = b''
    packet_dummy = criar_pacote(expected_seq, 1, b'')
    # Cliente envia nome e tamanho do arquivo para o servidor
    
    nome_seg = criar_pacote(num_seq, 0, filename)
    verifica = enviar_arquivo(udp, end_servidor, nome_seg, num_seq)

    num_seq = 1 - num_seq


    # Para o tamanho(Int) ser envciado para o datagrama, precisa ser castado para Str
    tamanho = str(filesize)
    tamanho_seg = criar_pacote(num_seq, 0, tamanho)\

    enviar_arquivo(udp, end_servidor, tamanho_seg, num_seq)
    num_seq = 1 - num_seq
    print(f"Enviando {filename} ({filesize} bytes) para {end_servidor}")

    # Loop para envio do arquivo original do cliente para o servidor
    with open(FILE_PATH, 'rb') as f:
        while True:
            chunk = f.read(BUFFER_SIZE)
            if not chunk:
                break
            chunk_seg = criar_pacote(num_seq, 0, chunk)
            enviar_arquivo(udp, end_servidor, chunk_seg, num_seq)
            num_seq = 1 - num_seq
            

    print("Envio completo. Aguardando devolução do servidor...")

    # Cliente recebe o nome do arquivo atualizado e o seu tamanho
    while True:
        nome_ret_seg, _ = udp.recvfrom(1024)
        num_seq1, flag, nome_bin = verifica_segmento(nome_ret_seg)
        if flag == 1:
            print(f"[{end_servidor}] Recebido ACK onde se esperava dados (nome) — ignorando.")
            udp.sendto(packet_dummy, end_servidor)
            continue
        if num_seq1 == expected_seq:
            nome_ret = nome_bin.decode('utf-8')
            ack_seg = criar_pacote(num_seq1, 1, b'')
            udp.sendto(ack_seg, end_servidor)
            expected_seq = 1 - num_seq1
            # datagrama inicialmente em binario deve ser decodificado para str
            filename = nome_bin.decode('utf-8')
            break
        else: 
            print(f"[{end_servidor}] Pacote de nome duplicado/fora de ordem (seq={num_seq}). Reenviando último ACK.")
            udp.sendto(packet_dummy, end_servidor)

    while True:
        tamanho_ret_seg, _ = udp.recvfrom(1024)
        num_seq2, flag2, tamanho_bin = verifica_segmento(tamanho_ret_seg)
        if flag2 == 1: 
            print(f"[{end_servidor}] Recebido ACK onde se esperava dados (nome) — ignorando.")
            udp.sendto(ack_seg, end_servidor)
            continue
        if num_seq2 == expected_seq: 
            tamanho_ret = int(tamanho_bin.decode('utf-8'))
            ack_seg = criar_pacote(num_seq2, 1, b'')
            udp.sendto(ack_seg, end_servidor)
            expected_seq = 1 - num_seq2
            # datagrama precisa ser decodificado para str e depois castado para Int
            print(f"[{end_servidor}] Arquivo que será recebido: {nome_ret} ({tamanho_ret} bytes)")
            break
        else: 
            print(f"[{end_servidor}] Pacote de nome duplicado/fora de ordem (seq={num_seq2}). Reenviando último ACK.")
            udp.sendto(ack_seg, end_servidor)
    print(f"Servidor devolverá: {nome_ret} ({tamanho_ret} bytes)")

    #Diretorio downloads(comum do Windows) sera utilizado para o recebimento dos arquivos atualizados
    os.makedirs('downloads', exist_ok=True)
    end_final = os.path.join('downloads', nome_ret)

    received = 0
    n = 25
    # Loop para o recebimento dos arquivos atualizados enviados pelo servidor
    with open(end_final, 'wb') as f:
        while received < tamanho_ret:
            seg_chunk, _ = udp.recvfrom(BUFFER_SIZE+2)
            seq_num, chunk_flag, chunk = verifica_segmento(seg_chunk)
            if chunk_flag == 1: 
                print(f"[{end_servidor}] Recebido ACK onde se esperava dados (nome) — ignorando.")
                udp.sendto(ack_seg, end_servidor)
                continue
            if seq_num == expected_seq:
                f.write(chunk)
                received += len(chunk)
                ack_seg = criar_pacote(seq_num, 1, b'')
                udp.sendto(ack_seg, end_servidor)
                expected_seq = 1 - seq_num
                # progresso do recebimento do arquivo printado no terminal durante execucao 
                if received >= (n * (tamanho_ret // 100)) and n <= 100:
                    print(f" -> %{n} do arquivo foi recebido")
                    n += 25
            else:
                print(f"[{end_servidor}] Pacote de nome duplicado/fora de ordem (seq={seq_num}). Reenviando último ACK.")
                udp.sendto(ack_seg, end_servidor)

    print("Arquivo devolvido salvo em:", end_final)
    #Fecha a porta do cliente
    udp.close()


main()
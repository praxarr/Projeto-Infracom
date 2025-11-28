import socket
import os
import random
# Ip 0.0.0.0 indica que o servidor recebe arquivos de qualquer IP, incluindo IPs publicos

BUFFER_SIZE = 1024
LISTEN_IP = '0.0.0.0'
LISTEN_PORT = 5019
HEADER_TAM = 2
NUM_TENTATIVAS = 10

def verifica_segmento(segmento:bytes):
    if len(segmento) < HEADER_TAM:
        return None
    num_seq = int(segmento[0])
    flag = int(segmento[1])
    payload = segmento[2:]
    return num_seq, flag, payload

def criar_pacote(seq: int, flag: int, payload: bytes) :
    header = seq.to_bytes(1, 'big') + flag.to_bytes(1, 'big')
    if isinstance(payload, str):
        payload = payload.encode('utf-8')
    
    return header + payload

def enviar_arquivo(udp, endereco, segmento: bytes, num_seq):
    tentativas = 0
    while tentativas < NUM_TENTATIVAS:
        udp.settimeout(0.5)
        perda = random.uniform(0, 1)

        # 1. Decisão de Envio ou Simulação de Perda
        if perda <= 0.05:  # 5% de chance de perda simulada
            print(f"[SIMULAÇÃO] Pacote {num_seq} perdido no envio.")
        else:
            udp.sendto(segmento, endereco)
            print(f"[ENVIO] Pacote {num_seq} enviado para a rede.")
            _, _, payload = verifica_segmento(segmento)

        try:
            # 2. Espera pelo ACK (Ocorre tenhamos enviado ou não)
            cabecalho, _ = udp.recvfrom(20)
            ack_num, ack_flag, _ = verifica_segmento(cabecalho)

            if ack_flag == 1 and ack_num == num_seq:
                # ACK correto recebido
                print(f"[RECEBIMENTO] ACK {ack_num} recebido corretamente.")
                udp.settimeout(None)
                break 
            else:
                print(f"[{endereco}] ACK incorreto (seq={ack_num}). Ignorando.")

        except socket.timeout:
            # Se simulamos perda (não enviamos), vai cair aqui após 0.5s.
            # Se enviamos e o ACK perdeu, vai cair aqui também.
            tentativas += 1
            print(f"[{endereco}] Timeout (Tentativa {tentativas}/{NUM_TENTATIVAS}). Retransmitindo...")
            
    udp.settimeout(None)



def recebe_arquivo(udp):

    expected_seq = 0
    payload = b''
    packet_dummy = criar_pacote(expected_seq, 1, b'')
    # servidor inicialmente recebe o nome do arquivo a ser enviado pelo cliente e o endereco do remetente
    while True:
        pacote, end_cliente =  udp.recvfrom(1024)
        num_seq1, flag, nome_bin = verifica_segmento(pacote)
        if flag == 1:
            print(f"[{end_cliente}] Recebido ACK onde se esperava dados (nome) — ignorando.")
            continue

        if num_seq1 == expected_seq:
            filename = nome_bin.decode('utf-8')
            ack_seg = criar_pacote(num_seq1, 1, b'')
            udp.sendto(ack_seg, end_cliente)
            expected_seq = 1 - num_seq1
            # datagrama inicialmente em binario deve ser decodificado para str
            filename = nome_bin.decode('utf-8')
            print(f"[{filename}]")
            break
        else: 
            print(f"[{end_cliente}] Pacote de nome duplicado/fora de ordem (seq={num_seq1}). Reenviando último ACK.")
            udp.sendto(packet_dummy, end_cliente)
        # o segundo datagrama recebido pelo servidor se refere ao tamanho do arquivo
    while True:
        pacote_tam, _ = udp.recvfrom(1024)
        num_seq2, flag2, tamanho_bin = verifica_segmento(pacote_tam)
        if flag2 == 1: 
            print(f"[{end_cliente}] Recebido ACK onde se esperava dados (nome) — ignorando.")
            continue
        if num_seq2 == expected_seq: 
            filesize = int(tamanho_bin.decode('utf-8'))
            ack_seg = criar_pacote(num_seq2, 1, b'')
            udp.sendto(ack_seg, end_cliente)
            expected_seq = 1 - expected_seq
            # datagrama precisa ser decodificado para str e depois castado para Int
            print(f"[{end_cliente}] Arquivo que será recebido: {filename} ({filesize} bytes)")
            break
        else: 
            print(f"[{end_cliente}] Pacote de nome duplicado/fora de ordem (seq={num_seq2}). Reenviando último ACK.")
            udp.sendto(ack_seg, end_cliente)
    # Diretorio criado para escrever o arquivo enviado pelo cliente

    os.makedirs('recebidos', exist_ok=True)
    end_recebidos = os.path.join('recebidos', filename)

    received = 0
    n = 25
    
    # loop para realizar a escrita do arquivo apontado pelo diretorio a partir de cada datagrama que compoe o arquivo. 
    # escrita binaria eh utilizada para compatibilidade com diferentes tipos de arquivos\
    print(f"vai entrar no loop de recebimento dos pacotes")
    with open(end_recebidos, 'wb') as f:
        while received < filesize:
            seg_chunk, _ = udp.recvfrom(BUFFER_SIZE+2)
            seq_num, chunk_flag, chunk = verifica_segmento(seg_chunk)
            if chunk_flag == 1: 
                print(f"[{end_cliente}] Recebido ACK onde se esperava dados (nome) — ignorando.")
                continue
            if seq_num == expected_seq:
                f.write(chunk)
                received += len(chunk)
                ack_seg = criar_pacote(seq_num, 1, b'')
                udp.sendto(ack_seg, end_cliente)
                expected_seq = 1 - expected_seq
                # progresso do recebimento do arquivo printado no terminal durante execucao 
                if received >= (n * (filesize // 100)) and n <= 100:
                    print(f" -> %{n} do arquivo foi recebido")
                    n += 25
            else:
                print(f"[{end_cliente}] Pacote de nome duplicado/fora de ordem (seq={seq_num}). Reenviando último ACK.")
                udp.sendto(ack_seg, end_cliente)
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

    num_seq = 0

    nome_ret_seg = criar_pacote(num_seq, 0, nome_retorno)
    enviar_arquivo(udp, end_cliente, nome_ret_seg, num_seq)

    num_seq = 1 - num_seq

    tamanho_ret_seg = criar_pacote(num_seq, 0, tamanho_ret)
    enviar_arquivo(udp, end_cliente, tamanho_ret_seg, num_seq)

    num_seq = 1 - num_seq

    # loop para o envio de cada datagrama que compoe o arquivo retornado
    with open(end_retorno, 'rb') as f:
        while True:
            chunk = f.read(BUFFER_SIZE)
            if not chunk:
                break
            chunk_seg = criar_pacote(num_seq, 0, chunk)
            enviar_arquivo(udp, end_cliente, chunk_seg, num_seq)
            num_seq = 1 - num_seq
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

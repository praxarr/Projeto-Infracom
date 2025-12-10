import socket
import sys
import threading
import random
import time
from common import criar_pacote, verifica_segmento

BUFFER_SIZE = 1024
NUM_TENTATIVAS = 10

# Variáveis Globais de Controle
seq_num = 0       
ack_received = threading.Event() # Evento para sinalizar que o ACK chegou

def listener(udp, dest_addr):
    """Thread única que lê TUDO do socket"""
    global seq_num
    while True:
        try:
            data, addr = udp.recvfrom(BUFFER_SIZE)
            if addr != dest_addr: continue
            
            r_seq, r_flag, r_payload = verifica_segmento(data)
            
            if r_flag == 1:
                # ACK
                # verificamos se o seqnum bate
                if r_seq == seq_num:
                    ack_received.set()
            else:
                # Dados
                msg = r_payload.decode('utf-8')
                # Apaga a linha de input atual visualmente e printa a msg
                print(f"\r[SERVER]: {msg}" + " " * 20)
                print(f"> ", end="", flush=True)
                
                # Envia ACK de volta pro servidor
                ack_pkt = criar_pacote(r_seq, 1, b'')
                udp.sendto(ack_pkt, dest_addr)
                
        except OSError:
            break # Socket fechado

def rdt_send(udp, endereco, mensagem):
    global seq_num
    
    pkt = criar_pacote(seq_num, 0, mensagem)
    tentativas = 0
    
    while tentativas < NUM_TENTATIVAS:
        ack_received.clear() # Prepara para esperar o ACK
        
        # Simula perda 
        if random.random() <= 0.05:
            print(f"\r[SIMULAÇÃO] Pacote {seq_num} perdido no envio.\n> ", end="")
        else:
            udp.sendto(pkt, endereco)
        
        # Espera o ACK ser setado pela thread listener por 1 segundo
        if ack_received.wait(timeout=1.0):
            # ACK recebido
            seq_num = 1 - seq_num
            return True
        else:
            # Timeout
            tentativas += 1
            print(f"\r[TIMEOUT] Sem resposta. Retentando ({tentativas}/{NUM_TENTATIVAS})...\n> ", end="")
            
    print("\nERRO: Servidor indisponível.")
    return False

def main():
    if len(sys.argv) < 3:
        print("Uso: python cliente.py <IP> <PORT>")
        SERVER_IP = '127.0.0.1'
        SERVER_PORT = 5000
    else:
        SERVER_IP = sys.argv[1]
        SERVER_PORT = int(sys.argv[2])

    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    dest = (SERVER_IP, SERVER_PORT)

    # Inicia a thread que ouve o servidor
    t = threading.Thread(target=listener, args=(udp, dest), daemon=True)
    t.start()

    print("HuntCin Cliente")
    nome = input("Nome: ")
    if rdt_send(udp, dest, f"login {nome}"):
        print("> ", end="", flush=True) # Prompt inicial
        
        while True:
            try:
                cmd = input() # O input fica travado esperando o enter
                
                if not cmd: 
                    print("> ", end="", flush=True)
                    continue

                if cmd == 'logout':
                    rdt_send(udp, dest, "logout")
                    break
                
                if cmd.startswith("move") or cmd in ["hint", "suggest"]:
                    rdt_send(udp, dest, cmd)
                    # Não precisamos esperar resposta aqui, o listener vai printar
                else:
                    print("Comandos: move <up/down/left/right>, hint, suggest, logout")
                    print("> ", end="", flush=True)

            except KeyboardInterrupt:
                # ao Ctrl+C, faz logout
                print("\nSaindo...")
                rdt_send(udp, dest, "logout")
                break
    
    udp.close()

if __name__ == "__main__":
    main()
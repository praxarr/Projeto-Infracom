import socket
import sys
import threading
import random
import time
from common import criar_pacote, verifica_segmento

SERVER_IP_FIXO = '127.0.0.1' 
SERVER_PORT_FIXO = 5555      

BUFFER_SIZE = 1024
NUM_TENTATIVAS = 10

# Variáveis Globais de Controle
seq_num = 0       
ack_received = threading.Event() 

def listener(udp, dest_addr):
    global seq_num
    while True:
        try:
            data, addr = udp.recvfrom(BUFFER_SIZE)
            if addr != dest_addr: continue
            
            r_seq, r_flag, r_payload = verifica_segmento(data)
            
            if r_flag == 1:
                if r_seq == seq_num:
                    ack_received.set()
            else:
                msg = r_payload.decode('utf-8')
                print(f"\r[SERVER] {msg}" + " " * 20)
                print(f"> ", end="", flush=True)
                
                ack_pkt = criar_pacote(r_seq, 1, b'')
                udp.sendto(ack_pkt, dest_addr)
        except OSError:
            break 

def rdt_send(udp, endereco, mensagem):
    global seq_num
    pkt = criar_pacote(seq_num, 0, mensagem)
    tentativas = 0
    
    while tentativas < NUM_TENTATIVAS:
        ack_received.clear()
        
        # Simula perda (5%)
        if random.random() <= 0.05:
            pass
        else:
            udp.sendto(pkt, endereco)
        
        if ack_received.wait(timeout=1.0):
            seq_num = 1 - seq_num
            return True
        else:
            tentativas += 1
            print(f"\r[TIMEOUT] Retentando ({tentativas}/{NUM_TENTATIVAS})...\n> ", end="")
            
    print("\nERRO: Servidor indisponível.")
    return False

def main():
    if len(sys.argv) < 3:
        print("Uso: python cliente.py <SEU_IP> <SUA_PORTA>")
        print("Exemplo: python cliente.py 127.0.0.1 5000")
        return

    # Argumentos definem QUEM SOU EU
    MY_IP = sys.argv[1]
    MY_PORT = int(sys.argv[2])

    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    try:
        udp.bind((MY_IP, MY_PORT))
        print(f"--- Cliente rodando na porta {MY_PORT} ---")
    except Exception as e:
        print(f"Erro: A porta {MY_PORT} já está em uso ou é inválida.")
        return

    # O Destino é fixo
    dest = (SERVER_IP_FIXO, SERVER_PORT_FIXO)

    t = threading.Thread(target=listener, args=(udp, dest), daemon=True)
    t.start()

    print("--- HuntCin ---")
    nome = input("Nome: ")
    if rdt_send(udp, dest, f"login {nome}"):
        print("> ", end="", flush=True) 
        
        while True:
            try:
                cmd = input() 
                if not cmd: 
                    print("> ", end="", flush=True)
                    continue
                if cmd == 'logout':
                    rdt_send(udp, dest, "logout")
                    break
                if cmd.startswith("move") or cmd in ["hint", "suggest"]:
                    rdt_send(udp, dest, cmd)
                else:
                    print("Comandos: move <up/down/left/right>, hint, suggest, logout")
                    print("> ", end="", flush=True)
            except KeyboardInterrupt:
                rdt_send(udp, dest, "logout")
                break
    udp.close()

if __name__ == "__main__":
    main()
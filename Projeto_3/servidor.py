import socket
import threading
import time
import random
from common import criar_pacote, verifica_segmento

# Configurações
LISTEN_IP = '0.0.0.0'
LISTEN_PORT = 5555
BUFFER_SIZE = 1024

# Estado do Jogo
players = {} 
grid_size = 3
treasure_pos = (0, 0)

udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp.bind((LISTEN_IP, LISTEN_PORT))
udp.setblocking(False) 

print(f"HuntCin Server rodando em {LISTEN_IP}:{LISTEN_PORT}")

def reset_treasure():
    global treasure_pos
    while True:
        x = random.randint(1, 3)
        y = random.randint(1, 3)
        if (x, y) != (1, 1):
            treasure_pos = (x, y)
            break
    print(f"[SERVER]: Tesouro escondido em {treasure_pos}")

def broadcast(message):
    print(f"[BROADCAST] {message}")
    to_remove = []
    for addr, player in players.items():
        try:
            player['seq_out'] = 1 - player['seq_out']
            pkt = criar_pacote(player['seq_out'], 0, message)
            udp.sendto(pkt, addr)
        except:
            to_remove.append(addr)
    for k in to_remove:
        del players[k]

def handle_login(addr, name):
    for p in players.values():
        if p['name'] == name:
            return "ERRO: Nome ja existe"
    
    players[addr] = {
        'name': name,
        'pos': [1, 1],
        'seq_in': 1,   # Já consumimos o seq 0 no login, esperamos o 1 agora
        'seq_out': 0,
        'hints': 1,
        'suggest': 1,
        'score' : 0
    }
    print(f"[LOGIN] {name} entrou de {addr}")
    return "Voce esta online!"

def handle_move(addr, direction):
    if addr not in players: return "Faça login primeiro"
    p = players[addr]
    nx, ny = p['pos']
    if direction == 'up': ny += 1
    elif direction == 'down': ny -= 1
    elif direction == 'right': nx += 1
    elif direction == 'left': nx -= 1
    else: return "Comando invalido"

    if 1 <= nx <= 3 and 1 <= ny <= 3:
        p['pos'] = [nx, ny]
        if (nx, ny) == treasure_pos:
            broadcast(f"O jogador {p['name']} encontrou o tesouro na posicao {treasure_pos}!")
            placar = "Placar Atual:\n"
            for i in players.values():
                placar += f"- {i['name']} : {i['score']} ponto(s) \n"
            broadcast(placar)
            reset_treasure()
            reset_positions()
            return "PARABENS! Voce achou o tesouro."
        else:
            return f"Posicao atualizada: {nx},{ny}"
    else:
        return "Movimento invalido (fora do grid)"

def handle_hint(addr):
    p = players.get(addr)
    if not p or p['hints'] <= 0: return "Sem dicas restantes."
    p['hints'] -= 1
    tx, ty = treasure_pos
    px, py = p['pos']
    if ty > py: return "O tesouro esta mais acima."
    if ty < py: return "O tesouro esta mais abaixo."
    if tx > px: return "O tesouro esta mais a direita."
    if tx < px: return "O tesouro esta mais a esquerda."
    return "Voce esta na mesma linha/coluna!"

def handle_suggest(addr):
    p = players.get(addr)
    if not p or p['suggest'] <= 0: return "Sem sugestoes restantes."
    p['suggest'] -= 1
    tx, ty = treasure_pos
    px, py = p['pos']
    if ty > py: return "Sugestao: move up"
    if ty < py: return "Sugestao: move down"
    if tx > px: return "Sugestao: move right"
    if tx < px: return "Sugestao: move left"
    return "Sugestao: olhe ao seu redor"

def reset_positions():
    for p in players.values():
        p['pos'] = [1, 1]
    broadcast("Nova rodada! Todos em (1,1).")

def game_loop():
    reset_treasure()
    while True:
        try:
            try:
                data, addr = udp.recvfrom(BUFFER_SIZE)
            except BlockingIOError:
                continue 
            except socket.error:
                continue

            seq, flag, payload = verifica_segmento(data)
            
            if flag == 1: continue # Ignora ACKs recebidos pelo server

            msg_str = payload.decode('utf-8').strip()
            
            # Lógica RDT Servidor
            if addr in players:
                esperado = players[addr]['seq_in']
                if seq != esperado:
                    # Envia ACK do anterior (retransmissão)
                    udp.sendto(criar_pacote(seq, 1, b''), addr)
                    continue
                players[addr]['seq_in'] = 1 - players[addr]['seq_in']
            
            # Manda ACK para o cliente (Confirmando recebimento)
            udp.sendto(criar_pacote(seq, 1, b''), addr)

            # Processa Comando
            parts = msg_str.split()
            cmd = parts[0].lower()
            response = ""

            if cmd == 'login':
                nome = parts[1] if len(parts) > 1 else f"User-{random.randint(100,999)}"
                response = handle_login(addr, nome)
            elif cmd == 'logout':
                if addr in players: del players[addr]
                print(f"Client {addr} saiu.")
            elif cmd == 'move':
                direction = parts[1] if len(parts) > 1 else ""
                response = handle_move(addr, direction)
                if addr in players: # Broadcast só se player ainda existe
                    state_msg = f"Estado: " + ", ".join([f"{v['name']}{tuple(v['pos'])}" for v in players.values()])
                    broadcast(state_msg)
            elif cmd == 'hint': response = handle_hint(addr)
            elif cmd == 'suggest': response = handle_suggest(addr)
            
            if response and addr in players:
                players[addr]['seq_out'] = 1 - players[addr]['seq_out']
                pkt_resp = criar_pacote(players[addr]['seq_out'], 0, response)
                udp.sendto(pkt_resp, addr)

        except Exception as e:
            print(f"Erro: {e}")

if __name__ == "__main__":
    try: game_loop()
    except KeyboardInterrupt: udp.close()

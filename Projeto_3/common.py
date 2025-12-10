# common.py
import struct

HEADER_TAM = 2

def verifica_segmento(segmento: bytes):
    if len(segmento) < HEADER_TAM:
        return None, None, None
    num_seq = int(segmento[0])
    flag = int(segmento[1])
    payload = segmento[2:]
    return num_seq, flag, payload

def criar_pacote(seq: int, flag: int, payload):
    # Garante que seq e flag caibam em 1 byte
    header = seq.to_bytes(1, 'big') + flag.to_bytes(1, 'big')
    if isinstance(payload, str):
        payload = payload.encode('utf-8')
    return header + payload
# Projeto-Infracom
Parte 2 do projeto da disciplina Infraestrutura de Comunicação (IF-678)

Integrantes:
- Elisson Rodrigo da Silva Araujo
- Pedro Henrique Andrade da Silva
- Théo Praxar Farias Lopes

## Descrição do Projeto
Evolução do sistema cliente-servidor para implementar **Transferência Confiável de Dados** (Reliable Data Transfer) utilizando o protocolo UDP em Python. O sistema garante a integridade e a ordem dos dados através da implementação do algoritmo **RDT 3.0 (Stop-and-Wait)**, simulando um canal de rede sujeito a perdas de pacotes.

## Objetivos e Decisões de Projeto

### **Protocolo RDT 3.0 (Stop-and-Wait)**
- **Decisão**: Implementar controle de fluxo baseado em "Para e Espera" com bit alternante (0 e 1).
- **Objetivo**: Garantir que cada pacote seja recebido e confirmado antes do envio do próximo.
- **Benefício**: Confiabilidade total na transferência, eliminando perda de dados ou corrupção de ordem.

### **Cabeçalho Customizado (Header)**
- **Decisão**: Adicionar um cabeçalho de 2 bytes (`Seq Num` + `Flag`) no início de cada datagrama.
- **Objetivo**: Permitir que o receptor distinga dados novos de retransmissões e identifique pacotes de confirmação (ACKs).
- **Desafio**: Manipular bytes brutos para separar corretamente o cabeçalho do conteúdo (payload).

### **Simulação de Perda de Pacotes**
- **Decisão**: Implementar um gerador de números aleatórios (`random`) antes do envio físico no socket.
- **Objetivo**: Simular um canal não confiável descartando pacotes propositalmente (ex: 5% de chance).
- **Benefício**: Validar visualmente a robustez do algoritmo de recuperação de erros (retransmissão) via logs no terminal.

## Desafios Encontrados

### **1. Detecção de Perdas (Timeout)**
- **Desafio**: O UDP não informa se um pacote foi entregue ou perdido.
- **Solução**: Implementar um temporizador (`socket.settimeout`) após cada envio.
- **Mecanismo**: Se o ACK não chegar dentro de 0.5s, o sistema assume perda e retransmite o último pacote.

### **2. Tratamento de Duplicatas**
- **Desafio**: Se um ACK for perdido, o remetente reenvia o dado, criando duplicidade no destino.
- **Solução**: Verificar o número de sequência (0 ou 1) antes de processar.
- **Protocolo**: Se o número de sequência for igual ao último recebido, o receptor descarta o conteúdo e apenas reenvia o ACK.

### **3. Sincronização de Estados**
- **Desafio**: Manter cliente e servidor sincronizados quanto ao pacote esperado (0 ou 1).
- **Solução**: Máquina de estados finitos onde a mudança de estado só ocorre após confirmação positiva.
- **Mecanismo**: Uso de variáveis de controle (`expected_seq` e `num_seq`) alternadas (1 - seq).

## Estrutura de Diretórios
    Projeto 2 Infracom/
    ├── cliente.py       # Lógica de envio/recebimento com RDT
    ├── servidor.py      # Lógica de recebimento/envio com RDT
    ├── recebidos/       # Arquivos recebidos pelo servidor
    ├── retornados/      # Arquivos processados para retorno
    └── downloads/       # Arquivos devolvidos ao cliente

## Funcionalidades Implementadas

### **Servidor (`servidor.py`)**
- Escuta na porta `5019` utilizando protocolo RDT 3.0.
- Verifica integridade e sequência de cada pacote recebido.
- Envia ACKs (Confirmações) para pacotes corretos.
- Simula perdas de pacotes durante o processo de devolução do arquivo ao cliente.

### **Cliente (`cliente.py`)**
- Fragmenta o arquivo e adiciona cabeçalhos de controle.
- Aguarda confirmação (ACK) para cada pacote enviado.
- Detecta *timeouts* e realiza retransmissão automática.
- Exibe logs detalhados de envio, perda simulada e retransmissão.

## Como Executar

### **Servidor:**
```bash
python servidor.py
```

### **Cliente:**
```bash
python cliente.py <SERVER_IP> <SERVER_PORT> <ARQUIVO>
```

#### Exemplo
```bash
python cliente.py 127.0.0.1 5019 pequeno.txt
```    

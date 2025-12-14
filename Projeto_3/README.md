# Projeto-Infracom
Parte 3 do projeto da disciplina Infraestrutura de Comunicação (IF-678)

Integrantes:
- Elisson Rodrigo da Silva Araujo
- Pedro Henrique Andrade da Silva
- Théo Praxar Farias Lopes

## Descrição do Projeto
Implementação do sistema **"HuntCin"**, um jogo multiplayer de "Caça ao Tesouro" baseado em linha de comando. O projeto evolui a arquitetura cliente-servidor anterior para suportar múltiplos clientes simultâneos em um Grid 3x3, mantendo a **Transferência Confiável de Dados (RDT 3.0)** sobre UDP. O sistema gerencia estados de jogo, colisões e atualizações em tempo real (broadcast) para todos os jogadores conectados.

## Objetivos e Decisões de Projeto

### **Arquitetura Multiplayer com RDT 3.0**
- **Decisão**: Utilizar I/O não bloqueante (`setblocking(False)`) e Threads para separar o recebimento de mensagens da lógica de envio.
- **Objetivo**: Permitir que o servidor gerencie múltiplos jogadores simultaneamente sem que o protocolo "Stop-and-Wait" de um cliente trave o jogo para os outros.
- **Benefício**: Fluidez no jogo, onde comandos de movimento e atualizações de estado (Broadcast) ocorrem de forma assíncrona.

### **Protocolo de Aplicação e Comandos**
- **Decisão**: Implementar um parser de comandos textuais (`login`, `move`, `hint`, `suggest`).
- **Objetivo**: Traduzir as entradas do usuário em ações no Grid 3x3 validado pelo servidor.
- **Mecanismo**: O servidor atua como a "única fonte da verdade", validando posições e calculando a lógica do tesouro, enquanto os clientes apenas renderizam o estado atual.

### **Sincronização de Estado (Broadcast)**
- **Decisão**: Enviar o estado atualizado do grid para todos os clientes conectados após qualquer movimento válido.
- **Objetivo**: Garantir que todos os jogadores tenham a visão atualizada de onde os oponentes estão.
- **Desafio**: Gerenciar o envio de pacotes RDT para múltiplos destinos quase simultaneamente.

## Desafios Encontrados

### **1. Concorrência e "Race Conditions"**
- **Desafio**: O cliente precisava enviar comandos (esperando ACK) e receber atualizações do servidor (Broadcast) ao mesmo tempo.
- **Solução**: Implementação de Threads separadas no cliente (`listener` para escutar o servidor e `main` para input do usuário) coordenadas por eventos (`threading.Event`).
- **Mecanismo**: O `listener` processa ACKs para liberar o envio do próximo pacote e exibe mensagens de jogo automaticamente.

### **2. Gerenciamento de Sequência em Ambiente Assíncrono**
- **Desafio**: Diferenciar um ACK de um pacote de dados (Broadcast) e manter a sincronia dos bits de sequência (0 e 1) quando pacotes podem se cruzar na rede.
- **Solução**: Verificação rigorosa das flags no cabeçalho.
- **Protocolo**: O servidor mantém um estado de sequência (`seq_in`/`seq_out`) individual para cada cliente conectado.

### **3. Lógica do Jogo e Limites**
- **Desafio**: Garantir regras de negócio (limites do grid 3x3, posição do tesouro não ser (1,1)) em um ambiente stateless (UDP).
- **Solução**: Persistência em memória no servidor (dicionário `players`) que valida cada requisição antes de confirmar a ação.

## Estrutura de Diretórios
    Projeto 3 Infracom/
    ├── common.py        # Funções compartilhadas (criação de pacote, checksum simulado)
    ├── cliente.py       # Interface do jogador, RDT Sender e Thread de Escuta
    ├── servidor.py      # Lógica do jogo, Grid 3x3, Broadcast e Gerenciamento de Clientes
    └── README.md        # Documentação do projeto

## Funcionalidades Implementadas

### **Servidor (`servidor.py`)**
- Gerencia o Grid 3x3 e a posição aleatória do tesouro (exceto em 1,1).
- Processa logins únicos e remove jogadores via `logout`.
- Implementa lógica de dicas (`hint`) e sugestões (`suggest`).
- Realiza Broadcast de estado para sincronizar todos os clientes.

### **Cliente (`cliente.py`)**
- Interface de linha de comando interativa.
- Implementa RDT 3.0 com retransmissão automática em caso de perda simulada ou timeout.
- Thread dedicada para recebimento de atualizações do jogo em tempo real.

## Como Executar

### **1. Iniciar o Servidor:**
```bash
python servidor.py
```
O servidor iniciará na porta 5000 e exibirá a posição secreta do tesouro no log.

### **2. Iniciar Clientes (em terminais diferentes):**
```bash
python cliente.py <SERVER_IP> <SERVER_PORT>
```

### **Exemplo de Uso:**

#### **Terminal 1 (Jogador 1):**
```bash
python cliente.py 127.0.0.1 5000
# Digite o nome: Felipe
# Comandos: move right, hint, suggest
```

#### **Terminal 2 (Jogador 2):**
```bash
python cliente.py 127.0.0.1 5000
# Digite o nome: Vitor
# Comandos: move up
```

## **Lista de Comandos Disponíveis:**
- **login <nome>:** Conecta ao jogo (automático no início).
- **move <up|down|left|right>:**: Move o personagem no grid.
- **hint:** Recebe uma dica sobre a direção do tesouro (1 por partida).
- **suggest:**: Recebe uma sugestão de movimento (1 por partida).
- **logout:** Sai do jogo e desconecta.


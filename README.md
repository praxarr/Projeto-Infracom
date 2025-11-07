# Projeto-Infracom
Parte 1 do projeto da disciplina Infraestrutura de Comunicação (IF-678)

## Descrição do Projeto
Implementação de um sistema cliente-servidor para transferência de arquivos utilizando protocolo UDP em Python. O sistema permite que um cliente envie um arquivo para o servidor, que por sua vez armazena o arquivo e o devolve com um nome modificado.

## Objetivos e Decisões de Projeto

### **Arquitetura Cliente-Servidor**
- **Decisão**: Separar cliente e servidor em arquivos distintos (`cliente.py` e `servidor.py`)
- **Objetivo**: Permitir execução independente e facilitar a escalabilidade para funcionalidades futuras
- **Benefício**: Modularização que simplifica manutenção e testes

### **Buffer Size Limitado (1024 bytes)**
- **Decisão**: Implementar fragmentação de arquivos em pacotes de 1024 bytes
- **Objetivo**: Simular condições reais de rede onde pacotes possuem tamanho máximo
- **Desafio**: Garantir reconstrução correta do arquivo no destino independente do tipo

### **Manipulação de Diferentes Tipos de Arquivos**
- **Decisão**: Utilizar modo binário (`'rb'` e `'wb'`) para leitura e escrita
- **Objetivo**: Suportar qualquer tipo de arquivo (texto, imagens, binários)
- **Benefício**: Compatibilidade universal com diferentes formatos

## Desafios Encontrados

### **1. Controle de Fluxo sem TCP**
- **Desafio**: UDP não garante entrega ordenada ou confiável dos pacotes
- **Solução**: Implementar lógica de reconstrução baseada no tamanho total do arquivo
- **Mecanismo**: Contador de bytes recebidos para determinar conclusão do transferência

### **2. Separação de Metadados e Dados**
- **Desafio**: Distinguir entre informações do arquivo (nome, tamanho) e seu conteúdo
- **Solução**: Enviar metadados em pacotes separados antes do conteúdo
- **Protocolo**: 
  1. Nome do arquivo (string)
  2. Tamanho do arquivo (int como string)
  3. Conteúdo fragmentado (bytes)

### **3. Feedback de Progresso**
- **Desafio**: Fornecer indicação visual do andamento da transferência
- **Solução**: Implementar prints em intervalos de 25% do progresso
- **Benefício**: Melhor experiência do usuário durante transferências grandes

## Estrutura de Diretórios
    projeto/
    ├── cliente.py
    ├── servidor.py
    ├── recebidos/ # Arquivos recebidos pelo servidor
    ├── retornados/ # Arquivos processados para retorno
    └── downloads/ # Arquivos devolvidos ao cliente

## Funcionalidades Implementadas

### **Servidor (`servidor.py`)**
- Escuta em `0.0.0.0:5015` para receber conexões de qualquer IP
- Recebe arquivos fragmentados e os reconstroi
- Armazena arquivos na pasta `recebidos/`
- Cria cópia com prefixo `ret_` na pasta `retornados/`
- Devolve arquivo modificado ao cliente

### **Cliente (`cliente.py`)**
- Envia arquivo especificado via linha de comando
- Fragmenta arquivo em pacotes de 1024 bytes
- Recebe arquivo processado do servidor
- Salva resultado na pasta `downloads/`

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
python3 cliente.py 127.0.0.1 5015 teste_img.jpeg
```    

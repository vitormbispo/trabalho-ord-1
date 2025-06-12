import io
import sys
from dataclasses import dataclass

@dataclass
class Filme:
    '''
    Armazena os dados de um filme
    '''
    id:int
    titulo:str
    diretor:str
    ano:int
    genero:str
    duracao:int
    elenco:str
    byte_offset:int
    apagado:bool

@dataclass
class Indice:
    '''
    Armazena a chave primária (ID do filme)
    e o seu byte offset
    '''
    chave:int # ID do filme é a chave
    byte_offset:int

def redefinir_cabeca_leitura(arq:io.TextIOWrapper):
    '''
    Retorna a cabeça de leitura para o início do arquivo
    pulando o cabeçalho
    '''
    arq.seek(4)

def le_filme(arq:io.TextIOWrapper) -> Filme:
    '''
    Lê o pŕoximo filme da sequência do arquivo 'arq' e o retorna
    ''' 
    byte_offset = arq.tell()
    read_bytes = arq.read(2)
    tam_reg = int.from_bytes(read_bytes)

    if(tam_reg):
        try:
            filme = arq.read(tam_reg).decode('utf8')
        except UnicodeDecodeError as e:#Caracter incompatível com UTF8. Registro apagado
            return Filme(None,None,None,None,None,None,None,None,True)

        if(filme[0] == '*'): # Registro apagado!
            return Filme(None,None,None,None,None,None,None,None,True)
        campos = filme.split('|')
        return Filme(int(campos[0]), campos[1], campos[2], int(campos[3]), campos[4], int(campos[5]), campos[6],byte_offset,False)
    else:
        return None # Fim do arquivo

def acessa_filme(arq:io.TextIOWrapper,offset:int) -> Filme:
    '''
    Acessa diretamente o registro de filme no 'offset'
    '''
    
    arq.seek(offset)
    tam_reg = int.from_bytes(arq.read(2))

    if(tam_reg):
        try:
            filme = arq.read(tam_reg).decode('utf8')
        except UnicodeDecodeError:             # Caracter incompatível com UTF8. Registro apagado
            return Filme(None,None,None,None,None,None,None,None,True)
        
        if(filme[0] == '*'): # Se o registro está marcado como excluído:
            return Filme(None,None,None,None,None,None,None,None,True)

        campos = filme.split('|') # Separa os campos
        return Filme(int(campos[0]), campos[1], campos[2], int(campos[3]), campos[4], int(campos[5]), campos[6],offset,False) # Cria um novo tipo filme
    else:
        return None # Filme não encontrado

def busca_filme(arq:io.TextIOWrapper,id:int,indices:list[Indice]) -> Filme:
    '''
    Faz uma busca binária no 'arq' usando os 'indices' procurando pelo filme com o
    'id'. Retorna o filme encontrado ou None caso não seja encontrado.
    '''
    inicio = 0
    fim = len(indices)-1

    while(inicio <= fim):
        meio = (inicio+fim)//2
        if indices[meio].chave == id: return acessa_filme(arq,indices[meio].byte_offset)
        if indices[meio].chave < id: inicio = meio+1
        else: fim = meio-1
    return None
    
    
    split = len(indices)//2 # Divide a lista ao meio
    
    # CASOS BASE ----------------------------------------------------------------
    if(indices[split].chave == id): # Encontrou o filme, acessa e retorna
        return acessa_filme(arq,indices[split].byte_offset)
    elif(split == 0): # Acabou a lista, não retorna nada
        return None
    #----------------------------------------------------------------------------

    # Define em qual dos lados da lista dividida a busca continuará:
    novoIndices = indices[split:] if id > indices[split].chave else indices[:split] 

    return busca_filme(arq,id,novoIndices) # CASO RECURSIVO

def lista_indices(arq:io.TextIOWrapper) -> list[Indice]:
    '''
    Retorna uma lista da classe Indice contendo ID e byteoffset dos filmes.
    Essa lista já é ordenada por ID.
    '''

    lista:list[Indice] = []
    redefinir_cabeca_leitura(arq)
    filme = le_filme(arq)
    
    while filme:
        if(filme.apagado):
            filme = le_filme(arq)
            continue

        if len(lista) == 0: # Primeiro elemento
            if(not filme.apagado):
                lista.append(Indice(filme.id,filme.byte_offset))
            filme = le_filme(arq)
            continue

        for i in range(len(lista)):
            # Inserindo ordenado
            if(filme.id <= lista[i].chave):
                lista.insert(i,Indice(filme.id,filme.byte_offset))
                break
            
            if i >= len(lista) - 1:
                # Chegou no final, adiciona ao fim
                lista.append(Indice(filme.id,filme.byte_offset))
        filme = le_filme(arq)

    return lista
        
def apaga_filme(arq:io.TextIOWrapper,filme:Filme) -> None:
    '''
    Apaga o registro do 'filme' do 'arq'
    '''
    
    arq.seek(filme.byte_offset)
    tamanho = int.from_bytes(arq.read(2))
    arq.write(b'*')
    adicionar_a_led(arq,filme.byte_offset,tamanho)

def adicionar_a_led(arq:io.TextIOWrapper,offset:int,tamanho:int):
    '''
    Adiciona o 'offset' de um filme à LED de forma ordenada por 'tamanho'
    '''
    arq.seek(0)
    anter = 0
    endereco = int.from_bytes(arq.read(4),signed=True)
    encontrado = False
    while(endereco != -1 and not encontrado):
        arq.seek(endereco)
        espaco_disponivel = int.from_bytes(arq.read(2),signed=True)
        
        if(espaco_disponivel > tamanho):
            encontrado = True
        else:
            anter = endereco+3
            arq.read(1) # Pula o caracter de marcação
            endereco = int.from_bytes(arq.read(4),signed=True)
            continue

    # Escreve
    arq.seek(anter)
    arq.write(offset.to_bytes(4,signed=True))
    arq.seek(offset+3) # Pula o tamanho e a marcação
    arq.write(endereco.to_bytes(4,signed=True))

def encontrar_melhor_espaço(arq:io.TextIOWrapper,tam:int):
    arq.seek(0)
    endereco = int.from_bytes(arq.read(4),signed=True)
    while(endereco != -1):
        arq.seek(endereco)
        espaco = int.from_bytes(arq.read(2),signed=True)
        if espaco >= tam:
            return endereco
        else:
            arq.read(1) # Pula a marcação
            endereco = int.from_bytes(arq.read(4),signed=True)
    return None
    
def imprime_led(arq:io.TextIOWrapper):
    '''
    Imprime a LED em um novo arquivo de texto
    '''
    log:io.TextIOWrapper = open("log-imprime-led.txt","w")
    log.write("LED -> ")

    arq.seek(0)
    endereco = int.from_bytes(arq.read(4),signed=True)
    espacos = 0
    while(endereco != -1):
        arq.seek(endereco)
        tam = int.from_bytes(arq.read(2))
        arq.read(1)
        log.write(f"[offset: {endereco}, tam: {tam}] -> ")
        espacos+=1
        endereco = int.from_bytes(arq.read(4),signed=True)
    log.write("fim\n")
    log.write(f"Total: {espacos} espaços disponíveis.\n")
    log.write("A LED foi impressa com sucesso!")
    log.close()



def compactar(arq:io.TextIOWrapper):
    '''
    Reescreve um novo arquivo compactado apenas com os registros válidos.
    '''
    compactado = open("filmes_compactado.dat","wb")
    redefinir_cabeca_leitura(arq)
    filme = le_filme(arq)
    
    compactado.write(int.to_bytes(-1,4,signed=True)) # Escreve a cabeça da LED
    while(filme):
        if filme.apagado: 
            filme = le_filme(arq)
            continue
        reg = filme_para_registro(filme).encode()
        tam = len(reg).to_bytes(2)
        compactado.write(tam)
        compactado.write(reg)
        filme = le_filme(arq)
    compactado.close()
    
    
def executa_operacoes(arq:io.TextIOBase,arq_ops:str,indices:list[Indice]):
    ops:io.TextIOBase = open(arq_ops,"r")
    operacao:str = ops.readline()
    log:io.TextIOBase = open("log_operacoes.txt","w+")

    while operacao:
        op = operacao[0]
        arg = operacao[2:]
        match op:
            case "b": # Busca
                chave = arg
                log.write(f"Busca pelo registro de chave \"{chave.strip()}\"\n")
                filme:Filme = busca_filme(arq,int(chave),indices)
                if filme != None and not filme.apagado:
                    arq.seek(filme.byte_offset)
                    tam = int.from_bytes(arq.read(2))
                    reg = filme_para_registro(filme)
                    log.write(f"{reg} ({len(reg.encode())} bytes) \nLocal: offset = {filme.byte_offset} bytes ({hex(filme.byte_offset)})\n\n")
                else:
                    log.write(f"Erro: registro não encontrado!\n\n")
            case "r": # Remoção
                chave = arg
                log.write(f"Remoção do registro de chave \"{chave.strip()}\"\n")
                filme:Filme = busca_filme(arq,int(chave),indices)
                if filme != None and not filme.apagado:
                    arq.seek(filme.byte_offset)
                    tam = int.from_bytes(arq.read(2))
                    apaga_filme(arq,filme)
                    indices = lista_indices(arq)
                    log.write(f"Registro removido! ({tam} bytes)\nLocal: offset = {filme.byte_offset} bytes ({hex(filme.byte_offset)})\n\n")
                else:
                    log.write(f"Erro: registro não encontrado!\n\n")
            case "i": # Inserção
                novo_filme = arg
                log.write(f"Inserção do registro de chave \"{novo_filme.split("|")[0]}\" ({len(novo_filme.encode())} bytes)\n")
                local, eof = inserir_filme(arq,novo_filme,indices)
                
                if local == -1: # ID repetido
                    log.write("Erro: ID já existe!\n\n")
                else:
                    indices = lista_indices(arq)
                
                    if(eof):
                        log.write("Local: fim do arquivo\n\n")
                    else:
                        log.write(f"Local: offset = {local} bytes ({hex(local)})\n\n")
                
        operacao = ops.readline()
    log.write(f"As operações do arquivo operacoes.txt foram executadas com sucesso!")
    log.close()
    ops.close()

def remover_da_led(arq: io.TextIOWrapper,offset:int):
    arq.seek(0)
    anter = 0
    prox = int.from_bytes(arq.read(4),signed=True)

    while(prox != -1 and prox != offset):
        anter = prox
        arq.seek(prox+3)
        prox = int.from_bytes(arq.read(4),signed=True)

    if(prox == -1):
        print("Erro: offset não pertence à LED.")
        return False
    
    arq.seek(prox)
    arq.read(3) # Pula tamanho e marcação
    prox = int.from_bytes(arq.read(4),signed=True)
    
    # CASO PATOLÓGICO: anter é a cabeça da LED. Não se pula os 3 bytes.
    arq.seek(anter+3 if anter != 0 else anter)
    arq.write(prox.to_bytes(4,signed=True))
    return True

def validar_id(arq:io.TextIOWrapper,id:int,indices:list[Indice]):
    '''
    Retorna se o ID existe na lista de indices ou não
    '''
    filme = busca_filme(arq,id,indices)
    return filme != None and not filme.apagado

def inserir_filme(arq: io.TextIOWrapper, registro_str: str,indices:list[Indice]) -> int:
    '''
    Insere um novo registro no arquivo pela estratégia de best-fit.
    '''
    if validar_id(arq,int(registro_str.split("|")[0]),indices): return -1,False

    registro = registro_str.encode('utf-8')
    tam = len(registro)
    tam_bytes = tam.to_bytes(2, 'big')

    offset = encontrar_melhor_espaço(arq,tam)
    if offset == None: # Sem espaço na LED, inserindo no fim do arquivo:
        arq.read()
        offset_inserido = arq.tell()
        arq.write(tam_bytes)
        arq.write(registro)
        return offset_inserido, True # Retorna o offset e se foi no fim do arquivo
    else:
        remover_da_led(arq,offset)
        arq.seek(offset)
        tamanho_anterior = int.from_bytes(arq.read(2))
        arq.write(registro)
        arq.write(b'\0'*(tamanho_anterior-tam)) # Preenche a sobra com 0
        return offset, False

def filme_para_registro(filme:Filme):
    '''
    Converte um objeto do tipo 'Filme' para uma string
    formatada como um registro
    '''
    return f"{filme.id}|{filme.titulo}|{filme.diretor}|{filme.ano}|{filme.genero}|{filme.duracao}|{filme.elenco}"

def main():
    args:list[str] = sys.argv
    assert len(args) >= 3, "Argumentos inválidos.\n Uso do programa: [nome-arquivo] [-e, -c, -p]"
    caminho_arq = args[1]
    op = args[2]
    arq = open(caminho_arq,"rb+")

    match op:
        case "-e":
            assert len(args) == 4, "Argumentos inválidos.\n Uso: [nome-arquivo] -e [arquivo-operacoes]"
            lista = lista_indices(arq)
            executa_operacoes(arq,args[3],lista)
        case "-c":
            compactar(arq)
        case "-p":
            imprime_led(arq)
    arq.close()

if __name__ == "__main__":
    main()

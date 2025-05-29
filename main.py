import io
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

def importa_filmes() -> io.TextIOWrapper:
    '''
    Abre o arquivo de filmes e o retorna
    '''
    # Abre o arquivo no modo de leitura binário
    arq:io.TextIOWrapper = open("filmes copy.dat","rb+")
    # Move a cabeça de leitura para frente do cabeçalho
    redefinir_cabeca_leitura(arq)
    return arq

def cabeca_da_led(arq:io.TextIOWrapper) -> int:
    '''
    Retorna o byte offset da cabeça da LED.
    '''
    arq.seek(0)
    cab = int.from_bytes(arq.read(4),signed=True)
    redefinir_cabeca_leitura(arq)
    return cab

def definir_cabeca_led(arq:io.TextIOWrapper,nova_cabeca:int) -> None:
    '''
    Define uma nova cabeça para a LED
    '''
    arq.seek(0)
    arq.write(nova_cabeca)
    redefinir_cabeca_leitura(arq)


def le_filme(arq:io.TextIOWrapper) -> Filme:
    '''
    Lê o pŕoximo filme da sequência do arquivo 'arq' e o retorna
    ''' 
    byte_offset = arq.tell()
    tam_reg = int.from_bytes(arq.read(2))

    if(tam_reg):
        coded = arq.read(tam_reg)
        try:
            filme = coded.decode('utf8')
        except UnicodeDecodeError as e:
            print("Caracter incompatível com UTF8. Registro apagado")
            return Filme(None,None,None,None,None,None,None,None,True)
        #print("PRIMEIRO: "+filme[0])
        if(filme[0] == '*'): # Registro apagado!
            print("APAGADO!!")
            return Filme(None,None,None,None,None,None,None,None,True)
        campos = filme.split('|')
        return Filme(int(campos[0]), campos[1], campos[2], int(campos[3]), campos[4], int(campos[5]), campos[6],byte_offset,False)
    else:
        return None

def acessa_filme(arq:io.TextIOWrapper,offset:int) -> Filme:
    '''
    Acessa diretamente o registro de filme no 'offset'
    '''
    
    arq.seek(offset)
    tam_reg = int.from_bytes(arq.read(2))

    if(tam_reg):
        coded = arq.read(tam_reg)
        try:
            filme = coded.decode('utf8')
        except UnicodeDecodeError as e:
            print("Caracter incompatível com UTF8. Registro apagado")
            return Filme(None,None,None,None,None,None,None,None,True)
        
        if(filme[0] == '*'): # Se o registro está marcado como excluído:
            print("Esse registro foi apagado.")
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


def inicializar() -> io.TextIOWrapper:
    '''
    Inicializa o arquivo
    '''
    arq = importa_filmes()
    return arq

def lista_indices(arq:io.TextIOWrapper) -> list[Indice]:
    '''
    Retorna uma lista da classe Indice
    contendo ID e byteoffset dos filmes.
    Essa lista já é ordenada por ID
    '''
    filme:Filme = le_filme(arq)

    lista:list[Indice] = []

    while filme:
        if(filme.apagado):
            filme = le_filme(arq)
            continue
        # Primeiro elemento
        if len(lista) == 0:
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
        

def conta_filmes(arq:io.TextIOWrapper):
    '''
    Retorna a quantidade de filmes no arquivo.
    '''
    redefinir_cabeca_leitura(arq) # Retornando ao início do arquivo
    filme:Filme = le_filme(arq)
    count = 0
    while(filme):
        count+=1
        filme = le_filme(arq)
    return count

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
    Adiciona o offset à LED
    
    -> -1

    56
    32|DADOS DADOS -> 32*-1DOS DADOS
    -> 56 -> -1

    72
    12|DADOS DADOS -> 12*103

    ->72 -> 103 -> 56 -> -1

    103
    23|DADOS DADOS -> 32*56
    '''
    arq.seek(0)
    anter = 0
    endereco = int.from_bytes(arq.read(4),signed=True)

    while(endereco != -1):
        arq.seek(endereco)
        espaco_disponivel = int.from_bytes(arq.read(2),signed=True)
        
        if(espaco_disponivel > tamanho):
            arq.seek(anter)
            arq.write(offset.to_bytes(4,signed=True))
            # DEBUG
            arq.seek(anter)
            tam = int.from_bytes(arq.read(2))
            reg = arq.read(tam)
            print(tam,reg)

            arq.seek(offset+3)
            arq.write(endereco.to_bytes(4,signed=True))
            #DEBUG
            arq.seek(offset)
            tam = int.from_bytes(arq.read(2))
            reg = arq.read(tam)
            print(tam,reg)
            print(reg[1:5])
            return
        else:
            anter = endereco+3
            arq.read(1)
            endereco = int.from_bytes(arq.read(4),signed=True)
            print(endereco)
            continue
            #32*-1
    # Escreve no final   
    arq.seek(anter)
    arq.write(offset.to_bytes(4,signed=True))
    arq.seek(offset+3)
    arq.write(endereco.to_bytes(4,signed=True))

    
def le_led(arq:io.TextIOWrapper):
    arq.seek(0)
    endereco = int.from_bytes(arq.read(4),signed=True)
    lista = ""
    while(endereco != -1):
        
        arq.seek(endereco)
        tam = int.from_bytes(arq.read(2))
        arq.read(1)
        lista += f"{endereco} ({tam} bytes) -> "
        endereco = int.from_bytes(arq.read(4),signed=True)
    lista += "-1 #"
    print(lista)

def main():
    arq = inicializar()
    redefinir_cabeca_leitura(arq)
    lista = lista_indices(arq)
    print(len(lista))
    filme = busca_filme(arq,lista[0].chave,lista)
    print(filme)
    
    apaga_filme(arq,filme)
    filme = busca_filme(arq,lista[0].chave,lista)
    le_led(arq)

if __name__ == "__main__":
    main()
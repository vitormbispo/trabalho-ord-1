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

@dataclass
class Indice:
    '''
    Armazena a chave primária(ID do filme)
    e o seu byte offset
    '''
    chave:int # ID do filme é a chave
    byte_offset:int

def redefinir_cabeca_leitura(arq:io.TextIOWrapper):
    '''
    Retorna a cabeça de leitura para o início do arquivo
    '''
    arq.seek(4)

def importa_filmes() -> io.TextIOWrapper:
    '''
    Abre o arquivo de filmes e o retorna
    '''
    # Abre o arquivo no modo de leitura binário
    arq:io.TextIOWrapper = open("filmes.dat","rb")
    # Move a cabeça de leitura para frente do cabeçalho
    redefinir_cabeca_leitura(arq)
    return arq

def cabeca_da_led(arq:io.TextIOWrapper) -> int:
    '''
    Retorna o byte offset da cabeça da LED.
    '''
    arq.seek(0)
    cab = int.from_bytes(arq.read(4))
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
        filme = arq.read(tam_reg).decode('utf8','strict')
        campos = filme.split('|')
        return Filme(int(campos[0]), campos[1], campos[2], int(campos[3]), campos[4], int(campos[5]), campos[6],byte_offset)
    else:
        return None

def acessa_filme(arq:io.TextIOWrapper,offset:int) -> Filme:
    '''
    Acessa diretamente o registro de filme no 'offset'
    '''
    
    arq.seek(offset)
    tam_reg = int.from_bytes(arq.read(2))

    if(tam_reg):
        filme = arq.read(tam_reg).decode('utf8','strict')
        if(filme[0] == "*"): # Se o registro está marcado como excluído:
            print("Esse registro foi apagado.")
            return None

        campos = filme.split('|') # Separa os campos
        return Filme(int(campos[0]), campos[1], campos[2], int(campos[3]), campos[4], int(campos[5]), campos[6],offset) # Cria um novo tipo filme
    else:
        return None # Filme não encontrado

def busca_filme(arq:io.TextIOWrapper,id:int,indices:list[Indice]) -> Filme:
    '''
    Faz uma busca binária no 'arq' usando os 'indices' procurando pelo filme com o
    'id'. Retorna o filme encontrado ou None caso não seja encontrado.
    '''

    split = len(indices)//2 # Divide a lista ao meio
    
    # CASOS BASE ----------------------------------------------------------------
    if(split == 0): # Acabou a lista, não retorna nada
        return None

    if(indices[split].chave == id): # Encontrou o filme, acessa e retorna
        return acessa_filme(arq,indices[split].byte_offset)
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

def lista_indices(arq:io.TextIOWrapper):
    '''
    Retorna uma lista da classe Indice
    contendo ID e byteoffset dos filmes.
    Essa lista já é ordenada por ID
    '''
    filme = le_filme(arq)

    lista:list[Indice] = []

    while filme:
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


def main():
    arq = inicializar()
    redefinir_cabeca_leitura(arq)
    lista = lista_indices(arq)
    print(busca_filme(arq,113,lista))


if __name__ == "__main__":
    main()
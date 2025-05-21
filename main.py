import io
from dataclasses import dataclass

# Classe para armazenar os dados de um filme
@dataclass
class Filme:
    id:int
    titulo:str
    diretor:str
    ano:int
    genero:str
    duracao:int
    elenco:str


def redefinir_cabeça_leitura(arq:io.TextIOWrapper):
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
    redefinir_cabeça_leitura(arq)
    return arq


def le_filme(arq:io.TextIOWrapper) -> Filme:
    '''
    Lê o pŕoximo filme da sequência do arquivo 'arq' e o retorna
    ''' 
    tam_reg = int.from_bytes(arq.read(2))
    if(tam_reg):
        filme = arq.read(tam_reg).decode('utf8','strict')
        campos = filme.split('|')
        return Filme(int(campos[0]), campos[1], campos[2], int(campos[3]), campos[4], int(campos[5]), campos[6])
    else:

        return None

def busca_filme(arq:io.TextIOWrapper,id:int) -> Filme:
    '''
    Faz uma busca sequencial no 'arq' procurando pelo filme de
    'id'. Retorna o filme encontrado ou None caso não seja encontrado.
    '''
    redefinir_cabeça_leitura(arq) # Retornando ao início do arquivo
    filme:Filme = le_filme(arq)

    while(filme):
        if(filme.id == id):
            return filme
        filme = le_filme(arq)
    print("Filme não encontrado!")
    return None

def main():
    arq = importa_filmes()
    
    filme:Filme = busca_filme(arq,78)
    if(filme):
        print(filme)
    else:
        print("Filme não encontrado")

if __name__ == "__main__":
    main()
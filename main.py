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

def importa_filmes() -> io.TextIOWrapper:
    '''
    Abre o arquivo de filmes e o retorna
    '''
    # Abre o arquivo no modo de leitura binário
    arq:io.TextIOWrapper = open("filmes.dat","rb")
    # Move a cabeça de leitura para frente do cabeçalho
    arq.seek(4)
    return arq


def le_filme(arq:io.TextIOWrapper) -> Filme:
    '''
    Lê o pŕoximo filme da sequência do arquivo 'arq' e o retorna
    ''' 
    tam_reg = int.from_bytes(arq.read(2))
    filme = arq.read(tam_reg).decode('utf8','strict')
    campos = filme.split('|')
    return Filme(campos[0], campos[1], campos[2], campos[3], campos[4], campos[5], campos[6])


def main():
    arq = importa_filmes()
    
    filme:Filme = le_filme(arq)
    print(filme.titulo)

if __name__ == "__main__":
    main()
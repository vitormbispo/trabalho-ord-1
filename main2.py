import io
from dataclasses import dataclass
import sys

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
    try:
        # Abre o arquivo no modo de leitura/escrita binário
        arq:io.TextIOWrapper = open("filmes.dat","rb+")
        return arq
    except FileNotFoundError:
        #  Caso o arquivo não exista, o programa deve apresentar uma mensagem de erro e terminar.
        print("Erro: O arquivo filmes.dat não foi encontrado.")
        sys.exit(1)


def le_filme(arq:io.TextIOWrapper) -> Filme:
    '''
    Lê o pŕoximo filme da sequência do arquivo 'arq' e o retorna
    ''' 
    byte_offset = arq.tell()
    tam_bytes = arq.read(2)

    if not tam_bytes:
        return None

    tam_reg = int.from_bytes(tam_bytes, 'big')

    if(tam_reg):
        try:
            filme_data = arq.read(tam_reg)
            filme = filme_data.decode('utf8')
        except UnicodeDecodeError as e:
            #Caracter incompatível com UTF8. Registro apagado
            return Filme(None,None,None,None,None,None,None,byte_offset,True)

        if(filme[0] == '*'): # Registro apagado!
            return Filme(None,None,None,None,None,None,None,byte_offset,True)
        campos = filme.split('|')
        return Filme(int(campos[0]), campos[1], campos[2], int(campos[3]), campos[4], int(campos[5]), campos[6],byte_offset,False)
    else:
        return None

def acessa_filme(arq:io.TextIOWrapper,offset:int) -> Filme:
    '''
    Acessa diretamente o registro de filme no 'offset'
    '''
    
    arq.seek(offset)
    tam_reg = int.from_bytes(arq.read(2),'big')

    if(tam_reg):
        try:
            filme = arq.read(tam_reg).decode('utf8')
        except UnicodeDecodeError as e:
            # Caracter incompatível com UTF8. Registro apagado
            return Filme(None,None,None,None,None,None,None,offset,True)
        
        if(filme[0] == '*'): # Se o registro está marcado como excluído:
            return Filme(None,None,None,None,None,None,None,offset,True)

        campos = filme.split('|') # Separa os campos
        return Filme(int(campos[0]), campos[1], campos[2], int(campos[3]), campos[4], int(campos[5]), campos[6],offset,False) # Cria um novo tipo filme
    else:
        return None # Filme não encontrado

def busca_filme(arq:io.TextIOWrapper,id:int,indices:list[Indice]) -> Filme:
    '''
    Faz uma busca binária no 'arq' usando os 'indices' procurando pelo filme com o
    'id'. Retorna o filme encontrado ou None caso não seja encontrado.
    '''
    if not indices:
        return None

    esquerda, direita = 0, len(indices) - 1

    while esquerda <= direita:
        meio = (esquerda + direita) // 2
        if indices[meio].chave == id:
            return acessa_filme(arq, indices[meio].byte_offset)
        elif indices[meio].chave < id:
            esquerda = meio + 1
        else:
            direita = meio - 1
    return None


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
    redefinir_cabeca_leitura(arq)
    lista:list[Indice] = []
    filme = le_filme(arq)
    
    while filme:
        if not filme.apagado:
            lista.append(Indice(filme.id,filme.byte_offset))
        filme = le_filme(arq)

    lista.sort(key=lambda x: x.chave)
    return lista

# >>> INÍCIO DO CÓDIGO ADICIONADO <<<

def buscar_melhor_espaco_led(arq: io.TextIOWrapper, tamanho_necessario: int):
    """
    Busca na LED o menor espaço que comporte o novo registro (Best-Fit).
    Retorna o offset do espaço, seu tamanho, e informações para remover o nó da lista.
    """
    arq.seek(0)
    cabeca_led = int.from_bytes(arq.read(4), 'big', signed=True)

    if cabeca_led == -1:
        return None, None, None, None

    melhor_offset = -1
    melhor_tamanho_bloco = float('inf')
    ponteiro_para_melhor_bloco_offset = 0
    ponteiro_next_do_melhor_bloco = -1

    ponteiro_anterior_offset = 0
    offset_atual = cabeca_led

    while offset_atual != -1:
        arq.seek(offset_atual)
        tamanho_bloco = int.from_bytes(arq.read(2), 'big', signed=False)
        arq.read(1)  # Pula o '*'
        proximo_offset = int.from_bytes(arq.read(4), 'big', signed=True)

        if tamanho_necessario <= tamanho_bloco < melhor_tamanho_bloco:
            melhor_tamanho_bloco = tamanho_bloco
            melhor_offset = offset_atual
            ponteiro_para_melhor_bloco_offset = ponteiro_anterior_offset
            ponteiro_next_do_melhor_bloco = proximo_offset

        ponteiro_anterior_offset = offset_atual + 3  # Local do ponteiro 'próximo' no registro atual
        offset_atual = proximo_offset

    if melhor_offset != -1:
        return melhor_offset, melhor_tamanho_bloco, ponteiro_para_melhor_bloco_offset, ponteiro_next_do_melhor_bloco
    else:
        return None, None, None, None

def insere_filme(arq: io.TextIOWrapper, log: io.TextIOBase, id_filme: int, dados_filme: str):
    """
    Insere um novo filme no arquivo, reutilizando espaço da LED (best-fit) ou
    adicionando ao final do arquivo.
    """
    #  Cada filme possui um identificador único que servirá como chave primária, o qual segue o campo de tamanho.
    registro_str = f"{id_filme}|{dados_filme}"
    filme_bytes = registro_str.encode('utf-8')
    tamanho_necessario = len(filme_bytes)

    log.write(f'Inserção do registro de chave "{id_filme}" ({tamanho_necessario} bytes)\n')

    #  No momento da inserção de novos registros, a LED deverá ser consultada utilizando a estratégia melhor ajuste (best-fit).
    offset, tamanho_reutilizado, ponteiro_prev_offset, ponteiro_next_valor = buscar_melhor_espaco_led(arq, tamanho_necessario)

    novo_offset = -1

    if offset is not None:
        #  Se existir um espaço disponível para a inserção, o novo registro deverá ser inserido nesse espaço.
        # Remove o bloco da LED ao fazer o ponteiro anterior apontar para o próximo
        arq.seek(ponteiro_prev_offset)
        arq.write(ponteiro_next_valor.to_bytes(4, 'big', signed=True))

        # Escreve o novo registro no espaço reutilizado
        arq.seek(offset)
        #  os campos de tamanho dos registros têm 2 bytes (um número inteiro sem sinal).
        arq.write(tamanho_necessario.to_bytes(2, 'big', signed=False))
        arq.write(filme_bytes)

        #  Log da inserção com reutilização de espaço.
        log.write(f'Tamanho do espaço reutilizado: {tamanho_reutilizado} bytes\n')
        log.write(f'Local: offset = {offset} bytes ({hex(offset)})\n\n')
        novo_offset = offset
    else:
        #  Caso não seja encontrado na LED um espaço adequado, ele deverá ser inserido no final do arquivo.
        arq.seek(0, 2)
        final_offset = arq.tell()
        arq.write(tamanho_necessario.to_bytes(2, 'big', signed=False))
        arq.write(filme_bytes)

        #  Log da inserção no fim do arquivo.
        log.write('Local: fim do arquivo\n\n')
        novo_offset = final_offset

    return novo_offset
# >>> FIM DO CÓDIGO ADICIONADO <<<

def apaga_filme(arq:io.TextIOWrapper,filme:Filme) -> None:
    '''
    Apaga o registro do 'filme' do 'arq'
    '''
    
    arq.seek(filme.byte_offset)
    tamanho = int.from_bytes(arq.read(2), 'big')
    arq.seek(filme.byte_offset + 2) # Pula o campo de tamanho para marcar
    #  A remoção de registros será lógica
    arq.write(b'*')
    adicionar_a_led(arq,filme.byte_offset,tamanho)

def adicionar_a_led(arq:io.TextIOWrapper,offset:int,tamanho:int):
    '''
    Adiciona o 'offset' de um filme à LED. A lista não é ordenada aqui.
    A busca best-fit cuida da lógica de encontrar o melhor espaço.
    A inserção é feita no início da lista para simplicidade.
    '''
    arq.seek(0)
    cabeca_atual = int.from_bytes(arq.read(4), 'big', signed=True)

    # O novo espaço removido aponta para a antiga cabeça da lista
    arq.seek(offset + 3) # Posição do ponteiro no registro removido
    arq.write(cabeca_atual.to_bytes(4, 'big', signed=True))

    # A cabeça da lista agora aponta para o novo espaço removido
    arq.seek(0)
    arq.write(offset.to_bytes(4, 'big', signed=True))


def le_led(arq:io.TextIOWrapper):
    '''
    Exibe a LED
    '''
    #  Sempre que ativada, essa funcionalidade apresentará na tela os offsets dos espaços disponíveis...
    arq.seek(0)
    endereco = int.from_bytes(arq.read(4),'big',signed=True)
    lista_str = "LED -> "
    count = 0
    while(endereco != -1):
        count += 1
        arq.seek(endereco)
        tam = int.from_bytes(arq.read(2),'big', signed=False)
        lista_str += f"[offset: {endereco}, tam: {tam}] -> "
        arq.read(1) # Pula o '*'
        endereco = int.from_bytes(arq.read(4),'big',signed=True)
    
    lista_str += "[offset: -1]"
    print(lista_str)
    print(f"Total: {count} espacos disponiveis")


def compact(arq:io.TextIOWrapper):
    #  Sempre que ativada, essa funcionalidade deverá gerar uma nova versão do arquivo filmes.dat...
    if not arq:
        return False
    
    redefinir_cabeca_leitura(arq)
    filmes_validos = []
    filme = le_filme(arq)
    while filme:
        if not filme.apagado:
            arq.seek(filme.byte_offset)
            tamanho = int.from_bytes(arq.read(2), 'big')
            arq.seek(filme.byte_offset)
            filmes_validos.append(arq.read(2 + tamanho))
        filme = le_filme(arq)

    # Zera o cabeçalho da LED e reescreve o arquivo
    arq.seek(0)
    arq.write((-1).to_bytes(4, 'big', signed=True))
    for registro in filmes_validos:
        arq.write(registro)
    
    arq.truncate() # Remove o lixo restante no final do arquivo
    print("Arquivo compactado com sucesso.")
    return True

def executa_operacoes(arq:io.TextIOBase,indices:list[Indice]):
    #  A execução do arquivo de operações será acionada pela linha de comando...
    try:
        ops:io.TextIOBase = open("operacoes.txt","r")
    except FileNotFoundError:
        print("Erro: Arquivo de operações 'operacoes.txt' não encontrado.")
        return

    log:io.TextIOBase = open("log_operacoes.txt","w+", encoding='utf-8')

    operacao:str = ops.readline()

    while operacao:
        #  O arquivo de operações deve possuir uma operação por linha...
        args = operacao.strip().split(" ")
        op = args[0]
        match op:
            case "b": # Busca
                chave = args[1]
                log.write(f"Busca pelo registro de chave \"{chave.strip()}\"\n")
                filme:Filme = busca_filme(arq,int(chave),indices)
                if filme is not None and not filme.apagado:
                    arq.seek(filme.byte_offset)
                    tam = int.from_bytes(arq.read(2), 'big')
                    #  Exemplo de saída da busca.
                    log.write(f"{filme_para_registro(filme)} ({tam} bytes)\n")
                else:
                    #  Exemplo de saída de erro na remoção (aplicável à busca).
                    log.write(f"Erro: registro não encontrado!\n")
                log.write("\n")

            case "r": # Remoção
                chave = args[1]
                log.write(f"Remoção do registro de chave \"{chave.strip()}\"\n")
                filme:Filme = busca_filme(arq,int(chave),indices)
                if filme is not None and not filme.apagado:
                    arq.seek(filme.byte_offset)
                    tam = int.from_bytes(arq.read(2), 'big')
                    apaga_filme(arq,filme)
                    # Remove o índice da lista em memória
                    indices[:] = [idx for idx in indices if idx.chave != int(chave)]
                    #  Exemplo de saída da remoção.
                    log.write(f"Registro removido! ({tam} bytes)\nLocal: offset = {filme.byte_offset} ({hex(filme.byte_offset)})\n\n")
                else:
                    log.write(f"Erro: registro não encontrado!\n\n")
            
            # >>> INÍCIO DA MODIFICAÇÃO <<<
            case "i": # Inserção 
                chave_str = args[1]
                dados_filme = " ".join(args[2:])
                
                novo_offset = insere_filme(arq, log, int(chave_str), dados_filme)
                
                # Adiciona o novo filme à lista de índices em memória para buscas futuras na mesma execução
                novo_id = int(chave_str)
                novo_indice = Indice(chave=novo_id, byte_offset=novo_offset)
                
                # Insere o novo índice mantendo a lista ordenada
                inserted = False
                for i in range(len(indices)):
                    if novo_id < indices[i].chave:
                        indices.insert(i, novo_indice)
                        inserted = True
                        break
                if not inserted:
                    indices.append(novo_indice)
            # >>> FIM DA MODIFICAÇÃO <<<

        operacao = ops.readline()

    ops.close()
    log.close()
    print("Arquivo 'log_operacoes.txt' gerado com sucesso.")

def filme_para_registro(filme:Filme):
    '''
    Converte um objeto do tipo 'Filme' para uma string
    formatada como um registro
    '''
    return f"{filme.id}|{filme.titulo}|{filme.diretor}|{filme.ano}|{filme.genero}|{filme.duracao}|{filme.elenco}"

def main():
    #  O programa principal que processa os argumentos da linha de comando.
    if len(sys.argv) < 2:
        print("Uso: python programa.py [-e | -p | -c]")
        return

    flag = sys.argv[1]
    arq = inicializar()

    if flag == "-e":
        redefinir_cabeca_leitura(arq)
        lista = lista_indices(arq)
        executa_operacoes(arq,lista)
    elif flag == "-p":
        #  A funcionalidade de impressão da LED também será acessada via linha de comando...
        le_led(arq)
    elif flag == "-c":
        #  A funcionalidade de compactação do arquivo filmes.dat também será acessada via linha de comando...
        compact(arq)
    else:
        print(f"Flag '{flag}' não reconhecida.")

    arq.close()


if __name__ == "__main__":
    main()
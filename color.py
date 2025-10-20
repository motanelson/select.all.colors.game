import pygame
import random
import csv
import time
import sys

# --- 1. Configurações e Cores VGA ---
# 15 Cores VGA (sem Amarelo)
# A ordem é importante para a sequência do jogo (Preto -> Azul -> ... -> Branco)
VGA_COLORS = {
    "PRETO": (0, 0, 0),
    "AZUL": (0, 0, 170),
    "VERDE": (0, 170, 0),
    "CIANO": (0, 170, 170),
    "VERMELHO": (170, 0, 0),
    "MAGENTA": (170, 0, 170),
    "CASTANHO": (170, 85, 0), # Brown / Laranja Escuro
    "CINZENTO CLARO": (170, 170, 170),
    "CINZENTO ESCURO": (85, 85, 85),
    "AZUL CLARO": (85, 85, 255),
    "VERDE CLARO": (85, 255, 85),
    "CIANO CLARO": (85, 255, 255),
    "VERMELHO CLARO": (255, 85, 85),
    "MAGENTA CLARO": (255, 85, 255),
    "BRANCO": (255, 255, 255),
}

# Cor Amarela para Peças Viradas (Cor Excluída da Lista principal)
YELLOW = (255, 255, 85) # Um Amarelo claro/VGA

# Constantes do Jogo
GRID_SIZE = 8
TILE_SIZE = 60
GRID_START_Y = 100 # Início da grelha abaixo do placar/tempo
MARGIN = 5 # Espaçamento entre os retângulos
HEADER_HEIGHT = GRID_START_Y # Altura da área de tempo/placar
SCREEN_WIDTH = GRID_SIZE * TILE_SIZE + (GRID_SIZE + 1) * MARGIN
SCREEN_HEIGHT = SCREEN_WIDTH + HEADER_HEIGHT # Altura total da janela
TABLE_FILE = 'table.csv'

# --- 2. Funções Auxiliares ---

def load_scores():
    """Carrega o placar (scores) do arquivo CSV."""
    scores = []
    try:
        with open(TABLE_FILE, mode='r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            # Pula o cabeçalho
            next(reader, None)
            for row in reader:
                # Converte o tempo para float e salva
                scores.append({'nome': row[0], 'tempo': float(row[1])})
    except FileNotFoundError:
        # Cria o arquivo se não existir
        save_scores(scores)
    except Exception as e:
        print(f"Erro ao carregar scores: {e}")
    
    # Ordena pelo tempo, do menor para o maior
    scores.sort(key=lambda x: x['tempo'])
    return scores

def save_scores(scores):
    """Salva o placar (scores) no arquivo CSV."""
    scores.sort(key=lambda x: x['tempo']) # Garante que está ordenado
    try:
        with open(TABLE_FILE, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Nome', 'Tempo (segundos)'])
            for score in scores:
                writer.writerow([score['nome'], f"{score['tempo']:.2f}"])
    except Exception as e:
        print(f"Erro ao salvar scores: {e}")

def create_grid():
    """Cria a grelha 8x8 com as 15 cores sorteadas aleatoriamente."""
    # Lista das cores disponíveis para o sorteio
    color_list = list(VGA_COLORS.values())
    
    # Preenche a grelha com as 64 cores sorteadas
    grid_colors = [random.choice(color_list) for _ in range(GRID_SIZE * GRID_SIZE)]
    random.shuffle(grid_colors)
    
    # Cria a matriz da grelha
    grid = []
    for i in range(GRID_SIZE):
        row = []
        for j in range(GRID_SIZE):
            # Armazena a cor original e o estado (virada/completa)
            row.append({
                'color': grid_colors.pop(),
                'rect': pygame.Rect(
                    MARGIN + j * (TILE_SIZE + MARGIN),
                    GRID_START_Y + MARGIN + i * (TILE_SIZE + MARGIN),
                    TILE_SIZE, TILE_SIZE
                ),
                'completed': False
            })
        grid.append(row)
    return grid

# --- 3. Inicialização do Pygame ---
pygame.init()
pygame.font.init()

# Setup da janela
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
clock = pygame.time.Clock()
font_time = pygame.font.SysFont('Arial', 30, bold=True)
font_message = pygame.font.SysFont('Arial', 40, bold=True)
font_score = pygame.font.SysFont('Arial', 24)

# --- 4. Variáveis do Jogo ---
grid = create_grid()
all_colors = list(VGA_COLORS.values())
current_color_index = 0
target_color = all_colors[current_color_index]
current_color_name = list(VGA_COLORS.keys())[current_color_index]
cells_completed = 0

game_started = False
game_over = False
start_time = 0.0
end_time = 0.0
total_time = 0.0
running = True

# --- 5. Funções de Desenho ---

def draw_grid():
    """Desenha a grelha de retângulos."""
    for row in grid:
        for tile in row:
            # Se a peça estiver virada/correta, desenha Amarelo
            if tile['completed']:
                pygame.draw.rect(screen, YELLOW, tile['rect'])
            else:
                # Caso contrário, desenha a cor original da peça
                pygame.draw.rect(screen, tile['color'], tile['rect'])

def draw_header(elapsed_time):
    """Desenha o tempo no título da janela e o fundo com a cor alvo."""
    
    # Cor de fundo (Cor Alvo)
    pygame.draw.rect(screen, target_color, (0, SCREEN_HEIGHT - 50, SCREEN_WIDTH, 50))
    
    # Desenha o nome da cor alvo
    text_color = (255, 255, 255) if sum(target_color) < 382.5 else (0, 0, 0) # Cor do texto (preto ou branco)
    color_text = font_time.render(f"Cor a Juntar: {current_color_name}", True, text_color)
    screen.blit(color_text, (10, SCREEN_HEIGHT - 45))

    # Desenha o tempo no topo da janela
    time_text = f"Tempo: {elapsed_time:.2f}s | Peças: {cells_completed}/64"
    pygame.display.set_caption(f"Caça-Cores | {time_text}")

def draw_game_over_screen():
    """Desenha o placar (score board) ao terminar o jogo."""
    global total_time, font_score
    
    # Fundo semi-transparente
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    overlay.set_alpha(200) # Semi-transparente
    overlay.fill((0, 0, 0))
    screen.blit(overlay, (0, 0))

    # Título
    title_text = font_message.render("JOGO CONCLUÍDO!", True, (255, 255, 0))
    screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, 50))
    
    # Tempo total
    time_text = font_message.render(f"O Seu Tempo: {total_time:.2f} segundos", True, (255, 255, 255))
    screen.blit(time_text, (SCREEN_WIDTH // 2 - time_text.get_width() // 2, 120))
    
    # Placar (Scores)
    scores = load_scores()
    
    score_title = font_time.render("Quadro de Pontuação (Top 10):", True, (0, 255, 255))
    screen.blit(score_title, (50, 200))

    y_offset = 250
    # Desenha os 10 melhores
    for i, score in enumerate(scores[:10]):
        text = font_score.render(f"{i+1}. {score['nome']} - {score['tempo']:.2f}s", True, (255, 255, 255))
        screen.blit(text, (50, y_offset + i * 30))
        
    # Mensagem de reinício
    restart_text = font_time.render("Pressione ENTER para Jogar Novamente", True, (255, 165, 0))
    screen.blit(restart_text, (SCREEN_WIDTH // 2 - restart_text.get_width() // 2, SCREEN_HEIGHT - 100))


def get_player_name():
    """Permite ao jogador introduzir o seu nome."""
    global screen
    name = ""
    input_active = True
    input_rect = pygame.Rect(SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2, 300, 50)
    
    while input_active:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    # Garante que o nome não está vazio antes de continuar
                    if name:
                        input_active = False
                elif event.key == pygame.K_BACKSPACE:
                    name = name[:-1]
                else:
                    # Limita o nome para não ultrapassar o campo
                    if font_message.size(name + event.unicode)[0] < input_rect.width - 10:
                        name += event.unicode

        screen.fill((20, 20, 20)) # Limpa o ecrã
        
        # Desenha a mensagem
        prompt_text = font_message.render("Introduza o Seu Nome:", True, (255, 255, 255))
        screen.blit(prompt_text, (SCREEN_WIDTH // 2 - prompt_text.get_width() // 2, SCREEN_HEIGHT // 2 - 60))
        
        # Desenha a caixa de input
        pygame.draw.rect(screen, (255, 255, 255), input_rect, 2)
        
        # Desenha o texto do nome
        txt_surface = font_message.render(name, True, (255, 255, 255))
        screen.blit(txt_surface, (input_rect.x + 5, input_rect.y + 5))
        
        pygame.display.flip()
        clock.tick(30)
        
    return name

# --- 6. Game Loop Principal ---

while running:
    # Lógica de Tempo
    if game_started and not game_over:
        current_time = time.time()
        elapsed_time = current_time - start_time
    elif game_over:
        elapsed_time = total_time
    else:
        # Antes de começar
        elapsed_time = 0.0

    # --- 6.1 Tratamento de Eventos ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        if game_over and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                # Reiniciar o jogo
                grid = create_grid()
                current_color_index = 0
                target_color = all_colors[current_color_index]
                current_color_name = list(VGA_COLORS.keys())[current_color_index]
                cells_completed = 0
                game_over = False
                game_started = False
                start_time = 0.0
                total_time = 0.0
                pygame.display.set_caption("Caça-Cores | Pressione para Começar")
                
        if not game_started and not game_over and event.type == pygame.MOUSEBUTTONDOWN:
            # Iniciar o jogo no primeiro clique
            game_started = True
            start_time = time.time()
        
        if game_started and not game_over and event.type == pygame.MOUSEBUTTONDOWN:
            pos = event.pos
            # Verifica se o clique foi em algum quadrado da grelha
            for i in range(GRID_SIZE):
                for j in range(GRID_SIZE):
                    tile = grid[i][j]
                    if tile['rect'].collidepoint(pos):
                        
                        if not tile['completed']:
                            # Lógica de "Juntar as Peças"
                            if tile['color'] == target_color:
                                # Peça correta!
                                tile['completed'] = True
                                cells_completed += 1
                                
                                # Verifica se a cor atual está completa (todas as 4 peças)
                                # Em 64 peças e 15 cores, a cor mais presente tem 5 peças,
                                # as restantes têm 4. É mais fácil verificar a cor completada
                                
                                count_current_color_on_grid = sum(1 for row in grid for t in row if t['color'] == target_color)
                                count_completed_of_current_color = sum(1 for row in grid for t in row if t['completed'] and t['color'] == target_color)
                                
                                if count_completed_of_current_color == count_current_color_on_grid:
                                    # Mudar para a próxima cor
                                    current_color_index += 1
                                    
                                    if current_color_index < len(all_colors):
                                        # Próxima cor alvo
                                        target_color = all_colors[current_color_index]
                                        current_color_name = list(VGA_COLORS.keys())[current_color_index]
                                    else:
                                        # Fim do jogo (Todas as 15 cores completas)
                                        game_over = True
                                        end_time = time.time()
                                        total_time = end_time - start_time
                                        
                                        # Guarda a pontuação
                                        player_name = get_player_name()
                                        scores = load_scores()
                                        scores.append({'nome': player_name, 'tempo': total_time})
                                        save_scores(scores)
                                        pygame.display.set_caption("FIM DO JOGO")
                                    
    # --- 6.2 Desenho ---
    screen.fill((40, 40, 40)) # Fundo principal Cinzento Escuro
    
    if not game_started and not game_over:
        # Tela de Início
        start_message = font_message.render("Caça-Cores: Clique para Começar", True, (0, 255, 0))
        instructions_line1 = font_time.render("Objetivo: Encontrar todas as peças da cor no fundo.", True, (255, 255, 255))
        instructions_line2 = font_time.render("As peças corretas ficam AMARELAS.", True, (255, 255, 0))
        screen.blit(start_message, (SCREEN_WIDTH // 2 - start_message.get_width() // 2, SCREEN_HEIGHT // 2 - 80))
        screen.blit(instructions_line1, (SCREEN_WIDTH // 2 - instructions_line1.get_width() // 2, SCREEN_HEIGHT // 2 + 0))
        screen.blit(instructions_line2, (SCREEN_WIDTH // 2 - instructions_line2.get_width() // 2, SCREEN_HEIGHT // 2 + 40))

    elif not game_over:
        # Jogo em Andamento
        draw_grid()
        draw_header(elapsed_time)
        
    elif game_over:
        # Tela de Fim de Jogo/Placar
        draw_game_over_screen()

    # Atualiza a janela
    pygame.display.flip()
    
    # Limita o FPS
    clock.tick(60)

pygame.quit()
sys.exit()

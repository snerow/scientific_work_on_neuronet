import pygame
import random

# Инициализация pygame
pygame.init()

# Цвета
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
COLORS = [
    (0, 255, 255),  # I - голубой
    (0, 0, 255),  # J - синий
    (255, 165, 0),  # L - оранжевый
    (255, 255, 0),  # O - желтый
    (0, 255, 0),  # S - зеленый
    (128, 0, 128),  # T - фиолетовый
    (255, 0, 0)  # Z - красный
]

# Настройки игры
BLOCK_SIZE = 30  # Размер одного блока
GRID_WIDTH = 10  # Ширина игрового поля в блоках
GRID_HEIGHT = 20  # Высота игрового поля в блоках
GAME_AREA_LEFT = 100  # Отступ игрового поля слева
GAME_AREA_TOP = 50  # Отступ игрового поля сверху

# Фигуры тетриса (каждая фигура - список позиций блоков относительно центра)
SHAPES = [
    [[1, 1, 1, 1]],  # I
    [[1, 0, 0], [1, 1, 1]],  # J
    [[0, 0, 1], [1, 1, 1]],  # L
    [[1, 1], [1, 1]],  # O
    [[0, 1, 1], [1, 1, 0]],  # S
    [[0, 1, 0], [1, 1, 1]],  # T
    [[1, 1, 0], [0, 1, 1]]  # Z
]

# Настройка экрана
screen_width = GAME_AREA_LEFT + GRID_WIDTH * BLOCK_SIZE + 200
screen_height = GAME_AREA_TOP + GRID_HEIGHT * BLOCK_SIZE + 50
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Тетрис")

clock = pygame.time.Clock()
FPS = 60
fall_speed = 0.5  # Скорость падения (секунды на клетку)
fall_time = 0

# Игровые переменные
grid = [[0 for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
current_piece = None
next_piece = None
current_x = GRID_WIDTH // 2
current_y = 0
score = 0
game_over = False
pause = False

# Шрифты
font = pygame.font.SysFont('Arial', 24)
big_font = pygame.font.SysFont('Arial', 40)


def new_piece():
    """Создает новую случайную фигуру"""
    global current_piece, current_x, current_y, next_piece

    if next_piece is None:
        # Если следующей фигуры нет, создаем две случайные
        piece_idx = random.randint(0, len(SHAPES) - 1)
        next_piece_idx = random.randint(0, len(SHAPES) - 1)
        current_piece = (piece_idx, SHAPES[piece_idx], COLORS[piece_idx])
        next_piece = (next_piece_idx, SHAPES[next_piece_idx], COLORS[next_piece_idx])
    else:
        # Иначе используем подготовленную следующую фигуру
        current_piece = next_piece
        next_piece_idx = random.randint(0, len(SHAPES) - 1)
        next_piece = (next_piece_idx, SHAPES[next_piece_idx], COLORS[next_piece_idx])

    current_x = GRID_WIDTH // 2 - len(current_piece[1][0]) // 2
    current_y = 0

    # Проверка на проигрыш (если новая фигура не может быть размещена)
    if check_collision():
        return False
    return True


def check_collision():
    """Проверяет столкновение текущей фигуры с границами или другими блоками"""
    shape = current_piece[1]
    for y, row in enumerate(shape):
        for x, cell in enumerate(row):
            if cell:
                # Проверка границ
                if (current_x + x < 0 or current_x + x >= GRID_WIDTH or
                        current_y + y >= GRID_HEIGHT):
                    return True
                # Проверка на другие блоки (кроме верхней границы)
                if current_y + y >= 0 and grid[current_y + y][current_x + x]:
                    return True
    return False


def rotate_piece():
    """Поворачивает текущую фигуру на 90 градусов"""
    global current_piece

    # Для квадрата (O) вращение не нужно
    if current_piece[0] == 3:
        return

    # Получаем текущую фигуру и ее индекс
    piece_idx, shape, color = current_piece

    # Создаем повернутую фигуру
    rotated = []
    for x in range(len(shape[0])):
        new_row = []
        for y in range(len(shape) - 1, -1, -1):
            new_row.append(shape[y][x])
        rotated.append(new_row)

    # Сохраняем старую фигуру на случай, если повернутая не подойдет
    old_shape = shape
    current_piece = (piece_idx, rotated, color)

    # Проверяем столкновения после поворота
    if check_collision():
        # Если есть столкновение - возвращаем старую фигуру
        current_piece = (piece_idx, old_shape, color)


def draw_grid():
    """Рисует сетку игрового поля"""
    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            rect = pygame.Rect(
                GAME_AREA_LEFT + x * BLOCK_SIZE,
                GAME_AREA_TOP + y * BLOCK_SIZE,
                BLOCK_SIZE, BLOCK_SIZE
            )
            pygame.draw.rect(screen, GRAY, rect, 1)


def draw_blocks():
    """Рисует все блоки на игровом поле"""
    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            if grid[y][x]:
                rect = pygame.Rect(
                    GAME_AREA_LEFT + x * BLOCK_SIZE,
                    GAME_AREA_TOP + y * BLOCK_SIZE,
                    BLOCK_SIZE, BLOCK_SIZE
                )
                pygame.draw.rect(screen, grid[y][x], rect)
                pygame.draw.rect(screen, WHITE, rect, 1)


def draw_current_piece():
    """Рисует текущую падающую фигуру"""
    if current_piece is None:
        return

    shape = current_piece[1]
    color = current_piece[2]

    for y, row in enumerate(shape):
        for x, cell in enumerate(row):
            if cell and current_y + y >= 0:
                rect = pygame.Rect(
                    GAME_AREA_LEFT + (current_x + x) * BLOCK_SIZE,
                    GAME_AREA_TOP + (current_y + y) * BLOCK_SIZE,
                    BLOCK_SIZE, BLOCK_SIZE
                )
                pygame.draw.rect(screen, color, rect)
                pygame.draw.rect(screen, WHITE, rect, 1)


def draw_next_piece():
    """Рисует следующую фигуру"""
    if next_piece is None:
        return

    # Координаты области для отображения следующей фигуры
    next_left = GAME_AREA_LEFT + GRID_WIDTH * BLOCK_SIZE + 50
    next_top = GAME_AREA_TOP + 100

    # Рисуем заголовок
    text = font.render("Следующая:", True, WHITE)
    screen.blit(text, (next_left, next_top - 40))

    shape = next_piece[1]
    color = next_piece[2]

    # Рисуем фигуру
    for y, row in enumerate(shape):
        for x, cell in enumerate(row):
            if cell:
                rect = pygame.Rect(
                    next_left + x * BLOCK_SIZE,
                    next_top + y * BLOCK_SIZE,
                    BLOCK_SIZE, BLOCK_SIZE
                )
                pygame.draw.rect(screen, color, rect)
                pygame.draw.rect(screen, WHITE, rect, 1)


def draw_score():
    """Отображает текущий счет"""
    score_text = font.render(f"Счет: {score}", True, WHITE)
    screen.blit(score_text, (GAME_AREA_LEFT + GRID_WIDTH * BLOCK_SIZE + 50, GAME_AREA_TOP))


def lock_piece():
    """Фиксирует текущую фигуру на игровом поле"""
    global grid, score

    shape = current_piece[1]
    color = current_piece[2]

    for y, row in enumerate(shape):
        for x, cell in enumerate(row):
            if cell and current_y + y >= 0:
                grid[current_y + y][current_x + x] = color

    # Проверяем заполненные линии
    lines_cleared = 0
    for y in range(GRID_HEIGHT):
        if all(grid[y]):
            lines_cleared += 1
            # Удаляем линию и сдвигаем все выше
            for y2 in range(y, 0, -1):
                grid[y2] = grid[y2 - 1][:]
            grid[0] = [0] * GRID_WIDTH

    # Начисляем очки за очищенные линии
    if lines_cleared == 1:
        score += 100
    elif lines_cleared == 2:
        score += 300
    elif lines_cleared == 3:
        score += 500
    elif lines_cleared == 4:
        score += 800


def draw_game_over():
    """Отображает сообщение о конце игры"""
    if game_over:
        text = big_font.render("ИГРА ОКОНЧЕНА", True, (255, 0, 0))
        text_rect = text.get_rect(center=(screen_width // 2, screen_height // 2 - 50))
        screen.blit(text, text_rect)

        restart_text = font.render("Нажмите R для рестарта", True, WHITE)
        restart_rect = restart_text.get_rect(center=(screen_width // 2, screen_height // 2 + 20))
        screen.blit(restart_text, restart_rect)


def draw_pause():
    """Отображает сообщение о паузе"""
    if pause:
        # Затемняем экран
        s = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        s.fill((0, 0, 0, 128))
        screen.blit(s, (0, 0))

        text = big_font.render("ПАУЗА", True, WHITE)
        text_rect = text.get_rect(center=(screen_width // 2, screen_height // 2 - 50))
        screen.blit(text, text_rect)

        continue_text = font.render("Нажмите P для продолжения", True, WHITE)
        continue_rect = continue_text.get_rect(center=(screen_width // 2, screen_height // 2 + 20))
        screen.blit(continue_text, continue_rect)


def reset_game():
    """Сбрасывает игровое состояние для новой игры"""
    global grid, current_piece, next_piece, current_x, current_y, score, game_over

    grid = [[0 for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
    current_piece = None
    next_piece = None
    current_x = GRID_WIDTH // 2
    current_y = 0
    score = 0
    game_over = False

    # Создаем первую фигуру
    new_piece()


# Основной игровой цикл
reset_game()
running = True

while running:
    # Обработка событий
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if not game_over and not pause:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    current_x -= 1
                    if check_collision():
                        current_x += 1
                elif event.key == pygame.K_RIGHT:
                    current_x += 1
                    if check_collision():
                        current_x -= 1
                elif event.key == pygame.K_DOWN:
                    current_y += 1
                    if check_collision():
                        current_y -= 1
                        lock_piece()
                        if not new_piece():
                            game_over = True
                elif event.key == pygame.K_UP:
                    rotate_piece()
                elif event.key == pygame.K_SPACE:
                    # Мгновенное падение
                    while not check_collision():
                        current_y += 1
                    current_y -= 1
                    lock_piece()
                    if not new_piece():
                        game_over = True
                elif event.key == pygame.K_p:
                    pause = True

        elif game_over:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                reset_game()

        elif pause:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_p:
                pause = False

    # Обновление игры
    if not game_over and not pause:
        # Автоматическое падение фигуры
        fall_time += clock.get_rawtime() / 1000  # Время в секундах
        clock.tick(FPS)

        if fall_time >= fall_speed:
            fall_time = 0
            current_y += 1
            if check_collision():
                current_y -= 1
                lock_piece()
                if not new_piece():
                    game_over = True

    # Отрисовка
    screen.fill(BLACK)

    # Рисуем игровое поле
    draw_grid()
    draw_blocks()
    draw_current_piece()

    # Рисуем интерфейс
    draw_next_piece()
    draw_score()

    # Рисуем сообщения (если нужно)
    draw_game_over()
    draw_pause()

    pygame.display.flip()

pygame.quit()
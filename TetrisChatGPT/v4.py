import pygame
import random

# Константы
WIDTH = 300
HEIGHT = 600
BLOCK_SIZE = 30
TEXT_HEIGHT = 50  # Высота текстового поля
ROWS = HEIGHT // BLOCK_SIZE
COLS = WIDTH // BLOCK_SIZE
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

# Фигуры Тетромино
SHAPES = [
    [[1, 1, 1, 1]],  # I
    [[1, 1], [1, 1]],  # O
    [[0, 1, 0], [1, 1, 1]],  # T
    [[1, 0, 0], [1, 1, 1]],  # L
    [[0, 0, 1], [1, 1, 1]]   # J
]

class Piece:
    def __init__(self):
        self.shape = random.choice(SHAPES)
        self.color = WHITE
        self.x = COLS // 2 - len(self.shape[0]) // 2
        self.y = 0

    def rotate(self):
        self.shape = [list(row) for row in zip(*self.shape[::-1])]

def check_collision(board, piece):
    for y, row in enumerate(piece.shape):
        for x, value in enumerate(row):
            if value:
                if (x + piece.x < 0 or x + piece.x >= COLS or
                        y + piece.y >= ROWS or
                        (y + piece.y >= 0 and board[y + piece.y][x + piece.x])):
                    return True
    return False

def add_piece_to_board(board, piece):
    for y, row in enumerate(piece.shape):
        for x, value in enumerate(row):
            if value:
                board[y + piece.y][x + piece.x] = piece.color

def clear_rows(board):
    full_rows = 0
    for i, row in enumerate(board):
        if all(row):
            full_rows += 1
            del board[i]
            board.insert(0, [0] * COLS)
    return full_rows

def draw_text(screen, text, color, pos):
    font = pygame.font.Font(None, 36)
    text_surface = font.render(text, True, color)
    screen.blit(text_surface, pos)


def draw_board(screen, board):
    for y, row in enumerate(board):
        for x, value in enumerate(row):
            if value:
                pygame.draw.rect(screen, value, (x * BLOCK_SIZE, y * BLOCK_SIZE + 40, BLOCK_SIZE, BLOCK_SIZE))

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT + 40))  # Увеличиваем высоту окна
    clock = pygame.time.Clock()

    board = [[0] * COLS for _ in range(ROWS)]
    current_piece = Piece()
    drop_time = 0
    score = 0
    level = 1
    speed = 500

    while True:
        screen.fill(BLACK)

        # Обработка событий
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    current_piece.x -= 1
                    if check_collision(board, current_piece):
                        current_piece.x += 1
                elif event.key == pygame.K_RIGHT:
                    current_piece.x += 1
                    if check_collision(board, current_piece):
                        current_piece.x -= 1
                elif event.key == pygame.K_DOWN:
                    current_piece.y += 1
                    if check_collision(board, current_piece):
                        current_piece.y -= 1
                elif event.key == pygame.K_UP:
                    current_piece.rotate()
                    if check_collision(board, current_piece):
                        current_piece.rotate()

        drop_time += clock.get_rawtime()
        if drop_time > speed:
            current_piece.y += 1
            if check_collision(board, current_piece):
                current_piece.y -= 1
                add_piece_to_board(board, current_piece)

                if current_piece.y == 0:
                    print("Игра окончена!")
                    pygame.quit()
                    return
                
                added_rows = clear_rows(board)
                score += added_rows * 100  # Очки за заполненные строки
                current_piece = Piece()
                
                if check_collision(board, current_piece):
                    print("Игра окончена!")
                    pygame.quit()
                    return

                if score >= level * 1000:
                    level += 1
                    speed = max(100, speed - 50)

            drop_time = 0

        draw_board(screen, board)  # Отрисовка доски
        draw_text(screen, f"Очки: {score}", WHITE, (10, 10))  # Изменение позиции текста
        draw_text(screen, f"Уровень: {level}", WHITE, (10, 50))  # Изменение позиции текста

        for y, row in enumerate(current_piece.shape):
            for x, value in enumerate(row):
                if value:
                    pygame.draw.rect(screen, current_piece.color, ((current_piece.x + x) * BLOCK_SIZE, (current_piece.y + y) * BLOCK_SIZE + 40, BLOCK_SIZE, BLOCK_SIZE))

        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()

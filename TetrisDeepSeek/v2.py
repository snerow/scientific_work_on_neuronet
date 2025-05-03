import pygame
import random
import os
import json
from pygame import mixer

# Инициализация pygame и микшера для звуков
pygame.init()
mixer.init()

# Пути к файлам
if not os.path.exists('tetris_data'):
    os.makedirs('tetris_data')
HIGH_SCORE_FILE = 'tetris_data/high_scores.json'

# Цвета
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
DARK_GRAY = (50, 50, 50)
BLUE = (0, 120, 215)
COLORS = [
    (0, 255, 255),  # I - голубой
    (0, 0, 255),    # J - синий
    (255, 165, 0),  # L - оранжевый
    (255, 255, 0),  # O - желтый
    (0, 255, 0),    # S - зеленый
    (128, 0, 128),  # T - фиолетовый
    (255, 0, 0)     # Z - красный
]

# Настройки игры
BLOCK_SIZE = 30
GRID_WIDTH = 10
GRID_HEIGHT = 20
GAME_AREA_LEFT = 100
GAME_AREA_TOP = 50
PREVIEW_SIZE = 5  # Размер области предпросмотра в блоках

# Фигуры тетриса с центрами вращения
SHAPES = [
    {"shape": [[1, 1, 1, 1]], "center": (1.5, 0.5)},  # I
    {"shape": [[1, 0, 0], [1, 1, 1]], "center": (1, 1)},  # J
    {"shape": [[0, 0, 1], [1, 1, 1]], "center": (1, 1)},  # L
    {"shape": [[1, 1], [1, 1]], "center": (0.5, 0.5)},  # O
    {"shape": [[0, 1, 1], [1, 1, 0]], "center": (1, 1)},  # S
    {"shape": [[0, 1, 0], [1, 1, 1]], "center": (1, 1)},  # T
    {"shape": [[1, 1, 0], [0, 1, 1]], "center": (1, 1)}   # Z
]

# Настройка экрана
screen_width = GAME_AREA_LEFT + GRID_WIDTH * BLOCK_SIZE + 300
screen_height = GAME_AREA_TOP + GRID_HEIGHT * BLOCK_SIZE + 50
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Тетрис - Улучшенная версия")

# Загрузка звуков
try:
    rotate_sound = mixer.Sound('tetris_data/rotate.wav')
    clear_sound = mixer.Sound('tetris_data/clear.wav')
    fall_sound = mixer.Sound('tetris_data/fall.wav')
    gameover_sound = mixer.Sound('tetris_data/gameover.wav')
except:
    # Создаем пустые звуки, если файлы не найдены
    class DummySound:
        def play(self): pass
    rotate_sound = clear_sound = fall_sound = gameover_sound = DummySound()

clock = pygame.time.Clock()
FPS = 60

# Шрифты
try:
    font = pygame.font.Font('tetris_data/font.ttf', 24)
    big_font = pygame.font.Font('tetris_data/font.ttf', 40)
    title_font = pygame.font.Font('tetris_data/font.ttf', 60)
except:
    font = pygame.font.SysFont('Arial', 24)
    big_font = pygame.font.SysFont('Arial', 40)
    title_font = pygame.font.SysFont('Arial', 60)

class Particle:
    """Класс для частиц анимации"""
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.size = random.randint(2, 5)
        self.vx = random.uniform(-2, 2)
        self.vy = random.uniform(-3, -1)
        self.lifetime = random.uniform(0.5, 1.5)
        self.age = 0
    
    def update(self, dt):
        self.x += self.vx * dt * 60
        self.y += self.vy * dt * 60
        self.vy += 0.1 * dt * 60
        self.age += dt
        return self.age < self.lifetime
    
    def draw(self, surface):
        alpha = 255 * (1 - self.age / self.lifetime)
        color = (*self.color[:3], int(alpha))
        pos = (int(self.x), int(self.y))
        pygame.draw.circle(surface, color, pos, int(self.size))

def load_high_scores():
    """Загружает рекорды из файла"""
    try:
        with open(HIGH_SCORE_FILE, 'r') as f:
            return json.load(f)
    except:
        return {"scores": [], "levels": []}

def save_high_scores(scores):
    """Сохраняет рекорды в файл"""
    with open(HIGH_SCORE_FILE, 'w') as f:
        json.dump(scores, f)

class Game:
    def __init__(self):
        self.reset_game()
        self.high_scores = load_high_scores()
        self.particles = []
        self.state = "menu"  # menu, game, gameover
        self.ghost_piece_alpha = 80
        self.background_offset = 0
        self.background_speed = 10
        
        # Создаем фоновую текстуру
        self.background = pygame.Surface((screen_width, screen_height))
        for y in range(0, screen_height, 20):
            for x in range(0, screen_width, 20):
                if (x + y) % 40 == 0:
                    pygame.draw.rect(self.background, DARK_GRAY, (x, y, 20, 20))
    
    def reset_game(self):
        """Сбрасывает игровое состояние для новой игры"""
        self.grid = [[0 for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        self.current_piece = None
        self.next_piece = None
        self.current_x = GRID_WIDTH // 2
        self.current_y = 0
        self.score = 0
        self.level = 1
        self.lines_cleared = 0
        self.game_over = False
        self.pause = False
        self.fall_time = 0
        self.fall_speed = self.calculate_fall_speed()
        self.hold_piece = None
        self.can_hold = True
        self.combo = 0
        
        # Создаем первую фигуру
        self.new_piece()
    
    def calculate_fall_speed(self):
        """Вычисляет скорость падения на основе уровня"""
        return max(0.05, 0.5 - (self.level - 1) * 0.05)
    
    def new_piece(self):
        """Создает новую случайную фигуру"""
        if self.next_piece is None:
            # Если следующей фигуры нет, создаем две случайные
            piece_idx = random.randint(0, len(SHAPES) - 1)
            next_piece_idx = random.randint(0, len(SHAPES) - 1)
            self.current_piece = {
                "index": piece_idx,
                "shape": SHAPES[piece_idx]["shape"],
                "color": COLORS[piece_idx],
                "center": SHAPES[piece_idx]["center"]
            }
            self.next_piece = {
                "index": next_piece_idx,
                "shape": SHAPES[next_piece_idx]["shape"],
                "color": COLORS[next_piece_idx],
                "center": SHAPES[next_piece_idx]["center"]
            }
        else:
            # Иначе используем подготовленную следующую фигуру
            self.current_piece = self.next_piece
            next_piece_idx = random.randint(0, len(SHAPES) - 1)
            self.next_piece = {
                "index": next_piece_idx,
                "shape": SHAPES[next_piece_idx]["shape"],
                "color": COLORS[next_piece_idx],
                "center": SHAPES[next_piece_idx]["center"]
            }
        
        self.current_x = GRID_WIDTH // 2 - len(self.current_piece["shape"][0]) // 2
        self.current_y = 0
        self.can_hold = True
        
        # Проверка на проигрыш (если новая фигура не может быть размещена)
        if self.check_collision():
            self.game_over = True
            gameover_sound.play()
            self.add_high_score()
            self.state = "gameover"
    
    def hold_current_piece(self):
        """Меняет текущую фигуру с отложенной"""
        if not self.can_hold:
            return
        
        if self.hold_piece is None:
            self.hold_piece = self.current_piece
            self.new_piece()
        else:
            self.current_piece, self.hold_piece = self.hold_piece, self.current_piece
            self.current_x = GRID_WIDTH // 2 - len(self.current_piece["shape"][0]) // 2
            self.current_y = 0
        
        self.can_hold = False
    
    def check_collision(self, x=None, y=None, shape=None):
        """Проверяет столкновение фигуры с границами или другими блоками"""
        if x is None:
            x = self.current_x
        if y is None:
            y = self.current_y
        if shape is None:
            shape = self.current_piece["shape"]
        
        for py, row in enumerate(shape):
            for px, cell in enumerate(row):
                if cell:
                    # Проверка границ
                    if (x + px < 0 or x + px >= GRID_WIDTH or 
                        y + py >= GRID_HEIGHT):
                        return True
                    # Проверка на другие блоки (кроме верхней границы)
                    if y + py >= 0 and self.grid[y + py][x + px]:
                        return True
        return False
    
    def rotate_piece(self):
        """Поворачивает текущую фигуру на 90 градусов"""
        # Для квадрата (O) вращение не нужно
        if self.current_piece["index"] == 3:
            return
        
        # Получаем текущую фигуру
        piece = self.current_piece
        old_shape = piece["shape"]
        
        # Создаем повернутую фигуру
        rotated = []
        for x in range(len(old_shape[0])):
            new_row = []
            for y in range(len(old_shape)-1, -1, -1):
                new_row.append(old_shape[y][x])
            rotated.append(new_row)
        
        # Проверяем столкновения после поворота
        old_x, old_y = self.current_x, self.current_y
        center_x = self.current_x + piece["center"][0]
        center_y = self.current_y + piece["center"][1]
        
        # Пытаемся сделать wall kick (сдвиг при вращении у стены)
        for dx, dy in [(0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)]:
            self.current_x = int(center_x - piece["center"][1] + dx)
            self.current_y = int(center_y - piece["center"][0] + dy)
            piece["shape"] = rotated
            
            if not self.check_collision():
                rotate_sound.play()
                return
        
        # Если ни один вариант не подошел - возвращаем старую фигуру
        piece["shape"] = old_shape
        self.current_x, self.current_y = old_x, old_y
    
    def draw_grid(self):
        """Рисует сетку игрового поля"""
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                rect = pygame.Rect(
                    GAME_AREA_LEFT + x * BLOCK_SIZE, 
                    GAME_AREA_TOP + y * BLOCK_SIZE, 
                    BLOCK_SIZE, BLOCK_SIZE
                )
                pygame.draw.rect(screen, (30, 30, 30), rect)
                pygame.draw.rect(screen, (20, 20, 20), rect, 1)
    
    def draw_ghost_piece(self):
        """Рисует прозрачную фигуру в месте, куда упадет текущая фигура"""
        if self.current_piece is None or self.game_over:
            return
        
        ghost_y = self.current_y
        while not self.check_collision(y=ghost_y + 1):
            ghost_y += 1
        
        shape = self.current_piece["shape"]
        color = (*self.current_piece["color"], self.ghost_piece_alpha)
        
        for y, row in enumerate(shape):
            for x, cell in enumerate(row):
                if cell:
                    rect = pygame.Rect(
                        GAME_AREA_LEFT + (self.current_x + x) * BLOCK_SIZE, 
                        GAME_AREA_TOP + (ghost_y + y) * BLOCK_SIZE, 
                        BLOCK_SIZE, BLOCK_SIZE
                    )
                    s = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA)
                    s.fill(color)
                    screen.blit(s, rect)
                    pygame.draw.rect(screen, (*color[:3], 150), rect, 1)
    
    def draw_blocks(self):
        """Рисует все блоки на игровом поле"""
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                if self.grid[y][x]:
                    rect = pygame.Rect(
                        GAME_AREA_LEFT + x * BLOCK_SIZE, 
                        GAME_AREA_TOP + y * BLOCK_SIZE, 
                        BLOCK_SIZE, BLOCK_SIZE
                    )
                    
                    # Рисуем блок с градиентом
                    color = self.grid[y][x]
                    darker = tuple(max(0, c - 40) for c in color)
                    pygame.draw.rect(screen, darker, rect)
                    
                    # Добавляем светлую полосу сверху для 3D эффекта
                    highlight = pygame.Rect(
                        rect.left + 2, rect.top + 2, 
                        rect.width - 4, rect.height // 3
                    )
                    lighter = tuple(min(255, c + 40) for c in color)
                    pygame.draw.rect(screen, lighter, highlight)
                    
                    # Обводка
                    pygame.draw.rect(screen, WHITE, rect, 1)
    
    def draw_current_piece(self):
        """Рисует текущую падающую фигуру"""
        if self.current_piece is None or self.game_over:
            return
        
        shape = self.current_piece["shape"]
        color = self.current_piece["color"]
        
        for y, row in enumerate(shape):
            for x, cell in enumerate(row):
                if cell and self.current_y + y >= 0:
                    rect = pygame.Rect(
                        GAME_AREA_LEFT + (self.current_x + x) * BLOCK_SIZE, 
                        GAME_AREA_TOP + (self.current_y + y) * BLOCK_SIZE, 
                        BLOCK_SIZE, BLOCK_SIZE
                    )
                    
                    # Рисуем блок с градиентом
                    darker = tuple(max(0, c - 40) for c in color)
                    pygame.draw.rect(screen, darker, rect)
                    
                    # Добавляем светлую полосу сверху для 3D эффекта
                    highlight = pygame.Rect(
                        rect.left + 2, rect.top + 2, 
                        rect.width - 4, rect.height // 3
                    )
                    lighter = tuple(min(255, c + 40) for c in color)
                    pygame.draw.rect(screen, lighter, highlight)
                    
                    # Обводка
                    pygame.draw.rect(screen, WHITE, rect, 1)
    
    def draw_next_piece(self):
        """Рисует следующую фигуру"""
        if self.next_piece is None:
            return
        
        # Координаты области для отображения следующей фигуры
        next_left = GAME_AREA_LEFT + GRID_WIDTH * BLOCK_SIZE + 50
        next_top = GAME_AREA_TOP + 100
        
        # Рисуем заголовок
        text = font.render("Следующая:", True, WHITE)
        screen.blit(text, (next_left, next_top - 40))
        
        # Рисуем рамку
        pygame.draw.rect(
            screen, BLUE, 
            (next_left - 10, next_top - 10, 
             PREVIEW_SIZE * BLOCK_SIZE + 20, PREVIEW_SIZE * BLOCK_SIZE + 20), 
            2
        )
        
        shape = self.next_piece["shape"]
        color = self.next_piece["color"]
        
        # Центрируем фигуру в области предпросмотра
        offset_x = (PREVIEW_SIZE - len(shape[0])) // 2
        offset_y = (PREVIEW_SIZE - len(shape)) // 2
        
        # Рисуем фигуру
        for y, row in enumerate(shape):
            for x, cell in enumerate(row):
                if cell:
                    rect = pygame.Rect(
                        next_left + (offset_x + x) * BLOCK_SIZE, 
                        next_top + (offset_y + y) * BLOCK_SIZE, 
                        BLOCK_SIZE, BLOCK_SIZE
                    )
                    pygame.draw.rect(screen, color, rect)
                    pygame.draw.rect(screen, WHITE, rect, 1)
    
    def draw_hold_piece(self):
        """Рисует отложенную фигуру"""
        if self.hold_piece is None:
            return
        
        # Координаты области для отложенной фигуры
        hold_left = GAME_AREA_LEFT - 150
        hold_top = GAME_AREA_TOP + 100
        
        # Рисуем заголовок
        text = font.render("Отложить:", True, WHITE)
        screen.blit(text, (hold_left, hold_top - 40))
        
        # Рисуем рамку
        pygame.draw.rect(
            screen, BLUE, 
            (hold_left - 10, hold_top - 10, 
             PREVIEW_SIZE * BLOCK_SIZE + 20, PREVIEW_SIZE * BLOCK_SIZE + 20), 
            2
        )
        
        shape = self.hold_piece["shape"]
        color = self.hold_piece["color"]
        
        # Центрируем фигуру в области предпросмотра
        offset_x = (PREVIEW_SIZE - len(shape[0])) // 2
        offset_y = (PREVIEW_SIZE - len(shape)) // 2
        
        # Рисуем фигуру
        for y, row in enumerate(shape):
            for x, cell in enumerate(row):
                if cell:
                    rect = pygame.Rect(
                        hold_left + (offset_x + x) * BLOCK_SIZE, 
                        hold_top + (offset_y + y) * BLOCK_SIZE, 
                        BLOCK_SIZE, BLOCK_SIZE
                    )
                    pygame.draw.rect(screen, color, rect)
                    pygame.draw.rect(screen, WHITE, rect, 1)
    
    def draw_score(self):
        """Отображает игровую статистику"""
        info_left = GAME_AREA_LEFT + GRID_WIDTH * BLOCK_SIZE + 50
        info_top = GAME_AREA_TOP + 300
        
        # Счет
        score_text = font.render(f"Счет: {self.score}", True, WHITE)
        screen.blit(score_text, (info_left, info_top))
        
        # Уровень
        level_text = font.render(f"Уровень: {self.level}", True, WHITE)
        screen.blit(level_text, (info_left, info_top + 40))
        
        # Линии
        lines_text = font.render(f"Линии: {self.lines_cleared}", True, WHITE)
        screen.blit(lines_text, (info_left, info_top + 80))
        
        # Комбо
        if self.combo > 0:
            combo_text = font.render(f"Комбо: x{self.combo}", True, (255, 215, 0))
            screen.blit(combo_text, (info_left, info_top + 120))
    
    def draw_game_over(self):
        """Отображает сообщение о конце игры"""
        if not self.game_over:
            return
        
        # Затемняем экран
        s = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        s.fill((0, 0, 0, 180))
        screen.blit(s, (0, 0))
        
        # Заголовок
        text = title_font.render("ИГРА ОКОНЧЕНА", True, (255, 50, 50))
        text_rect = text.get_rect(center=(screen_width//2, screen_height//2 - 100))
        screen.blit(text, text_rect)
        
        # Счет
        score_text = big_font.render(f"Ваш счет: {self.score}", True, WHITE)
        score_rect = score_text.get_rect(center=(screen_width//2, screen_height//2 - 20))
        screen.blit(score_text, score_rect)
        
        # Рекорд
        if self.high_scores["scores"]:
            high_score = max(self.high_scores["scores"])
            if self.score >= high_score:
                record_text = big_font.render("НОВЫЙ РЕКОРД!", True, (255, 215, 0))
                record_rect = record_text.get_rect(center=(screen_width//2, screen_height//2 + 40))
                screen.blit(record_text, record_rect)
        
        # Инструкции
        restart_text = font.render("Нажмите R для рестарта", True, WHITE)
        restart_rect = restart_text.get_rect(center=(screen_width//2, screen_height//2 + 120))
        screen.blit(restart_text, restart_rect)
        
        menu_text = font.render("Нажмите M для выхода в меню", True, WHITE)
        menu_rect = menu_text.get_rect(center=(screen_width//2, screen_height//2 + 160))
        screen.blit(menu_text, menu_rect)
    
    def draw_pause(self):
        """Отображает сообщение о паузе"""
        if not self.pause:
            return
        
        # Затемняем экран
        s = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        s.fill((0, 0, 0, 150))
        screen.blit(s, (0, 0))
        
        text = title_font.render("ПАУЗА", True, WHITE)
        text_rect = text.get_rect(center=(screen_width//2, screen_height//2 - 50))
        screen.blit(text, text_rect)
        
        continue_text = font.render("Нажмите P для продолжения", True, WHITE)
        continue_rect = continue_text.get_rect(center=(screen_width//2, screen_height//2 + 20))
        screen.blit(continue_text, continue_rect)
    
    def draw_menu(self):
        """Рисует главное меню"""
        # Фон
        screen.fill(BLACK)
        self.background_offset += self.background_speed * clock.get_time() / 1000
        if self.background_offset >= 20:
            self.background_offset = 0
        
        # Анимированный фон
        for y in range(-20, screen_height, 20):
            for x in range(-20, screen_width, 20):
                pos_x = x + self.background_offset
                pos_y = y + self.background_offset
                if (pos_x + pos_y) % 40 == 0:
                    pygame.draw.rect(screen, DARK_GRAY, (pos_x, pos_y, 20, 20))
        
        # Заголовок
        title = title_font.render("ТЕТРИС", True, BLUE)
        title_shadow = title_font.render("ТЕТРИС", True, (0, 60, 120))
        title_rect = title.get_rect(center=(screen_width//2, screen_height//4))
        screen.blit(title_shadow, (title_rect.x + 5, title_rect.y + 5))
        screen.blit(title, title_rect)
        
        # Кнопки
        button_y = screen_height // 2
        button_height = 60
        button_width = 300
        
        # Кнопка "Новая игра"
        pygame.draw.rect(
            screen, BLUE, 
            (screen_width//2 - button_width//2, button_y, button_width, button_height),
            border_radius=10
        )
        pygame.draw.rect(
            screen, WHITE, 
            (screen_width//2 - button_width//2, button_y, button_width, button_height),
            2, border_radius=10
        )
        start_text = big_font.render("Новая игра", True, WHITE)
        start_rect = start_text.get_rect(center=(screen_width//2, button_y + button_height//2))
        screen.blit(start_text, start_rect)
        
        # Кнопка "Рекорды"
        pygame.draw.rect(
            screen, BLUE, 
            (screen_width//2 - button_width//2, button_y + button_height + 20, button_width, button_height),
            border_radius=10
        )
        pygame.draw.rect(
            screen, WHITE, 
            (screen_width//2 - button_width//2, button_y + button_height + 20, button_width, button_height),
            2, border_radius=10
        )
        scores_text = big_font.render("Рекорды", True, WHITE)
        scores_rect = scores_text.get_rect(center=(screen_width//2, button_y + button_height + 20 + button_height//2))
        screen.blit(scores_text, scores_rect)
        
        # Управление
        controls_y = button_y + 2 * (button_height + 20) + 40
        controls_text = [
            "Управление:",
            "← → - Движение влево/вправо",
            "↑ - Поворот",
            "↓ - Ускоренное падение",
            "Пробел - Мгновенное падение",
            "C - Отложить фигуру",
            "P - Пауза"
        ]
        
        for i, line in enumerate(controls_text):
            text = font.render(line, True, WHITE)
            screen.blit(text, (screen_width//2 - button_width//2, controls_y + i * 30))
    
    def draw_high_scores(self):
        """Отображает экран с рекордами"""
        # Фон
        screen.fill(BLACK)
        
        # Заголовок
        title = title_font.render("РЕКОРДЫ", True, BLUE)
        title_rect = title.get_rect(center=(screen_width//2, 100))
        screen.blit(title, title_rect)
        
        # Лучшие счета
        if not self.high_scores["scores"]:
            no_scores = font.render("Пока нет рекордов!", True, WHITE)
            no_rect = no_scores.get_rect(center=(screen_width//2, screen_height//2))
            screen.blit(no_scores, no_rect)
        else:
            # Топ-5 результатов
            top_scores = sorted(self.high_scores["scores"], reverse=True)[:5]
            for i, score in enumerate(top_scores):
                score_text = big_font.render(f"{i+1}. {score}", True, WHITE)
                score_rect = score_text.get_rect(center=(screen_width//2, 200 + i * 60))
                screen.blit(score_text, score_rect)
        
        # Кнопка назад
        back_text = font.render("Нажмите M для возврата в меню", True, WHITE)
        back_rect = back_text.get_rect(center=(screen_width//2, screen_height - 50))
        screen.blit(back_text, back_rect)
    
    def lock_piece(self):
        """Фиксирует текущую фигуру на игровом поле"""
        shape = self.current_piece["shape"]
        color = self.current_piece["color"]
        
        for y, row in enumerate(shape):
            for x, cell in enumerate(row):
                if cell and self.current_y + y >= 0:
                    self.grid[self.current_y + y][self.current_x + x] = color
        
        # Проверяем заполненные линии
        lines_cleared = 0
        for y in range(GRID_HEIGHT):
            if all(self.grid[y]):
                lines_cleared += 1
                # Удаляем линию и сдвигаем все выше
                for y2 in range(y, 0, -1):
                    self.grid[y2] = self.grid[y2-1][:]
                self.grid[0] = [0] * GRID_WIDTH
                
                # Создаем частицы для анимации
                for x in range(GRID_WIDTH):
                    for _ in range(5):
                        px = GAME_AREA_LEFT + x * BLOCK_SIZE + BLOCK_SIZE // 2
                        py = GAME_AREA_TOP + y * BLOCK_SIZE + BLOCK_SIZE // 2
                        self.particles.append(Particle(px, py, color))
        
        if lines_cleared > 0:
            clear_sound.play()
            self.lines_cleared += lines_cleared
            
            # Начисляем очки за очищенные линии
            if lines_cleared == 1:
                self.score += 100 * self.level
                self.combo += 1
            elif lines_cleared == 2:
                self.score += 300 * self.level
                self.combo += 2
            elif lines_cleared == 3:
                self.score += 500 * self.level
                self.combo += 3
            elif lines_cleared == 4:
                self.score += 800 * self.level
                self.combo += 4
            
            # Бонус за комбо
            if self.combo > 1:
                self.score += 50 * self.level * (self.combo - 1)
        else:
            self.combo = 0
        
        # Проверяем уровень
        self.level = 1 + self.lines_cleared // 10
        self.fall_speed = self.calculate_fall_speed()
    
    def add_high_score(self):
        """Добавляет текущий счет в таблицу рекордов"""
        self.high_scores["scores"].append(self.score)
        self.high_scores["levels"].append(self.level)
        save_high_scores(self.high_scores)
    
    def update_particles(self, dt):
        """Обновляет частицы анимации"""
        self.particles = [p for p in self.particles if p.update(dt)]
    
    def draw_particles(self):
        """Рисует частицы анимации"""
        for particle in self.particles:
            particle.draw(screen)
    
    def run(self):
        """Основной игровой цикл"""
        running = True
        
        while running:
            dt = clock.tick(FPS) / 1000.0  # Delta time в секундах
            
            # Обработка событий
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                if event.type == pygame.KEYDOWN:
                    if self.state == "menu":
                        if event.key == pygame.K_RETURN:
                            self.state = "game"
                            self.reset_game()
                        elif event.key == pygame.K_s:
                            self.state = "highscores"
                    
                    elif self.state == "highscores":
                        if event.key == pygame.K_m:
                            self.state = "menu"
                    
                    elif self.state == "game":
                        if not self.game_over and not self.pause:
                            if event.key == pygame.K_LEFT:
                                self.current_x -= 1
                                if self.check_collision():
                                    self.current_x += 1
                            elif event.key == pygame.K_RIGHT:
                                self.current_x += 1
                                if self.check_collision():
                                    self.current_x -= 1
                            elif event.key == pygame.K_DOWN:
                                self.current_y += 1
                                if self.check_collision():
                                    self.current_y -= 1
                                    self.lock_piece()
                                    fall_sound.play()
                                    if not self.new_piece():
                                        self.game_over = True
                                        self.add_high_score()
                                        self.state = "gameover"
                            elif event.key == pygame.K_UP:
                                self.rotate_piece()
                            elif event.key == pygame.K_SPACE:
                                # Мгновенное падение
                                while not self.check_collision(y=self.current_y + 1):
                                    self.current_y += 1
                                self.current_y -= 1
                                self.lock_piece()
                                fall_sound.play()
                                if not self.new_piece():
                                    self.game_over = True
                                    self.add_high_score()
                                    self.state = "gameover"
                            elif event.key == pygame.K_c:
                                self.hold_current_piece()
                            elif event.key == pygame.K_p:
                                self.pause = True
                        
                        elif self.pause:
                            if event.key == pygame.K_p:
                                self.pause = False
                    
                    elif self.state == "gameover":
                        if event.key == pygame.K_r:
                            self.state = "game"
                            self.reset_game()
                        elif event.key == pygame.K_m:
                            self.state = "menu"
            
            # Обновление игры
            if self.state == "game" and not self.game_over and not self.pause:
                # Автоматическое падение фигуры
                self.fall_time += dt
                
                if self.fall_time >= self.fall_speed:
                    self.fall_time = 0
                    self.current_y += 1
                    if self.check_collision():
                        self.current_y -= 1
                        self.lock_piece()
                        fall_sound.play()
                        if not self.new_piece():
                            self.game_over = True
                            self.add_high_score()
                            self.state = "gameover"
                
                # Обновление частиц
                self.update_particles(dt)
            
            # Отрисовка
            if self.state == "menu":
                self.draw_menu()
            elif self.state == "highscores":
                self.draw_high_scores()
            elif self.state == "game":
                # Фон
                screen.fill(BLACK)
                
                # Игровое поле
                self.draw_grid()
                self.draw_ghost_piece()
                self.draw_blocks()
                self.draw_current_piece()
                self.draw_particles()
                
                # Интерфейс
                self.draw_next_piece()
                self.draw_hold_piece()
                self.draw_score()
                
                # Сообщения
                self.draw_game_over()
                self.draw_pause()
            elif self.state == "gameover":
                # Фон
                screen.fill(BLACK)
                
                # Игровое поле
                self.draw_grid()
                self.draw_blocks()
                self.draw_particles()
                
                # Интерфейс
                self.draw_next_p
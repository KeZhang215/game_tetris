import pygame
import random

# 初始化pygame
pygame.init()

# 游戏配置
SCREEN_WIDTH = 300
SCREEN_HEIGHT = 600
BLOCK_SIZE = 30
GRID_WIDTH = SCREEN_WIDTH // BLOCK_SIZE
GRID_HEIGHT = SCREEN_HEIGHT // BLOCK_SIZE

# 颜色定义
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
COLORS = [
    (0, 255, 255),    # 青色 - I
    (255, 255, 0),    # 黄色 - O
    (128, 0, 128),    # 紫色 - T
    (0, 255, 0),      # 绿色 - S
    (255, 0, 0),      # 红色 - Z
    (0, 0, 255),      # 蓝色 - J
    (255, 165, 0),    # 橙色 - L
]

# 方块形状定义
SHAPES = [
    [[1, 1, 1, 1]],  # I
    [[1, 1], [1, 1]],  # O
    [[0, 1, 0], [1, 1, 1]],  # T
    [[0, 1, 1], [1, 1, 0]],  # S
    [[1, 1, 0], [0, 1, 1]],  # Z
    [[1, 0, 0], [1, 1, 1]],  # J
    [[0, 0, 1], [1, 1, 1]],  # L
]


class Tetromino:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.shape_id = random.randint(0, len(SHAPES) - 1)
        self.shape = SHAPES[self.shape_id]
        self.color = COLORS[self.shape_id]
        self.rotation = 0
        # 30%概率显示装饰文字
        rand = random.random()
        if rand < 0.3:
            self.decoration = random.choice(['qq', 'kk'])
        else:
            self.decoration = None

    def rotate(self):
        """旋转方块"""
        self.shape = [list(row) for row in zip(*self.shape[::-1])]


class TetrisGame:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("俄罗斯方块")
        self.clock = pygame.time.Clock()
        # 网格存储格式: {'color': color_tuple, 'decoration': 'qq'/'kk'/None}
        self.grid = [[None for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        self.current_piece = None
        self.game_over = False
        self.game_win = False
        self.paused = False
        self.score = 0
        self.fall_time = 0
        self.fall_speed = 500  # 毫秒
        # 长按移动相关
        self.move_time = 0
        self.move_delay = 100  # 长按移动间隔（毫秒）
        self.spawn_piece()

    def spawn_piece(self):
        """生成新方块"""
        self.current_piece = Tetromino(GRID_WIDTH // 2 - 1, 0)
        # 检查新方块生成位置是否与已有方块冲突（只检查网格中已有的方块）
        for y, row in enumerate(self.current_piece.shape):
            for x, cell in enumerate(row):
                if cell:
                    grid_y = self.current_piece.y + y
                    grid_x = self.current_piece.x + x
                    if grid_y >= 0 and self.grid[grid_y][grid_x]:
                        self.game_over = True
                        return

    def check_collision(self, piece, offset_x, offset_y):
        """检查碰撞"""
        for y, row in enumerate(piece.shape):
            for x, cell in enumerate(row):
                if cell:
                    new_x = piece.x + x + offset_x
                    new_y = piece.y + y + offset_y
                    if (new_x < 0 or new_x >= GRID_WIDTH or
                        new_y >= GRID_HEIGHT or
                        (new_y >= 0 and self.grid[new_y][new_x] is not None)):
                        return True
        return False

    def lock_piece(self):
        """锁定方块到网格"""
        for y, row in enumerate(self.current_piece.shape):
            for x, cell in enumerate(row):
                if cell and self.current_piece.y + y >= 0:
                    self.grid[self.current_piece.y + y][self.current_piece.x + x] = {
                        'color': self.current_piece.color,
                        'decoration': self.current_piece.decoration
                    }
        self.clear_lines()
        self.spawn_piece()

    def clear_lines(self):
        """消除满行"""
        lines_cleared = 0
        y = GRID_HEIGHT - 1
        while y >= 0:
            if all(cell is not None for cell in self.grid[y]):
                del self.grid[y]
                self.grid.insert(0, [None for _ in range(GRID_WIDTH)])
                lines_cleared += 1
            else:
                y -= 1

        if lines_cleared > 0:
            self.score += lines_cleared * 10
            # 检查是否达到500分通关
            if self.score >= 500:
                self.game_win = True

    def move(self, dx, dy):
        """移动方块"""
        if not self.check_collision(self.current_piece, dx, dy):
            self.current_piece.x += dx
            self.current_piece.y += dy
            return True
        return False

    def rotate_piece(self):
        """旋转方块"""
        original_shape = [row[:] for row in self.current_piece.shape]
        self.current_piece.rotate()
        if self.check_collision(self.current_piece, 0, 0):
            self.current_piece.shape = original_shape

    def drop(self):
        """快速下落"""
        while self.move(0, 1):
            pass

    def get_drop_position(self):
        """计算方块的落点位置"""
        if not self.current_piece:
            return None

        drop_y = self.current_piece.y
        # 模拟下落，直到碰撞
        while not self.check_collision(self.current_piece, 0, drop_y - self.current_piece.y + 1):
            drop_y += 1

        return drop_y

    def draw_grid(self):
        """绘制网格"""
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                block_x = x * BLOCK_SIZE
                block_y = y * BLOCK_SIZE
                if self.grid[y][x]:
                    # 绘制方块颜色
                    pygame.draw.rect(self.screen, self.grid[y][x]['color'],
                                   (block_x, block_y, BLOCK_SIZE - 1, BLOCK_SIZE - 1))
                    # 如果有装饰文字，则绘制
                    if self.grid[y][x]['decoration']:
                        font = pygame.font.Font(None, 18)
                        text = font.render(self.grid[y][x]['decoration'], True, BLACK)
                        text_rect = text.get_rect(center=(block_x + BLOCK_SIZE // 2,
                                                          block_y + BLOCK_SIZE // 2))
                        self.screen.blit(text, text_rect)
                else:
                    pygame.draw.rect(self.screen, GRAY,
                                   (block_x, block_y, BLOCK_SIZE - 1, BLOCK_SIZE - 1), 1)

    def draw_ghost_piece(self):
        """绘制落点预览（半透明方块）"""
        if self.current_piece:
            drop_y = self.get_drop_position()
            if drop_y is not None and drop_y != self.current_piece.y:
                # 创建半透明表面
                ghost_surface = pygame.Surface((BLOCK_SIZE - 1, BLOCK_SIZE - 1))
                ghost_surface.set_alpha(80)  # 设置透明度（0-255）
                ghost_surface.fill(self.current_piece.color)

                for y, row in enumerate(self.current_piece.shape):
                    for x, cell in enumerate(row):
                        if cell:
                            block_x = (self.current_piece.x + x) * BLOCK_SIZE
                            block_y = (drop_y + y) * BLOCK_SIZE
                            self.screen.blit(ghost_surface, (block_x, block_y))

    def draw_piece(self):
        """绘制当前方块"""
        if self.current_piece:
            for y, row in enumerate(self.current_piece.shape):
                for x, cell in enumerate(row):
                    if cell:
                        block_x = (self.current_piece.x + x) * BLOCK_SIZE
                        block_y = (self.current_piece.y + y) * BLOCK_SIZE
                        pygame.draw.rect(self.screen, self.current_piece.color,
                                       (block_x, block_y, BLOCK_SIZE - 1, BLOCK_SIZE - 1))

                        # 如果有装饰文字，则绘制
                        if self.current_piece.decoration:
                            font = pygame.font.Font(None, 18)
                            text = font.render(self.current_piece.decoration, True, BLACK)
                            text_rect = text.get_rect(center=(block_x + BLOCK_SIZE // 2,
                                                              block_y + BLOCK_SIZE // 2))
                            self.screen.blit(text, text_rect)

    def draw_score(self):
        """绘制分数"""
        font = pygame.font.Font(None, 36)
        text = font.render(f"Score: {self.score}", True, WHITE)
        self.screen.blit(text, (10, 10))

    def draw_game_over(self):
        """绘制游戏结束画面"""
        font = pygame.font.Font(None, 48)
        text = font.render("GAME OVER", True, WHITE)
        text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self.screen.blit(text, text_rect)

        font_small = pygame.font.Font(None, 24)
        restart_text = font_small.render("Press R to Restart", True, WHITE)
        restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
        self.screen.blit(restart_text, restart_rect)

    def draw_win(self):
        """绘制游戏胜利画面"""
        font = pygame.font.Font(None, 48)
        text = font.render("YOU WIN!", True, WHITE)
        text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self.screen.blit(text, text_rect)

        font_small = pygame.font.Font(None, 24)
        restart_text = font_small.render("Press R to Restart", True, WHITE)
        restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
        self.screen.blit(restart_text, restart_rect)

    def draw_paused(self):
        """绘制暂停画面"""
        font = pygame.font.Font(None, 48)
        text = font.render("PAUSED", True, WHITE)
        text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self.screen.blit(text, text_rect)

        font_small = pygame.font.Font(None, 24)
        continue_text = font_small.render("Press SPACE to Continue", True, WHITE)
        continue_rect = continue_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
        self.screen.blit(continue_text, continue_rect)

    def reset_game(self):
        """重置游戏"""
        self.grid = [[None for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        self.current_piece = None
        self.game_over = False
        self.game_win = False
        self.paused = False
        self.score = 0
        self.fall_time = 0
        self.move_time = 0
        self.spawn_piece()

    def run(self):
        """主游戏循环"""
        running = True
        while running:
            delta_time = self.clock.get_time()

            # 只在非暂停状态下更新计时器
            if not self.paused:
                self.fall_time += delta_time
                self.move_time += delta_time

            # 事件处理
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                if event.type == pygame.KEYDOWN:
                    if self.game_over or self.game_win:
                        if event.key == pygame.K_r:
                            self.reset_game()
                    elif event.key == pygame.K_SPACE:
                        # 切换暂停状态
                        self.paused = not self.paused
                    elif not self.paused:
                        if event.key == pygame.K_LEFT:
                            self.move(-1, 0)
                            self.move_time = 0  # 重置移动计时器
                        elif event.key == pygame.K_RIGHT:
                            self.move(1, 0)
                            self.move_time = 0  # 重置移动计时器
                        elif event.key == pygame.K_DOWN:
                            self.move(0, 1)
                            self.move_time = 0  # 重置移动计时器
                        elif event.key == pygame.K_UP:
                            self.rotate_piece()

            # 长按持续移动（只在非暂停状态下）
            if not self.game_over and not self.game_win and not self.paused and self.move_time >= self.move_delay:
                keys = pygame.key.get_pressed()
                if keys[pygame.K_LEFT]:
                    self.move(-1, 0)
                    self.move_time = 0
                elif keys[pygame.K_RIGHT]:
                    self.move(1, 0)
                    self.move_time = 0
                elif keys[pygame.K_DOWN]:
                    self.move(0, 1)
                    self.move_time = 0

            # 自动下落（只在非暂停状态下）
            if not self.game_over and not self.game_win and not self.paused and self.fall_time >= self.fall_speed:
                if not self.move(0, 1):
                    self.lock_piece()
                self.fall_time = 0

            # 绘制
            self.screen.fill(BLACK)
            self.draw_grid()
            self.draw_ghost_piece()  # 先绘制半透明的落点预览
            self.draw_piece()  # 再绘制当前方块
            self.draw_score()

            if self.game_over:
                self.draw_game_over()
            elif self.game_win:
                self.draw_win()
            elif self.paused:
                self.draw_paused()

            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()


if __name__ == "__main__":
    game = TetrisGame()
    game.run()

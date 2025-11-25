import pygame
import sys
import random
from enum import Enum

# Initialize Pygame
pygame.init()

# Constants
BOARD_SIZE = 15
CELL_SIZE = 40
MARGIN = 50
BOARD_WIDTH = CELL_SIZE * (BOARD_SIZE - 1)
WINDOW_SIZE = BOARD_WIDTH + 2 * MARGIN
INFO_HEIGHT = 100
BUTTON_HEIGHT = 60

# Colors
BG_COLOR = (222, 184, 135)  # Light brown background
LINE_COLOR = (0, 0, 0)  # Black grid lines
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
HIGHLIGHT_COLOR = (255, 0, 0)
BUTTON_COLOR = (100, 150, 200)
BUTTON_HOVER_COLOR = (120, 170, 220)
TEXT_COLOR = (50, 50, 50)

# Game States
class GameState(Enum):
    MENU = 1
    PLAYING = 2
    GAME_OVER = 3

# Game Modes
class GameMode(Enum):
    TWO_PLAYER = 1
    AI_EASY = 2
    AI_HARD = 3

# Player Colors
class Player(Enum):
    BLACK = 1
    WHITE = 2

    def opposite(self):
        return Player.WHITE if self == Player.BLACK else Player.BLACK


class Button:
    """Button class for UI elements"""
    def __init__(self, x, y, width, height, text, font_size=24):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = pygame.font.Font(None, font_size)
        self.hovered = False

    def draw(self, screen):
        color = BUTTON_HOVER_COLOR if self.hovered else BUTTON_COLOR
        pygame.draw.rect(screen, color, self.rect, border_radius=10)
        pygame.draw.rect(screen, BLACK, self.rect, 2, border_radius=10)

        text_surface = self.font.render(self.text, True, WHITE)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                return True
        return False


class Board:
    """Game board class"""
    def __init__(self):
        self.grid = [[None for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        self.last_move = None

    def is_valid_move(self, row, col):
        """Check if a move is valid"""
        return 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE and self.grid[row][col] is None

    def place_stone(self, row, col, player):
        """Place a stone on the board"""
        if self.is_valid_move(row, col):
            self.grid[row][col] = player
            self.last_move = (row, col)
            return True
        return False

    def check_win(self, row, col, player):
        """Check if placing a stone at (row, col) results in a win"""
        directions = [
            (0, 1),   # Horizontal
            (1, 0),   # Vertical
            (1, 1),   # Diagonal \
            (1, -1)   # Diagonal /
        ]

        for dr, dc in directions:
            count = 1

            # Check positive direction
            r, c = row + dr, col + dc
            while 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and self.grid[r][c] == player:
                count += 1
                r += dr
                c += dc

            # Check negative direction
            r, c = row - dr, col - dc
            while 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and self.grid[r][c] == player:
                count += 1
                r -= dr
                c -= dc

            if count == 5:
                return True

        return False

    def get_empty_cells(self):
        """Get all empty cells"""
        return [(r, c) for r in range(BOARD_SIZE) for c in range(BOARD_SIZE) if self.grid[r][c] is None]

    def get_cells_near_stones(self, distance=2):
        """Get empty cells near existing stones (for AI optimization)"""
        cells = set()
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if self.grid[r][c] is not None:
                    for dr in range(-distance, distance + 1):
                        for dc in range(-distance, distance + 1):
                            nr, nc = r + dr, c + dc
                            if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE and self.grid[nr][nc] is None:
                                cells.add((nr, nc))
        return list(cells) if cells else [(BOARD_SIZE // 2, BOARD_SIZE // 2)]

    def reset(self):
        """Reset the board"""
        self.grid = [[None for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        self.last_move = None

    def save_state(self):
        """Save current board state"""
        return [row[:] for row in self.grid], self.last_move

    def restore_state(self, state):
        """Restore board state"""
        self.grid, self.last_move = state


class AI:
    """AI player with different difficulty levels"""
    def __init__(self, difficulty, player):
        self.difficulty = difficulty
        self.player = player
        self.opponent = player.opposite()

    def get_move(self, board):
        """Get AI move based on difficulty"""
        if self.difficulty == GameMode.AI_EASY:
            return self._easy_move(board)
        else:
            return self._hard_move(board)

    def _easy_move(self, board):
        """Easy AI: Pattern-based strategy with some randomness"""
        # First move: center with slight randomness
        if board.last_move is None:
            center = BOARD_SIZE // 2
            offset = random.choice([-1, 0, 1])
            return (center + offset, center + offset)

        valid_moves = board.get_cells_near_stones(distance=2)

        # Check for winning move (always take it)
        for r, c in valid_moves:
            if board.is_valid_move(r, c):
                board.grid[r][c] = self.player
                if board.check_win(r, c, self.player):
                    board.grid[r][c] = None
                    return (r, c)
                board.grid[r][c] = None

        # Block opponent's winning move (always block)
        for r, c in valid_moves:
            if board.is_valid_move(r, c):
                board.grid[r][c] = self.opponent
                if board.check_win(r, c, self.opponent):
                    board.grid[r][c] = None
                    return (r, c)
                board.grid[r][c] = None

        # Score-based move selection with patterns
        move_scores = []
        for r, c in valid_moves:
            if board.is_valid_move(r, c):
                score = self._evaluate_move_simple(board, r, c)
                move_scores.append((score, r, c))

        if move_scores:
            # Sort by score
            move_scores.sort(reverse=True)

            # 70% chance to pick best move, 30% chance to pick from top 3
            if random.random() < 0.7 or len(move_scores) == 1:
                return (move_scores[0][1], move_scores[0][2])
            else:
                top_moves = move_scores[:min(3, len(move_scores))]
                chosen = random.choice(top_moves)
                return (chosen[1], chosen[2])

        return (BOARD_SIZE // 2, BOARD_SIZE // 2)

    def _evaluate_move_simple(self, board, row, col):
        """Simple evaluation for easy AI"""
        score = 0
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]

        # Evaluate both player's and opponent's patterns
        for player in [self.player, self.opponent]:
            multiplier = 1.0 if player == self.player else 1.2  # Slightly favor defense

            for dr, dc in directions:
                # Count consecutive stones in this direction
                count = 1
                open_ends = 0

                # Positive direction
                r, c = row + dr, col + dc
                while 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and board.grid[r][c] == player:
                    count += 1
                    r += dr
                    c += dc
                if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and board.grid[r][c] is None:
                    open_ends += 1

                # Negative direction
                r, c = row - dr, col - dc
                while 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and board.grid[r][c] == player:
                    count += 1
                    r -= dr
                    c -= dc
                if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and board.grid[r][c] is None:
                    open_ends += 1

                # Score patterns
                if count == 4:
                    score += 500 * multiplier
                elif count == 3:
                    if open_ends == 2:
                        score += 100 * multiplier
                    elif open_ends == 1:
                        score += 30 * multiplier
                elif count == 2:
                    if open_ends == 2:
                        score += 20 * multiplier
                    elif open_ends == 1:
                        score += 5 * multiplier

        # Add small bonus for center positions
        center = BOARD_SIZE // 2
        distance_from_center = abs(row - center) + abs(col - center)
        score += (BOARD_SIZE - distance_from_center) * 0.5

        return score

    def _hard_move(self, board):
        """Hard AI: Advanced Minimax with alpha-beta pruning and threat analysis"""
        # First move: center
        if board.last_move is None:
            return (BOARD_SIZE // 2, BOARD_SIZE // 2)

        valid_moves = board.get_cells_near_stones(distance=2)

        # Check for immediate win
        for r, c in valid_moves:
            if board.is_valid_move(r, c):
                board.grid[r][c] = self.player
                if board.check_win(r, c, self.player):
                    board.grid[r][c] = None
                    return (r, c)
                board.grid[r][c] = None

        # Check for immediate block
        for r, c in valid_moves:
            if board.is_valid_move(r, c):
                board.grid[r][c] = self.opponent
                if board.check_win(r, c, self.opponent):
                    board.grid[r][c] = None
                    return (r, c)
                board.grid[r][c] = None

        # Check for critical threats (opponent has open 4 or double 3)
        critical_defense = self._find_critical_defense(board)
        if critical_defense:
            return critical_defense

        # Evaluate moves with minimax
        best_move = None
        best_score = float('-inf')

        # Score all moves first
        move_scores = []
        for r, c in valid_moves:
            if board.is_valid_move(r, c):
                quick_score = self._evaluate_move_advanced(board, r, c, self.player)
                move_scores.append((quick_score, r, c))

        # Sort and only search top moves deeply
        move_scores.sort(reverse=True)
        top_moves = move_scores[:min(10, len(move_scores))]

        alpha = float('-inf')
        beta = float('inf')

        for _, r, c in top_moves:
            board.grid[r][c] = self.player
            score = self._minimax(board, 3, False, alpha, beta)  # Depth increased to 3
            board.grid[r][c] = None

            if score > best_score:
                best_score = score
                best_move = (r, c)

            alpha = max(alpha, best_score)
            if beta <= alpha:
                break

        return best_move if best_move else (top_moves[0][1], top_moves[0][2])

    def _find_critical_defense(self, board):
        """Find if opponent has critical threats that must be defended"""
        valid_moves = board.get_cells_near_stones(distance=2)
        threats = []

        for r, c in valid_moves:
            if board.is_valid_move(r, c):
                threat_level = self._evaluate_threat(board, r, c, self.opponent)
                if threat_level >= 1000:  # Critical threat
                    threats.append((threat_level, r, c))

        if threats:
            threats.sort(reverse=True)
            return (threats[0][1], threats[0][2])
        return None

    def _evaluate_threat(self, board, row, col, player):
        """Evaluate threat level of a position"""
        board.grid[row][col] = player
        threat = 0
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]

        for dr, dc in directions:
            count = 1
            open_ends = 0

            # Positive direction
            r, c = row + dr, col + dc
            while 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and board.grid[r][c] == player:
                count += 1
                r += dr
                c += dc
            if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and board.grid[r][c] is None:
                open_ends += 1

            # Negative direction
            r, c = row - dr, col - dc
            while 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and board.grid[r][c] == player:
                count += 1
                r -= dr
                c -= dc
            if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and board.grid[r][c] is None:
                open_ends += 1

            # Threat scoring
            if count >= 4:
                threat += 10000
            elif count == 3 and open_ends == 2:
                threat += 5000
            elif count == 3 and open_ends == 1:
                threat += 1000

        board.grid[row][col] = None
        return threat

    def _evaluate_move_advanced(self, board, row, col, player):
        """Advanced move evaluation"""
        score = 0
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]

        board.grid[row][col] = player

        for dr, dc in directions:
            count = 1
            open_ends = 0
            space_after_open = 0

            # Positive direction
            r, c = row + dr, col + dc
            while 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and board.grid[r][c] == player:
                count += 1
                r += dr
                c += dc
            if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE:
                if board.grid[r][c] is None:
                    open_ends += 1
                    # Check if there's space for 5
                    r2, c2 = r + dr, c + dc
                    if 0 <= r2 < BOARD_SIZE and 0 <= c2 < BOARD_SIZE:
                        space_after_open += 1

            # Negative direction
            r, c = row - dr, col - dc
            while 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and board.grid[r][c] == player:
                count += 1
                r -= dr
                c -= dc
            if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE:
                if board.grid[r][c] is None:
                    open_ends += 1
                    r2, c2 = r - dr, c - dc
                    if 0 <= r2 < BOARD_SIZE and 0 <= c2 < BOARD_SIZE:
                        space_after_open += 1

            # Advanced scoring
            if count >= 4:
                score += 100000
            elif count == 3:
                if open_ends == 2:
                    score += 50000
                elif open_ends == 1:
                    score += 1000
            elif count == 2:
                if open_ends == 2:
                    score += 500
                elif open_ends == 1:
                    score += 50

        board.grid[row][col] = None
        return score

    def _minimax(self, board, depth, is_maximizing, alpha, beta):
        """Minimax algorithm with alpha-beta pruning and improved evaluation"""
        if depth == 0:
            return self._evaluate_board_advanced(board)

        # Get candidate moves and sort them for better pruning
        valid_moves = board.get_cells_near_stones(distance=2)

        # Score moves quickly and only search best ones
        if depth >= 2:
            move_scores = []
            for r, c in valid_moves:
                if board.is_valid_move(r, c):
                    score = self._quick_score(board, r, c)
                    move_scores.append((score, r, c))
            move_scores.sort(reverse=True)
            valid_moves = [(r, c) for _, r, c in move_scores[:15]]  # Top 15 moves
        else:
            valid_moves = valid_moves[:20]

        if is_maximizing:
            max_eval = float('-inf')
            for r, c in valid_moves:
                if not board.is_valid_move(r, c):
                    continue

                board.grid[r][c] = self.player

                if board.check_win(r, c, self.player):
                    board.grid[r][c] = None
                    return 100000 - (3 - depth) * 100  # Prefer faster wins

                eval = self._minimax(board, depth - 1, False, alpha, beta)
                board.grid[r][c] = None
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)

                if beta <= alpha:
                    break
            return max_eval if max_eval != float('-inf') else 0
        else:
            min_eval = float('inf')
            for r, c in valid_moves:
                if not board.is_valid_move(r, c):
                    continue

                board.grid[r][c] = self.opponent

                if board.check_win(r, c, self.opponent):
                    board.grid[r][c] = None
                    return -100000 + (3 - depth) * 100  # Prefer delaying losses

                eval = self._minimax(board, depth - 1, True, alpha, beta)
                board.grid[r][c] = None
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)

                if beta <= alpha:
                    break
            return min_eval if min_eval != float('inf') else 0

    def _quick_score(self, board, row, col):
        """Quick heuristic score for move ordering"""
        score = 0
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]

        for player in [self.player, self.opponent]:
            mult = 1 if player == self.player else 1.1

            for dr, dc in directions:
                count = 1
                r, c = row + dr, col + dc
                while 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and board.grid[r][c] == player:
                    count += 1
                    r += dr
                    c += dc
                r, c = row - dr, col - dc
                while 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and board.grid[r][c] == player:
                    count += 1
                    r -= dr
                    c -= dc

                if count >= 3:
                    score += count * count * mult

        return score

    def _evaluate_board_advanced(self, board):
        """Advanced board evaluation"""
        score = 0

        # Evaluate all positions
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if board.grid[r][c] == self.player:
                    score += self._evaluate_position_advanced(board, r, c, self.player)
                elif board.grid[r][c] == self.opponent:
                    score -= self._evaluate_position_advanced(board, r, c, self.opponent) * 1.1

        return score

    def _evaluate_position_advanced(self, board, row, col, player):
        """Advanced position evaluation with pattern recognition"""
        score = 0
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]

        for dr, dc in directions:
            count = 1
            open_ends = 0
            blocked_ends = 0

            # Positive direction
            r, c = row + dr, col + dc
            while 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and board.grid[r][c] == player:
                count += 1
                r += dr
                c += dc
            if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE:
                if board.grid[r][c] is None:
                    open_ends += 1
                else:
                    blocked_ends += 1

            # Negative direction
            r, c = row - dr, col - dc
            while 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and board.grid[r][c] == player:
                count += 1
                r -= dr
                c -= dc
            if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE:
                if board.grid[r][c] is None:
                    open_ends += 1
                else:
                    blocked_ends += 1

            # Pattern scoring
            if count >= 5:
                score += 1000000
            elif count == 4:
                if open_ends == 2:
                    score += 100000
                elif open_ends == 1:
                    score += 10000
                else:
                    score += 1000
            elif count == 3:
                if open_ends == 2:
                    score += 10000
                elif open_ends == 1:
                    score += 1000
                else:
                    score += 100
            elif count == 2:
                if open_ends == 2:
                    score += 500
                elif open_ends == 1:
                    score += 50

        return score


class GomokuGame:
    """Main game class"""
    def __init__(self):
        self.fullscreen = False
        self.screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE + INFO_HEIGHT + BUTTON_HEIGHT))
        pygame.display.set_caption("Gomoku (Five in a Row)")
        self.clock = pygame.time.Clock()

        self.board = Board()
        self.state = GameState.MENU
        self.mode = None
        self.current_player = Player.BLACK
        self.winner = None
        self.ai = None

        # Undo feature - separate for each player
        self.undo_available_black = True
        self.undo_available_white = True
        self.move_history = []  # List of (row, col, player) tuples

        # AI timing
        self.ai_thinking = False
        self.ai_think_start_time = 0
        self.ai_think_delay = 0

        # Fonts
        self.title_font = pygame.font.Font(None, 64)
        self.info_font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)

        # Sound effects
        try:
            # Create realistic sound effects
            self.move_sound = pygame.mixer.Sound(buffer=self._generate_stone_click())
            self.win_sound = pygame.mixer.Sound(buffer=self._generate_victory_melody())
        except:
            self.move_sound = None
            self.win_sound = None

        # Menu buttons
        self._create_menu_buttons()

        # Game buttons
        self._create_game_buttons()

        # Window control buttons (macOS style)
        self._create_window_controls()

    def _generate_stone_click(self):
        """Generate a crisp stone-on-board impact sound"""
        import math
        import random as rand

        sample_rate = 22050
        duration = 0.12  # Shorter for more crispness
        num_samples = int(sample_rate * duration)

        samples = []

        for i in range(num_samples):
            t = i / sample_rate

            # Faster exponential decay for sharper impact
            decay = math.exp(-25 * t)  # Increased decay rate

            # Reduced low frequency resonance (lighter wood tone)
            base_freq = 250 + 30 * math.sin(2 * math.pi * 15 * t)  # Higher base frequency
            base_wave = math.sin(2 * math.pi * base_freq * t)

            # Stronger higher harmonic for crisp stone contact (1200-1800 Hz)
            contact_freq = 1500 + 300 * math.sin(2 * math.pi * 40 * t)
            contact_wave = 0.6 * math.sin(2 * math.pi * contact_freq * t)  # Increased amplitude

            # Sharp initial click (stronger high frequency burst)
            click_intensity = math.exp(-120 * t)  # Even faster decay
            click_noise = rand.uniform(-1, 1) * click_intensity * 0.6  # Increased intensity

            # Brighter rattle/vibration (higher frequency)
            rattle_freq = 3500 + 800 * math.sin(2 * math.pi * 100 * t)
            rattle = 0.25 * math.sin(2 * math.pi * rattle_freq * t) * math.exp(-35 * t)

            # Add bright harmonic overtones
            overtone1 = 0.2 * math.sin(2 * math.pi * 2200 * t) * math.exp(-30 * t)
            overtone2 = 0.15 * math.sin(2 * math.pi * 4400 * t) * math.exp(-40 * t)

            # Combine all components with emphasis on high frequencies
            combined = (base_wave * 0.3 + contact_wave + click_noise + rattle + overtone1 + overtone2) * decay

            # Stronger compression for punchier impact
            if combined > 0.6:
                combined = 0.6 + (combined - 0.6) * 0.2
            elif combined < -0.6:
                combined = -0.6 + (combined + 0.6) * 0.2

            # Convert to 16-bit PCM with increased volume
            value = int(32767 * 0.65 * combined)  # Increased volume for clarity
            samples.append(value)

        # Convert to stereo bytes
        return bytes([(v >> 8) & 0xFF for v in samples for _ in range(2)])

    def _generate_victory_melody(self):
        """Generate a 3-second victory melody similar to Mario level complete"""
        import math
        sample_rate = 22050

        # Mario-style victory melody notes (frequency, duration in seconds)
        # Inspired by Super Mario Bros level complete fanfare
        melody = [
            (659, 0.15),  # E5
            (659, 0.15),  # E5
            (0, 0.15),    # Rest
            (659, 0.15),  # E5
            (0, 0.15),    # Rest
            (523, 0.15),  # C5
            (659, 0.15),  # E5
            (0, 0.15),    # Rest
            (784, 0.3),   # G5
            (0, 0.3),     # Rest
            (392, 0.3),   # G4
            (0, 0.3),     # Rest
            (523, 0.25),  # C5
            (0, 0.15),    # Rest
            (392, 0.25),  # G4
            (0, 0.15),    # Rest
            (330, 0.25),  # E4
            (0, 0.15),    # Rest
            (440, 0.2),   # A4
            (0, 0.1),     # Rest
            (494, 0.2),   # B4
            (0, 0.1),     # Rest
            (466, 0.15),  # A#4
            (440, 0.15),  # A4
            (0, 0.15),    # Rest
            (392, 0.25),  # G4
            (659, 0.25),  # E5
            (784, 0.25),  # G5
            (880, 0.3),   # A5
            (0, 0.1),     # Rest
            (698, 0.2),   # F5
            (784, 0.2),   # G5
            (0, 0.1),     # Rest
            (659, 0.25),  # E5
            (0, 0.1),     # Rest
            (523, 0.2),   # C5
            (587, 0.2),   # D5
            (494, 0.25),  # B4
        ]

        all_samples = []

        for freq, duration in melody:
            num_samples = int(sample_rate * duration)
            if freq == 0:  # Rest
                samples = [0] * num_samples
            else:
                # Generate sine wave with envelope for smoother sound
                samples = []
                for i in range(num_samples):
                    # Sine wave
                    t = i / sample_rate
                    amplitude = 0.3

                    # Apply envelope (attack-decay-sustain-release)
                    envelope = 1.0
                    attack_time = 0.01
                    release_time = 0.05

                    if t < attack_time:
                        envelope = t / attack_time
                    elif t > duration - release_time:
                        envelope = (duration - t) / release_time

                    value = int(32767 * amplitude * envelope * math.sin(2 * math.pi * freq * t))
                    samples.append(value)

            all_samples.extend(samples)

        # Convert to bytes (stereo)
        return bytes([(v >> 8) & 0xFF for v in all_samples for _ in range(2)])

    def _create_menu_buttons(self):
        """Create menu buttons"""
        self.menu_button_width = 300
        self.menu_button_height = 60
        self.menu_button_spacing = 20

        # Initial positions (will be updated in update_menu_positions)
        self.menu_buttons = {
            'two_player': Button(0, 0, self.menu_button_width, self.menu_button_height, "Two Player Mode", 32),
            'ai_easy': Button(0, 0, self.menu_button_width, self.menu_button_height, "AI Easy Mode", 32),
            'ai_hard': Button(0, 0, self.menu_button_width, self.menu_button_height, "AI Hard Mode", 32),
            'quit': Button(0, 0, self.menu_button_width, self.menu_button_height, "Quit", 32)
        }
        self.update_menu_positions()

    def update_menu_positions(self):
        """Update menu button positions based on screen mode"""
        screen_width, screen_height = self.screen.get_size()

        if self.fullscreen:
            # Center menu vertically and horizontally in fullscreen
            # Leave more space at top for title
            total_height = 4 * self.menu_button_height + 3 * self.menu_button_spacing
            start_y = (screen_height - total_height) // 2 + 50  # Push buttons down
            center_x = screen_width // 2 - self.menu_button_width // 2
        else:
            # Use original positions for windowed mode
            start_y = 200
            center_x = WINDOW_SIZE // 2 - self.menu_button_width // 2

        button_names = ['two_player', 'ai_easy', 'ai_hard', 'quit']
        for i, name in enumerate(button_names):
            y = start_y + i * (self.menu_button_height + self.menu_button_spacing)
            self.menu_buttons[name].rect.x = center_x
            self.menu_buttons[name].rect.y = y

    def _create_game_buttons(self):
        """Create game buttons"""
        self.button_width = 120
        self.button_height = 40
        self.button_spacing = 10

        # Initial positions (will be updated in update_button_positions)
        self.game_buttons = {
            'undo': Button(0, 0, self.button_width, self.button_height, "Undo"),
            'restart': Button(0, 0, self.button_width, self.button_height, "Restart"),
            'menu': Button(0, 0, self.button_width, self.button_height, "Menu"),
            'quit': Button(0, 0, self.button_width, self.button_height, "Quit")
        }
        self.update_button_positions()

    def update_button_positions(self):
        """Update button positions based on screen mode"""
        screen_width, screen_height = self.screen.get_size()

        if self.fullscreen:
            y_pos = screen_height - BUTTON_HEIGHT + 10
            center_x = screen_width // 2
        else:
            y_pos = WINDOW_SIZE + INFO_HEIGHT + 10
            center_x = WINDOW_SIZE // 2

        # 4 buttons: Undo, Restart, Menu, Quit
        total_width = 4 * self.button_width + 3 * self.button_spacing
        start_x = center_x - total_width // 2

        button_names = ['undo', 'restart', 'menu', 'quit']
        for i, name in enumerate(button_names):
            x = start_x + i * (self.button_width + self.button_spacing)
            self.game_buttons[name].rect.x = x
            self.game_buttons[name].rect.y = y_pos

    def _create_window_controls(self):
        """Create macOS-style window control buttons"""
        control_size = 12
        spacing = 8
        start_x = 12
        start_y = 12

        self.window_controls = [
            {
                'type': 'close',
                'rect': pygame.Rect(start_x, start_y, control_size, control_size),
                'color': (255, 95, 86),  # Red
                'hover_color': (255, 75, 66)
            },
            {
                'type': 'minimize',
                'rect': pygame.Rect(start_x + control_size + spacing, start_y, control_size, control_size),
                'color': (255, 189, 46),  # Yellow
                'hover_color': (255, 169, 26)
            },
            {
                'type': 'fullscreen',
                'rect': pygame.Rect(start_x + 2 * (control_size + spacing), start_y, control_size, control_size),
                'color': (39, 201, 63),  # Green
                'hover_color': (19, 181, 43)
            }
        ]

    def draw_window_controls(self):
        """Draw macOS-style window control buttons"""
        if self.fullscreen:
            return  # Don't show window controls in fullscreen

        mouse_pos = pygame.mouse.get_pos()

        # Only show controls when mouse is in top-left corner area
        control_area = pygame.Rect(0, 0, 80, 40)
        if not control_area.collidepoint(mouse_pos):
            return

        for control in self.window_controls:
            # Check if mouse is hovering
            is_hover = control['rect'].collidepoint(mouse_pos)
            color = control['hover_color'] if is_hover else control['color']

            # Draw circle
            center = control['rect'].center
            radius = control['rect'].width // 2
            pygame.draw.circle(self.screen, color, center, radius)

            # Draw icon on hover
            if is_hover:
                if control['type'] == 'fullscreen':
                    # Draw diagonal arrows icon
                    icon_size = 4
                    cx, cy = center
                    # Top-left to bottom-right arrow
                    pygame.draw.line(self.screen, (0, 0, 0), (cx - icon_size, cy - icon_size), (cx + icon_size, cy + icon_size), 1)
                    # Bottom-left to top-right arrow
                    pygame.draw.line(self.screen, (0, 0, 0), (cx - icon_size, cy + icon_size), (cx + icon_size, cy - icon_size), 1)

    def get_board_dimensions(self):
        """Calculate board dimensions based on screen mode"""
        if self.fullscreen:
            # Get screen size
            screen_width, screen_height = self.screen.get_size()

            # Calculate maximum cell size to fit the screen
            available_width = screen_width - 2 * MARGIN
            available_height = screen_height - INFO_HEIGHT - BUTTON_HEIGHT - 2 * MARGIN

            max_cell_by_width = available_width // (BOARD_SIZE - 1)
            max_cell_by_height = available_height // (BOARD_SIZE - 1)

            cell_size = min(max_cell_by_width, max_cell_by_height, 60)  # Cap at 60px
            board_width = cell_size * (BOARD_SIZE - 1)

            # Center the board
            margin_x = (screen_width - board_width) // 2
            margin_y = (screen_height - INFO_HEIGHT - BUTTON_HEIGHT - board_width) // 2

            return cell_size, board_width, margin_x, margin_y
        else:
            return CELL_SIZE, BOARD_WIDTH, MARGIN, MARGIN

    def draw_board(self):
        """Draw the game board"""
        self.screen.fill(BG_COLOR)

        # Draw window controls (only in windowed mode)
        self.draw_window_controls()

        # Get dynamic board dimensions
        cell_size, board_width, margin_x, margin_y = self.get_board_dimensions()

        # Draw grid lines
        for i in range(BOARD_SIZE):
            # Vertical lines
            start_x = margin_x + i * cell_size
            pygame.draw.line(self.screen, LINE_COLOR,
                           (start_x, margin_y),
                           (start_x, margin_y + board_width), 2)
            # Horizontal lines
            start_y = margin_y + i * cell_size
            pygame.draw.line(self.screen, LINE_COLOR,
                           (margin_x, start_y),
                           (margin_x + board_width, start_y), 2)

        # Draw star points
        star_points = [(3, 3), (3, 11), (11, 3), (11, 11), (7, 7)]
        for r, c in star_points:
            x = margin_x + c * cell_size
            y = margin_y + r * cell_size
            pygame.draw.circle(self.screen, LINE_COLOR, (x, y), 5)

        # Draw stones
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if self.board.grid[r][c] is not None:
                    x = margin_x + c * cell_size
                    y = margin_y + r * cell_size
                    color = BLACK if self.board.grid[r][c] == Player.BLACK else WHITE
                    stone_radius = cell_size // 2 - 2
                    pygame.draw.circle(self.screen, color, (x, y), stone_radius)
                    if color == WHITE:
                        pygame.draw.circle(self.screen, BLACK, (x, y), stone_radius, 2)

        # Highlight last move
        if self.board.last_move:
            r, c = self.board.last_move
            x = margin_x + c * cell_size
            y = margin_y + r * cell_size
            highlight_radius = min(8, cell_size // 5)
            pygame.draw.circle(self.screen, HIGHLIGHT_COLOR, (x, y), highlight_radius, 3)

    def draw_info(self):
        """Draw game information"""
        screen_width, screen_height = self.screen.get_size()

        if self.fullscreen:
            info_y = screen_height - INFO_HEIGHT - BUTTON_HEIGHT + 10
            center_x = screen_width // 2
        else:
            info_y = WINDOW_SIZE + 10
            center_x = WINDOW_SIZE // 2

        if self.state == GameState.GAME_OVER:
            winner_text = f"{'Black' if self.winner == Player.BLACK else 'White'} wins!"
            text_surface = self.info_font.render(winner_text, True, TEXT_COLOR)
        else:
            turn_text = f"Current turn: {'Black' if self.current_player == Player.BLACK else 'White'}"
            text_surface = self.info_font.render(turn_text, True, TEXT_COLOR)

        text_rect = text_surface.get_rect(center=(center_x, info_y + 30))
        self.screen.blit(text_surface, text_rect)

        # Mode info
        if self.mode == GameMode.TWO_PLAYER:
            mode_text = "Mode: Two Player"
        elif self.mode == GameMode.AI_EASY:
            mode_text = "Mode: AI Easy"
        else:
            mode_text = "Mode: AI Hard"

        mode_surface = self.small_font.render(mode_text, True, TEXT_COLOR)
        mode_rect = mode_surface.get_rect(center=(center_x, info_y + 65))
        self.screen.blit(mode_surface, mode_rect)

        # Undo availability indicator
        if self.mode == GameMode.TWO_PLAYER:
            # Show undo status for both players in two-player mode
            black_undo_text = f"Black Undo: {'Available' if self.undo_available_black else 'Used'}"
            black_undo_color = (0, 150, 0) if self.undo_available_black else (150, 0, 0)
            white_undo_text = f"White Undo: {'Available' if self.undo_available_white else 'Used'}"
            white_undo_color = (0, 150, 0) if self.undo_available_white else (150, 0, 0)

            black_undo_surface = self.small_font.render(black_undo_text, True, black_undo_color)
            black_undo_rect = black_undo_surface.get_rect(topleft=(10, info_y + 10))
            self.screen.blit(black_undo_surface, black_undo_rect)

            white_undo_surface = self.small_font.render(white_undo_text, True, white_undo_color)
            white_undo_rect = white_undo_surface.get_rect(topleft=(10, info_y + 35))
            self.screen.blit(white_undo_surface, white_undo_rect)
        else:
            # AI mode: only show Black's (human player's) undo status
            undo_text = f"Undo: {'Available' if self.undo_available_black else 'Used'}"
            undo_color = (0, 150, 0) if self.undo_available_black else (150, 0, 0)
            undo_surface = self.small_font.render(undo_text, True, undo_color)
            undo_rect = undo_surface.get_rect(topleft=(10, info_y + 10))
            self.screen.blit(undo_surface, undo_rect)

    def draw_menu(self):
        """Draw main menu"""
        self.screen.fill(BG_COLOR)

        screen_width, screen_height = self.screen.get_size()
        center_x = screen_width // 2

        if self.fullscreen:
            # Position title in upper portion of screen in fullscreen
            # Calculate based on where buttons will be
            total_button_height = 4 * self.menu_button_height + 3 * self.menu_button_spacing
            buttons_start_y = (screen_height - total_button_height) // 2 + 50

            # Place title above buttons with adequate spacing
            title_y = buttons_start_y - 150  # 150px above first button
            subtitle_y = title_y + 70
        else:
            # Use original positions for windowed mode
            title_y = 100
            subtitle_y = 150

        # Title
        title_surface = self.title_font.render("GOMOKU", True, BLACK)
        title_rect = title_surface.get_rect(center=(center_x, title_y))
        self.screen.blit(title_surface, title_rect)

        # Subtitle
        subtitle_surface = self.small_font.render("Five in a Row", True, TEXT_COLOR)
        subtitle_rect = subtitle_surface.get_rect(center=(center_x, subtitle_y))
        self.screen.blit(subtitle_surface, subtitle_rect)

        # Buttons
        for button in self.menu_buttons.values():
            button.draw(self.screen)

    def toggle_fullscreen(self):
        """Toggle fullscreen mode"""
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE + INFO_HEIGHT + BUTTON_HEIGHT))

        # Update button positions for new screen size
        self.update_button_positions()
        self.update_menu_positions()

    def get_board_position(self, mouse_pos):
        """Convert mouse position to board coordinates"""
        x, y = mouse_pos

        # Get dynamic board dimensions
        cell_size, board_width, margin_x, margin_y = self.get_board_dimensions()

        if x < margin_x - cell_size // 2 or x > margin_x + board_width + cell_size // 2:
            return None
        if y < margin_y - cell_size // 2 or y > margin_y + board_width + cell_size // 2:
            return None

        col = round((x - margin_x) / cell_size)
        row = round((y - margin_y) / cell_size)

        return (row, col)

    def handle_menu_events(self, event):
        """Handle menu events"""
        if self.menu_buttons['two_player'].handle_event(event):
            self.start_game(GameMode.TWO_PLAYER)
        elif self.menu_buttons['ai_easy'].handle_event(event):
            self.start_game(GameMode.AI_EASY)
        elif self.menu_buttons['ai_hard'].handle_event(event):
            self.start_game(GameMode.AI_HARD)
        elif self.menu_buttons['quit'].handle_event(event):
            return False
        return True

    def handle_game_events(self, event):
        """Handle game events"""
        # Handle window control buttons (macOS style)
        if hasattr(self, 'window_controls'):
            for control in self.window_controls:
                if control['type'] == 'fullscreen' and control['rect'].collidepoint(pygame.mouse.get_pos()):
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        self.toggle_fullscreen()
                        return True

        # Handle buttons
        if self.game_buttons['undo'].handle_event(event):
            self.undo_move()
            return True
        elif self.game_buttons['restart'].handle_event(event):
            self.restart_game()
            return True
        elif self.game_buttons['menu'].handle_event(event):
            self.state = GameState.MENU
            return True
        elif self.game_buttons['quit'].handle_event(event):
            return False

        # Handle board clicks
        if event.type == pygame.MOUSEBUTTONDOWN and self.state == GameState.PLAYING:
            if self.mode != GameMode.TWO_PLAYER and self.current_player == Player.WHITE:
                return True  # AI's turn

            # Don't allow new moves while AI is thinking
            if self.ai_thinking:
                return True

            pos = self.get_board_position(event.pos)
            if pos:
                row, col = pos
                if self.make_move(row, col):
                    # Start AI thinking (non-blocking)
                    if self.mode != GameMode.TWO_PLAYER and self.state == GameState.PLAYING:
                        self.start_ai_thinking()

        return True

    def make_move(self, row, col):
        """Make a move on the board"""
        if self.board.place_stone(row, col, self.current_player):
            # Save move to history
            self.move_history.append((row, col, self.current_player))

            if self.move_sound:
                self.move_sound.play()

            if self.board.check_win(row, col, self.current_player):
                self.winner = self.current_player
                self.state = GameState.GAME_OVER
                if self.win_sound:
                    self.win_sound.play()
            else:
                self.current_player = self.current_player.opposite()

            return True
        return False

    def undo_move(self):
        """Undo the last move (each player gets one undo chance)"""
        if not self.move_history or self.state == GameState.GAME_OVER:
            return

        # Determine which player is requesting the undo
        # In AI mode, it's always the human player (Black)
        # In two-player mode, it's the player who made the last move
        if self.mode != GameMode.TWO_PLAYER:
            # AI mode: only Black (human) can undo, and we undo both moves
            if not self.undo_available_black or len(self.move_history) < 2:
                return
            requesting_player = Player.BLACK
        else:
            # Two-player mode: the last player to move wants to undo
            if len(self.move_history) == 0:
                return
            last_move_player = self.move_history[-1][2]

            # Check if this player has undo available
            if last_move_player == Player.BLACK and not self.undo_available_black:
                return
            elif last_move_player == Player.WHITE and not self.undo_available_white:
                return
            requesting_player = last_move_player

        # Perform the undo
        if self.mode != GameMode.TWO_PLAYER and len(self.move_history) >= 2:
            # AI mode: undo both AI's move and player's move
            self.move_history.pop()
            self.move_history.pop()
        elif len(self.move_history) >= 1:
            # Two-player mode: just undo one move
            self.move_history.pop()
        else:
            return

        # Rebuild board from history
        self.board.reset()
        temp_history = self.move_history[:]
        self.move_history = []

        # Replay all moves
        for row, col, player in temp_history:
            self.board.grid[row][col] = player
            self.board.last_move = (row, col)
            self.move_history.append((row, col, player))

        # Update current player
        if len(self.move_history) % 2 == 0:
            self.current_player = Player.BLACK
        else:
            self.current_player = Player.WHITE

        # Mark undo as used for the requesting player
        if requesting_player == Player.BLACK:
            self.undo_available_black = False
        else:
            self.undo_available_white = False

    def start_ai_thinking(self):
        """Start AI thinking process with delay"""
        if self.ai:
            # Calculate thinking time based on difficulty and game state
            if self.mode == GameMode.AI_EASY:
                # Easy AI: 0.5-1.2 seconds
                self.ai_think_delay = random.randint(500, 1200)
            else:
                # Hard AI: 0.8-2.0 seconds (longer thinking for complex positions)
                num_stones = sum(1 for r in range(BOARD_SIZE) for c in range(BOARD_SIZE) if self.board.grid[r][c] is not None)

                # More stones = more thinking time
                if num_stones < 10:
                    self.ai_think_delay = random.randint(800, 1400)
                elif num_stones < 30:
                    self.ai_think_delay = random.randint(1000, 1800)
                else:
                    self.ai_think_delay = random.randint(1200, 2000)

            self.ai_thinking = True
            self.ai_think_start_time = pygame.time.get_ticks()

    def update_ai(self):
        """Update AI state and make move when ready"""
        if self.ai_thinking:
            current_time = pygame.time.get_ticks()
            if current_time - self.ai_think_start_time >= self.ai_think_delay:
                # AI has finished thinking, make the move
                row, col = self.ai.get_move(self.board)
                self.make_move(row, col)
                self.ai_thinking = False

    def start_game(self, mode):
        """Start a new game"""
        self.mode = mode
        self.state = GameState.PLAYING
        self.board.reset()
        self.current_player = Player.BLACK
        self.winner = None
        self.undo_available_black = True
        self.undo_available_white = True
        self.move_history = []
        self.ai_thinking = False

        if mode in [GameMode.AI_EASY, GameMode.AI_HARD]:
            self.ai = AI(mode, Player.WHITE)
        else:
            self.ai = None

    def restart_game(self):
        """Restart current game"""
        self.board.reset()
        self.current_player = Player.BLACK
        self.winner = None
        self.state = GameState.PLAYING
        self.undo_available_black = True
        self.undo_available_white = True
        self.move_history = []
        self.ai_thinking = False

    def run(self):
        """Main game loop"""
        running = True

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                # Handle keyboard shortcuts
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_F11:
                        self.toggle_fullscreen()
                    elif event.key == pygame.K_ESCAPE and self.fullscreen:
                        self.toggle_fullscreen()

                if self.state == GameState.MENU:
                    running = self.handle_menu_events(event)
                else:
                    running = self.handle_game_events(event)

            # Update AI if it's thinking
            if self.state == GameState.PLAYING:
                self.update_ai()

            # Draw
            if self.state == GameState.MENU:
                self.draw_menu()
            else:
                self.draw_board()
                self.draw_info()
                for button in self.game_buttons.values():
                    button.draw(self.screen)

            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()
        sys.exit()


def main():
    game = GomokuGame()
    game.run()


if __name__ == "__main__":
    main()

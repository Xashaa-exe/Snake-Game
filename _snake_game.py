import pygame
import pygame.locals
from pygame import *
import time
import random
import math
import hashlib

# Global Constants
SIZE = 40
BACKGROUND_COLOR = (135, 206, 235)


class Apple:
    def __init__(self, parent_screen):
        self.parent_screen = parent_screen
        self.image_red = pygame.image.load('resources/apple (1).jpg').convert()
        self.image_gold = pygame.image.load('resources/golden_apple.png').convert()
        self.x = SIZE * 3
        self.y = SIZE * 3
        self.is_golden = False

    def draw(self):
        if self.is_golden:
            self.parent_screen.blit(self.image_gold, (self.x, self.y))
        else:
            self.parent_screen.blit(self.image_red, (self.x, self.y))

    def move(self):
        self.x = random.randint(1, 29) * SIZE
        self.y = random.randint(1, 15) * SIZE
        self.is_golden = random.random() < 0.2


class Snake:
    def __init__(self, parent_screen, length):
        self.length = length
        self.parent_screen = parent_screen
        self.block = pygame.image.load('resources/block.jpg').convert()
        self.x = [SIZE] * length
        self.y = [SIZE] * length
        self.direction = 'down'

    def increase_length(self):
        self.length += 1
        self.x.append(-1)
        self.y.append(-1)

    def draw(self):
        for i in range(self.length):
            self.parent_screen.blit(self.block, (self.x[i], self.y[i]))

    def move_left(self):
        self.direction = 'left'

    def move_right(self):
        self.direction = 'right'

    def move_up(self):
        self.direction = 'up'

    def move_down(self):
        self.direction = 'down'

    def walk(self):
        # Move body blocks from tail to head
        for i in range(self.length - 1, 0, -1):
            self.x[i] = self.x[i - 1]
            self.y[i] = self.y[i - 1]

        # Move the snake head
        if self.direction == 'left':
            self.x[0] -= SIZE
        if self.direction == 'right':
            self.x[0] += SIZE
        if self.direction == 'up':
            self.y[0] -= SIZE
        if self.direction == 'down':
            self.y[0] += SIZE

        self.draw()


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption('Snake Game')
        pygame.mixer.init()

        self.surface = pygame.display.set_mode((1200, 675))
        self.snake = Snake(self.surface, 1)
        self.snake.draw()
        self.apple = Apple(self.surface)
        self.apple.draw()
        self.score_bg = pygame.image.load('resources/score_bg.png').convert_alpha()

        self.shake_duration = 0
        self.is_settings = False
        self.speed = 0.2
        self.score_color_val = 0
        self.high_score = 0

        self.play_background_music()
        pygame.mixer.music.set_volume(0.1)
        self.load_high_score()

    def play_background_music(self):
        pygame.mixer.music.load('resources/background_music.mp3')
        pygame.mixer.music.play(-1, 0)

    def play_sound(self, sound_name):
        sound = None
        if sound_name == "crash":
            sound = pygame.mixer.Sound("resources/crash.mp3")
        elif sound_name == 'ding':
            sound = pygame.mixer.Sound("resources/ding.mp3")

        if sound is not None:
            pygame.mixer.Sound.play(sound)

    def is_collision(self, x1, y1, x2, y2):
        if x1 >= x2 and x1 < x2 + SIZE:
            if y1 >= y2 and y1 < y2 + SIZE:
                return True
        return False

    def render_background(self):
        bg = pygame.image.load('resources/Background_Snake.jpg')
        self.surface.blit(bg, (0, 0))

    def load_high_score(self):
        try:
            with open('high_score.txt', 'r') as f:
                lines = f.read().splitlines()
                file_score = int(lines[0])
                file_hash = lines[1]

                # Secure verification to prevent local file cheating
                secret_salt = 'my_secret_snake_game_123'
                expected_data = f'{file_score}:{secret_salt}'
                expected_hash = hashlib.sha256(expected_data.encode()).hexdigest()

                if file_hash == expected_hash:
                    self.high_score = file_score
                else:
                    print('⚠️ Cheat Detected! High score file was modified.')
                    self.high_score = 0
                    self.save_high_score()
        except Exception:
            self.high_score = 0

    def play(self):
        # 1. Screen Shake Calculation
        offset_x = 0
        offset_y = 0
        if self.shake_duration > 0:
            offset_x = random.randint(-2, 2)
            offset_y = random.randint(-2, 2)
            self.shake_duration -= 1

        # 2. Render background
        bg = pygame.image.load('resources/Background_Snake.jpg')
        self.surface.blit(bg, (offset_x, offset_y))

        # Render score panel background
        score_bg_scaled = pygame.transform.scale(self.score_bg, (380, 150))
        self.surface.blit(score_bg_scaled, (700 + offset_x, 15 + offset_y))

        # 3. Render active game entities
        self.snake.walk()
        self.apple.draw()
        self.display_score()
        pygame.display.flip()

        # 4. Scenario: Snake eating the apple
        if self.is_collision(self.snake.x[0], self.snake.y[0], self.apple.x, self.apple.y):
            self.play_sound("ding")
            self.shake_duration = 3

            if self.apple.is_golden:
                for _ in range(3):
                    self.snake.increase_length()
                if self.speed > 0.04:
                    self.speed -= 0.02
            else:
                self.snake.increase_length()
                if self.speed > 0.05:
                    self.speed -= 0.01

            self.apple.move()

        # 5. Scenario: Snake colliding with its own body
        for i in range(3, self.snake.length):
            if self.is_collision(self.snake.x[0], self.snake.y[0], self.snake.x[i], self.snake.y[i]):
                self.play_sound('crash')
                raise Exception("Collision Occurred")

        # 6. Scenario: Boundary Check
        if not (0 <= self.snake.x[0] <= 1160 and 0 <= self.snake.y[0] <= 635):
            self.play_sound('crash')
            raise Exception('Hit the wall')

    def reset(self):
        # Full state reset on game restart
        self.snake = Snake(self.surface, length=1)
        self.snake.direction = 'down'
        self.apple = Apple(self.surface)
        self.speed = 0.2

    def show_game_over(self):
        self.render_background()
        font = pygame.font.SysFont('arial', 35)

        line1 = font.render(f'Final Score: {self.snake.length - 1}', True, (255, 255, 255))
        self.surface.blit(line1, (200, 100))

        line_hs = font.render(f'Best Record: {self.high_score}', True, (255, 215, 0))
        self.surface.blit(line_hs, (200, 50))

        line2 = font.render('To play again press Enter. To exit press Escape', True, (255, 255, 255))
        self.surface.blit(line2, (200, 150))

        pygame.display.flip()
        pygame.mixer.music.pause()

    def show_settings(self):
        self.render_background()
        font = pygame.font.SysFont('arial', 30)

        current_vol = int(pygame.mixer.music.get_volume() * 100)

        title = font.render('SETTINGS & CONTROLS', True, (255, 215, 0))
        vol_text = font.render(f'1. Music Volume: {current_vol}%  [Press LEFT / RIGHT]', True, (255, 255, 255))

        control_move = font.render('2. Movement: ARROW KEYS (Up, Down, Left, Right)', True, (220, 220, 220))
        control_pause = font.render('3. Pause Game: Press SPACE', True, (220, 220, 220))

        back_text = font.render('Press BACKSPACE to Return to Game', True, (0, 255, 0))

        self.surface.blit(title, (200, 80))
        self.surface.blit(vol_text, (200, 150))
        self.surface.blit(control_move, (200, 210))
        self.surface.blit(control_pause, (200, 270))
        self.surface.blit(back_text, (200, 360))

        pygame.display.flip()

    def show_pause_screen(self):
        font = pygame.font.SysFont('arial', 40, bold=True)
        pause_text = font.render('GAME PAUSED', True, (255, 215, 0))
        resume_text = font.render('Press SPACE to Resume', True, (255, 255, 255))

        # Overlay text on top of the current frame
        self.surface.blit(pause_text, (450, 250))
        self.surface.blit(resume_text, (400, 320))
        pygame.display.flip()

    def display_score(self):
        font = pygame.font.SysFont('arial', 25, bold=True)

        # Dynamic color transformation using sine waves
        self.score_color_val += 5
        r = (math.sin(self.score_color_val * 0.05) * 127 + 128)
        g = (math.sin(self.score_color_val * 0.05 + 2) * 127 + 128)
        b = (math.sin(self.score_color_val * 0.05 + 4) * 127 + 128)

        score = font.render(f'Score: {self.snake.length - 1}', True, (r, g, b))
        self.surface.blit(score, (800, 40))

        high_score_text = font.render(f'High Score: {self.high_score}', True, (r, g, b))
        self.surface.blit(high_score_text, (800, 85))

    def save_high_score(self):
        actual_score = self.snake.length - 1
        if actual_score > self.high_score:
            self.high_score = actual_score
            secret_salt = 'my_secret_snake_game_123'
            data_to_hash = f'{self.high_score}:{secret_salt}'
            secure_hash = hashlib.sha256(data_to_hash.encode()).hexdigest()
            with open('high_score.txt', 'w') as f:
                f.write(f'{self.high_score}\n{secure_hash}')

    def run(self):
        running = True
        pause = False  # State flag for game over condition
        is_paused = False  # State flag for manual pausing (SPACE)

        while running:
            for event in pygame.event.get():
                if event.type == QUIT:
                    running = False
                elif event.type == KEYDOWN:
                    if event.key == K_ESCAPE:
                        running = False

                    # Toggle pause mode
                    if event.key == K_SPACE and not pause and not self.is_settings:
                        is_paused = not is_paused
                        if is_paused:
                            pygame.mixer.music.pause()
                        else:
                            pygame.mixer.music.unpause()

                    # Toggle settings overlay
                    if event.key == K_TAB and not pause and not is_paused:
                        self.is_settings = True

                    if event.key == K_BACKSPACE and self.is_settings:
                        self.is_settings = False

                    # Restart game on game over
                    if event.key == K_RETURN and pause:
                        pygame.mixer.music.unpause()
                        pause = False
                        is_paused = False
                        self.is_settings = False
                        self.reset()

                    # Adjust audio volume within the settings screen
                    if self.is_settings:
                        current_volume = pygame.mixer.music.get_volume()
                        if event.key == K_RIGHT:
                            pygame.mixer.music.set_volume(min(1.0, current_volume + 0.1))
                        if event.key == K_LEFT:
                            pygame.mixer.music.set_volume(max(0.0, current_volume - 0.1))

                    # Standard game controls
                    if not pause and not self.is_settings and not is_paused:
                        if event.key == K_UP:
                            self.snake.move_up()
                        if event.key == K_DOWN:
                            self.snake.move_down()
                        if event.key == K_LEFT:
                            self.snake.move_left()
                        if event.key == K_RIGHT:
                            self.snake.move_right()

            try:
                if self.is_settings:
                    self.show_settings()
                elif is_paused:
                    self.show_pause_screen()
                elif not pause:
                    self.play()
            except Exception:
                self.save_high_score()
                self.show_game_over()
                pause = True

            time.sleep(self.speed)


if __name__ == '__main__':
    game = Game()
    game.run()
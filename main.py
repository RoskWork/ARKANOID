import pygame
import sys
import random
import math
from game_objects import Paddle, Ball, Brick, PowerUp, Laser, Particle, Firework

# -- General Setup --
pygame.init()
pygame.mixer.init()
clock = pygame.time.Clock()

# -- Screen Setup --
screen_width = 800
screen_height = 600
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("PyGame Arkanoid")

# -- Colors --
BG_COLOR = pygame.Color('grey12')
BRICK_COLORS = [(178, 34, 34), (255, 165, 0), (255, 215, 0), (50, 205, 50)]

# -- Font Setup --
title_font = pygame.font.Font(None, 70)
game_font = pygame.font.Font(None, 40)
message_font = pygame.font.Font(None, 30)

# -- Sound Setup --
try:
    bounce_sound = pygame.mixer.Sound('bounce.wav')
    brick_break_sound = pygame.mixer.Sound('brick_break.wav')
    game_over_sound = pygame.mixer.Sound('game_over.wav')
    laser_sound = pygame.mixer.Sound('laser.wav')
    all_sounds = [bounce_sound, brick_break_sound, game_over_sound, laser_sound]
except pygame.error as e:
    print(f"Warning: Sound file not found. {e}")


    class DummySound:
        def play(self): pass

        def set_volume(self, volume): pass


    bounce_sound, brick_break_sound, game_over_sound, laser_sound = DummySound(), DummySound(), DummySound(), DummySound()
    all_sounds = [bounce_sound, brick_break_sound, game_over_sound, laser_sound]

# -- Game Objects --
paddle = Paddle(screen_width, screen_height)
balls = [Ball(screen_width, screen_height)]

# --- Level Data ---
LEVELS = [
    # Level 1
    {
        'rows': 4,
        'cols': 10,
        'layout': [
            '..........',
            '..........',
            '..........',
            '..........'
        ]
    },
    # Level 2
    {
        'rows': 5,
        'cols': 10,
        'layout': [
            'X.X.X.X.X.',
            '.X.X.X.X.X',
            'X.X.X.X.X.',
            '.X.X.X.X.X',
            'X.X.X.X.X.'
        ]
    },
    # Level 3 - More challenging layout
    {
        'rows': 6,
        'cols': 10,
        'layout': [
            'XXXXXXXXXX',
            'X........X',
            'X.X....X.X',
            'X..X..X..X',
            'X...XX...X',
            'XXXXXXXXXX'
        ]
    }
]


# --- Brick Wall Setup Function ---
def create_brick_wall(level_num):
    bricks = []
    if level_num - 1 >= len(LEVELS):
        return bricks

    level_data = LEVELS[level_num - 1]
    brick_rows = level_data['rows']
    brick_cols = level_data['cols']
    brick_width = 75
    brick_height = 20
    brick_padding = 5
    wall_start_y = 50

    for row_idx in range(brick_rows):
        for col_idx in range(brick_cols):
            if 'layout' in level_data and row_idx < len(level_data['layout']) and \
                    col_idx < len(level_data['layout'][row_idx]) and \
                    level_data['layout'][row_idx][col_idx] == 'X':
                x = col_idx * (brick_width + brick_padding) + brick_padding
                y = row_idx * (brick_height + brick_padding) + wall_start_y
                color = BRICK_COLORS[row_idx % len(BRICK_COLORS)]
                bricks.append(Brick(x, y, brick_width, brick_height, color))
            elif 'layout' not in level_data:
                x = col_idx * (brick_width + brick_padding) + brick_padding
                y = row_idx * (brick_height + brick_padding) + wall_start_y
                color = BRICK_COLORS[row_idx % len(BRICK_COLORS)]
                bricks.append(Brick(x, y, brick_width, brick_height, color))
    return bricks


bricks = create_brick_wall(1)
power_ups = []
lasers = []
particles = []
fireworks = []

# --- Game Variables ---
game_state = 'title_screen'
score = 0
lives = 3
display_message = ""
message_timer = 0
firework_timer = 0
current_level = 1
is_muted = False

# --- Mute Button ---
mute_button_rect = pygame.Rect(350, 10, 70, 30)

# -- Main Game Loop --
while True:
    # --- Event Handling ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                if game_state == 'title_screen':
                    game_state = 'playing'
                elif game_state in ['game_over', 'you_win']:
                    paddle.reset()
                    balls = [Ball(screen_width, screen_height)]
                    bricks = create_brick_wall(1)
                    score = 0
                    lives = 3
                    power_ups.clear()
                    lasers.clear()
                    particles.clear()
                    fireworks.clear()
                    current_level = 1
                    game_state = 'title_screen'
                for ball in balls:
                    if ball.is_glued:
                        ball.is_glued = False
                        break

            if event.key == pygame.K_f and paddle.has_laser:
                lasers.append(Laser(paddle.rect.centerx - 30, paddle.rect.top))
                lasers.append(Laser(paddle.rect.centerx + 30, paddle.rect.top))
                if not is_muted: laser_sound.play()

        if event.type == pygame.MOUSEBUTTONDOWN:
            if mute_button_rect.collidepoint(event.pos):
                is_muted = not is_muted
                for sound in all_sounds:
                    sound.set_volume(0 if is_muted else 1)

    # --- Drawing and Updating based on Game State ---
    screen.fill(BG_COLOR)

    if game_state == 'title_screen':
        title_surface = title_font.render("ARKANOID", True, (255, 255, 255))
        title_rect = title_surface.get_rect(center=(screen_width / 2, screen_height / 2 - 50))
        screen.blit(title_surface, title_rect)

        start_surface = game_font.render("Press SPACE to Start", True, (255, 255, 255))
        start_rect = start_surface.get_rect(center=(screen_width / 2, screen_height / 2 + 20))
        screen.blit(start_surface, start_rect)

    elif game_state == 'playing':
        # --- Update all game objects ---
        paddle.update()
        keys = pygame.key.get_pressed()

        balls_to_remove = []
        balls_to_add = []

        for ball in balls[:]:
            ball_status, collision_object = ball.update(paddle, keys[pygame.K_SPACE])

            if ball_status == 'lost':
                balls_to_remove.append(ball)
                # Check if this was the last ball *before* removing it
                if len(balls) - len(balls_to_remove) == 0:
                    lives -= 1
                    if lives <= 0:
                        game_state = 'game_over'
                        if not is_muted: game_over_sound.play()
                    else:
                        balls.append(Ball(screen_width, screen_height))
                        paddle.reset()
            elif collision_object in ['wall', 'paddle']:
                if not is_muted: bounce_sound.play()
                for _ in range(5):
                    particles.append(Particle(ball.rect.centerx, ball.rect.centery, (255, 255, 0), 1, 3, 1, 3, 0))

            for brick in bricks[:]:
                if ball.rect.colliderect(brick.rect):
                    ball.speed_y *= -1
                    for _ in range(15):
                        particles.append(
                            Particle(brick.rect.centerx, brick.rect.centery, brick.color, 1, 4, 1, 4, 0.05))
                    bricks.remove(brick)
                    score += 10
                    if not is_muted: brick_break_sound.play()
                    if random.random() < 0.3:
                        power_up_type = random.choice(['grow', 'laser', 'glue', 'slow', 'multi_ball', 'life_up'])
                        power_up = PowerUp(brick.rect.centerx, brick.rect.centery, power_up_type)
                        power_ups.append(power_up)
                    break

        for ball in balls_to_remove:
            if ball in balls:
                balls.remove(ball)

        # If all balls are lost and game is not over, add a new ball (this handles the case where multiple balls are lost at once)
        if not balls and lives > 0 and game_state == 'playing':
            balls.append(Ball(screen_width, screen_height))
            paddle.reset()

        for power_up in power_ups[:]:
            power_up.update()
            if power_up.rect.top > screen_height:
                power_ups.remove(power_up)
            elif paddle.rect.colliderect(power_up.rect):
                display_message = power_up.PROPERTIES[power_up.type]['message']
                message_timer = 120
                if power_up.type in ['grow', 'laser', 'glue']:
                    paddle.activate_power_up(power_up.type)
                elif power_up.type == 'slow':
                    for ball in balls:
                        ball.activate_power_up(power_up.type)
                elif power_up.type == 'multi_ball':
                    for _ in range(2):
                        new_ball = Ball(screen_width, screen_height)
                        new_ball.speed_x *= random.choice((1, -1))
                        new_ball.speed_y *= random.choice((1, -1))
                        balls_to_add.append(new_ball)
                elif power_up.type == 'life_up':
                    lives += 1
                power_ups.remove(power_up)

        balls.extend(balls_to_add)

        for laser in lasers[:]:
            laser.update()
            if laser.rect.bottom < 0:
                lasers.remove(laser)
            else:
                for brick in bricks[:]:
                    if laser.rect.colliderect(brick.rect):
                        for _ in range(10):
                            particles.append(
                                Particle(brick.rect.centerx, brick.rect.centery, brick.color, 1, 3, 1, 3, 0.05))
                        bricks.remove(brick)
                        lasers.remove(laser)
                        score += 10
                        if not is_muted: brick_break_sound.play()
                        break

        if not bricks:
            current_level += 1
            if current_level - 1 < len(LEVELS):
                display_message = f"LEVEL {current_level}!"
                message_timer = 120
                bricks = create_brick_wall(current_level)
                paddle.reset()
                for ball in balls: ball.reset()
                power_ups.clear()
                lasers.clear()
            else:
                game_state = 'you_win'

        # --- Draw all game objects ---
        paddle.draw(screen)
        for ball in balls:
            ball.draw(screen)
        for brick in bricks:
            brick.draw(screen)
        for power_up in power_ups:
            power_up.draw(screen)
        for laser in lasers:
            laser.draw(screen)

        # --- Draw UI ---
        score_text = game_font.render(f"Score: {score}", True, (255, 255, 255))
        screen.blit(score_text, (10, 10))
        lives_text = game_font.render(f"Lives: {lives}", True, (255, 255, 255))
        screen.blit(lives_text, (screen_width - lives_text.get_width() - 10, 10))
        level_text = game_font.render(f"Level: {current_level}", True, (255, 255, 255))
        screen.blit(level_text, (10, 50))


    elif game_state in ['game_over', 'you_win']:
        if game_state == 'you_win':
            firework_timer -= 1
            if firework_timer <= 0:
                fireworks.append(Firework(screen_width, screen_height))
                firework_timer = random.randint(20, 50)

            for firework in fireworks[:]:
                firework.update()
                if firework.is_dead():
                    fireworks.remove(firework)

            for firework in fireworks:
                firework.draw(screen)

        message = "GAME OVER" if game_state == 'game_over' else "YOU WIN!"
        text_surface = game_font.render(message, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=(screen_width / 2, screen_height / 2 - 20))
        screen.blit(text_surface, text_rect)

        final_score_surface = game_font.render(f"Final Score: {score}", True, (255, 255, 255))
        final_score_rect = final_score_surface.get_rect(center=(screen_width / 2, screen_height / 2 + 0))
        screen.blit(final_score_surface, final_score_rect)

        restart_surface = game_font.render("Press SPACE to return to Title", True, (255, 255, 255))
        restart_rect = restart_surface.get_rect(center=(screen_width / 2, screen_height / 2 + 30))
        screen.blit(restart_surface, restart_rect)

    # --- Update effects and messages (these run in all states) ---
    if message_timer > 0:
        message_timer -= 1
        message_surface = message_font.render(display_message, True, (255, 255, 255))
        message_rect = message_surface.get_rect(center=(screen_width / 2, screen_height - 60))
        screen.blit(message_surface, message_rect)

    for particle in particles[:]:
        particle.update()
        if particle.size <= 0:
            particles.remove(particle)
    for particle in particles:
        particle.draw(screen)

    # --- Draw Mute Button ---
    mute_text = "MUTE" if not is_muted else "UNMUTE"
    mute_color = (255, 0, 0) if not is_muted else (0, 255, 0)
    pygame.draw.rect(screen, mute_color, mute_button_rect)
    mute_text_surface = message_font.render(mute_text, True, (255, 255, 255))
    mute_text_rect = mute_text_surface.get_rect(center=mute_button_rect.center)
    screen.blit(mute_text_surface, mute_text_rect)

    # --- Final Display Update ---
    pygame.display.flip()
    clock.tick(60)
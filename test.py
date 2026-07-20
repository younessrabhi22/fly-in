import pygame
import random
import sys

pygame.init() # Init pygame
W, H = 600, 600 # Screen setup

screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Catch the Falling Blocks")

WHT, BLU, RED, BLK = (255, 255, 255), (0, 200, 255), (255, 0, 0), (0, 0, 0) # Colors

# Clock and font
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 36)

# Paddle and block
paddle = pygame.Rect(W // 2 - 60, H - 20, 120, 10)
block = pygame.Rect(random.randint(0, W - 20), 0, 20, 20)
b_speed = 5

score = 0 # Score

# Game loop
run = True
while run:
    screen.fill(BLK)

    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    # Paddle movement
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT] and paddle.left > 0:
        paddle.move_ip(-8, 0)
    if keys[pygame.K_RIGHT] and paddle.right < W:
        paddle.move_ip(8, 0)

    # Move block
    block.y += b_speed

    # Block caught
    if block.colliderect(paddle):
        block.y = 0
        block.x = random.randint(0, W - 20)
        score += 1
        b_speed += 0.5  # Speed up

    # Block missed
    if block.y > H:
        game_over = font.render(f"Game Over! Final Score: {score}", True, RED)
        screen.blit(game_over, (W // 2 - 150, H // 2))
        pygame.display.flip()
        pygame.time.wait(2000)
        run = False

    # Draw objects
    pygame.draw.rect(screen, WHT, paddle)
    pygame.draw.rect(screen, BLU, block)

    # Display score
    score_text = font.render(f"Score: {score}", True, WHT)
    screen.blit(score_text, (10, 10))

    pygame.display.flip()
    clock.tick(60)



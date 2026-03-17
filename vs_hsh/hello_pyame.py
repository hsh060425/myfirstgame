import pygame
import sys

pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("My First Pygame")

WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
BLACK = (0, 0, 0) # 글자 색상을 위해 추가

# 1. 폰트 설정 (시스템 기본 폰트, 크기 30)
font = pygame.font.SysFont(None, 30)

clock = pygame.time.Clock()
running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill(WHITE)
    pygame.draw.circle(screen, BLUE, (400, 300), 50)

    # 2. FPS 계산 및 문자열 만들기 (clock.get_fps()는 소수점으로 나와서 정수로 변환)
    fps_text = font.render(f"FPS: {int(clock.get_fps())}", True, BLACK)
    
    # 3. 화면에 그리기 (좌측 상단 10, 10 위치)
    screen.blit(fps_text, (10, 10))

    pygame.display.flip()
    clock.tick(10)

pygame.quit()
sys.exit()
import pygame
import sys

pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Moving Circle")

WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
BLACK = (0, 0, 0)

font = pygame.font.SysFont(None, 30)

# --- 새로운 변수 추가 ---
circle_x = 400  # 원의 가로 위치
circle_y = 300  # 원의 세로 위치
speed = 5       # 원이 한 번에 움직일 속도(픽셀)

clock = pygame.time.Clock()
running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # --- 키보드 입력 확인 ---
    keys = pygame.key.get_pressed() # 현재 눌린 모든 키의 상태를 가져옵니다.
    if keys[pygame.K_LEFT]:         # 왼쪽 방향키가 눌렸다면
        circle_x -= speed
    if keys[pygame.K_RIGHT]:        # 오른쪽 방향키가 눌렸다면
        circle_x += speed
    if keys[pygame.K_UP]:           # 위쪽 방향키가 눌렸다면
        circle_y -= speed
    if keys[pygame.K_DOWN]:         # 아래쪽 방향키가 눌렸다면
        circle_y += speed

    screen.fill(WHITE)
    
    # 원을 그릴 때 고정된 좌표 대신 변수(circle_x, circle_y)를 사용합니다.
    pygame.draw.circle(screen, BLUE, (circle_x, circle_y), 50)

    # FPS 출력
    fps_text = font.render(f"FPS: {int(clock.get_fps())}", True, BLACK)
    screen.blit(fps_text, (10, 10))

    pygame.display.flip()
    clock.tick(10)

pygame.quit()
sys.exit()
import pygame
import sys

pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("FPS Independent Movement")

WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
BLACK = (0, 0, 0)

font = pygame.font.SysFont(None, 30)

# 위치 변수 (소수점 계산을 위해 실수로 설정)
circle_x = 400.0
circle_y = 300.0

# 속도 설정: "1초에 몇 픽셀을 갈 것인가?" (예: 1초에 300픽셀)
speed = 300 

clock = pygame.time.Clock()
running = True

while running:
    # 1. 델타 타임 계산 (지난 프레임으로부터 몇 초가 흘렀는지 계산)
    # clock.tick(60)은 밀리초(ms)를 반환하므로 1000으로 나누어 '초' 단위로 만듭니다.
    dt = clock.tick(120) / 1000.0

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()
    
    # 2. 이동 공식: 위치 += 속도 * 시간(dt)
    if keys[pygame.K_LEFT]:
        circle_x -= speed * dt
    if keys[pygame.K_RIGHT]:
        circle_x += speed * dt
    if keys[pygame.K_UP]:
        circle_y -= speed * dt
    if keys[pygame.K_DOWN]:
        circle_y += speed * dt

    screen.fill(WHITE)
    
    # 원 그리기 (좌표는 정수여야 하므로 int로 변환)
    pygame.draw.circle(screen, BLUE, (int(circle_x), int(circle_y)), 50)

    # FPS 출력
    fps_text = font.render(f"FPS: {int(clock.get_fps())}", True, BLACK)
    screen.blit(fps_text, (10, 10))

    pygame.display.flip()

pygame.quit()
sys.exit()
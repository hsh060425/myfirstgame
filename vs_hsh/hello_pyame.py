import pygame
import sys
import random  # 가시의 위치를 무작위로 정하기 위해 추가

pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Avoid the Spikes!")

WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)  # 가시 색상

font = pygame.font.SysFont(None, 30)

# 플레이어 설정
circle_x, circle_y = 400.0, 300.0
player_speed = 300 
player_radius = 50

# 가시(장애물) 설정
spikes = []          # 가시들을 담을 리스트
spike_speed = 400    # 가시가 날아오는 속도
spike_radius = 15    # 플레이어보다 작게 설정
spawn_timer = 0      # 가시 생성 타이머

clock = pygame.time.Clock()
running = True

while running:
    dt = clock.tick(60) / 1000.0

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # 플레이어 이동 제어
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]: circle_x -= player_speed * dt
    if keys[pygame.K_RIGHT]: circle_x += player_speed * dt
    if keys[pygame.K_UP]: circle_y -= player_speed * dt
    if keys[pygame.K_DOWN]: circle_y += player_speed * dt

    # --- 가시 생성 로직 ---
    spawn_timer += dt
    if spawn_timer > 0.5:  # 0.5초마다 하나씩 생성
        # 오른쪽 화면 밖에서 생성되어 왼쪽으로 날아옴
        new_spike = {
            "x": 850, 
            "y": random.randint(0, 600) # 높이는 무작위
        }
        spikes.append(new_spike)
        spawn_timer = 0

    # --- 가시 이동 및 관리 ---
    for spike in spikes[:]: # 리스트 복사본으로 반복 (삭제 시 오류 방지)
        spike["x"] -= spike_speed * dt # 왼쪽으로 이동
        
        # 화면 왼쪽 끝으로 사라진 가시는 리스트에서 삭제
        if spike["x"] < -50:
            spikes.remove(spike)

    # --- 화면 그리기 ---
    screen.fill(WHITE)
    
    # 플레이어 그리기
    pygame.draw.circle(screen, BLUE, (int(circle_x), int(circle_y)), player_radius)

    # 모든 가시 그리기
    for spike in spikes:
        # 가시를 빨간색 작은 원으로 표현 (삼각형 등으로 바꿀 수 있음)
        pygame.draw.circle(screen, RED, (int(spike["x"]), int(spike["y"])), spike_radius)

    # FPS 출력
    fps_text = font.render(f"FPS: {int(clock.get_fps())} | Spikes: {len(spikes)}", True, BLACK)
    screen.blit(fps_text, (10, 10))

    pygame.display.flip()

pygame.quit()
sys.exit()
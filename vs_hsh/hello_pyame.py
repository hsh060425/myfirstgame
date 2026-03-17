import pygame
import sys
import random
import math

pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Spikes Game - Game Over!")

WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)

font = pygame.font.SysFont(None, 30)
# 게임오버용 큰 폰트
large_font = pygame.font.SysFont(None, 80)

player_x, player_y = 400.0, 300.0
player_speed = 350 
player_radius = 20 

spikes = []
spike_speed = 300
spike_radius = 10
spawn_timer = 0

# --- 게임 상태 변수 ---
game_over = False

clock = pygame.time.Clock()
running = True

while running:
    dt = clock.tick(60) / 1000.0

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        # 게임 오버 상태에서 R키를 누르면 재시작
        if game_over and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                game_over = False
                player_x, player_y = 400.0, 300.0
                spikes = []
                spawn_timer = 0

    # --- 게임이 실행 중일 때만 로직 계산 ---
    if not game_over:
        # 플레이어 이동
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]: player_x -= player_speed * dt
        if keys[pygame.K_RIGHT]: player_x += player_speed * dt
        if keys[pygame.K_UP]: player_y -= player_speed * dt
        if keys[pygame.K_DOWN]: player_y += player_speed * dt

        # 가시 생성
        spawn_timer += dt
        if spawn_timer > 0.4:
            side = random.randint(0, 3)
            if side == 0: sx, sy = random.randint(0, 800), -20
            elif side == 1: sx, sy = random.randint(0, 800), 620
            elif side == 2: sx, sy = -20, random.randint(0, 600)
            else: sx, sy = 820, random.randint(0, 600)

            dx = player_x - sx
            dy = player_y - sy
            dist = math.hypot(dx, dy)
            if dist != 0:
                vx = (dx / dist) * spike_speed
                vy = (dy / dist) * spike_speed
            else: vx, vy = 0, 0

            spikes.append({"x": sx, "y": sy, "vx": vx, "vy": vy})
            spawn_timer = 0

        # 가시 이동 및 충돌 체크
        for spike in spikes[:]:
            spike["x"] += spike["vx"] * dt
            spike["y"] += spike["vy"] * dt
            
            # --- 충돌 체크 로직 ---
            # 플레이어와 가시 사이의 거리를 구함
            distance = math.hypot(player_x - spike["x"], player_y - spike["y"])
            # 거리가 두 반지름의 합보다 작으면 충돌!
            if distance < (player_radius + spike_radius):
                game_over = True

            if spike["x"] < -150 or spike["x"] > 950 or spike["y"] < -150 or spike["y"] > 750:
                spikes.remove(spike)

    # --- 그리기 ---
    screen.fill(WHITE)
    
    # 플레이어와 가시 그리기
    pygame.draw.circle(screen, BLUE, (int(player_x), int(player_y)), player_radius)
    for spike in spikes:
        pygame.draw.circle(screen, RED, (int(spike["x"]), int(spike["y"])), spike_radius)

    # 게임 오버 메시지 표시
    if game_over:
        over_text = large_font.render("GAME OVER", True, BLACK)
        retry_text = font.render("Press 'R' to Restart", True, BLACK)
        # 화면 중앙에 배치
        screen.blit(over_text, (230, 250))
        screen.blit(retry_text, (300, 330))

    # 정보 출력
    fps_text = font.render(f"FPS: {int(clock.get_fps())}", True, BLACK)
    screen.blit(fps_text, (10, 10))

    pygame.display.flip()

pygame.quit()
sys.exit()
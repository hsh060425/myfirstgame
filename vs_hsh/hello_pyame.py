import pygame
import sys
import random
import math

pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Spiky Survival - Growing Difficulty")

WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GOLD = (218, 165, 32)

font = pygame.font.SysFont(None, 30)
large_font = pygame.font.SysFont(None, 80)

player_x, player_y = 400.0, 300.0
player_speed = 350 
player_radius = 20 

# 가시 초기 설정
spikes = []
base_spike_speed = 250    # 시작 속도
base_spawn_interval = 0.6 # 시작 생성 간격
spike_radius = 12         # 삼각형의 크기(중심에서 꼭짓점까지 거리)
spawn_timer = 0

survival_time = 0.0
high_score = 0.0 
game_over = False

clock = pygame.time.Clock()
running = True

while running:
    dt = clock.tick(60) / 1000.0

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if game_over and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                game_over, player_x, player_y = False, 400.0, 300.0
                spikes, spawn_timer, survival_time = [], 0, 0.0

    if not game_over:
        survival_time += dt

        # --- 실시간 난이도 조절 ---
        # 1초당 속도가 10씩 증가
        current_spike_speed = base_spike_speed + (survival_time * 10)
        # 1초당 생성 간격이 0.01초씩 짧아짐 (최소 0.1초 제한)
        current_spawn_interval = max(0.1, base_spawn_interval - (survival_time * 0.01))

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]: player_x -= player_speed * dt
        if keys[pygame.K_RIGHT]: player_x += player_speed * dt
        if keys[pygame.K_UP]: player_y -= player_speed * dt
        if keys[pygame.K_DOWN]: player_y += player_speed * dt

        # 가시 생성
        spawn_timer += dt
        if spawn_timer > current_spawn_interval:
            side = random.randint(0, 3)
            if side == 0: sx, sy = random.randint(0, 800), -30
            elif side == 1: sx, sy = random.randint(0, 800), 630
            elif side == 2: sx, sy = -30, random.randint(0, 600)
            else: sx, sy = 830, random.randint(0, 600)

            dx = player_x - sx
            dy = player_y - sy
            dist = math.hypot(dx, dy)
            
            if dist != 0:
                # 현재 난이도가 반영된 속도 적용
                vx = (dx / dist) * current_spike_speed
                vy = (dy / dist) * current_spike_speed
                # 가시가 날아가는 각도 계산 (라디안)
                angle = math.atan2(vy, vx)
            else:
                vx, vy, angle = 0, 0, 0

            spikes.append({"x": sx, "y": sy, "vx": vx, "vy": vy, "angle": angle})
            spawn_timer = 0

        # 가시 이동 및 충돌 체크
        for spike in spikes[:]:
            spike["x"] += spike["vx"] * dt
            spike["y"] += spike["vy"] * dt
            
            # 원형 충돌 판정 (삼각형이어도 원형 판정이 가장 효율적이고 자연스럽습니다)
            distance = math.hypot(player_x - spike["x"], player_y - spike["y"])
            if distance < (player_radius + (spike_radius * 0.7)): # 판정을 살짝 너그럽게 조정
                game_over = True
                if survival_time > high_score: high_score = survival_time

            if spike["x"] < -200 or spike["x"] > 1000 or spike["y"] < -200 or spike["y"] > 800:
                spikes.remove(spike)

    # --- 그리기 ---
    screen.fill(WHITE)
    
    # 플레이어
    pygame.draw.circle(screen, BLUE, (int(player_x), int(player_y)), player_radius)

    # 삼각형 가시 그리기
    for spike in spikes:
        # 가시가 날아가는 방향(angle)을 기준으로 삼각형의 세 꼭짓점 계산
        # 1. 앞쪽 꼭짓점 (진행 방향)
        p1 = (spike["x"] + math.cos(spike["angle"]) * spike_radius,
              spike["y"] + math.sin(spike["angle"]) * spike_radius)
        # 2. 뒤쪽 왼쪽 꼭짓점
        p2 = (spike["x"] + math.cos(spike["angle"] + 2.5) * spike_radius,
              spike["y"] + math.sin(spike["angle"] + 2.5) * spike_radius)
        # 3. 뒤쪽 오른쪽 꼭짓점
        p3 = (spike["x"] + math.cos(spike["angle"] - 2.5) * spike_radius,
              spike["y"] + math.sin(spike["angle"] - 2.5) * spike_radius)
        
        pygame.draw.polygon(screen, RED, [p1, p2, p3])

    # UI 정보
    screen.blit(font.render(f"Time: {survival_time:.2f}s", True, BLACK), (10, 10))
    screen.blit(font.render(f"Best: {high_score:.2f}s", True, GOLD), (10, 40))
    screen.blit(font.render(f"Speed: {int(current_spike_speed)}", True, BLACK), (10, 70))
    screen.blit(font.render(f"Interval: {current_spawn_interval:.2f}s", True, BLACK), (10, 100))

    if game_over:
        screen.blit(large_font.render("GAME OVER", True, BLACK), (230, 200))
        screen.blit(font.render(f"Final Record: {survival_time:.2f}s", True, RED), (315, 300))
        screen.blit(font.render("Press 'R' to Restart", True, BLACK), (310, 350))

    pygame.display.flip()

pygame.quit()
sys.exit()
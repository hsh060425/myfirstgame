import pygame
import sys
import random
import math

pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Spikes Game - High Score")

WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GOLD = (218, 165, 32) # 최고 기록용 황금색 추가

font = pygame.font.SysFont(None, 30)
large_font = pygame.font.SysFont(None, 80)

player_x, player_y = 400.0, 300.0
player_speed = 350 
player_radius = 20 

spikes = []
spike_speed = 300
spike_radius = 10
spawn_timer = 0

survival_time = 0.0
# --- 최고 기록 변수 추가 ---
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
                game_over = False
                player_x, player_y = 400.0, 300.0
                spikes = []
                spawn_timer = 0
                survival_time = 0.0

    if not game_over:
        survival_time += dt

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]: player_x -= player_speed * dt
        if keys[pygame.K_RIGHT]: player_x += player_speed * dt
        if keys[pygame.K_UP]: player_y -= player_speed * dt
        if keys[pygame.K_DOWN]: player_y += player_speed * dt

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

        for spike in spikes[:]:
            spike["x"] += spike["vx"] * dt
            spike["y"] += spike["vy"] * dt
            
            distance = math.hypot(player_x - spike["x"], player_y - spike["y"])
            if distance < (player_radius + spike_radius):
                game_over = True
                # --- 게임 오버 시 최고 기록 업데이트 ---
                if survival_time > high_score:
                    high_score = survival_time

            if spike["x"] < -150 or spike["x"] > 950 or spike["y"] < -150 or spike["y"] > 750:
                spikes.remove(spike)

    # --- 그리기 ---
    screen.fill(WHITE)
    
    pygame.draw.circle(screen, BLUE, (int(player_x), int(player_y)), player_radius)
    for spike in spikes:
        pygame.draw.circle(screen, RED, (int(spike["x"]), int(spike["y"])), spike_radius)

    # UI 정보 출력
    time_text = font.render(f"Time: {survival_time:.2f}s", True, BLACK)
    # 화면 상단에 최고 기록 표시
    high_score_text = font.render(f"Best: {high_score:.2f}s", True, GOLD)
    spike_count_text = font.render(f"Spikes: {len(spikes)}", True, BLACK)

    screen.blit(time_text, (10, 10))
    screen.blit(high_score_text, (10, 40)) # 시간 아래에 최고 기록 표시
    screen.blit(spike_count_text, (10, 70))

    if game_over:
        over_text = large_font.render("GAME OVER", True, BLACK)
        final_score_text = font.render(f"Final Time: {survival_time:.2f}s", True, RED)
        # 최고 기록 달성 여부에 따른 메시지
        if survival_time >= high_score and survival_time > 0:
            best_msg = "NEW BEST SCORE!"
            best_color = GOLD
        else:
            best_msg = f"Best Record: {high_score:.2f}s"
            best_color = BLACK
            
        record_text = font.render(best_msg, True, best_color)
        retry_text = font.render("Press 'R' to Restart", True, BLACK)
        
        screen.blit(over_text, (230, 200))
        screen.blit(final_score_text, (330, 280))
        screen.blit(record_text, (315, 320))
        screen.blit(retry_text, (300, 380))

    pygame.display.flip()

pygame.quit()
sys.exit()
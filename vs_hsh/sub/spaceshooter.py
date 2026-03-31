import pygame
import random
import sys

pygame.init()

# --- 설정 및 상수 ---
WIDTH, HEIGHT = 800, 600
FPS = 60

WHITE   = (255, 255, 255)
BLACK   = (0,   0,   0)
GRAY    = (20,  20,  40)
BLUE    = (50,  150, 255)
RED     = (220, 50,  50)
YELLOW  = (240, 220, 0)
GREEN   = (50,  220, 80)
ORANGE  = (255, 165, 0)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Space Shooter - Infinite Scaling")
clock = pygame.time.Clock()

def get_korean_font(size):
    candidates = ["malgungothic", "applegothic", "nanumgothic", "notosanscjk"]
    for name in candidates:
        font = pygame.font.SysFont(name, size)
        if font.get_ascent() > 0: return font
    return pygame.font.SysFont(None, size)

font = get_korean_font(25)
font_big = get_korean_font(70)

PLAYER_W, PLAYER_H = 40, 40
ENEMY_W,  ENEMY_H  = 40, 40
BULLET_W, BULLET_H = 6,  14
MAX_HP = 100

# --- 난이도 계산 함수 (시간 기준) ---
def get_difficulty(elapsed_seconds):
    # 1. 이동 속도: 2.0에서 시작, 15초당 0.5씩 증가 (최대 8.0)
    speed = min(12.0, 2.0 + (elapsed_seconds / 15))
    
    # 2. 생성 간격: 60프레임에서 시작, 점차 단축 (최소 6프레임)
    spawn_delay = max(6, 60 - (elapsed_seconds / 3))
    
    # 3. 적 체력: 1에서 시작, 20초마다 1씩 증가
    enemy_hp = 1 + (elapsed_seconds / 20)
    
    # 4. 적 충돌 데미지: 15에서 시작, 30초마다 5씩 증가
    collision_damage = 15 + (elapsed_seconds / 30) * 5
    
    return speed, spawn_delay, enemy_hp, collision_damage

# --- 그리기 함수들 ---
def draw_player(surf, rect):
    cx = rect.centerx
    pygame.draw.polygon(surf, BLUE, [
        (cx, rect.top), (rect.left, rect.bottom),
        (cx, rect.bottom - 8), (rect.right, rect.bottom),
    ])
    pygame.draw.rect(surf, YELLOW, (cx - 4, rect.bottom - 10, 8, 10))

def draw_enemy(surf, enemy_obj):
    rect = enemy_obj['rect']
    hp_ratio = enemy_obj['hp'] / enemy_obj['max_hp']
    
    # 적의 강함에 따라 색상 변경
    color = (max(50, 255 - (enemy_obj['max_hp'] * 20)), 50, 50)
    pygame.draw.rect(surf, color, rect, border_radius=5)
    
    # 적 체력 바 (머리 위)
    if enemy_obj['max_hp'] > 1:
        bar_w = rect.width
        pygame.draw.rect(surf, RED, (rect.x, rect.y - 10, bar_w, 4))
        pygame.draw.rect(surf, GREEN, (rect.x, rect.y - 10, bar_w * hp_ratio, 4))

def draw_hud(score, hp, elapsed_seconds, e_hp, e_dmg):
    screen.blit(font.render(f"Score: {score}", True, WHITE), (20, 20))
    screen.blit(font.render(f"Time: {elapsed_seconds}s", True, ORANGE), (20, 50))
    
    # 플레이어 HP 바
    bar_width = 200
    pygame.draw.rect(screen, (100, 0, 0), (WIDTH - bar_width - 20, 25, bar_width, 20))
    hp_width = max(0, (hp / MAX_HP) * bar_width)
    pygame.draw.rect(screen, GREEN, (WIDTH - bar_width - 20, 25, hp_width, 20))
    
    # 적 스펙 정보
    spec_txt = font.render(f"Enemy [HP: {int(e_hp)} | DMG: {int(e_dmg)}]", True, (150, 150, 150))
    screen.blit(spec_txt, (WIDTH // 2 - spec_txt.get_width() // 2, 20))

def game_over_screen(score, elapsed_seconds):
    screen.fill((10, 10, 30))
    msg = font_big.render("GAME OVER", True, RED)
    screen.blit(msg, (WIDTH//2 - msg.get_width()//2, 180))
    
    res = font.render(f"Survived: {elapsed_seconds}s | Score: {score}", True, WHITE)
    screen.blit(res, (WIDTH//2 - res.get_width()//2, 280))
    
    retry = font.render("Press 'R' to Restart or 'Q' to Quit", True, YELLOW)
    screen.blit(retry, (WIDTH//2 - retry.get_width()//2, 350))
    
    pygame.display.flip()
    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT: pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_r: return True
                if e.key == pygame.K_q: pygame.quit(); sys.exit()

# --- 메인 게임 루프 ---
def main():
    player = pygame.Rect(WIDTH//2 - 20, HEIGHT-70, PLAYER_W, PLAYER_H)
    hp = MAX_HP
    score = 0
    bullets = []
    enemies = []
    spawn_timer = 0
    invincible = 0
    shoot_cd = 0
    
    start_ticks = pygame.time.get_ticks()
    stars = [[random.randint(0, WIDTH), random.randint(0, HEIGHT), random.randint(1, 2)] for _ in range(60)]

    while True:
        clock.tick(FPS)
        elapsed_seconds = (pygame.time.get_ticks() - start_ticks) // 1000
        cur_speed, cur_spawn_delay, cur_e_hp, cur_e_dmg = get_difficulty(elapsed_seconds)

        for e in pygame.event.get():
            if e.type == pygame.QUIT: pygame.quit(); sys.exit()

        # 조작
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] and player.left > 0: player.x -= 6
        if keys[pygame.K_RIGHT] and player.right < WIDTH: player.x += 6
        if keys[pygame.K_UP] and player.top > 0: player.y -= 6
        if keys[pygame.K_DOWN] and player.bottom < HEIGHT: player.y += 6

        # 발사
        shoot_cd -= 1
        if keys[pygame.K_SPACE] and shoot_cd <= 0:
            bullets.append(pygame.Rect(player.centerx - BULLET_W//2, player.top, BULLET_W, BULLET_H))
            shoot_cd = 12

        # 이동
        for b in bullets[:]:
            b.y -= 10
            if b.bottom < 0: bullets.remove(b)

        spawn_timer += 1
        if spawn_timer >= cur_spawn_delay:
            spawn_timer = 0
            enemies.append({
                'rect': pygame.Rect(random.randint(0, WIDTH-ENEMY_W), -ENEMY_H, ENEMY_W, ENEMY_H),
                'hp': cur_e_hp, 'max_hp': cur_e_hp, 'dmg': cur_e_dmg
            })

        for en in enemies[:]:
            en['rect'].y += cur_speed
            if en['rect'].top > HEIGHT: enemies.remove(en)

        # 충돌: 총알 vs 적
        for b in bullets[:]:
            for en in enemies[:]:
                if b.colliderect(en['rect']):
                    if b in bullets: bullets.remove(b)
                    en['hp'] -= 1
                    if en['hp'] <= 0:
                        if en in enemies: enemies.remove(en)
                        score += 10 + (en['max_hp'] * 2)
                    break

        # 충돌: 플레이어 vs 적
        if invincible > 0:
            invincible -= 1
        else:
            for en in enemies[:]:
                if player.colliderect(en['rect']):
                    hp -= en['dmg']
                    invincible = 60
                    enemies.remove(en)
                    if hp <= 0:
                        if game_over_screen(score, elapsed_seconds):
                            main() # 재시작
                        return

        # 그리기
        screen.fill(GRAY)
        for s in stars:
            s[1] += 1
            if s[1] > HEIGHT: s[1] = 0; s[0] = random.randint(0, WIDTH)
            pygame.draw.circle(screen, WHITE, (s[0], s[1]), s[2])

        for b in bullets: pygame.draw.rect(screen, YELLOW, b)
        for en in enemies: draw_enemy(screen, en)
        
        if (invincible // 5) % 2 == 0:
            draw_player(screen, player)
            
        draw_hud(score, hp, elapsed_seconds, cur_e_hp, cur_e_dmg)
        pygame.display.flip()

if __name__ == "__main__":
    main()
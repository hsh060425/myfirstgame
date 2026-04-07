import pygame
import random
import sys
import os

pygame.init()
pygame.mixer.init() # 사운드 재생을 위한 초기화

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
PURPLE  = (160, 32, 240)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Space Shooter - Image & Sound")
clock = pygame.time.Clock()

# --- 리소스 로드 함수 ---
PLAYER_W, PLAYER_H = 45, 45
BULLET_W, BULLET_H = 15, 30 # 총알 이미지 크기에 맞게 조정

def load_image(file_name, width, height):
    try:
        img = pygame.image.load(file_name).convert_alpha()
        return pygame.transform.scale(img, (width, height))
    except:
        print(f"파일 '{file_name}'을 찾을 수 없습니다.")
        return None

def load_sound(file_name):
    try:
        return pygame.mixer.Sound(file_name)
    except:
        print(f"사운드 '{file_name}'을 찾을 수 없습니다.")
        return None

# 리소스 불러오기
PLAYER_IMAGE = load_image("./assets/images/player.png", PLAYER_W, PLAYER_H)
BULLET_IMAGE = load_image("./assets/images/lazer.png", BULLET_W, BULLET_H)
SHOOT_SOUND  = load_sound("./assets/sounds/lazer.wav")

if SHOOT_SOUND:
    SHOOT_SOUND.set_volume(0.3) # 소리 크기 조절 (0.0 ~ 1.0)

# --- 폰트 설정 ---
def get_korean_font(size):
    candidates = ["malgungothic", "applegothic", "nanumgothic", "notosanscjk"]
    for name in candidates:
        font = pygame.font.SysFont(name, size)
        if font.get_ascent() > 0: return font
    return pygame.font.SysFont(None, size)

font_small = get_korean_font(18)
font = get_korean_font(25)
font_big = get_korean_font(70)

# --- 상수 ---
ENEMY_W,  ENEMY_H  = 40, 40
ITEM_SIZE = 20
MAX_HP = 100

# --- 난이도 계산 ---
def get_difficulty(elapsed_seconds):
    speed = min(12.0, 2.0 + (elapsed_seconds / 15))
    spawn_delay = max(6, 60 - (elapsed_seconds / 3))
    enemy_hp = 1 + (elapsed_seconds / 20)
    collision_damage = 15 + (elapsed_seconds / 30) * 5
    return speed, spawn_delay, enemy_hp, collision_damage

# --- 그리기 함수들 ---
def draw_player(surf, rect):
    if PLAYER_IMAGE:
        surf.blit(PLAYER_IMAGE, rect.topleft)
    else:
        cx = rect.centerx
        pygame.draw.polygon(surf, BLUE, [(cx, rect.top), (rect.left, rect.bottom), (cx, rect.bottom - 8), (rect.right, rect.bottom)])

def draw_bullet(surf, b_obj):
    if BULLET_IMAGE:
        # 이미지의 중심을 맞추기 위해 보정하여 출력
        surf.blit(BULLET_IMAGE, b_obj['rect'].topleft)
    else:
        pygame.draw.rect(surf, YELLOW, b_obj['rect'])

def draw_enemy(surf, enemy_obj):
    rect = enemy_obj['rect']
    hp_ratio = enemy_obj['hp'] / enemy_obj['max_hp']
    color = (max(50, 255 - (int(enemy_obj['max_hp']) * 20)), 50, 50)
    pygame.draw.rect(surf, color, rect, border_radius=5)
    if enemy_obj['max_hp'] > 1:
        pygame.draw.rect(surf, RED, (rect.x, rect.y - 10, rect.width, 4))
        pygame.draw.rect(surf, GREEN, (rect.x, rect.y - 10, rect.width * hp_ratio, 4))

def draw_hud(score, hp, elapsed_seconds, e_hp, e_dmg, p_dmg, p_fire_rate, p_move):
    screen.blit(font.render(f"Score: {score}", True, WHITE), (20, 20))
    screen.blit(font.render(f"Time: {elapsed_seconds}s", True, ORANGE), (20, 50))
    
    bar_width = 200
    pygame.draw.rect(screen, (100, 0, 0), (WIDTH - bar_width - 20, 25, bar_width, 20))
    pygame.draw.rect(screen, GREEN, (WIDTH - bar_width - 20, 25, max(0, (hp / MAX_HP) * bar_width), 20))

    stats_y = HEIGHT - 100
    screen.blit(font_small.render(f"STR (공격력): {p_dmg}", True, RED), (20, stats_y))
    screen.blit(font_small.render(f"AGI (연사력): {int(20 - p_fire_rate)}", True, YELLOW), (20, stats_y + 25))
    screen.blit(font_small.render(f"SPD (이동속도): {p_move}", True, BLUE), (20, stats_y + 50))

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
    player = pygame.Rect(WIDTH//2 - PLAYER_W//2, HEIGHT-70, PLAYER_W, PLAYER_H)
    hp = MAX_HP
    score = 0
    
    p_dmg = 1
    p_fire_rate = 10
    p_move = 6
    
    bullets = []
    enemies = []
    items = []
    
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

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] and player.left > 0: player.x -= p_move
        if keys[pygame.K_RIGHT] and player.right < WIDTH: player.x += p_move
        if keys[pygame.K_UP] and player.top > 0: player.y -= p_move
        if keys[pygame.K_DOWN] and player.bottom < HEIGHT: player.y += p_move

        # --- 발사 및 사운드 재생 ---
        shoot_cd -= 1
        if keys[pygame.K_SPACE] and shoot_cd <= 0:
            bullets.append({'rect': pygame.Rect(player.centerx - BULLET_W//2, player.top - BULLET_H, BULLET_W, BULLET_H), 'dmg': p_dmg})
            shoot_cd = p_fire_rate
            if SHOOT_SOUND:
                SHOOT_SOUND.play()

        for b in bullets[:]:
            b['rect'].y -= 12 # 총알 속도
            if b['rect'].bottom < 0: bullets.remove(b)

        spawn_timer += 1
        if spawn_timer >= cur_spawn_delay:
            spawn_timer = 0
            enemies.append({'rect': pygame.Rect(random.randint(0, WIDTH-ENEMY_W), -ENEMY_H, ENEMY_W, ENEMY_H),
                            'hp': cur_e_hp, 'max_hp': cur_e_hp, 'dmg': cur_e_dmg})

        for en in enemies[:]:
            en['rect'].y += cur_speed
            if en['rect'].top > HEIGHT: enemies.remove(en)

        for it in items[:]:
            it['rect'].y += 3
            if it['rect'].colliderect(player):
                if it['type'] == 'dmg': p_dmg += 1
                elif it['type'] == 'spd': p_fire_rate = max(4, p_fire_rate - 1)
                elif it['type'] == 'move': p_move = min(12, p_move + 0.5)
                elif it['type'] == 'heal': hp = min(MAX_HP, hp + 20)
                items.remove(it)
            elif it['rect'].top > HEIGHT:
                items.remove(it)

        for b in bullets[:]:
            for en in enemies[:]:
                if b['rect'].colliderect(en['rect']):
                    if b in bullets: bullets.remove(b)
                    en['hp'] -= b['dmg']
                    if en['hp'] <= 0:
                        if random.random() < 0.2:
                            itype = random.choice(['dmg', 'spd', 'move', 'heal'])
                            icolor = {'dmg': RED, 'spd': YELLOW, 'move': BLUE, 'heal': GREEN}[itype]
                            items.append({'rect': pygame.Rect(en['rect'].centerx, en['rect'].centery, ITEM_SIZE, ITEM_SIZE),
                                          'type': itype, 'color': icolor})
                        if en in enemies: enemies.remove(en)
                        score += 10 + (int(en['max_hp']) * 2)
                    break

        if invincible > 0: invincible -= 1
        else:
            for en in enemies[:]:
                if player.colliderect(en['rect']):
                    hp -= en['dmg']
                    invincible = 60
                    enemies.remove(en)
                    if hp <= 0:
                        if game_over_screen(score, elapsed_seconds): main()
                        return

        # --- 그리기 ---
        screen.fill(GRAY)
        for s in stars:
            s[1] += 1
            if s[1] > HEIGHT: s[1] = 0; s[0] = random.randint(0, WIDTH)
            pygame.draw.circle(screen, WHITE, (s[0], s[1]), s[2])

        for b in bullets: draw_bullet(screen, b)
        for en in enemies: draw_enemy(screen, en)
        
        for it in items:
            pygame.draw.circle(screen, it['color'], it['rect'].center, ITEM_SIZE // 2)
            label = it['type'][0].upper() if it['type'] != 'heal' else 'H'
            txt = font_small.render(label, True, BLACK)
            screen.blit(txt, (it['rect'].x + 5, it['rect'].y))
        
        if (invincible // 5) % 2 == 0: 
            draw_player(screen, player)
            
        draw_hud(score, hp, elapsed_seconds, cur_e_hp, cur_e_dmg, p_dmg, p_fire_rate, p_move)
        pygame.display.flip()

if __name__ == "__main__":
    main()
import pygame
import random
import sys
import os
import math

pygame.init()
pygame.mixer.init()

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
pygame.display.set_caption("Space Shooter - Drone System")
clock = pygame.time.Clock()

# --- 리소스 로드 함수 ---
PLAYER_W, PLAYER_H = 45, 45
BULLET_W, BULLET_H = 15, 30
DRONE_W, DRONE_H = 22, 22
BOSS_W, BOSS_H = 120, 100

def load_image(file_name, width, height):
    try:
        if not os.path.exists(file_name):
            print(f"파일을 찾을 수 없습니다: {file_name}")
            return None
        img = pygame.image.load(file_name).convert_alpha()
        print(f"파일을 찾았다: {file_name}")
        return pygame.transform.scale(img, (width, height))
    except Exception as e:
        print(f"이미지 로드 에러 ({file_name}): {e}")
        return None

def load_sound(file_name):
    try: return pygame.mixer.Sound(file_name)
    except: return None

# os.chdir(os.path.dirname(os.path.abspath(__file__)))
# print(os.getcwd())
# 이미지 및 사운드 로드
PLAYER_IMAGE = load_image("./assets/images/player.png", PLAYER_W, PLAYER_H)
BULLET_IMAGE = load_image("./assets/images/lazer.png", BULLET_W, BULLET_H)
BOSS_IMAGE   = load_image("./assets/images/boss.png", BOSS_W, BOSS_H)
SHOOT_SOUND  = load_sound("./assets/sounds/lazer.wav")
if SHOOT_SOUND: SHOOT_SOUND.set_volume(0.1)

# 배경 음악 추가
try:
    pygame.mixer.music.load("./assets/sounds/bgm.mp3")
    pygame.mixer.music.set_volume(0.3)
    pygame.mixer.music.play(-1)
except Exception as e:
    print(f"BGM 로드 에러: {e}")

# --- 폰트 설정 ---
def get_korean_font(size):
    candidates = ["malgungothic", "applegothic", "nanumgothic", "notosanscjk", "consolas"]
    for name in candidates:
        font = pygame.font.SysFont(name, size)
        if font.get_ascent() > 0: return font
    return pygame.font.SysFont(None, size)

font_small = get_korean_font(16)
font = get_korean_font(25)
font_big = get_korean_font(70)

ENEMY_W, ENEMY_H = 40, 40
ITEM_SIZE = 20
MAX_HP = 100

def get_difficulty(elapsed_seconds):
    # 시간이 지날수록 적 스피드와 체력 증가
    speed = min(15.0, 2.0 + (elapsed_seconds / 10))
    spawn_delay = max(5, 60 - (elapsed_seconds / 2))
    enemy_hp = 1 + (elapsed_seconds / 15)
    return speed, spawn_delay, enemy_hp

# --- 그리기 함수들 ---
def draw_player(surf, rect):
    if PLAYER_IMAGE: surf.blit(PLAYER_IMAGE, rect.topleft)
    else: pygame.draw.polygon(surf, BLUE, [(rect.centerx, rect.top), (rect.left, rect.bottom), (rect.right, rect.bottom)])

def draw_drone(surf, rect):
    pygame.draw.circle(surf, PURPLE, rect.center, DRONE_W // 2)
    pygame.draw.circle(surf, WHITE, (rect.centerx - 4, rect.centery - 4), 3) # 광택
    pygame.draw.circle(surf, WHITE, rect.center, DRONE_W // 2, 2)

def draw_enemy(surf, enemy_obj):
    rect = enemy_obj['rect']
    hp_ratio = enemy_obj['hp'] / enemy_obj['max_hp']
    # 체력이 높을수록 더 붉은색
    color_val = max(50, 255 - int(enemy_obj['max_hp'] * 10))
    color = (255, color_val, color_val) if enemy_obj.get('is_boss') else (color_val, 50, 50)
    
    if enemy_obj.get('is_boss') and BOSS_IMAGE:
        surf.blit(BOSS_IMAGE, rect.topleft)
    else:
        pygame.draw.rect(surf, color, rect, border_radius=5)
        
    if enemy_obj['max_hp'] > 1:
        pygame.draw.rect(surf, RED, (rect.x, rect.y - 10, rect.width, 4))
        pygame.draw.rect(surf, GREEN, (rect.x, rect.y - 10, rect.width * hp_ratio, 4))

def draw_hud(score, hp, drone_count, drone_spread, stats, boss_timer):
    screen.blit(font.render(f"Score: {score}", True, WHITE), (20, 20))
    screen.blit(font_small.render(f"Drones: {drone_count} | Spread: {int(drone_spread)}", True, PURPLE), (20, 50))
    
    # 보스 타이머 표시
    boss_txt = f"Next Boss: {max(0, int(boss_timer))}s"
    screen.blit(font.render(boss_txt, True, RED), (WIDTH // 2 - 60, 20))

    # 먹은 스텟 표시
    stat_txt = f"DMG:{stats['dmg']} SPD:{stats['spd']} MOV:{stats['move']} HEAL:{stats['heal']} DRN:{stats['drone']}"
    screen.blit(font_small.render(stat_txt, True, YELLOW), (20, 80))

    cheat_txt = "[F1-F4:Cheats] [Z/X:Drone Spread]"
    screen.blit(font_small.render(cheat_txt, True, (100, 255, 100)), (20, HEIGHT - 30))
    
    bar_width = 200
    pygame.draw.rect(screen, (100, 0, 0), (WIDTH - bar_width - 20, 25, bar_width, 20))
    pygame.draw.rect(screen, GREEN, (WIDTH - bar_width - 20, 25, max(0, (hp / MAX_HP) * bar_width), 20))

# --- 메인 루프 ---
def main():
    player = pygame.Rect(WIDTH//2 - PLAYER_W//2, HEIGHT-70, PLAYER_W, PLAYER_H)
    hp = MAX_HP
    score = 0
    p_dmg = 1
    p_fire_rate = 15
    p_move = 6

    # 스텟 추적
    stats = {'dmg': 0, 'spd': 0, 'move': 0, 'heal': 0, 'drone': 0}

    drones = []
    drone_spread = 60

    bullets = []
    enemies = []
    items = []

    spawn_timer = 0
    boss_spawn_interval = 30 # 30초마다 보스
    boss_timer = boss_spawn_interval
    invincible = 0
    shoot_cd = 0

    start_ticks = pygame.time.get_ticks()
    stars = [[random.randint(0, WIDTH), random.randint(0, HEIGHT), random.randint(1, 2)] for _ in range(60)]

    while True:
        dt = clock.tick(FPS) / 1000.0
        elapsed_seconds = (pygame.time.get_ticks() - start_ticks) // 1000
        cur_speed, cur_spawn_delay, cur_e_hp = get_difficulty(elapsed_seconds)
        
        boss_timer -= dt
        if boss_timer <= 0:
            boss_timer = boss_spawn_interval
            # 보스 스폰
            enemies.append({
                'rect': pygame.Rect(WIDTH//2 - BOSS_W//2, -BOSS_H, BOSS_W, BOSS_H),
                'hp': cur_e_hp * 50, 'max_hp': cur_e_hp * 50, 'is_boss': True,
                'vx': 2, 'vy': 1
            })

        for e in pygame.event.get():
            if e.type == pygame.QUIT: pygame.quit(); sys.exit()
            
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_F1:
                    itype = random.choice(['dmg', 'spd', 'move', 'heal'])
                    icolor = {'dmg': RED, 'spd': YELLOW, 'move': BLUE, 'heal': GREEN}[itype]
                    items.append({'rect': pygame.Rect(player.centerx, player.centery - 100, ITEM_SIZE, ITEM_SIZE),
                                  'type': itype, 'color': icolor})
                if e.key == pygame.K_F2:
                    items.append({'rect': pygame.Rect(player.centerx, player.centery - 100, ITEM_SIZE, ITEM_SIZE),
                                  'type': 'drone', 'color': PURPLE})
                if e.key == pygame.K_F3:
                    drones.append({'rect': pygame.Rect(0, 0, DRONE_W, DRONE_H),
                                   'px': float(player.centerx), 'py': float(player.centery), 'shoot_cd': 30})
                if e.key == pygame.K_F4:
                    drones.clear()

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] and player.left > 0: player.x -= p_move
        if keys[pygame.K_RIGHT] and player.right < WIDTH: player.x += p_move
        if keys[pygame.K_UP] and player.top > 0: player.y -= p_move
        if keys[pygame.K_DOWN] and player.bottom < HEIGHT: player.y += p_move
        
        if keys[pygame.K_z]: drone_spread = max(10, drone_spread - 2)
        if keys[pygame.K_x]: drone_spread = min(300, drone_spread + 2)

        shoot_cd -= 1
        if keys[pygame.K_SPACE] and shoot_cd <= 0:
            bullets.append({'rect': pygame.Rect(player.centerx - BULLET_W//2, player.top - BULLET_H, BULLET_W, BULLET_H), 'dmg': p_dmg})
            shoot_cd = p_fire_rate
            if SHOOT_SOUND: SHOOT_SOUND.play()

        t = pygame.time.get_ticks() / 1000.0
        for i, dn in enumerate(drones):
            side = -1 if i % 2 == 0 else 1
            row = (i // 2) +1
            float_y = math.sin(t * 2.0 + i) * 12.0 + math.sin(t * 4.5 + i * 0.5) * 4.0
            float_x = math.cos(t * 1.5 + i) * 6.0
            target_x = player.centerx + side * (drone_spread * row) + float_x
            target_y = player.centery + (row * 15) + float_y
            dn['px'] += (target_x - dn['px']) * 0.08
            dn['py'] += (target_y - dn['py']) * 0.08
            dn['rect'].centerx, dn['rect'].centery = int(dn['px']), int(dn['py'])
            dn['shoot_cd'] -= 1
            if dn['shoot_cd'] <= 0:
                bullets.append({'rect': pygame.Rect(dn['rect'].centerx - BULLET_W//2, dn['rect'].top - BULLET_H, BULLET_W, BULLET_H), 'dmg': p_dmg})
                dn['shoot_cd'] = p_fire_rate * 2.5
                if SHOOT_SOUND: SHOOT_SOUND.play()

        # 총알 로직 (화면 밖으로 나가면 삭제)
        screen_rect = pygame.Rect(0, 0, WIDTH, HEIGHT)
        for b in bullets[:]:
            b['rect'].y -= 12
            if not screen_rect.colliderect(b['rect']):
                bullets.remove(b)

        # 적 스폰
        spawn_timer += 1
        if spawn_timer >= cur_spawn_delay:
            spawn_timer = 0
            enemies.append({'rect': pygame.Rect(random.randint(0, WIDTH-ENEMY_W), -ENEMY_H, ENEMY_W, ENEMY_H),
                            'hp': cur_e_hp, 'max_hp': cur_e_hp})

        # 적 이동
        for en in enemies[:]:
            if en.get('is_boss'):
                en['rect'].x += en['vx']
                en['rect'].y += en['vy']
                if en['rect'].left <= 0 or en['rect'].right >= WIDTH: en['vx'] *= -1
                if en['rect'].top <= 10 or en['rect'].bottom >= HEIGHT // 2: en['vy'] *= -1
            else:
                en['rect'].y += cur_speed
                if en['rect'].top > HEIGHT: enemies.remove(en)

        # 아이템 로직
        for it in items[:]:
            it['rect'].y += 3
            if it['rect'].colliderect(player):
                stats[it['type']] += 1
                if it['type'] == 'dmg': p_dmg += 1
                elif it['type'] == 'spd': p_fire_rate = max(4, p_fire_rate - 1)
                elif it['type'] == 'move': p_move = min(12, p_move + 0.5)
                elif it['type'] == 'heal': hp = min(MAX_HP, hp + 20)
                elif it['type'] == 'drone':
                    drones.append({'rect': pygame.Rect(0, 0, DRONE_W, DRONE_H),
                                   'px': float(player.centerx), 'py': float(player.centery), 'shoot_cd': 30})
                items.remove(it)
            elif it['rect'].top > HEIGHT: items.remove(it)

        # 충돌 검사
        for b in bullets[:]:
            for en in enemies[:]:
                if b['rect'].colliderect(en['rect']):
                    if b in bullets: bullets.remove(b)
                    en['hp'] -= b['dmg']
                    if en['hp'] <= 0:
                        # 아이템 드롭 확률 (보스는 100% 드론 아이템 드롭)
                        drop_chance = 1.0 if en.get('is_boss') else 0.25
                        if random.random() < drop_chance:
                            itype = 'drone' if en.get('is_boss') else random.choice(['dmg', 'spd', 'move', 'heal', 'drone'])
                            icolor = {'dmg': RED, 'spd': YELLOW, 'move': BLUE, 'heal': GREEN, 'drone': PURPLE}[itype]
                            items.append({'rect': pygame.Rect(en['rect'].centerx, en['rect'].centery, ITEM_SIZE, ITEM_SIZE),
                                          'type': itype, 'color': icolor})
                        if en in enemies: enemies.remove(en)
                        score += 500 if en.get('is_boss') else 10
                    break

        if invincible > 0: invincible -= 1
        else:
            for en in enemies[:]:
                if player.colliderect(en['rect']):
                    hp -= 20
                    invincible = 60
                    if not en.get('is_boss'): enemies.remove(en)
                    if hp <= 0: main()

        # --- 그리기 ---
        screen.fill(GRAY)
        for s in stars:
            s[1] += 1
            if s[1] > HEIGHT: s[1] = 0; s[0] = random.randint(0, WIDTH)
            pygame.draw.circle(screen, (70, 70, 100), (s[0], s[1]), s[2])

        for b in bullets:
            if BULLET_IMAGE: screen.blit(BULLET_IMAGE, b['rect'].topleft)
            else: pygame.draw.rect(screen, YELLOW, b['rect'])
            
        for en in enemies: draw_enemy(screen, en)
        for dn in drones: draw_drone(screen, dn['rect'])
        
        for it in items:
            pygame.draw.circle(screen, it['color'], it['rect'].center, ITEM_SIZE // 2)
            label = 'D' if it['type'] == 'drone' else it['type'][0].upper()
            screen.blit(font_small.render(label, True, BLACK), (it['rect'].x + 6, it['rect'].y + 2))
        
        if (invincible // 5) % 2 == 0: draw_player(screen, player)
        draw_hud(score, hp, len(drones), drone_spread, stats, boss_timer)
        pygame.display.flip()

if __name__ == "__main__":
    main()
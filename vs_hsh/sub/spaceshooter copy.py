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
DARK_PURPLE = (60, 0, 100)
GOLD    = (255, 200, 0)
PANEL   = (15, 15, 35)
PANEL2  = (25, 25, 55)
BORDER  = (80, 80, 160)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Space Shooter - Drone System")
clock = pygame.time.Clock()

PLAYER_W, PLAYER_H = 45, 45
BULLET_W, BULLET_H = 15, 30
DRONE_W, DRONE_H = 22, 22

def load_image(file_name, width, height):
    try:
        img = pygame.image.load(file_name).convert_alpha()
        return pygame.transform.scale(img, (width, height))
    except: return None

def load_sound(file_name):
    try: return pygame.mixer.Sound(file_name)
    except: return None

PLAYER_IMAGE = load_image("./assets/images/player.png", PLAYER_W, PLAYER_H)
BULLET_IMAGE = load_image("./assets/images/lazer.png", BULLET_W, BULLET_H)
SHOOT_SOUND  = load_sound("./assets/sounds/lazer.wav")
if SHOOT_SOUND: SHOOT_SOUND.set_volume(0.2)

def get_korean_font(size):
    candidates = ["malgungothic", "applegothic", "nanumgothic", "notosanscjk"]
    for name in candidates:
        font = pygame.font.SysFont(name, size)
        if font.get_ascent() > 0: return font
    return pygame.font.SysFont(None, size)

font_small = get_korean_font(16)
font       = get_korean_font(25)
font_med   = get_korean_font(32)
font_big   = get_korean_font(70)

ENEMY_W, ENEMY_H = 40, 40
ITEM_SIZE = 20
MAX_HP = 100

def get_difficulty(elapsed_seconds):
    speed = min(12.0, 2.0 + (elapsed_seconds / 15))
    spawn_delay = max(6, 60 - (elapsed_seconds / 3))
    enemy_hp = 1 + (elapsed_seconds / 20)
    return speed, spawn_delay, enemy_hp

# ─────────────────────────────────────────────
# 상점 데이터 정의
# ─────────────────────────────────────────────
SHOP_ITEMS = [
    # (id, 이름, 설명, 가격, 최대구매, 카테고리)
    ("bullet_count",  "멀티샷 +1",       "동시에 발사되는\n총알 수 +1\n(최대 5발)",   80,  4, "공격"),
    ("dmg_up",        "데미지 +1",       "총알 기본 데미지\n+1 증가",               60,  5, "공격"),
    ("fire_rate_up",  "연사속도 +1",     "발사 딜레이 감소\n(최대 연사속도까지)",      50,  8, "공격"),
    ("drone_slot",    "드론 슬롯 +1",    "드론 최대 보유\n수량 +1 증가",             100, 3, "드론"),
    ("drone_dmg",     "드론 데미지 +1",  "드론 총알 데미지\n+1 증가",                70,  4, "드론"),
    ("drone_rate",    "드론 연사 +1",    "드론 발사 딜레이\n감소",                   60,  5, "드론"),
    ("move_up",       "이동속도 +1",     "플레이어 이동\n속도 +0.5 증가",             40,  6, "방어"),
    ("max_hp_up",     "최대 체력 +20",   "최대 HP +20\n(현재 HP도 회복)",            90,  5, "방어"),
    ("item_drop",     "아이템 드롭 +5%", "적 처치 시 아이템\n드롭 확률 +5%",          70,  4, "특수"),
    ("item_boost",    "아이템 효과 +1",  "스탯 아이템의\n효과 +1 증가",              110, 3, "특수"),
    ("score_boost",   "점수 보너스 +5",  "적 처치 시 획득\n점수 +5 증가",             50,  5, "특수"),
    ("start_drone",   "시작 드론 +1",    "게임 시작 시\n드론 1개 지급",              120, 3, "드론"),
]

# ─────────────────────────────────────────────
# 영구 업그레이드 저장소 (게임 세션 간 유지)
# ─────────────────────────────────────────────
class PermanentUpgrades:
    def __init__(self):
        self.coins = 0
        self.total_score = 0
        self.purchased = {item[0]: 0 for item in SHOP_ITEMS}

    def get(self, key): return self.purchased.get(key, 0)
    def can_buy(self, item_id):
        for it in SHOP_ITEMS:
            if it[0] == item_id:
                price, max_buy = it[3], it[4]
                return (self.purchased[item_id] < max_buy) and (self.coins >= price)
        return False
    def buy(self, item_id):
        for it in SHOP_ITEMS:
            if it[0] == item_id and self.can_buy(item_id):
                self.coins -= it[3]  # it[3] = price
                self.purchased[item_id] += 1
                return True
        return False

upgrades = PermanentUpgrades()

# ─────────────────────────────────────────────
# 드로잉 유틸
# ─────────────────────────────────────────────
def draw_player(surf, rect):
    if PLAYER_IMAGE: surf.blit(PLAYER_IMAGE, rect.topleft)
    else: pygame.draw.polygon(surf, BLUE, [(rect.centerx, rect.top), (rect.left, rect.bottom), (rect.right, rect.bottom)])

def draw_drone(surf, rect):
    pygame.draw.circle(surf, PURPLE, rect.center, DRONE_W // 2)
    pygame.draw.circle(surf, WHITE, (rect.centerx - 4, rect.centery - 4), 3)
    pygame.draw.circle(surf, WHITE, rect.center, DRONE_W // 2, 2)

def draw_enemy(surf, enemy_obj):
    rect = enemy_obj['rect']
    hp_ratio = enemy_obj['hp'] / enemy_obj['max_hp']
    color = (max(50, 255 - (int(enemy_obj['max_hp']) * 20)), 50, 50)
    pygame.draw.rect(surf, color, rect, border_radius=5)
    if enemy_obj['max_hp'] > 1:
        pygame.draw.rect(surf, RED, (rect.x, rect.y - 10, rect.width, 4))
        pygame.draw.rect(surf, GREEN, (rect.x, rect.y - 10, rect.width * hp_ratio, 4))

def draw_hud(score, hp, max_hp, drone_count, drone_spread, coins):
    screen.blit(font.render(f"Score: {score}", True, WHITE), (20, 20))
    screen.blit(font_small.render(f"Drones: {drone_count} | Spread: {int(drone_spread)}", True, PURPLE), (20, 50))
    screen.blit(font_small.render(f"💰 {coins}", True, GOLD), (20, 70))
    cheat_txt = "[F1:Random Item] [F2:Drone Item] [F3:Inst Drone] [F4:Clear]"
    screen.blit(font_small.render(cheat_txt, True, (100, 255, 100)), (20, HEIGHT - 30))
    bar_width = 200
    pygame.draw.rect(screen, (100, 0, 0), (WIDTH - bar_width - 20, 25, bar_width, 20))
    pygame.draw.rect(screen, GREEN, (WIDTH - bar_width - 20, 25, max(0, (hp / max_hp) * bar_width), 20))
    screen.blit(font_small.render(f"HP: {int(hp)}/{max_hp}", True, WHITE), (WIDTH - bar_width - 20, 48))

def draw_button(surf, rect, text, color, hover=False):
    border_color = WHITE if hover else BORDER
    alpha_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    r, g, b = color
    alpha_surf.fill((r, g, b, 200 if hover else 160))
    surf.blit(alpha_surf, rect.topleft)
    pygame.draw.rect(surf, border_color, rect, 2, border_radius=8)
    label = font_med.render(text, True, WHITE)
    surf.blit(label, label.get_rect(center=rect.center))

# ─────────────────────────────────────────────
# 사망 화면
# ─────────────────────────────────────────────
def death_screen(score, coins_earned):
    upgrades.coins += coins_earned
    upgrades.total_score += score

    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))

    btn_shop    = pygame.Rect(WIDTH//2 - 160, 340, 140, 55)
    btn_retry   = pygame.Rect(WIDTH//2 - 0,   340, 140, 55)
    btn_quit    = pygame.Rect(WIDTH//2 + 160, 340, 140, 55)
    # 센터 보정
    btn_shop.centerx    = WIDTH//2 - 170
    btn_retry.centerx   = WIDTH//2
    btn_quit.centerx    = WIDTH//2 + 170

    anim = 0
    stars = [[random.randint(0, WIDTH), random.randint(0, HEIGHT), random.randint(1,2)] for _ in range(60)]

    while True:
        clock.tick(FPS)
        anim += 1
        mx, my = pygame.mouse.get_pos()

        for e in pygame.event.get():
            if e.type == pygame.QUIT: pygame.quit(); sys.exit()
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if btn_shop.collidepoint(mx, my):
                    shop_screen()
                    return "retry"
                if btn_retry.collidepoint(mx, my): return "retry"
                if btn_quit.collidepoint(mx, my): pygame.quit(); sys.exit()

        # 배경
        screen.fill(GRAY)
        for s in stars:
            s[1] += 0.5
            if s[1] > HEIGHT: s[1] = 0; s[0] = random.randint(0, WIDTH)
            pygame.draw.circle(screen, (70, 70, 100), (int(s[0]), int(s[1])), s[2])
        screen.blit(overlay, (0, 0))

        # 제목
        shake = math.sin(anim * 0.1) * 3
        title = font_big.render("GAME OVER", True, RED)
        screen.blit(title, title.get_rect(centerx=WIDTH//2, centery=180 + shake))

        # 점수
        sc_txt  = font_med.render(f"Score: {score}", True, WHITE)
        cn_txt  = font_med.render(f"획득 코인: {coins_earned}  (보유: {upgrades.coins})", True, GOLD)
        tot_txt = font_small.render(f"누적 점수: {upgrades.total_score}", True, (160, 160, 200))
        screen.blit(sc_txt,  sc_txt.get_rect(centerx=WIDTH//2, centery=265))
        screen.blit(cn_txt,  cn_txt.get_rect(centerx=WIDTH//2, centery=300))
        screen.blit(tot_txt, tot_txt.get_rect(centerx=WIDTH//2, centery=328))

        # 버튼
        draw_button(screen, btn_shop,  "🛒 상점",  DARK_PURPLE, btn_shop.collidepoint(mx, my))
        draw_button(screen, btn_retry, "▶ 다시하기", (0,80,0),  btn_retry.collidepoint(mx, my))
        draw_button(screen, btn_quit,  "✕ 나가기",  (80,0,0),  btn_quit.collidepoint(mx, my))

        pygame.display.flip()

# ─────────────────────────────────────────────
# 상점 화면
# ─────────────────────────────────────────────
def shop_screen():
    scroll = 0
    CARD_W, CARD_H = 160, 170
    COLS = 4
    PAD = 18
    GRID_X = (WIDTH - (CARD_W * COLS + PAD * (COLS - 1))) // 2
    GRID_Y = 120
    buy_msg = ""
    buy_msg_timer = 0

    categories = ["전체", "공격", "드론", "방어", "특수"]
    sel_cat = "전체"
    cat_rects = []

    stars = [[random.randint(0, WIDTH), random.randint(0, HEIGHT), random.randint(1, 2)] for _ in range(60)]

    btn_back = pygame.Rect(WIDTH - 140, HEIGHT - 60, 120, 40)

    while True:
        clock.tick(FPS)
        mx, my = pygame.mouse.get_pos()

        for e in pygame.event.get():
            if e.type == pygame.QUIT: pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE: return
            if e.type == pygame.MOUSEWHEEL: scroll = max(0, scroll - e.y * 30)

            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if btn_back.collidepoint(mx, my): return
                # 카테고리 탭
                for i, cr in enumerate(cat_rects):
                    if cr.collidepoint(mx, my):
                        sel_cat = categories[i]; scroll = 0

                # 아이템 카드 클릭
                filtered = [it for it in SHOP_ITEMS if sel_cat == "전체" or it[5] == sel_cat]
                for idx, item in enumerate(filtered):
                    col = idx % COLS
                    row = idx // COLS
                    cx = GRID_X + col * (CARD_W + PAD)
                    cy = GRID_Y + row * (CARD_H + PAD) - scroll
                    card_rect = pygame.Rect(cx, cy, CARD_W, CARD_H)
                    if card_rect.collidepoint(mx, my):
                        if upgrades.can_buy(item[0]):
                            upgrades.buy(item[0])
                            buy_msg = f"✅ {item[1]} 구매 완료!"
                        elif upgrades.purchased[item[0]] >= item[3]:
                            buy_msg = "❌ 최대 구매 횟수 도달"
                        else:
                            buy_msg = f"❌ 코인 부족! (필요: {item[3]})"
                        buy_msg_timer = 120

        buy_msg_timer = max(0, buy_msg_timer - 1)

        # --- 그리기 ---
        screen.fill(PANEL)
        for s in stars:
            s[1] += 0.3
            if s[1] > HEIGHT: s[1] = 0; s[0] = random.randint(0, WIDTH)
            pygame.draw.circle(screen, (50, 50, 80), (int(s[0]), int(s[1])), s[2])

        # 헤더
        pygame.draw.rect(screen, PANEL2, (0, 0, WIDTH, 55))
        pygame.draw.line(screen, BORDER, (0, 55), (WIDTH, 55), 2)
        title_s = font_med.render("🛒  업그레이드 상점", True, WHITE)
        screen.blit(title_s, title_s.get_rect(centery=27, x=20))
        coin_s = font_med.render(f"💰 {upgrades.coins}", True, GOLD)
        screen.blit(coin_s, coin_s.get_rect(centery=27, right=WIDTH - 20))

        # 카테고리 탭
        cat_rects.clear()
        for i, cat in enumerate(categories):
            cr = pygame.Rect(20 + i * 110, 65, 100, 30)
            cat_rects.append(cr)
            is_sel = cat == sel_cat
            pygame.draw.rect(screen, BORDER if is_sel else PANEL2, cr, border_radius=6)
            if is_sel: pygame.draw.rect(screen, WHITE, cr, 2, border_radius=6)
            ct = font_small.render(cat, True, WHITE if is_sel else (160,160,200))
            screen.blit(ct, ct.get_rect(center=cr.center))

        # 아이템 카드
        filtered = [it for it in SHOP_ITEMS if sel_cat == "전체" or it[5] == sel_cat]
        # 클리핑 영역
        clip_rect = pygame.Rect(0, GRID_Y - 10, WIDTH, HEIGHT - GRID_Y - 60)
        screen.set_clip(clip_rect)

        for idx, item in enumerate(filtered):
            iid, name, desc, price, max_buy, cat = item
            col = idx % COLS
            row = idx // COLS
            cx = GRID_X + col * (CARD_W + PAD)
            cy = GRID_Y + row * (CARD_H + PAD) - scroll
            card_rect = pygame.Rect(cx, cy, CARD_W, CARD_H)

            bought = upgrades.purchased[iid]
            affordable = upgrades.coins >= price
            maxed = bought >= max_buy
            hovered = card_rect.collidepoint(mx, my)

            # 카드 배경
            card_col = (40, 40, 70) if not maxed else (40, 60, 40)
            if hovered and not maxed: card_col = (60, 60, 110)
            pygame.draw.rect(screen, card_col, card_rect, border_radius=10)
            border_c = GOLD if hovered and not maxed else ((0,180,0) if maxed else BORDER)
            pygame.draw.rect(screen, border_c, card_rect, 2, border_radius=10)

            # 카테고리 배지
            cat_colors = {"공격": RED, "드론": PURPLE, "방어": BLUE, "특수": ORANGE}
            badge_col = cat_colors.get(cat, GRAY)
            badge = pygame.Rect(cx + 5, cy + 5, 40, 16)
            pygame.draw.rect(screen, badge_col, badge, border_radius=4)
            screen.blit(font_small.render(cat, True, WHITE), (badge.x + 3, badge.y + 1))

            # 이름
            n_s = font_small.render(name, True, WHITE)
            screen.blit(n_s, n_s.get_rect(centerx=cx + CARD_W//2, y=cy + 27))

            # 설명 (줄바꿈)
            for li, line in enumerate(desc.split('\n')):
                d_s = font_small.render(line, True, (180, 180, 220))
                screen.blit(d_s, d_s.get_rect(centerx=cx + CARD_W//2, y=cy + 52 + li * 18))

            # 구매 횟수
            prog = font_small.render(f"{bought}/{max_buy}", True, GOLD if not maxed else GREEN)
            screen.blit(prog, prog.get_rect(centerx=cx + CARD_W//2, y=cy + CARD_H - 46))

            # 가격 / 최대 버튼
            if maxed:
                pygame.draw.rect(screen, (0, 100, 0), pygame.Rect(cx + 15, cy + CARD_H - 30, CARD_W - 30, 22), border_radius=5)
                screen.blit(font_small.render("MAX ✔", True, GREEN),
                            font_small.render("MAX ✔", True, GREEN).get_rect(centerx=cx + CARD_W//2, centery=cy + CARD_H - 19))
            else:
                btn_col = (0, 120, 0) if affordable else (80, 0, 0)
                pygame.draw.rect(screen, btn_col, pygame.Rect(cx + 10, cy + CARD_H - 30, CARD_W - 20, 22), border_radius=5)
                price_s = font_small.render(f"💰 {price}", True, GOLD if affordable else (160,80,80))
                screen.blit(price_s, price_s.get_rect(centerx=cx + CARD_W//2, centery=cy + CARD_H - 19))

        screen.set_clip(None)

        # 구매 메시지
        if buy_msg_timer > 0:
            alpha = min(255, buy_msg_timer * 4)
            msg_s = font_med.render(buy_msg, True, GREEN if "✅" in buy_msg else RED)
            msg_s.set_alpha(alpha)
            screen.blit(msg_s, msg_s.get_rect(centerx=WIDTH//2, centery=HEIGHT - 75))

        # 뒤로가기 버튼
        draw_button(screen, btn_back, "← 돌아가기", DARK_PURPLE, btn_back.collidepoint(mx, my))

        pygame.display.flip()

# ─────────────────────────────────────────────
# 메인 게임 루프
# ─────────────────────────────────────────────
def main():
    # 업그레이드 적용 초기값
    player = pygame.Rect(WIDTH//2 - PLAYER_W//2, HEIGHT-70, PLAYER_W, PLAYER_H)
    
    p_dmg      = 1 + upgrades.get("dmg_up")
    p_fire_rate = max(4, 15 - upgrades.get("fire_rate_up"))
    p_move     = min(12, 6 + upgrades.get("move_up") * 0.5)
    bullet_count = 1 + upgrades.get("bullet_count")   # 동시 발사 총알 수
    
    drone_dmg_bonus  = upgrades.get("drone_dmg")
    drone_rate_bonus = upgrades.get("drone_rate")
    item_drop_bonus  = upgrades.get("item_drop") * 0.05
    item_boost       = upgrades.get("item_boost")
    score_bonus      = upgrades.get("score_boost") * 5
    max_drone_slots  = 3 + upgrades.get("drone_slot")

    max_hp = MAX_HP + upgrades.get("max_hp_up") * 20
    hp = max_hp

    score = 0
    coins_earned = 0

    drones = []
    # 시작 드론 지급
    for _ in range(upgrades.get("start_drone")):
        if len(drones) < max_drone_slots:
            drones.append({'rect': pygame.Rect(0, 0, DRONE_W, DRONE_H),
                           'px': float(player.centerx), 'py': float(player.centery), 'shoot_cd': 30})

    drone_spread = 60

    bullets = []
    enemies = []
    items = []

    spawn_timer = 0
    invincible = 0
    shoot_cd = 0

    start_ticks = pygame.time.get_ticks()
    stars = [[random.randint(0, WIDTH), random.randint(0, HEIGHT), random.randint(1, 2)] for _ in range(60)]

    base_drop_chance = 0.25

    while True:
        clock.tick(FPS)
        elapsed_seconds = (pygame.time.get_ticks() - start_ticks) // 1000
        cur_speed, cur_spawn_delay, cur_e_hp = get_difficulty(elapsed_seconds)

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
                    if len(drones) < max_drone_slots:
                        drones.append({'rect': pygame.Rect(0, 0, DRONE_W, DRONE_H),
                                       'px': float(player.centerx), 'py': float(player.centery), 'shoot_cd': 30})
                if e.key == pygame.K_F4:
                    drones.clear()
                if e.key == pygame.K_F5:
                    coins_earned+=1000

        # 조작
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]  and player.left > 0:      player.x -= p_move
        if keys[pygame.K_RIGHT] and player.right < WIDTH:  player.x += p_move
        if keys[pygame.K_UP]    and player.top > 0:        player.y -= p_move
        if keys[pygame.K_DOWN]  and player.bottom < HEIGHT: player.y += p_move
        if keys[pygame.K_z]: drone_spread = max(10, drone_spread - 2)
        if keys[pygame.K_x]: drone_spread = min(300, drone_spread + 2)

        # 발사 (멀티샷)
        shoot_cd -= 1
        if keys[pygame.K_SPACE] and shoot_cd <= 0:
            # 총알 수에 따라 균등 분산
            for bi in range(bullet_count):
                if bullet_count == 1:
                    bx = player.centerx - BULLET_W // 2
                else:
                    spread_px = (bullet_count - 1) * 12
                    bx = player.centerx - spread_px // 2 + bi * 12 - BULLET_W // 2
                bullets.append({'rect': pygame.Rect(bx, player.top - BULLET_H, BULLET_W, BULLET_H), 'dmg': p_dmg})
            shoot_cd = p_fire_rate
            if SHOOT_SOUND: SHOOT_SOUND.play()

        # 드론 업데이트
        t = pygame.time.get_ticks() / 1000.0
        eff_drone_fire_rate = max(8, int(p_fire_rate * 2.5) - drone_rate_bonus * 3)
        for i, dn in enumerate(drones):
            side = -1 if i % 2 == 0 else 1
            row = (i // 2) + 1
            float_y = math.sin(t * 2.0 + i) * 12.0 + math.sin(t * 4.5 + i * 0.5) * 4.0
            float_x = math.cos(t * 1.5 + i) * 6.0
            target_x = player.centerx + side * (drone_spread * row) + float_x
            target_y = player.centery + (row * 15) + float_y
            dn['px'] += (target_x - dn['px']) * 0.08
            dn['py'] += (target_y - dn['py']) * 0.08
            dn['rect'].centerx, dn['rect'].centery = int(dn['px']), int(dn['py'])
            dn['shoot_cd'] -= 1
            if dn['shoot_cd'] <= 0:
                bullets.append({'rect': pygame.Rect(dn['rect'].centerx - BULLET_W//2, dn['rect'].top - BULLET_H, BULLET_W, BULLET_H),
                                 'dmg': p_dmg + drone_dmg_bonus})
                dn['shoot_cd'] = eff_drone_fire_rate
                if SHOOT_SOUND: SHOOT_SOUND.play()

        # 총알 이동
        for b in bullets[:]:
            b['rect'].y -= 12
            if b['rect'].bottom < 0: bullets.remove(b)

        # 적 스폰
        spawn_timer += 1
        if spawn_timer >= cur_spawn_delay:
            spawn_timer = 0
            enemies.append({'rect': pygame.Rect(random.randint(0, WIDTH-ENEMY_W), -ENEMY_H, ENEMY_W, ENEMY_H),
                            'hp': cur_e_hp, 'max_hp': cur_e_hp})

        # 적 이동
        for en in enemies[:]:
            en['rect'].y += cur_speed
            if en['rect'].top > HEIGHT: enemies.remove(en)

        # 아이템 이동 및 획득
        heal_amt = 20 + item_boost * 5
        stat_bonus = 1 + item_boost
        for it in items[:]:
            it['rect'].y += 3
            if it['rect'].colliderect(player):
                if it['type'] == 'dmg':   p_dmg = min(p_dmg + stat_bonus, 20)
                elif it['type'] == 'spd': p_fire_rate = max(4, p_fire_rate - stat_bonus)
                elif it['type'] == 'move': p_move = min(12, p_move + 0.5 * stat_bonus)
                elif it['type'] == 'heal': hp = min(max_hp, hp + heal_amt)
                elif it['type'] == 'drone':
                    if len(drones) < max_drone_slots:
                        drones.append({'rect': pygame.Rect(0, 0, DRONE_W, DRONE_H),
                                       'px': float(player.centerx), 'py': float(player.centery), 'shoot_cd': 30})
                items.remove(it)
            elif it['rect'].top > HEIGHT: items.remove(it)

        # 충돌 검사 (총알-적)
        drop_chance = min(0.85, base_drop_chance + item_drop_bonus)
        for b in bullets[:]:
            for en in enemies[:]:
                if b['rect'].colliderect(en['rect']):
                    if b in bullets: bullets.remove(b)
                    en['hp'] -= b['dmg']
                    if en['hp'] <= 0:
                        if random.random() < drop_chance:
                            itype = random.choice(['dmg', 'spd', 'move', 'heal', 'drone'])
                            icolor = {'dmg': RED, 'spd': YELLOW, 'move': BLUE, 'heal': GREEN, 'drone': PURPLE}[itype]
                            items.append({'rect': pygame.Rect(en['rect'].centerx, en['rect'].centery, ITEM_SIZE, ITEM_SIZE),
                                          'type': itype, 'color': icolor})
                        if en in enemies: enemies.remove(en)
                        pts = 10 + score_bonus
                        score += pts
                        coins_earned += 1   # 적 처치 시 1코인
                    break

        # 플레이어-적 충돌
        if invincible > 0: invincible -= 1
        else:
            for en in enemies[:]:
                if player.colliderect(en['rect']):
                    hp -= 20
                    invincible = 60
                    enemies.remove(en)
                    if hp <= 0:
                        # ── 사망 처리 ──
                        result = death_screen(score, coins_earned)
                        if result == "retry": main()
                        return

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
        for dn in drones:  draw_drone(screen, dn['rect'])
        for it in items:
            pygame.draw.circle(screen, it['color'], it['rect'].center, ITEM_SIZE // 2)
            label = 'D' if it['type'] == 'drone' else it['type'][0].upper()
            screen.blit(font_small.render(label, True, BLACK), (it['rect'].x + 6, it['rect'].y + 2))

        if (invincible // 5) % 2 == 0: draw_player(screen, player)
        draw_hud(score, hp, max_hp, len(drones), drone_spread, coins_earned)
        pygame.display.flip()

if __name__ == "__main__":
    main()
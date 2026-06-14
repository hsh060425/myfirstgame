import pygame
import random
import math
import sys
import os

pygame.init()
WIDTH, HEIGHT = 800, 750
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Typing Isaac - Items & Combos (+Cheat)")
clock = pygame.time.Clock()

WHITE, BLACK = (255, 255, 255), (15, 15, 15)
FLOOR_COLOR, WALL_COLOR = (50, 45, 40), (35, 30, 25)
DOOR_OPEN, DOOR_LOCKED = (200, 160, 40), (100, 100, 100)
PLAYER_COLOR, PLAYER_IMMUNE = (100, 180, 255), (180, 220, 255)
ENEMY_COLOR, BOSS_COLOR = (220, 60, 60), (180, 40, 200)
UI_BG = (25, 25, 35)
HP_RED, HP_GREEN = (200, 50, 50), (50, 200, 50)
MM_CURRENT, MM_VISITED, MM_DISCOVERED, MM_BOSS = (255, 230, 0), (120, 120, 120), (60, 60, 60), (230, 50, 50)

FIELD_COLORS = {
    "attack": (255, 255, 255, 150), "fire": (255, 80, 0, 120),
    "poison": (100, 255, 50, 100), "ice": (100, 200, 255, 120),
    "steam": (200, 200, 220, 150), "tree": (34, 139, 34, 130),
    "bomb": (255, 100, 0, 180), "explosion": (255, 50, 50, 180),
    "heal": (50, 255, 150, 120), "guard": (255, 215, 0, 120),
    "plague_storm": (120, 30, 160, 160), "toxic_cloud": (70, 220, 40, 140),
    "wildfire": (255, 130, 0, 180), "sanctuary": (200, 255, 150, 150),
    "glacial_barricade": (150, 220, 255, 180), "counter_shield": (255, 200, 50, 180),
    "divine_grace": (255, 255, 200, 150)
}

# ── 상태이상 정의 ─────────────────────────────────────────────────────────────
# 각 상태이상: duration(틱), tick_dmg(틱당 피해), speed_mult(속도 배율), stun(스턴 여부)
STATUS_DEFS = {
    "burn":    {"duration": 180, "tick_dmg": 0.8,  "speed_mult": 1.0,  "stun": False, "color": (255, 100, 0)},
    "poison":  {"duration": 300, "tick_dmg": 0.3,  "speed_mult": 0.85, "stun": False, "color": (80,  220, 40)},
    "freeze":  {"duration": 120, "tick_dmg": 0.0,  "speed_mult": 0.2,  "stun": False, "color": (130, 200, 255)},
    "root":    {"duration": 90,  "tick_dmg": 0.0,  "speed_mult": 0.0,  "stun": True,  "color": (34,  139, 34)},
    "plague":  {"duration": 240, "tick_dmg": 0.6,  "speed_mult": 0.1,  "stun": False, "color": (140, 30,  160)},
}
# 원소 → 부여 상태이상 매핑
ELEMENT_STATUS = {
    "fire":   "burn",
    "poison": "poison",
    "ice":    "freeze",
    "tree":   "root",
}

pygame.font.init()
system_fonts = pygame.font.get_fonts()
kor_font = None
for f in ['malgungothic', 'applegothic', 'applesdgothicneo', 'nanumgothic', 'd2coding']:
    if f in system_fonts:
        kor_font = f
        break
font = pygame.font.SysFont(kor_font, 20)
big_font = pygame.font.SysFont(kor_font, 30)

SPRITE_DIR = os.path.join(os.path.dirname(__file__), "assets")

# 배경음악 설정
pygame.mixer.init()
bgm_loaded = False
for ext in ["mp3", "ogg", "wav"]:
    bgm_path = os.path.join(SPRITE_DIR, f"bgm.{ext}")
    if os.path.exists(bgm_path):
        try:
            pygame.mixer.music.load(bgm_path)
            pygame.mixer.music.set_volume(0.5)
            pygame.mixer.music.play(-1)  # 무한 반복
            bgm_loaded = True
            break
        except Exception as e:
            print(f"BGM 재생 오류 ({ext}): {e}")

if not bgm_loaded:
    print("재생 가능한 BGM 파일을 찾지 못했습니다. (assets 폴더에 bgm.mp3 등을 넣어주세요)")

def load_sprite(rel_path, scale=None):
    full = os.path.join(SPRITE_DIR, rel_path)
    try:
        img = pygame.image.load(full).convert_alpha()
        if scale:
            orig_w, orig_h = img.get_size()
            max_size = max(orig_w, orig_h)
            square_img = pygame.Surface((max_size, max_size), pygame.SRCALPHA)
            square_img.blit(img, ((max_size-orig_w)//2, (max_size-orig_h)//2))
            img = pygame.transform.scale(square_img, scale)
        return img
    except Exception:
        return None

def load_strip(rel_path, frame_w, frame_h, count, scale=None):
    full = os.path.join(SPRITE_DIR, rel_path)
    try:
        sheet = pygame.image.load(full).convert_alpha()
        frames = []
        for i in range(count):
            frame = sheet.subsurface(pygame.Rect(i * frame_w, 0, frame_w, frame_h))
            if scale:
                orig_w, orig_h = frame.get_size()
                max_size = max(orig_w, orig_h)
                sq = pygame.Surface((max_size, max_size), pygame.SRCALPHA)
                sq.blit(frame, ((max_size-orig_w)//2, (max_size-orig_h)//2))
                frame = pygame.transform.scale(sq, scale)
            frames.append(frame)
        return frames
    except Exception:
        return []

FRAME_SIZE = (48, 48)
FW, FH = 80, 80

BOSS_SIZE = (120, 120)
ENEMY_SPRITES = {
    "red_slime":      [load_sprite("red_slime.png",  FRAME_SIZE)],
    "yellow_eye":     [load_sprite("yellow_eyes.png",FRAME_SIZE)],
    "stone_guardian": [load_sprite("stone_guard.png",FRAME_SIZE )],
    "shadow_bat":     [load_sprite("shadow_bat.png", FRAME_SIZE)],
    "boss": {
        "idle": [load_sprite(f"boss_idle_{i}.png", BOSS_SIZE) for i in range(1, 6)],
        "slam": [load_sprite(f"boss_slam_{i}.png", BOSS_SIZE) for i in range(1, 6)],
        "summon": [load_sprite(f"boss_summon_{i}.png", BOSS_SIZE) for i in range(1, 6)],
        "dash": [load_sprite(f"boss_dash_{i}.png", BOSS_SIZE) for i in range(1, 6)],
        "shoot_spread": [load_sprite(f"boss_spread_{i}.png", BOSS_SIZE) for i in range(1, 3)],
        "shoot_continuous": [load_sprite(f"boss_continuous_{i}.png", BOSS_SIZE) for i in range(1, 3)],
    }
}
PLAYER_SPRITE = load_sprite("player.png", (48, 48))

player_particles = []

def spawn_player_particles(pos, color, count=1, speed=2.0, size_range=(2, 5)):
    for _ in range(count):
        angle = random.uniform(0, 2 * math.pi)
        spd = random.uniform(0.5, speed)
        player_particles.append({
            "pos": list(pos),
            "vel": [math.cos(angle)*spd, math.sin(angle)*spd],
            "color": color,
            "radius": random.uniform(*size_range),
            "alpha": 255,
            "decay": random.uniform(4, 8)
        })

def update_and_draw_particles(surface):
    for p in player_particles[:]:
        p["pos"][0] += p["vel"][0]; p["pos"][1] += p["vel"][1]
        p["alpha"] -= p["decay"]
        if p["alpha"] <= 0:
            player_particles.remove(p); continue
        size = max(1, int(p["radius"] * 2))
        psurf = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(psurf, (*p["color"], int(p["alpha"])), (size//2, size//2), p["radius"])
        surface.blit(psurf, (int(p["pos"][0]-size//2), int(p["pos"][1]-size//2)))

ENEMY_FALLBACK_COLORS = {
    "red_slime":      (220,  60,  60),
    "yellow_eye":     (255, 220,   0),
    "stone_guardian": (130, 130, 140),
    "shadow_bat":     ( 80,  40, 180),
    "boss":           (180,  40, 200),
}

# ──────────────────────────────────────────────
# 상태이상 헬퍼
# ──────────────────────────────────────────────
def apply_status(e, stype, dm=1.0):
    """적에게 상태이상을 부여. 이미 있으면 duration 갱신."""
    if stype not in STATUS_DEFS:
        return
    if "statuses" not in e:
        e["statuses"] = {}
    base = STATUS_DEFS[stype]
    # 중첩 시 지속시간 갱신 (최대 1.5배)
    existing = e["statuses"].get(stype, {})
    new_dur = base["duration"]
    if existing:
        new_dur = min(int(base["duration"] * 1.5), existing.get("timer", 0) + base["duration"])
    e["statuses"][stype] = {
        "timer": new_dur,
        "tick_dmg": base["tick_dmg"] * dm,
        "speed_mult": base["speed_mult"],
        "stun": base["stun"],
        "color": base["color"],
    }

def tick_statuses(e):
    """매 프레임 상태이상 처리 → (추가 피해, 속도 배율, 스턴 여부) 반환."""
    if "statuses" not in e:
        return 0.0, 1.0, False
    total_dmg = 0.0
    min_speed_mult = 1.0
    any_stun = False
    to_remove = []
    for stype, info in e["statuses"].items():
        total_dmg += info["tick_dmg"]
        min_speed_mult = min(min_speed_mult, info["speed_mult"])
        if info["stun"]:
            any_stun = True
        info["timer"] -= 1
        if info["timer"] <= 0:
            to_remove.append(stype)
    for s in to_remove:
        del e["statuses"][s]
    return total_dmg, min_speed_mult, any_stun

def draw_status_icons(surface, e):
    """HP바 위에 상태이상 아이콘(컬러 점) 표시."""
    if "statuses" not in e or not e["statuses"]:
        return
    px, py = int(e["pos"][0]), int(e["pos"][1])
    bar_w = e["radius"] * 3
    icon_x = px - bar_w // 2
    icon_y = py - e["radius"] - 26
    for i, (stype, info) in enumerate(e["statuses"].items()):
        cx = icon_x + i * 14
        # 깜박이는 효과: 남은 시간이 60틱 미만이면 깜박임
        if info["timer"] < 60 and (info["timer"] // 6) % 2 == 1:
            continue
        pygame.draw.circle(surface, info["color"], (cx, icon_y), 5)
        pygame.draw.circle(surface, WHITE, (cx, icon_y), 5, 1)

# ──────────────────────────────────────────────
# 적 팩토리
# ──────────────────────────────────────────────
def make_enemy(etype, pos):
    base = {
        "pos": list(pos), "type": etype, "radius": 16,
        "stun_timer": 0, "state": "idle",
        "anim_frame": 0, "anim_timer": 0, "anim_speed": 8,
        "facing_x": 1, "dead": False,
        "action_timer": 0, "bullet_timer": 0,
        "charge_dir": [0, 0], "charge_timer": 0, "orbit_angle": 0.0,
        "statuses": {},   # ← 상태이상 딕셔너리
    }
    presets = {
        "red_slime":      {"hp": 20,  "max_hp": 20,  "speed": 1.0, "base_speed": 1.0, "radius": 14},
        "yellow_eye":     {"hp": 15,  "max_hp": 15,  "speed": 1.5, "base_speed": 1.5, "radius": 13, "bullet_timer": 120},
        "stone_guardian": {"hp": 40,  "max_hp": 40,  "speed": 0.6, "base_speed": 0.6, "radius": 18,
                           "charge_timer": 0, "charge_cooldown": 180},
        "shadow_bat":     {"hp": 10,  "max_hp": 10,  "speed": 2.2, "base_speed": 2.2, "radius": 12,
                           "orbit_angle": random.uniform(0, math.pi*2), "action_timer": random.randint(120, 180)},
        "boss":           {
            "hp": 300, "max_hp": 300, "speed": 1.5, "base_speed": 1.5, "radius": 35,
            "boss_state": "idle", "phase": 1, "state_timer": 60,
            "target_pos": [0, 0], "dash_dir": [0, 0], "anim_speed": 12
        },
    }
    base.update(presets.get(etype, {}))
    
    # 난이도 스케일링
    stage = globals().get("current_stage", 1)
    hp_mult = 1.0 + (stage - 1) * 0.3
    spd_mult = 1.0 + (stage - 1) * 0.1
    if "max_hp" in base:
        base["max_hp"] *= hp_mult
        base["hp"] = base["max_hp"]
    if "speed" in base:
        base["base_speed"] = base.get("base_speed", 1.0) * spd_mult
        base["speed"] = base.get("speed", 1.0) * spd_mult
        
    return base

bullets = []

def spawn_bullet(pos, target_pos, dmg=8):
    dx, dy = target_pos[0]-pos[0], target_pos[1]-pos[1]
    dist = math.hypot(dx, dy)
    if dist == 0: return
    speed = 5
    bullets.append({
        "pos": list(pos), "vx": (dx/dist)*speed, "vy": (dy/dist)*speed,
        "radius": 6, "dmg": dmg, "timer": 180, "color": (255, 220, 0),
    })

def get_frame(e):
    frames = ENEMY_SPRITES.get(e["type"])
    if not frames: return None
    if isinstance(frames, dict):
        state = e.get("state", "idle")
        if state not in frames: state = "idle"
        state_frames = frames[state]
        if not state_frames or state_frames[0] is None: return None
        idx = min(e["anim_frame"], len(state_frames) - 1)
        return state_frames[idx]
    else:
        if frames[0] is None: return None
        idx = min(e["anim_frame"], len(frames) - 1)
        return frames[idx]

def advance_anim(e, loop=True):
    frames = ENEMY_SPRITES.get(e["type"])
    if isinstance(frames, dict):
        state = e.get("state", "idle")
        if state not in frames: state = "idle"
        state_frames = frames[state]
        count = len(state_frames) if state_frames else 4
        if state != "idle": loop = False
    elif isinstance(frames, list):
        count = len(frames) if len(frames) > 1 else 4
    else:
        count = 4

    e["anim_timer"] += 1
    if e["anim_timer"] >= e.get("anim_speed", 8):
        e["anim_timer"] = 0
        e["anim_frame"] += 1
        if e["anim_frame"] >= count:
            if loop: e["anim_frame"] = 0
            else:    e["anim_frame"] = count - 1; return True
    return False

def set_state(e, state):
    if e["state"] != state:
        e["state"] = state; e["anim_frame"] = 0; e["anim_timer"] = 0
        if e.get("type") == "boss":
            if state == "idle": e["anim_speed"] = max(1, 60 // 5)
            elif state == "slam": e["anim_speed"] = max(1, 155 // 5)
            elif state == "summon": e["anim_speed"] = max(1, 170 // 5)
            elif state == "dash": e["anim_speed"] = max(1, 180 // 5)
            elif state == "shoot_spread": e["anim_speed"] = max(1, 185 // 2)
            elif state == "shoot_continuous": e["anim_speed"] = max(1, 120 // 2)

def update_enemy(e, p_pos, p_hp, room_enemies, active_fields, dm):
    if e["dead"] or e["hp"] <= 0:
        if not e["dead"]:
            e["dead"] = True; set_state(e, "death")
        advance_anim(e, loop=False)
        return

    # ── 상태이상 틱 처리 ──────────────────────
    status_dmg, speed_mult, status_stun = tick_statuses(e)
    e["hp"] -= status_dmg

    # 상태이상 파티클 생성
    if e.get("statuses") and not e["dead"]:
        if random.random() < 0.5:  # 50% 확률로 파티클 생성
            stype = next(iter(e["statuses"]))
            color = STATUS_DEFS[stype]["color"]
            px = e["pos"][0] + random.uniform(-e["radius"], e["radius"])
            py = e["pos"][1] + random.uniform(-e["radius"], e["radius"])
            player_particles.append({
                "pos": [px, py],
                "vel": [random.uniform(-0.5, 0.5), random.uniform(-1.5, -0.5)],
                "color": color,
                "radius": random.uniform(2, 4),
                "alpha": 255,
                "decay": random.uniform(5, 10)
            })

    # 스턴 (스킬 스턴 OR 상태이상 스턴)
    if e.get("stun_timer", 0) > 0 or status_stun:
        if e.get("stun_timer", 0) > 0:
            e["stun_timer"] -= 1
        set_state(e, "hit")
        advance_anim(e, loop=False)
        return

    # 속도에 상태이상 배율 적용
    e["speed"] = e["base_speed"] * speed_mult

    etype = e["type"]

    if etype == "red_slime":
        dx, dy = p_pos[0]-e["pos"][0], p_pos[1]-e["pos"][1]
        dist = math.hypot(dx, dy)
        if dist > 0 and p_hp > 0:
            e["pos"][0] += (dx/dist)*e["speed"]; e["pos"][1] += (dy/dist)*e["speed"]
            e["facing_x"] = 1 if dx >= 0 else -1
            set_state(e, "idle")
        advance_anim(e)

    elif etype == "yellow_eye":
        dx, dy = p_pos[0]-e["pos"][0], p_pos[1]-e["pos"][1]
        dist = math.hypot(dx, dy)
        STOP_DIST = 180
        e["bullet_timer"] = e.get("bullet_timer", 120) - 1
        if dist > STOP_DIST and p_hp > 0:
            e["pos"][0] += (dx/dist)*e["speed"]; e["pos"][1] += (dy/dist)*e["speed"]
            e["facing_x"] = 1 if dx >= 0 else -1; set_state(e, "move")
        else:
            set_state(e, "idle")
        if e["bullet_timer"] <= 0:
            set_state(e, "shoot")
            spawn_bullet(list(e["pos"]), p_pos, dmg=8)
            e["bullet_timer"] = random.randint(90, 150)
        advance_anim(e)

    elif etype == "stone_guardian":
        dx, dy = p_pos[0]-e["pos"][0], p_pos[1]-e["pos"][1]
        dist = math.hypot(dx, dy)
        if e.get("charge_timer", 0) > 0:
            e["pos"][0] += e["charge_dir"][0]*e["speed"]*15
            e["pos"][1] += e["charge_dir"][1]*e["speed"]*15
            e["charge_timer"] -= 1; set_state(e, "charge")
            if e["charge_timer"] == 0:
                e["stun_timer"] = 45
        else:
            e["action_timer"] = e.get("action_timer", 0) - 1
            if e["action_timer"] <= 0 and dist < 1200 and p_hp > 0:
                if dist > 0: e["charge_dir"] = [dx/dist, dy/dist]
                e["charge_timer"] = 30
                e["action_timer"] = e.get("charge_cooldown", 180)
                e["facing_x"] = 1 if dx >= 0 else -1
            else:
                set_state(e, "idle")
        advance_anim(e)

    elif etype == "shadow_bat":
        if e.get("charge_timer", 0) > 0:
            e["pos"][0] += e["charge_dir"][0]*e["speed"]*3
            e["pos"][1] += e["charge_dir"][1]*e["speed"]*3
            e["charge_timer"] -= 1
            e["facing_x"] = 1 if e["charge_dir"][0] >= 0 else -1
            set_state(e, "charge")
        else:
            e["action_timer"] = e.get("action_timer", 0) - 1
            if e["action_timer"] <= 0 and p_hp > 0:
                dx, dy = p_pos[0]-e["pos"][0], p_pos[1]-e["pos"][1]
                dist = math.hypot(dx, dy)
                e["charge_dir"] = [dx/dist, dy/dist] if dist > 0 else [1, 0]
                e["charge_timer"] = 30
                e["action_timer"] = random.randint(150, 240)
                e["facing_x"] = 1 if dx >= 0 else -1; set_state(e, "charge")
            else:
                e["orbit_angle"] = e.get("orbit_angle", 0) + 0.04
                OR = 130
                tx = p_pos[0] + math.cos(e["orbit_angle"])*OR
                ty = p_pos[1] + math.sin(e["orbit_angle"])*OR
                tdx, tdy = tx-e["pos"][0], ty-e["pos"][1]
                td = math.hypot(tdx, tdy)
                if td > 0 and p_hp > 0:
                    spd = min(e["speed"]*2, td)
                    e["pos"][0] += (tdx/td)*spd; e["pos"][1] += (tdy/td)*spd
                    e["facing_x"] = 1 if tdx >= 0 else -1
                set_state(e, "move")
        advance_anim(e)

    else:  # boss
        bs = e.get("boss_state", "idle")
        ph = e.get("phase", 1)

        if bs == "idle":
            e["state_timer"] -= 1
            dx, dy = p_pos[0]-e["pos"][0], p_pos[1]-e["pos"][1]
            dist = math.hypot(dx, dy)
            if dist > 0 and p_hp > 0:
                e["pos"][0] += (dx/dist)*e["speed"]*0.4; e["pos"][1] += (dy/dist)*e["speed"]*0.4
            if e["state_timer"] <= 0 and p_hp > 0:
                patterns = ["slam", "summon", "dash", "shoot_spread", "shoot_continuous"]
                e["boss_state"] = random.choice(patterns)
                e["phase"] = 1
                e["state_timer"] = 40 # 1. 준비
        
        elif bs == "slam": # 내려찍는 모션
            if ph == 1: # 1. 준비
                e["state_timer"] -= 1
                if e["state_timer"] <= 0: e["phase"] = 2; e["state_timer"] = 30; e["target_pos"] = list(p_pos)
            elif ph == 2: # 2. 상승
                e["state_timer"] -= 1
                e["pos"][1] -= 6
                if e["state_timer"] <= 0:
                    e["phase"] = 3; e["state_timer"] = 15
                    e["pos"][0] = e["target_pos"][0]
                    e["pos"][1] = e["target_pos"][1] - 180 # 타겟 위치보다 높은 곳에서 하강 시작
            elif ph == 3: # 3. 하강
                e["state_timer"] -= 1
                e["pos"][1] += 12 # 15틱 동안 180 하강
                if e["state_timer"] <= 0:
                    e["pos"] = list(e["target_pos"]) # 정확히 맞춤
                    e["phase"] = 4; e["state_timer"] = 30
                    # 4. 충격: 장판 생성 (반경 100, 지속 15틱)
                    spawn_field("attack", list(e["pos"]), 100, 15, "ball")
            elif ph == 4: # 4. 충격 유지
                e["state_timer"] -= 1
                if e["state_timer"] <= 0: e["phase"] = 5; e["state_timer"] = 40
            elif ph == 5: # 5. 회복
                e["state_timer"] -= 1
                if e["state_timer"] <= 0: e["boss_state"] = "idle"; e["phase"] = 1; e["state_timer"] = 60

        elif bs == "summon": # 소환하는 패턴
            if ph == 1: # 1. 준비
                e["state_timer"] -= 1
                if e["state_timer"] <= 0: e["phase"] = 2; e["state_timer"] = 40
            elif ph == 2: # 2. 마법진 생성
                e["state_timer"] -= 1
                if e["state_timer"] <= 0:
                    e["phase"] = 3; e["state_timer"] = 20
                    # 3. 소환체 등장
                    for _ in range(2):
                        sx, sy = e["pos"][0] + random.randint(-60, 60), e["pos"][1] + random.randint(-60, 60)
                        world_map[current_coords]["enemies"].append(make_enemy("red_slime", [sx, sy]))
            elif ph == 3: # 3. 소환 대기
                e["state_timer"] -= 1
                if e["state_timer"] <= 0: e["phase"] = 4; e["state_timer"] = 20
            elif ph == 4: # 4. 소환 완료
                e["state_timer"] -= 1
                if e["state_timer"] <= 0: e["phase"] = 5; e["state_timer"] = 30
            elif ph == 5: # 5. 행동(회복)
                e["state_timer"] -= 1
                if e["state_timer"] <= 0: e["boss_state"] = "idle"; e["phase"] = 1; e["state_timer"] = 60

        elif bs == "dash": # 돌진하는 패턴
            if ph == 1: # 1. 준비
                e["state_timer"] -= 1
                if e["state_timer"] <= 0: e["phase"] = 2; e["state_timer"] = 40
            elif ph == 2: # 2. 전방 조준
                e["state_timer"] -= 1
                dx, dy = p_pos[0]-e["pos"][0], p_pos[1]-e["pos"][1]
                dist = math.hypot(dx, dy)
                if dist > 0: e["dash_dir"] = [dx/dist, dy/dist]
                if e["state_timer"] <= 0: e["phase"] = 3; e["state_timer"] = 20
            elif ph == 3: # 3. 돌진
                e["state_timer"] -= 1
                e["pos"][0] += e["dash_dir"][0] * 18
                e["pos"][1] += e["dash_dir"][1] * 18
                if e["state_timer"] <= 0: e["phase"] = 4; e["state_timer"] = 20
            elif ph == 4: # 4. 관통/피해 대기
                e["state_timer"] -= 1
                if e["state_timer"] <= 0: e["phase"] = 5; e["state_timer"] = 40
            elif ph == 5: # 5. 회복
                e["state_timer"] -= 1
                if e["state_timer"] <= 0: e["boss_state"] = "idle"; e["phase"] = 1; e["state_timer"] = 60
                
        elif bs == "shoot_spread": # 탄막 뿌리는 패턴
            if ph == 1: # 1. 준비
                e["state_timer"] -= 1
                if e["state_timer"] <= 0: e["phase"] = 2; e["state_timer"] = 40
            elif ph == 2: # 2. 에너지 축적
                e["state_timer"] -= 1
                if e["state_timer"] <= 0: e["phase"] = 3; e["state_timer"] = 15
            elif ph == 3: # 3. 탄막 발사
                e["state_timer"] -= 1
                if e["state_timer"] == 5:
                    for i in range(16):
                        angle = math.radians(i * (360/16))
                        target = [e["pos"][0] + math.cos(angle)*100, e["pos"][1] + math.sin(angle)*100]
                        spawn_bullet(list(e["pos"]), target, dmg=10)
                if e["state_timer"] <= 0: e["phase"] = 4; e["state_timer"] = 30
            elif ph == 4: # 4. 탄막 확산(대기)
                e["state_timer"] -= 1
                if e["state_timer"] <= 0: e["phase"] = 5; e["state_timer"] = 40
            elif ph == 5: # 5. 회복
                e["state_timer"] -= 1
                if e["state_timer"] <= 0: e["boss_state"] = "idle"; e["phase"] = 1; e["state_timer"] = 60

        elif bs == "shoot_continuous": # 연속 탄막 패턴
            if ph == 1: # 1. 준비
                e["state_timer"] -= 1
                if e["state_timer"] <= 0: e["phase"] = 2; e["state_timer"] = 20
            elif ph == 2: # 2. 1차 발사
                e["state_timer"] -= 1
                if e["state_timer"] == 10:
                    for i in range(8):
                        angle = math.radians(i * 45)
                        spawn_bullet(list(e["pos"]), [e["pos"][0]+math.cos(angle)*100, e["pos"][1]+math.sin(angle)*100], dmg=8)
                if e["state_timer"] <= 0: e["phase"] = 3; e["state_timer"] = 20
            elif ph == 3: # 3. 2차 발사
                e["state_timer"] -= 1
                if e["state_timer"] == 10:
                    for i in range(8):
                        angle = math.radians(i * 45 + 22.5)
                        spawn_bullet(list(e["pos"]), [e["pos"][0]+math.cos(angle)*100, e["pos"][1]+math.sin(angle)*100], dmg=8)
                if e["state_timer"] <= 0: e["phase"] = 4; e["state_timer"] = 20
            elif ph == 4: # 4. 3차 발사
                e["state_timer"] -= 1
                if e["state_timer"] == 10:
                    for i in range(8):
                        angle = math.radians(i * 45 + 11.25)
                        spawn_bullet(list(e["pos"]), [e["pos"][0]+math.cos(angle)*100, e["pos"][1]+math.sin(angle)*100], dmg=8)
                if e["state_timer"] <= 0: e["phase"] = 5; e["state_timer"] = 40
            elif ph == 5: # 5. 회복
                e["state_timer"] -= 1
                if e["state_timer"] <= 0: e["boss_state"] = "idle"; e["phase"] = 1; e["state_timer"] = 60

        if bs == "idle": set_state(e, "idle")
        else: set_state(e, bs)
        advance_anim(e)

    if not e["dead"]:
        e["pos"][0] = max(ROOM_RECT.left + e["radius"], min(e["pos"][0], ROOM_RECT.right - e["radius"]))
        e["pos"][1] = max(ROOM_RECT.top + e["radius"], min(e["pos"][1], ROOM_RECT.bottom - e["radius"]))


def draw_enemy(surface, e):
    px, py = int(e["pos"][0]), int(e["pos"][1])
    frame = get_frame(e)
    if frame:
        dx = player_pos[0] - px; dy = player_pos[1] - py
        angle = math.degrees(math.atan2(-dy, dx))
        rot = pygame.transform.rotate(frame, angle)

        if e["dead"]:
            frames_obj = ENEMY_SPRITES.get(e["type"])
            if isinstance(frames_obj, dict):
                count = len(frames_obj.get(e.get("state", "idle"), [])) or 5
            elif isinstance(frames_obj, list):
                count = len(frames_obj) or 4
            else:
                count = 4
            rot.set_alpha(max(0, int(255*(1 - e["anim_frame"]/max(1, count - 1)))))

        rect = rot.get_rect(center=(px, py))
        surface.blit(rot, rect)
    else:
        color = ENEMY_FALLBACK_COLORS.get(e["type"], ENEMY_COLOR)
        if e["dead"]:
            alpha_val = max(0, int(255*(e["anim_frame"]/4)))
            temp = pygame.Surface((e["radius"]*2, e["radius"]*2), pygame.SRCALPHA)
            pygame.draw.circle(temp, (*color, alpha_val), (e["radius"], e["radius"]), e["radius"])
            surface.blit(temp, (px-e["radius"], py-e["radius"]))
        else:
            if e["type"] == "boss" and not e["dead"]:
                bs = e.get("boss_state", "idle")
                ph = e.get("phase", 1)
                st = e.get("state_timer", 0)
                
                # 상태 텍스트 표시
                st_text = font.render(f"[{bs} - Phase {ph}]", True, WHITE)
                surface.blit(st_text, (px - st_text.get_width()//2, py - e["radius"] - 45))

                # 애니메이션 임시 이펙트 렌더링
                if bs == "slam":
                    if ph == 1: pygame.draw.circle(surface, (200, 50, 200), (px, py), e["radius"]+10, 3)
                    elif ph == 2:
                        tx, ty = int(e.get("target_pos", [px,py])[0]), int(e.get("target_pos", [px,py])[1])
                        pygame.draw.ellipse(surface, (50, 50, 50), (tx-40, ty-15, 80, 30))
                    elif ph == 3: pygame.draw.line(surface, (200, 100, 255), (px, py-150), (px, py), 8)
                    elif ph == 4: pygame.draw.circle(surface, (255, 100, 255), (px, py), e["radius"] + max(0, 30 - st)*4, 4)
                elif bs == "summon":
                    if ph == 2:
                        pygame.draw.circle(surface, (150, 0, 255), (px, py + e["radius"]), 50, 3)
                        pygame.draw.circle(surface, (150, 0, 255), (px, py + e["radius"]), max(1, int(50 * ((40-st)/40))), 1)
                elif bs == "dash":
                    if ph == 2:
                        ex, ey = px + e.get("dash_dir", [1,0])[0]*400, py + e.get("dash_dir", [1,0])[1]*400
                        pygame.draw.line(surface, (255, 50, 50), (px, py), (int(ex), int(ey)), 2)
                    elif ph == 3: color = (255, 100, 100)
                elif bs in ["shoot_spread", "shoot_continuous"]:
                    if ph == 2: pygame.draw.circle(surface, (255, 200, 0), (px, py), e["radius"] + max(1, 15 - int(st/3)), 3)

            pygame.draw.circle(surface, color, (px, py), e["radius"])
            if e.get("stun_timer", 0) > 0:
                pygame.draw.circle(surface, WHITE, (px, py), e["radius"]+4, 2)

    if not e["dead"]:
        bar_w = e["radius"] * 3
        bx, by = px - bar_w//2, py - e["radius"] - 14
        pygame.draw.rect(surface, HP_RED,   (bx, by, bar_w, 7))
        pygame.draw.rect(surface, HP_GREEN, (bx, by, int(bar_w * max(0, e["hp"]/e["max_hp"])), 7))
        draw_status_icons(surface, e)  # 상태이상 아이콘


ITEM_IMAGES = {}
def get_item_image(iid):
    if iid in ITEM_IMAGES: return ITEM_IMAGES[iid]
    path = os.path.join(SPRITE_DIR, f"{iid}.png")
    if os.path.exists(path):
        try:
            img = pygame.image.load(path).convert_alpha()
            img = pygame.transform.scale(img, (32, 32))
            ITEM_IMAGES[iid] = img; return img
        except: pass
    ITEM_IMAGES[iid] = None; return None

def draw_item_drop(surface, cx, cy, item_val, item_type):
    bounce = math.sin(pygame.time.get_ticks() * 0.005) * 5
    cy += int(bounce)
    pygame.draw.circle(surface, (255, 255, 255), (cx, cy), 20, 1)
    if item_type == "word":
        pygame.draw.rect(surface, (50, 100, 255), (cx-10, cy-12, 20, 24))
        pygame.draw.rect(surface, (255, 255, 255), (cx-8, cy-10, 16, 20))
        for oy in [-5, 0, 5]:
            pygame.draw.line(surface, (0, 0, 0), (cx-5, cy+oy), (cx+5, cy+oy), 2)
    elif item_type == "shape":
        pygame.draw.polygon(surface, (50, 255, 50),   [(cx, cy-15),(cx-12,cy),(cx,cy+15),(cx+12,cy)])
        pygame.draw.polygon(surface, (200, 255, 200), [(cx, cy-15),(cx-12,cy),(cx,cy+15),(cx+12,cy)], 2)
    else:
        iid = item_val["id"]
        img = get_item_image(iid)
        if img:
            surface.blit(img, (cx-img.get_width()//2, cy-img.get_height()//2))
        elif iid == "hp_up":
            pygame.draw.polygon(surface, (255,50,50), [(cx,cy+12),(cx-12,cy-2),(cx-6,cy-8),(cx,cy-2),(cx+6,cy-8),(cx+12,cy-2)])
        elif iid == "damage_up":
            pygame.draw.line(surface,(200,200,200),(cx-10,cy+10),(cx+10,cy-10),4)
            pygame.draw.line(surface,(139,69,19),(cx-12,cy+12),(cx-6,cy+6),4)
        elif iid == "speed_up":
            pygame.draw.polygon(surface,(100,200,100),[(cx-8,cy-10),(cx+4,cy-10),(cx+4,cy+10),(cx+12,cy+10),(cx+12,cy+14),(cx-8,cy+14)])
        elif iid == "defense_up":
            pygame.draw.polygon(surface,(100,100,200),[(cx-10,cy-12),(cx+10,cy-12),(cx+10,cy+6),(cx,cy+16),(cx-10,cy+6)])
        elif iid == "duration_up":
            pygame.draw.polygon(surface,(200,200,50),[(cx-10,cy-12),(cx+10,cy-12),(cx,cy),(cx-10,cy+12),(cx+10,cy+12)])
        elif iid == "radius_up":
            pygame.draw.circle(surface,(150,200,255),(cx-4,cy-4),8,3)
            pygame.draw.line(surface,(150,100,50),(cx+2,cy+2),(cx+10,cy+10),4)
        elif iid == "thorns":
            pygame.draw.circle(surface,(150,150,150),(cx,cy),10)
            for ang in range(0,360,45):
                r = math.radians(ang)
                pygame.draw.line(surface,(255,255,255),(cx,cy),(cx+math.cos(r)*16,cy+math.sin(r)*16),2)
        elif iid == "pet":
            pygame.draw.circle(surface,(255,100,150),(cx,cy+6),10)
            pygame.draw.circle(surface,(0,0,0),(cx-4,cy+4),2)
            pygame.draw.circle(surface,(0,0,0),(cx+4,cy+4),2)
        elif iid == "elemental_blade":
            pygame.draw.line(surface,(255,50,255),(cx-10,cy+10),(cx+10,cy-10),6)
            pygame.draw.line(surface,(255,255,255),(cx-10,cy+10),(cx+10,cy-10),2)
        elif iid == "map_reveal":
            pygame.draw.rect(surface,(200,180,140),(cx-12,cy-10,24,20))
            pygame.draw.line(surface,(150,130,90),(cx-4,cy-10),(cx-4,cy+10),2)
            pygame.draw.line(surface,(150,130,90),(cx+4,cy-10),(cx+4,cy+10),2)
        else:
            pygame.draw.circle(surface,(255,255,0),(cx,cy),12)


def generate_map(num_rooms=10):
    rooms = {}
    rooms[(0,0)] = {"visited":False,"type":"start","enemies":[],"cleared":True,"reward":None}
    directions = [(0,-1),(0,1),(-1,0),(1,0)]
    room_coords = [(0,0)]
    while len(rooms) < num_rooms:
        curr = random.choice(room_coords)
        dx, dy = random.choice(directions)
        nxt = (curr[0]+dx, curr[1]+dy)
        if nxt not in rooms:
            rooms[nxt] = {"visited":False,"type":"normal","enemies":[],"cleared":False,"reward":None}
            room_coords.append(nxt)
    rooms[room_coords[-1]]["type"] = "boss"
    return rooms

current_stage = 1
world_map = generate_map(10)
current_coords = (0,0)
ROOM_RECT = pygame.Rect(60, 60, WIDTH-120, HEIGHT-180)

player_pos = [WIDTH//2, ROOM_RECT.centery]
player_facing = [1,0]
player_speed = 5
player_radius = 15
player_words = ["attack"]
player_shapes = []
player_max_hp = 100
player_hp = 100
player_immune_timer = 0

player_stats = {
    "skill_duration_mult": 1.0, "radius_mult": 1.0,
    "damage_mult": 1.0, "speed_mult": 1.0,
    "thorns_damage": 0, "defense_up": 0.0
}
player_items = {"pet": False, "elemental_blade": False, "map_reveal": False}
acquired_items_counts = {}
pet_pos = [WIDTH//2, ROOM_RECT.centery]
pet_attack_timer = 0

STACKABLE_ITEMS = [
    {"id":"duration_up","name":"모래시계"}, {"id":"radius_up","name":"확대경"},
    {"id":"damage_up","name":"전사의 검"}, {"id":"speed_up","name":"바람의 부츠"},
    {"id":"thorns","name":"가시 갑옷"}, {"id":"hp_up","name":"생명의 심장"},
    {"id":"defense_up","name":"강철 방패"}
]
NON_STACKABLE_ITEMS = [
    {"id":"pet","name":"미니 슬라임"}, {"id":"elemental_blade","name":"속성 부여검"},
    {"id":"map_reveal","name":"마법 지도"}
]

input_text = ""
attack_timer = 0
attack_data = {"angle":0,"radius":0,"half_cone":0}
message = "플레이 해보세요"
message_timer = 180
active_fields = []

def spawn_field(f_type, pos, radius, duration, shape, vx=0, vy=0):
    active_fields.append({
        "pos": list(pos), "type": f_type, "radius": radius,
        "timer": duration, "max_timer": duration,
        "shape": shape, "vx": vx, "vy": vy
    })

# ── 크기 설정 테이블 ──────────────────────────────────────────────────────────
# shape별 기본 반지름 (ball/spike는 field보다 작게)
SHAPE_RADIUS = {
    "field":  80,
    "ball":   20,   # ← 축소 (기존 40)
    "spike":  40,   # ← 축소 (기존 60)
    "square": 60,
}
# shape별 기본 지속시간
SHAPE_DURATION = {
    "field":  240,
    "ball":   120,
    "spike":  60,
    "square": 300,
}
# 원소별 기본 지속시간 오버라이드
ELEMENT_DURATION = {
    "attack": 40,
    "bomb":   20,
    "guard":  300,
    "heal":   240,
}

def cast_spell(element, shape, p_pos, facing, target_e):
    # 반지름 결정
    radius = SHAPE_RADIUS.get(shape, 60)
    if element in ["bomb", "explosion"] and shape in ["ball","spike"]:
        radius = int(radius * 1.2)  # 폭발류는 약간 크게

    # 지속시간 결정
    duration = ELEMENT_DURATION.get(element, SHAPE_DURATION.get(shape, 240))
    if shape in SHAPE_DURATION and element not in ELEMENT_DURATION:
        duration = SHAPE_DURATION[shape]

    # radius_mult / duration_mult 적용
    radius = int(radius * player_stats["radius_mult"])
    if duration > 60:
        duration = int(duration * player_stats["skill_duration_mult"])

    vx, vy = 0, 0
    if shape == "field":
        spawn_pos = list(p_pos)
    elif shape == "ball":
        spawn_pos = list(p_pos)
        if target_e:
            dx,dy = target_e["pos"][0]-p_pos[0], target_e["pos"][1]-p_pos[1]
            dist = math.hypot(dx,dy)
            if dist > 0: vx,vy = (dx/dist)*12,(dy/dist)*12
        else:
            vx,vy = facing[0]*12, facing[1]*12
    elif shape == "spike":
        spawn_pos = list(target_e["pos"]) if target_e else [p_pos[0]+facing[0]*100, p_pos[1]+facing[1]*100]
    elif shape == "square":
        if target_e:
            dx,dy = target_e["pos"][0]-p_pos[0], target_e["pos"][1]-p_pos[1]
            dist = math.hypot(dx,dy)
            spawn_pos = [p_pos[0]+(dx/dist)*80, p_pos[1]+(dy/dist)*80] if dist > 0 else list(p_pos)
        else:
            spawn_pos = [p_pos[0]+facing[0]*80, p_pos[1]+facing[1]*80]

    spawn_field(element, spawn_pos, radius, duration, shape, vx, vy)

NORMAL_ENEMY_TYPES = ["red_slime", "yellow_eye", "stone_guardian", "shadow_bat"]

def enter_room(coords):
    global current_coords, message, message_timer
    current_coords = coords
    room = world_map[coords]
    room["visited"] = True
    active_fields.clear(); bullets.clear()
    if not room["cleared"] and len(room["enemies"])==0 and coords!=(0,0):
        if room["type"] == "normal":
            for _ in range(random.randint(2,4)):
                etype = random.choice(NORMAL_ENEMY_TYPES)
                e = make_enemy(etype, [
                    random.randint(150, WIDTH-150),
                    random.randint(150, ROOM_RECT.bottom-100)
                ])
                room["enemies"].append(e)
        elif room["type"] == "boss":
            e = make_enemy("boss", [WIDTH//2, ROOM_RECT.centery])
            room["enemies"].append(e)

enter_room((0,0))

def is_discovered(coords):
    if player_items.get("map_reveal", False): return True
    if world_map[coords]["visited"]: return True
    for dx,dy in [(0,1),(0,-1),(1,0),(-1,0)]:
        nb = (coords[0]+dx, coords[1]+dy)
        if nb in world_map and world_map[nb]["visited"]: return True
    return False

def draw_button(surface, text, rect, mouse_pos, mouse_click):
    hover = rect.collidepoint(mouse_pos)
    color = (80, 80, 80) if hover else (50, 50, 50)
    pygame.draw.rect(surface, color, rect)
    pygame.draw.rect(surface, WHITE, rect, 2)
    txt_surf = font.render(text, True, WHITE)
    surface.blit(txt_surf, (rect.centerx - txt_surf.get_width()//2, rect.centery - txt_surf.get_height()//2))
    return hover and mouse_click

game_state = "START_MENU"
game_over_timer = 0

def reset_game(full_reset=True):
    global current_stage, world_map, current_coords, player_pos, player_facing
    global player_words, player_shapes, player_max_hp, player_hp, player_immune_timer
    global player_stats, player_items, acquired_items_counts, pet_pos, pet_attack_timer
    global input_text, attack_timer, attack_data, message, message_timer
    global active_fields, bullets, player_particles, player_prev_hp
    
    if full_reset:
        current_stage = 1
        player_words = ["attack"]
        player_shapes = []
        player_max_hp = 100
        player_hp = 100
        player_stats = {
            "skill_duration_mult": 1.0, "radius_mult": 1.0,
            "damage_mult": 1.0, "speed_mult": 1.0,
            "thorns_damage": 0, "defense_up": 0.0
        }
        player_items = {"pet": False, "elemental_blade": False, "map_reveal": False}
        acquired_items_counts = {}
        input_text = ""
    else:
        current_stage += 1
        player_hp = player_max_hp
        input_text = ""
    
    world_map = generate_map(10 + current_stage)
    current_coords = (0,0)
    player_pos = [WIDTH//2, ROOM_RECT.centery]
    player_facing = [1,0]
    player_immune_timer = 0
    player_prev_hp = player_hp
    pet_pos = [WIDTH//2, ROOM_RECT.centery]
    pet_attack_timer = 0
    attack_timer = 0
    message = "플레이 해보세요" if full_reset else f"스테이지 {current_stage} 시작!"
    message_timer = 180
    active_fields.clear()
    bullets.clear()
    player_particles.clear()
    enter_room((0,0))

running = True
player_prev_hp = player_hp

while running:
    mouse_pos = pygame.mouse.get_pos()
    mouse_click = False

    screen.fill(BLACK)
    room = world_map[current_coords]
    living_enemies = [e for e in room["enemies"] if not e["dead"] and e["hp"] > 0]
    room_cleared = (len(living_enemies) == 0)

    if player_immune_timer > 0:
        player_immune_timer -= 1

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: mouse_click = True
        elif event.type == pygame.KEYDOWN:
            if game_state != "PLAYING":
                if game_state == "START_MENU" and event.key == pygame.K_RETURN: game_state = "PLAYING"
                elif game_state == "GAME_OVER" and event.key == pygame.K_RETURN: reset_game(True); game_state = "PLAYING"
                elif game_state == "STAGE_CLEAR" and event.key == pygame.K_RETURN: reset_game(False); game_state = "PLAYING"
                continue

            if event.key == pygame.K_RETURN:
                cmd = input_text.strip().lower()
                input_text = ""

                # ── 치트키 ────────────────────────────────────────────────────
                if cmd == "cheat":
                    player_words  = ["attack","fire","poison","ice","bomb","tree","guard","heal"]
                    player_shapes = ["ball","square","spike"]
                    player_items["pet"] = False
                    player_items["elemental_blade"] = player_items["map_reveal"] = True
                    acquired_items_counts.update({"미니 슬라임":1, "속성 부여검":1, "마법 지도":1})
                    player_stats.update({"speed_mult":1.5,"damage_mult":3.0,
                                         "skill_duration_mult":2.0,"radius_mult":1.5,
                                         "defense_up":0.5,"thorns_damage":20})
                    player_max_hp = 200; player_hp = 200
                    message = "치트 활성화!"; message_timer = 180; continue
                elif cmd == "cheat word":
                    player_words  = ["attack","fire","poison","ice","bomb","tree","guard","heal"]
                    player_shapes = ["ball","square","spike"]
                    message = "치트1: 모든 단어/형태!"; message_timer = 180; continue
                elif cmd == "cheat item":
                    player_items["pet"] = player_items["elemental_blade"] = player_items["map_reveal"] = True
                    acquired_items_counts.update({"미니 슬라임":1, "속성 부여검":1, "마법 지도":1})
                    player_stats.update({"speed_mult":1.5,"damage_mult":3.0,
                                         "skill_duration_mult":2.0,"radius_mult":1.5,
                                         "defense_up":0.5,"thorns_damage":20})
                    player_max_hp = 200; player_hp = 200
                    message = "치트2: 모든 아이템!"; message_timer = 180; continue

                tokens = cmd.split()
                if len(tokens) > 0:
                    element = tokens[0]
                    shape   = tokens[1] if len(tokens) > 1 else "field"

                    if element == "attack" and shape == "field":
                        attack_radius = 140 * player_stats["radius_mult"]
                        half_cone = math.radians(30)
                        base_angle = 0
                        if living_enemies:
                            closest_e = min(living_enemies, key=lambda e: math.hypot(e["pos"][0]-player_pos[0], e["pos"][1]-player_pos[1]))
                            dx = closest_e["pos"][0]-player_pos[0]
                            dy = closest_e["pos"][1]-player_pos[1]
                            base_angle = math.atan2(dy, dx)
                            for e in living_enemies:
                                edx = e["pos"][0]-player_pos[0]; edy = e["pos"][1]-player_pos[1]
                                dist = math.hypot(edx, edy)
                                if dist <= attack_radius:
                                    target_angle = math.atan2(edy, edx)
                                    angle_diff = (target_angle-base_angle+math.pi)%(2*math.pi)-math.pi
                                    if abs(angle_diff) <= half_cone:
                                        e["hp"] -= 15 * player_stats["damage_mult"]
                                        if player_items["elemental_blade"]:
                                            re = random.choice(["fire","ice","poison","bomb","tree"])
                                            if re in ELEMENT_STATUS:
                                                apply_status(e, ELEMENT_STATUS[re], player_stats["damage_mult"])
                                            elif re == "bomb":
                                                e["hp"] -= 10 * player_stats["damage_mult"]
                        attack_timer = 15
                        attack_data = {"angle":base_angle,"radius":attack_radius,"half_cone":half_cone}

                    elif element in player_words and (shape in player_shapes or shape == "field"):
                        closest_e = min(living_enemies, key=lambda e: math.hypot(e["pos"][0]-player_pos[0],e["pos"][1]-player_pos[1])) if living_enemies else None
                        cast_spell(element, shape, player_pos, player_facing, closest_e)
                    else:
                        message = "미획득 단어/형태 조합입니다!"; message_timer = 60

            elif event.key == pygame.K_BACKSPACE: input_text = input_text[:-1]
            elif event.key == pygame.K_SPACE:     input_text += " "
            elif event.unicode != "":
                if event.unicode.isalpha() or ('가'<=event.unicode<='힣'):
                    input_text += event.unicode

    if game_state == "START_MENU":
        title_surf = big_font.render("Magic Typing Game", True, (255, 200, 100))
        screen.blit(title_surf, (WIDTH//2 - title_surf.get_width()//2, HEIGHT//3))
        btn_start = pygame.Rect(WIDTH//2 - 100, HEIGHT//2, 200, 50)
        if draw_button(screen, "Start Game", btn_start, mouse_pos, mouse_click):
            game_state = "PLAYING"
        pygame.display.flip()
        clock.tick(60)
        continue

    elif game_state == "GAME_OVER":
        title_surf = big_font.render("GAME OVER", True, (255, 50, 50))
        screen.blit(title_surf, (WIDTH//2 - title_surf.get_width()//2, HEIGHT//3))
        btn_restart = pygame.Rect(WIDTH//2 - 100, HEIGHT//2, 200, 50)
        btn_quit = pygame.Rect(WIDTH//2 - 100, HEIGHT//2 + 70, 200, 50)
        if draw_button(screen, "Restart", btn_restart, mouse_pos, mouse_click):
            reset_game(True)
            game_state = "PLAYING"
        if draw_button(screen, "Quit", btn_quit, mouse_pos, mouse_click):
            running = False
        pygame.display.flip()
        clock.tick(60)
        continue

    elif game_state == "STAGE_CLEAR":
        title_surf = big_font.render("STAGE 3 CLEAR!", True, (100, 255, 100))
        screen.blit(title_surf, (WIDTH//2 - title_surf.get_width()//2, HEIGHT//3))
        btn_continue = pygame.Rect(WIDTH//2 - 100, HEIGHT//2, 200, 50)
        btn_restart = pygame.Rect(WIDTH//2 - 100, HEIGHT//2 + 70, 200, 50)
        btn_quit = pygame.Rect(WIDTH//2 - 100, HEIGHT//2 + 140, 200, 50)
        if draw_button(screen, "Continue", btn_continue, mouse_pos, mouse_click):
            reset_game(False)
            game_state = "PLAYING"
        if draw_button(screen, "Restart", btn_restart, mouse_pos, mouse_click):
            reset_game(True)
            game_state = "PLAYING"
        if draw_button(screen, "Quit", btn_quit, mouse_pos, mouse_click):
            running = False
        pygame.display.flip()
        clock.tick(60)
        continue

    # ── 플레이어 이동 ──────────────────────────────────────────────────────────
    if player_hp > 0:
        ps   = player_speed * player_stats["speed_mult"]
        keys = pygame.key.get_pressed()
        nx, ny = player_pos[0], player_pos[1]
        moving = False
        if keys[pygame.K_LEFT]:  nx -= ps; player_facing = [-1,0]; moving = True
        if keys[pygame.K_RIGHT]: nx += ps; player_facing = [1,0];  moving = True
        if keys[pygame.K_UP]:    ny -= ps; player_facing = [0,-1]; moving = True
        if keys[pygame.K_DOWN]:  ny += ps; player_facing = [0,1];  moving = True
        if moving:
            trail_pos = [player_pos[0]-player_facing[0]*12, player_pos[1]-player_facing[1]*12]
            spawn_player_particles(trail_pos, (100,180,255), count=1, speed=1.0, size_range=(2,4))
    else:
        nx, ny = player_pos[0], player_pos[1]

    door_w = 80
    if nx-player_radius < ROOM_RECT.left:
        tgt = (current_coords[0]-1, current_coords[1])
        if tgt in world_map and (ROOM_RECT.centery-door_w//2<ny<ROOM_RECT.centery+door_w//2) and room_cleared:
            enter_room(tgt); nx = ROOM_RECT.right-player_radius-10
        else: nx = ROOM_RECT.left+player_radius
    elif nx+player_radius > ROOM_RECT.right:
        tgt = (current_coords[0]+1, current_coords[1])
        if tgt in world_map and (ROOM_RECT.centery-door_w//2<ny<ROOM_RECT.centery+door_w//2) and room_cleared:
            enter_room(tgt); nx = ROOM_RECT.left+player_radius+10
        else: nx = ROOM_RECT.right-player_radius
    if ny-player_radius < ROOM_RECT.top:
        tgt = (current_coords[0], current_coords[1]-1)
        if tgt in world_map and (WIDTH//2-door_w//2<nx<WIDTH//2+door_w//2) and room_cleared:
            enter_room(tgt); ny = ROOM_RECT.bottom-player_radius-10
        else: ny = ROOM_RECT.top+player_radius
    elif ny+player_radius > ROOM_RECT.bottom:
        tgt = (current_coords[0], current_coords[1]+1)
        if tgt in world_map and (WIDTH//2-door_w//2<nx<WIDTH//2+door_w//2) and room_cleared:
            enter_room(tgt); ny = ROOM_RECT.top+player_radius+10
        else: ny = ROOM_RECT.bottom-player_radius
    player_pos[0], player_pos[1] = nx, ny

    # ── 속도 초기화 (상태이상 처리 전 base_speed로 리셋은 update_enemy에서) ──
    for e in room["enemies"]:
        if not e["dead"]:
            e["speed"] = e["base_speed"]

    # ── ball 이동 ──────────────────────────────────────────────────────────────
    for f in active_fields:
        if f["shape"] == "ball":
            f["pos"][0] += f["vx"]; f["pos"][1] += f["vy"]

    # ── 펫 ────────────────────────────────────────────────────────────────────
    if player_items["pet"] and player_hp > 0:
        pet_pos[0] += (player_pos[0]-35-pet_pos[0])*0.05
        pet_pos[1] += (player_pos[1]-35-pet_pos[1])*0.05
        pet_attack_timer -= 1
        if pet_attack_timer <= 0 and living_enemies:
            closest_e = min(living_enemies, key=lambda e: math.hypot(e["pos"][0]-pet_pos[0],e["pos"][1]-pet_pos[1]))
            dx,dy = closest_e["pos"][0]-pet_pos[0], closest_e["pos"][1]-pet_pos[1]
            dist = math.hypot(dx,dy)
            if dist > 0:
                vx,vy = (dx/dist)*10,(dy/dist)*10
                spawn_field("attack", list(pet_pos), int(25*player_stats["radius_mult"]), 30, "ball", vx, vy)
            pet_attack_timer = 90

    # ── 콤보 ──────────────────────────────────────────────────────────────────
    combo_removes, combo_adds = [], []
    def create_combo(ctype, base_rad, base_dur, cx, cy):
        r = int(base_rad*player_stats["radius_mult"])
        d = base_dur if base_dur<=60 else int(base_dur*player_stats["skill_duration_mult"])
        return {"pos":[cx,cy],"type":ctype,"radius":r,"timer":d,"max_timer":d,"shape":"field","vx":0,"vy":0}

    for i in range(len(active_fields)):
        for j in range(i+1, len(active_fields)):
            f1,f2 = active_fields[i], active_fields[j]
            if f1 in combo_removes or f2 in combo_removes: continue
            dist = math.hypot(f1["pos"][0]-f2["pos"][0], f1["pos"][1]-f2["pos"][1])
            if dist < f1["radius"]+f2["radius"]:
                combo = {f1["type"],f2["type"]}
                mx = (f1["pos"][0]+f2["pos"][0])/2; my = (f1["pos"][1]+f2["pos"][1])/2
                if   combo=={"fire","poison"}:   combo_removes.extend([f1,f2]); combo_adds.append(create_combo("explosion",    150,  20,mx,my))
                elif combo=={"fire","ice"}:       combo_removes.extend([f1,f2]); combo_adds.append(create_combo("steam",        130, 240,mx,my))
                elif combo=={"ice","poison"}:     combo_removes.extend([f1,f2]); combo_adds.append(create_combo("plague_storm", 140, 300,mx,my))
                elif combo=={"bomb","poison"}:    combo_removes.extend([f1,f2]); combo_adds.append(create_combo("toxic_cloud",  180, 400,mx,my))
                elif combo=={"heal","tree"}:      combo_removes.extend([f1,f2]); combo_adds.append(create_combo("sanctuary",    160, 300,mx,my))
                elif combo=={"fire","tree"}:      combo_removes.extend([f1,f2]); combo_adds.append(create_combo("wildfire",     150, 120,mx,my))
                elif combo=={"guard","ice"}:      combo_removes.extend([f1,f2]); combo_adds.append(create_combo("glacial_barricade",140,300,mx,my))
                elif combo=={"guard","bomb"}:     combo_removes.extend([f1,f2]); combo_adds.append(create_combo("counter_shield",  130,150,mx,my))
                elif combo=={"guard","heal"}:     combo_removes.extend([f1,f2]); combo_adds.append(create_combo("divine_grace",    160,240,mx,my))

    for f in combo_removes:
        if f in active_fields: active_fields.remove(f)
    active_fields.extend(combo_adds)

    # ── 필드 피해 + 상태이상 부여 ────────────────────────────────────────────
    for f in active_fields[:]:
        f["timer"] -= 1
        if f["timer"] <= 0:
            active_fields.remove(f); continue

        p_dist = math.hypot(player_pos[0]-f["pos"][0], player_pos[1]-f["pos"][1])
        is_p_hit = False
        if f["shape"] in ["field","ball","spike"] and p_dist <= f["radius"]+player_radius:
            is_p_hit = True
        elif f["shape"] == "square" and (abs(player_pos[0]-f["pos"][0])<=f["radius"]+player_radius) and (abs(player_pos[1]-f["pos"][1])<=f["radius"]+player_radius):
            is_p_hit = True

        if is_p_hit:
            if f["type"] == "heal":         player_hp = min(player_max_hp, player_hp+0.2)
            elif f["type"] == "guard":      player_immune_timer = max(player_immune_timer, 10)
            elif f["type"] == "sanctuary":  player_hp = min(player_max_hp, player_hp+0.5)
            elif f["type"] == "divine_grace":
                player_immune_timer = max(player_immune_timer, 10)
                player_hp = min(player_max_hp, player_hp+0.3)

        dm = player_stats["damage_mult"]

        # 필드와 접촉한 적 처리
        for e in living_enemies:
            dx,dy = e["pos"][0]-f["pos"][0], e["pos"][1]-f["pos"][1]
            dist = math.hypot(dx,dy)
            is_hit = False
            if f["shape"] in ["field","ball","spike"]:
                is_hit = dist <= f["radius"]+e["radius"]
            elif f["shape"] == "square":
                is_hit = (abs(dx)<=f["radius"]+e["radius"]) and (abs(dy)<=f["radius"]+e["radius"])

            if not is_hit:
                continue

            # ── 물리/넉백 효과 ────────────────────────────────────────────
            if f["shape"] == "field":
                e["speed"] *= 0.5
            elif f["shape"] == "spike":
                e["stun_timer"] = 30
            elif f["shape"] == "square":
                if dist > 0: e["pos"][0]+=(dx/dist)*8; e["pos"][1]+=(dy/dist)*8
            if f["type"] in ["sanctuary","glacial_barricade","counter_shield"]:
                if dist > 0:
                    kb = 12 if f["type"]=="counter_shield" else 5
                    e["pos"][0]+=(dx/dist)*kb; e["pos"][1]+=(dy/dist)*kb

            # ── 피해 + 상태이상 부여 ─────────────────────────────────────
            ftype = f["type"]

            # 직접 피해
            if ftype == "attack":
                e["hp"] -= 1.5 * dm
                if player_items["elemental_blade"] and random.random() < 0.1:
                    re = random.choice(["fire","ice","poison","tree"])
                    apply_status(e, ELEMENT_STATUS[re], dm)
            elif ftype == "bomb":
                e["hp"] -= 8 * dm
            elif ftype == "explosion":
                e["hp"] -= 8 * dm
            elif ftype == "steam":
                e["hp"] -= 1.0 * dm
            elif ftype == "toxic_cloud":
                e["hp"] -= 1.0 * dm
            elif ftype == "wildfire":
                e["hp"] -= 2.0 * dm
                apply_status(e, "burn", dm * 0.5)          # wildfire → 추가 burn
            elif ftype == "counter_shield":
                e["hp"] -= 4.0 * dm

            # 상태이상 부여 (원소 필드)
            elif ftype == "fire":
                apply_status(e, "burn", dm)
            elif ftype == "poison":
                apply_status(e, "poison", dm)
            elif ftype == "ice":
                apply_status(e, "freeze", dm)
            elif ftype == "tree":
                apply_status(e, "root", dm)

            # 콤보 상태이상
            elif ftype == "plague_storm":
                apply_status(e, "plague", dm)
            elif ftype == "glacial_barricade":
                apply_status(e, "freeze", dm * 1.5)

            # 주의: heal/guard/sanctuary/divine_grace 등은 플레이어 전용 → 적에게 무효

    # ── 총알 업데이트 ──────────────────────────────────────────────────────────
    for b in bullets[:]:
        b["pos"][0] += b["vx"]; b["pos"][1] += b["vy"]
        b["timer"] -= 1
        if b["timer"] <= 0 or not ROOM_RECT.collidepoint(b["pos"][0], b["pos"][1]):
            bullets.remove(b); continue
        if player_hp > 0 and player_immune_timer <= 0:
            bd = math.hypot(player_pos[0]-b["pos"][0], player_pos[1]-b["pos"][1])
            if bd < player_radius+b["radius"]:
                actual_dmg = b["dmg"]*(1.0-player_stats["defense_up"])
                player_hp = max(0, player_hp-actual_dmg)
                player_immune_timer = 60
                bullets.remove(b); continue

    # ── 적 AI ────────────────────────────────────────────────────────────────
    for e in room["enemies"]:
        update_enemy(e, player_pos, player_hp, living_enemies, active_fields, player_stats["damage_mult"])

    room["enemies"] = [e for e in room["enemies"] if not (e["dead"] and e["anim_frame"] >= 3)]

    # ── 적 충돌 / 플레이어 데미지 ─────────────────────────────────────────────
    for i, e in enumerate(living_enemies):
        for j in range(i+1, len(living_enemies)):
            oe = living_enemies[j]
            ex,ey = e["pos"][0]-oe["pos"][0], e["pos"][1]-oe["pos"][1]
            ed = math.hypot(ex,ey); emd = e["radius"]+oe["radius"]
            if ed < emd and ed > 0:
                ov = emd-ed
                e["pos"][0]+=(ex/ed)*(ov/2);   e["pos"][1]+=(ey/ed)*(ov/2)
                oe["pos"][0]-=(ex/ed)*(ov/2);  oe["pos"][1]-=(ey/ed)*(ov/2)

        pdx,pdy = player_pos[0]-e["pos"][0], player_pos[1]-e["pos"][1]
        pd = math.hypot(pdx,pdy); md = player_radius+e["radius"]
        if pd < md and pd > 0:
            player_pos[0]+=(pdx/pd)*(md-pd); player_pos[1]+=(pdy/pd)*(md-pd)
            if player_immune_timer <= 0 and player_hp > 0:
                stage = globals().get("current_stage", 1)
                dmg_mult = 1.0 + (stage - 1) * 0.2
                base_dmg = (25 if e["type"]=="boss" else 10) * dmg_mult
                actual_dmg = base_dmg*(1.0-player_stats["defense_up"])
                player_hp = max(0, player_hp-actual_dmg)
                player_immune_timer = 60
                if player_stats["thorns_damage"] > 0:
                    e["hp"] -= player_stats["thorns_damage"]

    # ── 방 클리어 / 보상 ──────────────────────────────────────────────────────
    if not room["cleared"] and room_cleared and current_coords!=(0,0):
        room["cleared"] = True
        all_elements=["fire","poison","ice","bomb","tree","guard","heal"]
        all_shapes   =["ball","square","spike"]
        av_words  = [w for w in all_elements if w not in player_words]
        av_shapes = [s for s in all_shapes   if s not in player_shapes]
        av_ns     = [it for it in NON_STACKABLE_ITEMS if not player_items.get(it["id"],False)]
        pool = []
        if av_words:  pool.extend(["word"]*2)
        if av_shapes: pool.extend(["shape"]*2)
        pool.extend(["stackable_item"]*4)
        if av_ns:     pool.extend(["non_stackable_item"]*2)
        if pool:
            r_type = random.choice(pool); r_val = None
            if   r_type=="word":              r_val=random.choice(av_words)
            elif r_type=="shape":             r_val=random.choice(av_shapes)
            elif r_type=="stackable_item":    r_val=random.choice(STACKABLE_ITEMS)
            elif r_type=="non_stackable_item":r_val=random.choice(av_ns)
            room["reward"]={"data":{"type":r_type,"value":r_val},"pos":[WIDTH//2,ROOM_RECT.centery]}
            if room["type"] == "boss":
                room["portal"] = [WIDTH//2, ROOM_RECT.top + 80]

    if room.get("reward"):
        rd=room["reward"]
        dist=math.hypot(rd["pos"][0]-player_pos[0], rd["pos"][1]-player_pos[1])
        if dist < 40:
            rv=rd["data"]["value"]; rt=rd["data"]["type"]
            if rt=="word":   player_words.append(rv);  message=f"단어 획득: '{rv}'!"
            elif rt=="shape":player_shapes.append(rv); message=f"형태 획득: '{rv}'!"
            elif rt in ["stackable_item","non_stackable_item"]:
                iid=rv["id"]; iname=rv["name"]
                acquired_items_counts[iname] = acquired_items_counts.get(iname, 0) + 1
                if   iid=="duration_up": player_stats["skill_duration_mult"]+=0.3
                elif iid=="radius_up":   player_stats["radius_mult"]+=0.25
                elif iid=="damage_up":   player_stats["damage_mult"]+=0.3
                elif iid=="speed_up":    player_stats["speed_mult"]+=0.15
                elif iid=="thorns":      player_stats["thorns_damage"]+=10
                elif iid=="hp_up":       player_max_hp+=30; player_hp+=30
                elif iid=="defense_up":  player_stats["defense_up"]=min(0.7,player_stats["defense_up"]+0.15)
                elif iid in ["pet","elemental_blade","map_reveal"]: player_items[iid]=True
                message=f"아이템 획득: {iname}!"
            message_timer=150; room["reward"]=None

    # ──────────────────────────────────────────
    # 렌더링
    # ──────────────────────────────────────────
    pygame.draw.rect(screen, WALL_COLOR,  (0,0,WIDTH,HEIGHT-100))
    pygame.draw.rect(screen, FLOOR_COLOR, ROOM_RECT)

    door_color = DOOR_OPEN if room_cleared else DOOR_LOCKED
    door_thick = 15
    for dx,dy in [(0,-1),(0,1),(-1,0),(1,0)]:
        nb=(current_coords[0]+dx, current_coords[1]+dy)
        if nb in world_map:
            if   (dx,dy)==(0,-1): pygame.draw.rect(screen,door_color,(WIDTH//2-door_w//2,ROOM_RECT.top-door_thick,door_w,door_thick+5))
            elif (dx,dy)==(0,1):  pygame.draw.rect(screen,door_color,(WIDTH//2-door_w//2,ROOM_RECT.bottom-5,door_w,door_thick+5))
            elif (dx,dy)==(-1,0): pygame.draw.rect(screen,door_color,(ROOM_RECT.left-door_thick,ROOM_RECT.centery-door_w//2,door_thick+5,door_w))
            elif (dx,dy)==(1,0):  pygame.draw.rect(screen,door_color,(ROOM_RECT.right-5,ROOM_RECT.centery-door_w//2,door_thick+5,door_w))

    if active_fields:
        fs = pygame.Surface((WIDTH,HEIGHT), pygame.SRCALPHA)
        for f in active_fields:
            color = FIELD_COLORS.get(f["type"],(255,255,255,100))
            if f["type"] in ["explosion","bomb","wildfire","counter_shield"]:
                fade = max(0, int(255*(f["timer"]/f["max_timer"])))
                color = (color[0],color[1],color[2],fade)
            if f["shape"] in ["ball","field"]:
                pygame.draw.circle(fs, color, (int(f["pos"][0]),int(f["pos"][1])), f["radius"])
            elif f["shape"] == "square":
                rect = pygame.Rect(f["pos"][0]-f["radius"],f["pos"][1]-f["radius"],f["radius"]*2,f["radius"]*2)
                pygame.draw.rect(fs,color,rect); pygame.draw.rect(fs,(255,255,255,100),rect,2)
            elif f["shape"] == "spike":
                pts=[]
                for k in range(8):
                    r = f["radius"] if k%2==0 else f["radius"]*0.4
                    ang = math.radians(k*45)
                    pts.append((f["pos"][0]+math.cos(ang)*r, f["pos"][1]+math.sin(ang)*r))
                pygame.draw.polygon(fs,color,pts)
        screen.blit(fs,(0,0))

    for b in bullets:
        pygame.draw.circle(screen, b["color"], (int(b["pos"][0]),int(b["pos"][1])), b["radius"])
        pygame.draw.circle(screen, WHITE,      (int(b["pos"][0]),int(b["pos"][1])), b["radius"], 1)

    if player_items["pet"] and player_hp > 0:
        pygame.draw.circle(screen,(255,150,200),(int(pet_pos[0]),int(pet_pos[1])),10)
        pygame.draw.circle(screen,WHITE,        (int(pet_pos[0]),int(pet_pos[1])),10,2)

    for e in room["enemies"]:
        draw_enemy(screen, e)

    if room.get("reward"):
        rv=room["reward"]["data"]["value"]; rt=room["reward"]["data"]["type"]
        draw_item_drop(screen, room["reward"]["pos"][0], room["reward"]["pos"][1], rv, rt)

    if room.get("portal"):
        px, py = room["portal"]
        pygame.draw.circle(screen, (50, 0, 150), (px, py), 25)
        pygame.draw.circle(screen, (150, 50, 255), (px, py), 20)
        pygame.draw.circle(screen, (255, 255, 255), (px, py), 15, 2)
        pt_text = font.render("Next Stage", True, WHITE)
        screen.blit(pt_text, (px - pt_text.get_width()//2, py - 40))
        
        if math.hypot(player_pos[0]-px, player_pos[1]-py) < 40:
            if current_stage >= 3:
                game_state = "STAGE_CLEAR"
            else:
                reset_game(False)

    update_and_draw_particles(screen)

    if player_hp > 0:
        if PLAYER_SPRITE:
            pulse = 1.0 + 0.05*math.sin(pygame.time.get_ticks()*0.005)
            spin_angle = (pygame.time.get_ticks()*0.05) % 360
            rotated_sprite = pygame.transform.rotate(PLAYER_SPRITE, spin_angle)
            w,h = rotated_sprite.get_size()
            scaled_sprite = pygame.transform.scale(rotated_sprite, (int(w*pulse),int(h*pulse)))
            if player_immune_timer > 0 and (player_immune_timer//4)%2==0:
                scaled_sprite.set_alpha(100)
            else:
                scaled_sprite.set_alpha(255)
            rect = scaled_sprite.get_rect(center=(int(player_pos[0]),int(player_pos[1])))
            screen.blit(scaled_sprite, rect)
            if player_immune_timer > 0:
                pygame.draw.circle(screen,WHITE,(int(player_pos[0]),int(player_pos[1])),player_radius+4,1)
        else:
            pc = PLAYER_IMMUNE if player_immune_timer > 0 else PLAYER_COLOR
            pygame.draw.circle(screen, pc, (int(player_pos[0]),int(player_pos[1])), player_radius)
            if player_immune_timer > 0:
                pygame.draw.circle(screen,WHITE,(int(player_pos[0]),int(player_pos[1])),player_radius+2,2)

    if attack_timer > 0:
        pts = [(player_pos[0],player_pos[1])]
        sa = attack_data["angle"]-attack_data["half_cone"]
        ea = attack_data["angle"]+attack_data["half_cone"]
        for k in range(11):
            theta = sa+(ea-sa)*(k/10)
            pts.append((player_pos[0]+math.cos(theta)*attack_data["radius"],
                        player_pos[1]+math.sin(theta)*attack_data["radius"]))
        pygame.draw.polygon(screen,WHITE,pts,3)
        attack_timer -= 1

    MMX,MMY,CELL,GAP = WIDTH-100,80,15,3
    for coords,info in world_map.items():
        if is_discovered(coords):
            dx2 = MMX+(coords[0]-current_coords[0])*(CELL+GAP)-CELL//2
            dy2 = MMY+(coords[1]-current_coords[1])*(CELL+GAP)-CELL//2
            c = MM_CURRENT if coords==current_coords else (MM_BOSS if info["type"]=="boss" else (MM_VISITED if info["visited"] else MM_DISCOVERED))
            pygame.draw.rect(screen,c,(dx2,dy2,CELL,CELL))
            pygame.draw.rect(screen,WHITE,(dx2,dy2,CELL,CELL),1)

    # 스탯창 (왼쪽 위 - 아이작 스타일)
    stat_start_x, stat_start_y, stat_gap = 15, 20, 24
    stats = [
        {"name": "HP", "val": f"{int(player_hp)}/{player_max_hp}", "color": WHITE if player_hp>25 else HP_RED},
        {"name": "DMG", "val": f"{player_stats['damage_mult']:.2f}", "color": WHITE},
        {"name": "SPD", "val": f"{player_stats['speed_mult']:.2f}", "color": WHITE},
        {"name": "DUR", "val": f"{player_stats['skill_duration_mult']:.2f}", "color": WHITE},
        {"name": "RAD", "val": f"{player_stats['radius_mult']:.2f}", "color": WHITE},
        {"name": "DEF", "val": f"{int(player_stats['defense_up']*100)}%", "color": WHITE},
        {"name": "THRN", "val": f"{player_stats['thorns_damage']}", "color": WHITE},
    ]

    for i, st in enumerate(stats):
        cx, cy = stat_start_x + 10, stat_start_y + i * stat_gap + 10
        if st["name"] == "HP":
            pygame.draw.polygon(screen, (255,50,50), [(cx,cy+6),(cx-6,cy-1),(cx-3,cy-4),(cx,cy-1),(cx+3,cy-4),(cx+6,cy-1)])
        elif st["name"] == "DMG":
            pygame.draw.line(screen,(200,200,200),(cx-5,cy+5),(cx+5,cy-5),2)
            pygame.draw.line(screen,(139,69,19),(cx-6,cy+6),(cx-3,cy+3),2)
        elif st["name"] == "SPD":
            pygame.draw.polygon(screen,(100,200,100),[(cx-4,cy-5),(cx+2,cy-5),(cx+2,cy+5),(cx+6,cy+5),(cx+6,cy+7),(cx-4,cy+7)])
        elif st["name"] == "DUR":
            pygame.draw.polygon(screen,(200,200,50),[(cx-5,cy-6),(cx+5,cy-6),(cx,cy),(cx-5,cy+6),(cx+5,cy+6)])
        elif st["name"] == "RAD":
            pygame.draw.circle(screen,(150,200,255),(cx-2,cy-2),4,2)
            pygame.draw.line(screen,(150,100,50),(cx+1,cy+1),(cx+5,cy+5),2)
        elif st["name"] == "DEF":
            pygame.draw.polygon(screen,(100,100,200),[(cx-5,cy-6),(cx+5,cy-6),(cx+5,cy+3),(cx,cy+8),(cx-5,cy+3)])
        elif st["name"] == "THRN":
            pygame.draw.circle(screen,(150,150,150),(cx,cy),5)
            for ang in range(0,360,45):
                r = math.radians(ang)
                pygame.draw.line(screen,(255,255,255),(cx,cy),(cx+math.cos(r)*8,cy+math.sin(r)*8),1)
        
        # 텍스트는 수치만 출력 (아이작 스타일)
        text_surf = font.render(st["val"], True, st["color"])
        screen.blit(text_surf, (cx + 20, cy - 10))

    # 아이템창 (우측 하단, 반투명, 다단 표시)
    item_lines = [f"{name} x{cnt}" if cnt > 1 else name for name, cnt in acquired_items_counts.items()]
    if not item_lines:
        item_lines = ["(없음)"]
        
    max_per_col = 6
    num_cols = max(1, (len(item_lines) + max_per_col - 1) // max_per_col)
    item_box_w = 140 * num_cols
    item_box_h = 40 + min(len(item_lines), max_per_col) * 20
    item_x = WIDTH - item_box_w - 15
    item_y = HEIGHT - 100 - 15 - item_box_h
    
    item_surf = pygame.Surface((item_box_w, item_box_h), pygame.SRCALPHA)
    item_surf.fill((*UI_BG, 180))
    pygame.draw.rect(item_surf, (*WHITE, 180), (0, 0, item_box_w, item_box_h), 2)
    item_surf.blit(font.render("[ 아이템 ]", True, (255, 230, 100)), (10, 10))
    for i, line in enumerate(item_lines):
        col = i // max_per_col
        row = i % max_per_col
        item_surf.blit(font.render(line, True, WHITE), (10 + col * 140, 35 + row * 20))
    screen.blit(item_surf, (item_x, item_y))

    if message_timer > 0:
        ms=font.render(message,True,(255,230,100))
        screen.blit(ms,(WIDTH//2-ms.get_width()//2, 20)); message_timer-=1

    ui_rect=pygame.Rect(0,HEIGHT-100,WIDTH,100)
    pygame.draw.rect(screen,UI_BG,ui_rect)
    pygame.draw.line(screen,WHITE,(0,HEIGHT-100),(WIDTH,HEIGHT-100),2)
    screen.blit(font.render(f"Words: {', '.join(player_words)}",True,(150,200,255)),(20,HEIGHT-92))
    screen.blit(font.render(f"Shapes: {', '.join(player_shapes)}",True,(200,255,150)),(20,HEIGHT-72))
    pygame.draw.rect(screen,BLACK,(20,HEIGHT-40,WIDTH-40,35))
    pygame.draw.rect(screen,WHITE,(20,HEIGHT-40,WIDTH-40,35),2)
    screen.blit(big_font.render(input_text+"_",True,WHITE),(30,HEIGHT-47))

    if player_hp < player_prev_hp:
        spawn_player_particles(player_pos,(220,60,60),count=15,speed=3.0,size_range=(3,6))
    if player_hp <= 0 and player_prev_hp > 0:
        spawn_player_particles(player_pos,(100,180,255),count=50,speed=5.0,size_range=(3,7))
    
    if player_hp <= 0:
        game_over_timer += 1
        if game_over_timer > 90:
            game_state = "GAME_OVER"
            game_over_timer = 0

    player_prev_hp = player_hp

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
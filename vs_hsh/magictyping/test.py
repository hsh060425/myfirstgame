import pygame
import random
import math
import sys

# 1. 초기화 및 기본 설정
pygame.init()
WIDTH, HEIGHT = 800, 750
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Typing Isaac - Dynamic Shapes & Combos")
clock = pygame.time.Clock()

# 색상 정의
WHITE, BLACK = (255, 255, 255), (15, 15, 15)
FLOOR_COLOR, WALL_COLOR = (50, 45, 40), (35, 30, 25)
DOOR_OPEN, DOOR_LOCKED = (200, 160, 40), (100, 100, 100)
PLAYER_COLOR, PLAYER_IMMUNE = (100, 180, 255), (180, 220, 255)
ENEMY_COLOR, BOSS_COLOR = (220, 60, 60), (180, 40, 200)
UI_BG = (25, 25, 35)
HP_RED, HP_GREEN = (200, 50, 50), (50, 200, 50)
MM_CURRENT, MM_VISITED, MM_DISCOVERED, MM_BOSS = (255, 230, 0), (120, 120, 120), (60, 60, 60), (230, 50, 50)

# 속성별 장판/이펙트 색상
FIELD_COLORS = {
    "attack": (255, 255, 255, 150),
    "fire": (255, 80, 0, 120),
    "poison": (100, 255, 50, 100),
    "ice": (100, 200, 255, 120),
    "steam": (200, 200, 220, 150),
    "tree": (34, 139, 34, 130),
    "explosion": (255, 50, 50, 180),
    "heal": (50, 255, 150, 120),
    "guard": (255, 215, 0, 120)
}

font = pygame.font.SysFont(None, 30)
big_font = pygame.font.SysFont(None, 40)

# 2. 맵 생성
def generate_map(num_rooms=10):
    rooms = {}
    rooms[(0, 0)] = {"visited": False, "type": "start", "enemies": [], "cleared": True, "reward": None}
    directions = [(0, -1), (0, 1), (-1, 0), (1, 0)]
    room_coords = [(0, 0)]
    
    while len(rooms) < num_rooms:
        curr = random.choice(room_coords)
        dx, dy = random.choice(directions)
        next_room = (curr[0] + dx, curr[1] + dy)
        if next_room not in rooms:
            rooms[next_room] = {"visited": False, "type": "normal", "enemies": [], "cleared": False, "reward": None}
            room_coords.append(next_room)
            
    rooms[room_coords[-1]]["type"] = "boss"
    return rooms

world_map = generate_map(10)
current_coords = (0, 0)
ROOM_RECT = pygame.Rect(60, 60, WIDTH - 120, HEIGHT - 180)

# 플레이어 초기 상태 (attack만 보유)
player_pos = [WIDTH // 2, ROOM_RECT.centery]
player_facing = [1, 0] # 플레이어가 마지막으로 바라본 방향
player_speed = 5
player_radius = 15
player_words = ["attack"] 
player_shapes = [] 
player_max_hp = 100
player_hp = 100
player_immune_timer = 0

input_text = ""
message = "'attack' 타이핑! 적을 잡아 속성과 형태 획득!"
message_timer = 180

active_fields = []

# 장판 및 스킬 생성 
def spawn_field(f_type, pos, radius, duration, shape, vx=0, vy=0):
    interacted = False
    for f in active_fields[:]:
        dist = math.hypot(f["pos"][0] - pos[0], f["pos"][1] - pos[1])
        if dist < f["radius"] + radius:
            combo = {f_type, f["type"]}
            if combo == {"fire", "poison"}:
                active_fields.remove(f)
                active_fields.append({"pos": f["pos"], "type": "explosion", "radius": 150, "timer": 20, "shape": "aura", "vx": 0, "vy": 0})
                interacted = True
                break
            elif combo == {"fire", "ice"}:
                active_fields.remove(f)
                active_fields.append({"pos": f["pos"], "type": "steam", "radius": 130, "timer": 240, "shape": "aura", "vx": 0, "vy": 0})
                interacted = True
                break
    
    if not interacted:
        active_fields.append({
            "pos": list(pos), "type": f_type, "radius": radius, 
            "timer": duration, "max_timer": duration, 
            "shape": shape, "vx": vx, "vy": vy
        })

# 스킬 위치 계산 로직
def cast_spell(element, shape, p_pos, facing, target_e):
    duration, radius = 240, 80
    
    if element == "attack": duration, radius = 20, 100
    elif element == "bomb": duration, radius = 20, 120
    elif element == "guard": duration, radius = 300, 60
    elif element == "heal": duration, radius = 240, 70

    if shape == "spike": duration, radius = min(duration, 60), 60
    elif shape == "ball": duration, radius = min(duration, 120), 30
    elif shape == "square": duration, radius = 300, 50

    vx, vy = 0, 0
    
    # [1] 기본 (내 주변 오라)
    if shape == "aura":
        spawn_pos = list(p_pos)
    # [2] 구형 투사체 (적을 향해 날아감)
    elif shape == "ball":
        spawn_pos = list(p_pos)
        if target_e:
            dx, dy = target_e["pos"][0] - p_pos[0], target_e["pos"][1] - p_pos[1]
            dist = math.hypot(dx, dy)
            if dist > 0: vx, vy = (dx/dist)*8, (dy/dist)*8
        else:
            vx, vy = facing[0]*8, facing[1]*8
    # [3] 가시 (적 발밑 즉시 생성)
    elif shape == "spike":
        spawn_pos = list(target_e["pos"]) if target_e else [p_pos[0] + facing[0]*100, p_pos[1] + facing[1]*100]
    # [4] 네모 장애물 (적을 가로막도록 설치)
    elif shape == "square":
        if target_e:
            dx, dy = target_e["pos"][0] - p_pos[0], target_e["pos"][1] - p_pos[1]
            dist = math.hypot(dx, dy)
            spawn_pos = [p_pos[0] + (dx/dist)*80, p_pos[1] + (dy/dist)*80] if dist > 0 else list(p_pos)
        else:
            spawn_pos = [p_pos[0] + facing[0]*80, p_pos[1] + facing[1]*80]
            
    spawn_field(element, spawn_pos, radius, duration, shape, vx, vy)

def enter_room(coords):
    global current_coords, message, message_timer
    current_coords = coords
    room = world_map[coords]
    room["visited"] = True
    active_fields.clear()
    
    if not room["cleared"] and len(room["enemies"]) == 0 and coords != (0,0):
        if room["type"] == "normal":
            for _ in range(random.randint(2, 4)):
                room["enemies"].append({
                    "pos": [random.randint(150, WIDTH-150), random.randint(150, ROOM_RECT.bottom - 100)],
                    "hp": 50, "max_hp": 50, "speed": 2.0, "base_speed": 2.0, "type": "normal", "radius": 12
                })
        elif room["type"] == "boss":
            room["enemies"].append({
                "pos": [WIDTH//2, ROOM_RECT.centery],
                "hp": 300, "max_hp": 300, "speed": 1.5, "base_speed": 1.5, "type": "boss", "radius": 35
            })

enter_room((0,0))

def is_discovered(coords):
    if world_map[coords]["visited"]: return True
    for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
        neighbor = (coords[0] + dx, coords[1] + dy)
        if neighbor in world_map and world_map[neighbor]["visited"]: return True
    return False

# 메인 게임 루프
running = True
while running:
    screen.fill(BLACK)
    room = world_map[current_coords]
    room_cleared = (len(room["enemies"]) == 0)
    
    if player_immune_timer > 0:
        player_immune_timer -= 1
        
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                cmd = input_text.strip().lower()
                input_text = ""
                tokens = cmd.split()
                
                if len(tokens) > 0:
                    element = tokens[0]
                    # 형태 단어가 없으면 'aura'(내 주변)를 기본값으로 사용
                    shape = tokens[1] if len(tokens) > 1 else "aura"
                    
                    if element in player_words and (shape in player_shapes or shape == "aura"):
                        closest_e = None
                        if room["enemies"]:
                            closest_e = min(room["enemies"], key=lambda e: math.hypot(e["pos"][0]-player_pos[0], e["pos"][1]-player_pos[1]))
                        
                        cast_spell(element, shape, player_pos, player_facing, closest_e)
                    else:
                        message = "미획득 단어/형태 조합입니다!"
                        message_timer = 60

            elif event.key == pygame.K_BACKSPACE: input_text = input_text[:-1]
            elif event.key == pygame.K_SPACE: input_text += " "
            elif event.unicode.isalpha(): input_text += event.unicode

    # 플레이어 이동 및 방향 기록
    if player_hp > 0:
        keys = pygame.key.get_pressed()
        new_x, new_y = player_pos[0], player_pos[1]
        if keys[pygame.K_LEFT]:  new_x -= player_speed; player_facing = [-1, 0]
        if keys[pygame.K_RIGHT]: new_x += player_speed; player_facing = [1, 0]
        if keys[pygame.K_UP]:    new_y -= player_speed; player_facing = [0, -1]
        if keys[pygame.K_DOWN]:  new_y += player_speed; player_facing = [0, 1]
    else:
        new_x, new_y = player_pos[0], player_pos[1]

    # 방 이동 충돌 처리
    door_w = 80
    if new_x - player_radius < ROOM_RECT.left:
        target = (current_coords[0] - 1, current_coords[1])
        if target in world_map and (ROOM_RECT.centery - door_w//2 < new_y < ROOM_RECT.centery + door_w//2) and room_cleared:
            enter_room(target); new_x = ROOM_RECT.right - player_radius - 10
        else: new_x = ROOM_RECT.left + player_radius
    elif new_x + player_radius > ROOM_RECT.right:
        target = (current_coords[0] + 1, current_coords[1])
        if target in world_map and (ROOM_RECT.centery - door_w//2 < new_y < ROOM_RECT.centery + door_w//2) and room_cleared:
            enter_room(target); new_x = ROOM_RECT.left + player_radius + 10
        else: new_x = ROOM_RECT.right - player_radius
    if new_y - player_radius < ROOM_RECT.top:
        target = (current_coords[0], current_coords[1] - 1)
        if target in world_map and (WIDTH//2 - door_w//2 < new_x < WIDTH//2 + door_w//2) and room_cleared:
            enter_room(target); new_y = ROOM_RECT.bottom - player_radius - 10
        else: new_y = ROOM_RECT.top + player_radius
    elif new_y + player_radius > ROOM_RECT.bottom:
        target = (current_coords[0], current_coords[1] + 1)
        if target in world_map and (WIDTH//2 - door_w//2 < new_x < WIDTH//2 + door_w//2) and room_cleared:
            enter_room(target); new_y = ROOM_RECT.top + player_radius + 10
        else: new_y = ROOM_RECT.bottom - player_radius
    player_pos[0], player_pos[1] = new_x, new_y

    # 적 상태 기본화
    for e in room["enemies"]:
        e["speed"] = e["base_speed"]
        
    # [새로운 장판(Field) 로직]
    for f in active_fields[:]:
        f["timer"] -= 1
        if f["timer"] <= 0:
            active_fields.remove(f)
            continue
            
        # 모양에 따른 이동 및 위치 갱신
        if f["shape"] == "ball":
            f["pos"][0] += f["vx"]
            f["pos"][1] += f["vy"]
        elif f["shape"] == "aura":
            # aura는 항상 플레이어 위치를 따라다님
            f["pos"] = list(player_pos)

        # 💡 장판과 [플레이어]의 상호작용 (heal, guard 적용)
        p_dist = math.hypot(player_pos[0] - f["pos"][0], player_pos[1] - f["pos"][1])
        is_p_hit = False
        if f["shape"] in ["aura", "ball", "spike"] and p_dist <= f["radius"] + player_radius: is_p_hit = True
        elif f["shape"] == "square" and (abs(player_pos[0]-f["pos"][0]) <= f["radius"]+player_radius) and (abs(player_pos[1]-f["pos"][1]) <= f["radius"]+player_radius): is_p_hit = True
        
        if is_p_hit:
            if f["type"] == "heal": player_hp = min(player_max_hp, player_hp + 0.2) # 지속 힐
            elif f["type"] == "guard": player_immune_timer = max(player_immune_timer, 10) # 닿아있는 동안 무적

        # 💡 장판과 [적]의 상호작용 (데미지 및 CC기)
        for e in room["enemies"]:
            is_hit = False
            dx, dy = e["pos"][0] - f["pos"][0], e["pos"][1] - f["pos"][1]
            dist = math.hypot(dx, dy)
            
            if f["shape"] in ["aura", "ball", "spike"]: is_hit = dist <= f["radius"] + e["radius"]
            elif f["shape"] == "square": is_hit = (abs(dx) <= f["radius"] + e["radius"]) and (abs(dy) <= f["radius"] + e["radius"])

            if is_hit:
                if f["type"] == "attack": e["hp"] -= 1.5
                elif f["type"] == "fire": e["hp"] -= 0.6
                elif f["type"] == "poison": e["hp"] -= 0.2
                elif f["type"] == "steam": e["hp"] -= 1.0
                elif f["type"] == "ice": e["speed"] *= 0.3
                elif f["type"] == "tree": e["speed"] = 0
                elif f["type"] == "explosion": e["hp"] -= 8

    room["enemies"] = [e for e in room["enemies"] if e["hp"] > 0]

    # 적 이동 & 물리적 충돌(Square 벽 막힘 기능 포함)
    for i, e in enumerate(room["enemies"]):
        dx, dy = player_pos[0] - e["pos"][0], player_pos[1] - e["pos"][1]
        dist = math.hypot(dx, dy)
        
        if dist > 0 and player_hp > 0:
            move_x = (dx/dist) * e["speed"]
            move_y = (dy/dist) * e["speed"]
            
            # X축 이동 후 Square 충돌 검사
            e["pos"][0] += move_x
            for f in active_fields:
                if f["shape"] == "square":
                    if abs(e["pos"][0] - f["pos"][0]) < f["radius"] + e["radius"] and abs(e["pos"][1] - f["pos"][1]) < f["radius"] + e["radius"]:
                        e["pos"][0] -= move_x # 통과 불가 (뒤로 밀어냄)
                        break
            
            # Y축 이동 후 Square 충돌 검사
            e["pos"][1] += move_y
            for f in active_fields:
                if f["shape"] == "square":
                    if abs(e["pos"][0] - f["pos"][0]) < f["radius"] + e["radius"] and abs(e["pos"][1] - f["pos"][1]) < f["radius"] + e["radius"]:
                        e["pos"][1] -= move_y # 통과 불가
                        break

        # 적끼리 뭉침 방지
        for j in range(i + 1, len(room["enemies"])):
            other_e = room["enemies"][j]
            ex, ey = e["pos"][0] - other_e["pos"][0], e["pos"][1] - other_e["pos"][1]
            e_dist = math.hypot(ex, ey)
            e_min_dist = e["radius"] + other_e["radius"]
            if e_dist < e_min_dist and e_dist > 0:
                e_overlap = e_min_dist - e_dist
                e["pos"][0] += (ex / e_dist) * (e_overlap / 2)
                e["pos"][1] += (ey / e_dist) * (e_overlap / 2)
                other_e["pos"][0] -= (ex / e_dist) * (e_overlap / 2)
                other_e["pos"][1] -= (ey / e_dist) * (e_overlap / 2)

        # 플레이어와 적 피격 충돌
        p_dx, p_dy = player_pos[0] - e["pos"][0], player_pos[1] - e["pos"][1]
        p_dist = math.hypot(p_dx, p_dy)
        min_dist = player_radius + e["radius"]
        if p_dist < min_dist and p_dist > 0:
            player_pos[0] += (p_dx / p_dist) * (min_dist - p_dist)
            player_pos[1] += (p_dy / p_dist) * (min_dist - p_dist)
            if player_immune_timer <= 0 and player_hp > 0:
                player_hp = max(0, player_hp - (25 if e["type"] == "boss" else 10))
                player_immune_timer = 60 

    # 방 클리어 시 무작위 단어/형태 보상 드랍
    if not room["cleared"] and len(room["enemies"]) == 0 and current_coords != (0,0):
        room["cleared"] = True
        all_elements = ["fire", "poison", "ice", "bomb", "tree", "guard", "heal"]
        all_shapes = ["ball", "square", "spike"]
        
        # 획득하지 않은 단어와 형태 목록 추리기
        available_rewards = [w for w in all_elements if w not in player_words] + [s for s in all_shapes if s not in player_shapes]
        
        if available_rewards:
            room["reward"] = {"word": random.choice(available_rewards), "pos": [WIDTH//2, ROOM_RECT.centery]}

    # 보상 획득 처리
    if room.get("reward"):
        dist = math.hypot(room["reward"]["pos"][0] - player_pos[0], room["reward"]["pos"][1] - player_pos[1])
        if dist < 40:
            new_word = room["reward"]["word"]
            if new_word in ["ball", "square", "spike"]: player_shapes.append(new_word)
            else: player_words.append(new_word)
            message = f"획득: '{new_word}'!"
            message_timer = 150
            room["reward"] = None

    # 렌더링
    pygame.draw.rect(screen, WALL_COLOR, (0, 0, WIDTH, HEIGHT - 100))
    pygame.draw.rect(screen, FLOOR_COLOR, ROOM_RECT)

    door_color = DOOR_OPEN if room_cleared else DOOR_LOCKED
    door_thick = 15
    for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
        neighbor = (current_coords[0] + dx, current_coords[1] + dy)
        if neighbor in world_map:
            if (dx, dy) == (0, -1): pygame.draw.rect(screen, door_color, (WIDTH//2 - door_w//2, ROOM_RECT.top - door_thick, door_w, door_thick + 5))
            elif (dx, dy) == (0, 1): pygame.draw.rect(screen, door_color, (WIDTH//2 - door_w//2, ROOM_RECT.bottom - 5, door_w, door_thick + 5))
            elif (dx, dy) == (-1, 0): pygame.draw.rect(screen, door_color, (ROOM_RECT.left - door_thick, ROOM_RECT.centery - door_w//2, door_thick + 5, door_w))
            elif (dx, dy) == (1, 0): pygame.draw.rect(screen, door_color, (ROOM_RECT.right - 5, ROOM_RECT.centery - door_w//2, door_thick + 5, door_w))

    # 장판(스킬) 렌더링
    if active_fields:
        field_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        for f in active_fields:
            color = FIELD_COLORS.get(f["type"], (255, 255, 255, 100))
            if f["type"] == "attack" and f["shape"] == "aura":
                # attack 기본 오라는 빠르게 사라지는 연출
                fade = max(0, int(255 * (f["timer"] / f["max_timer"])))
                color = (255, 255, 255, fade)
            
            if f["shape"] == "ball" or f["shape"] == "aura":
                pygame.draw.circle(field_surface, color, (int(f["pos"][0]), int(f["pos"][1])), f["radius"])
            elif f["shape"] == "square":
                rect = pygame.Rect(f["pos"][0] - f["radius"], f["pos"][1] - f["radius"], f["radius"]*2, f["radius"]*2)
                pygame.draw.rect(field_surface, color, rect)
                pygame.draw.rect(field_surface, (255,255,255,100), rect, 2) # 테두리로 장애물 느낌 강조
            elif f["shape"] == "spike":
                points = []
                for i in range(8):
                    r = f["radius"] if i % 2 == 0 else f["radius"] * 0.4
                    ang = math.radians(i * 45)
                    points.append((f["pos"][0] + math.cos(ang)*r, f["pos"][1] + math.sin(ang)*r))
                pygame.draw.polygon(field_surface, color, points)

        screen.blit(field_surface, (0, 0))

    # 적 렌더링
    for e in room["enemies"]:
        color = BOSS_COLOR if e["type"] == "boss" else ENEMY_COLOR
        pygame.draw.circle(screen, color, (int(e["pos"][0]), int(e["pos"][1])), e["radius"])
        bar_w = e["radius"] * 3
        bar_x, bar_y = e["pos"][0] - (bar_w / 2), e["pos"][1] - e["radius"] - 15
        pygame.draw.rect(screen, HP_RED, (bar_x, bar_y, bar_w, 8))
        pygame.draw.rect(screen, HP_GREEN, (bar_x, bar_y, int(bar_w * max(0, e["hp"] / e["max_hp"])), 8))

    if room.get("reward"):
        rw_text = font.render(f"[{room['reward']['word']}]", True, (255, 255, 0))
        screen.blit(rw_text, (room["reward"]["pos"][0] - rw_text.get_width()//2, room["reward"]["pos"][1] - 15))

    # 플레이어 렌더링
    if player_hp > 0:
        if player_immune_timer > 0:
            pygame.draw.circle(screen, PLAYER_IMMUNE, (int(player_pos[0]), int(player_pos[1])), player_radius)
            pygame.draw.circle(screen, WHITE, (int(player_pos[0]), int(player_pos[1])), player_radius + 2, 2)
        else:
            pygame.draw.circle(screen, PLAYER_COLOR, (int(player_pos[0]), int(player_pos[1])), player_radius)

    # UI 렌더링
    MM_X, MM_Y, CELL, GAP = WIDTH - 100, 80, 15, 3
    for coords, info in world_map.items():
        if is_discovered(coords):
            draw_x, draw_y = MM_X + (coords[0] - current_coords[0]) * (CELL + GAP) - CELL // 2, MM_Y + (coords[1] - current_coords[1]) * (CELL + GAP) - CELL // 2
            color = MM_CURRENT if coords == current_coords else (MM_BOSS if info["type"] == "boss" else (MM_VISITED if info["visited"] else MM_DISCOVERED))
            pygame.draw.rect(screen, color, (draw_x, draw_y, CELL, CELL))
            pygame.draw.rect(screen, WHITE, (draw_x, draw_y, CELL, CELL), 1)

    pygame.draw.rect(screen, UI_BG, (15, 15, 260, 35))
    pygame.draw.rect(screen, WHITE, (15, 15, 260, 35), 2)
    screen.blit(font.render(f"PLAYER HP: {player_hp}/{player_max_hp}", True, WHITE if player_hp > 25 else HP_RED), (30, 25))

    if message_timer > 0:
        msg_surf = font.render(message, True, (255, 230, 100))
        screen.blit(msg_surf, (WIDTH - msg_surf.get_width() - 20, 20))
        message_timer -= 1

    ui_rect = pygame.Rect(0, HEIGHT - 100, WIDTH, 100)
    pygame.draw.rect(screen, UI_BG, ui_rect)
    pygame.draw.line(screen, WHITE, (0, HEIGHT - 100), (WIDTH, HEIGHT - 100), 2)
    
    screen.blit(font.render(f"Words: {', '.join(player_words)}", True, (150, 200, 255)), (20, HEIGHT - 95))
    screen.blit(font.render(f"Shapes: {', '.join(player_shapes)}", True, (200, 255, 150)), (20, HEIGHT - 75))
    
    pygame.draw.rect(screen, BLACK, (20, HEIGHT - 45, WIDTH - 40, 35))
    pygame.draw.rect(screen, WHITE, (20, HEIGHT - 45, WIDTH - 40, 35), 2)
    screen.blit(big_font.render(input_text + "_", True, WHITE), (30, HEIGHT - 40))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
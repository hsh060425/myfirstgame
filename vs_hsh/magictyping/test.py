import pygame
import random
import math
import sys

# 1. 초기화 및 기본 설정
pygame.init()
WIDTH, HEIGHT = 800, 750
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Typing Isaac - Items & Combos (+Cheat)")
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

# 속성 및 콤보 색상
FIELD_COLORS = {
    "attack": (255, 255, 255, 150),
    "fire": (255, 80, 0, 120),
    "poison": (100, 255, 50, 100),
    "ice": (100, 200, 255, 120),
    "steam": (200, 200, 220, 150),
    "tree": (34, 139, 34, 130),
    "bomb": (255, 100, 0, 180),
    "explosion": (255, 50, 50, 180),
    "heal": (50, 255, 150, 120),
    "guard": (255, 215, 0, 120),
    "plague_storm": (120, 30, 160, 160), 
    "toxic_cloud": (70, 220, 40, 140),   
    "wildfire": (255, 130, 0, 180),      
    "sanctuary": (200, 255, 150, 150),
    "glacial_barricade": (150, 220, 255, 180), 
    "counter_shield": (255, 200, 50, 180),     
    "divine_grace": (255, 255, 200, 150)       
}

# 한글 폰트 설정 (UI 글자가 너무 크지 않도록 사이즈를 대폭 축소했습니다)
pygame.font.init()
system_fonts = pygame.font.get_fonts()
kor_font = None
for f in ['malgungothic', 'applegothic', 'applesdgothicneo', 'nanumgothic', 'd2coding']:
    if f in system_fonts:
        kor_font = f
        break

# 원본(30, 40)에서 비율에 맞게 축소 (20, 30)
font = pygame.font.SysFont(kor_font, 20)
big_font = pygame.font.SysFont(kor_font, 30)

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

player_pos = [WIDTH // 2, ROOM_RECT.centery]
player_facing = [1, 0] 
player_speed = 5
player_radius = 15
player_words = ["attack"] 
player_shapes = [] 
player_max_hp = 100
player_hp = 100
player_immune_timer = 0

player_stats = {
    "skill_duration_mult": 1.0,
    "radius_mult": 1.0,
    "damage_mult": 1.0,
    "speed_mult": 1.0,
    "thorns_damage": 0,
    "defense_up": 0.0
}
player_items = {
    "pet": False,
    "elemental_blade": False,
    "map_reveal": False
}
pet_pos = [WIDTH // 2, ROOM_RECT.centery]
pet_attack_timer = 0

STACKABLE_ITEMS = [
    {"id": "duration_up", "name": "모래시계"},
    {"id": "radius_up", "name": "확대경"},
    {"id": "damage_up", "name": "전사의 검"},
    {"id": "speed_up", "name": "바람의 부츠"},
    {"id": "thorns", "name": "가시 갑옷"},
    {"id": "hp_up", "name": "생명의 심장"},
    {"id": "defense_up", "name": "강철 방패"}
]

NON_STACKABLE_ITEMS = [
    {"id": "pet", "name": "미니 슬라임"},
    {"id": "elemental_blade", "name": "속성 부여검"},
    {"id": "map_reveal", "name": "마법 지도"}
]

input_text = ""
attack_timer = 0
attack_data = {"angle": 0, "radius": 0, "half_cone": 0}
message = "플레이 해보세요"
message_timer = 180

active_fields = []

def spawn_field(f_type, pos, radius, duration, shape, vx=0, vy=0):
    active_fields.append({
        "pos": list(pos), "type": f_type, "radius": radius, 
        "timer": duration, "max_timer": duration, 
        "shape": shape, "vx": vx, "vy": vy
    })

def cast_spell(element, shape, p_pos, facing, target_e):
    duration, radius = 240, 80
    
    if element == "attack": duration, radius = 40, 80
    elif element == "bomb": duration, radius = 20, 120
    elif element == "guard": duration, radius = 300, 60
    elif element == "heal": duration, radius = 240, 70

    if shape == "spike": duration, radius = min(duration, 60), 60
    elif shape == "ball": duration, radius = min(duration, 120), 40
    elif shape == "square": duration, radius = 300, 60

    if duration > 60: 
        duration = int(duration * player_stats["skill_duration_mult"])
    radius = int(radius * player_stats["radius_mult"])

    vx, vy = 0, 0
    
    if shape == "field": 
        spawn_pos = list(p_pos)
    elif shape == "ball":
        spawn_pos = list(p_pos)
        if target_e:
            dx, dy = target_e["pos"][0] - p_pos[0], target_e["pos"][1] - p_pos[1]
            dist = math.hypot(dx, dy)
            if dist > 0: vx, vy = (dx/dist)*12, (dy/dist)*12
        else: vx, vy = facing[0]*12, facing[1]*12
    elif shape == "spike":
        spawn_pos = list(target_e["pos"]) if target_e else [p_pos[0] + facing[0]*100, p_pos[1] + facing[1]*100]
    elif shape == "square":
        if target_e:
            dx, dy = target_e["pos"][0] - p_pos[0], target_e["pos"][1] - p_pos[1]
            dist = math.hypot(dx, dy)
            spawn_pos = [p_pos[0] + (dx/dist)*80, p_pos[1] + (dy/dist)*80] if dist > 0 else list(p_pos)
        else: spawn_pos = [p_pos[0] + facing[0]*80, p_pos[1] + facing[1]*80]
            
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
                    "hp": 50, "max_hp": 50, "speed": 2.0, "base_speed": 2.0, 
                    "type": "normal", "radius": 12, "stun_timer": 0
                })
        elif room["type"] == "boss":
            room["enemies"].append({
                "pos": [WIDTH//2, ROOM_RECT.centery],
                "hp": 300, "max_hp": 300, "speed": 1.5, "base_speed": 1.5, 
                "type": "boss", "radius": 35, "stun_timer": 0
            })

enter_room((0,0))

def is_discovered(coords):
    if player_items.get("map_reveal", False): return True
    if world_map[coords]["visited"]: return True
    for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
        neighbor = (coords[0] + dx, coords[1] + dy)
        if neighbor in world_map and world_map[neighbor]["visited"]: return True
    return False

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
                
                # 치트키 시스템
                if cmd == "cheat":
                    player_words = ["attack", "fire", "poison", "ice", "bomb", "tree", "guard", "heal"]
                    player_shapes = ["ball", "square", "spike"]
                    player_items["pet"] = True
                    player_items["elemental_blade"] = True
                    player_items["map_reveal"] = True
                    player_stats["speed_mult"] = 1.5
                    player_stats["damage_mult"] = 3.0
                    player_stats["skill_duration_mult"] = 2.0
                    player_stats["radius_mult"] = 1.5
                    player_stats["defense_up"] = 0.5
                    player_stats["thorns_damage"] = 20
                    player_max_hp = 200
                    player_hp = 200
                    message = " 치트 활성화: 단어, 형태, 아이템 모두 획득!"
                    message_timer = 180
                    continue
                elif cmd == "cheat word":
                    player_words = ["attack", "fire", "poison", "ice", "bomb", "tree", "guard", "heal"]
                    player_shapes = ["ball", "square", "spike"]
                    message = " 치트1 활성화: 모든 마법 단어와 형태 획득!"
                    message_timer = 180
                    continue
                elif cmd == "cheat item":
                    player_items["pet"] = True
                    player_items["elemental_blade"] = True
                    player_items["map_reveal"] = True
                    player_stats["speed_mult"] = 1.5
                    player_stats["damage_mult"] = 3.0
                    player_stats["skill_duration_mult"] = 2.0
                    player_stats["radius_mult"] = 1.5
                    player_stats["defense_up"] = 0.5
                    player_stats["thorns_damage"] = 20
                    player_max_hp = 200
                    player_hp = 200
                    message = " 치트2 활성화: 모든 아이템 및 스탯 상승!"
                    message_timer = 180
                    continue

                tokens = cmd.split()
                if len(tokens) > 0:
                    element = tokens[0]
                    shape = tokens[1] if len(tokens) > 1 else "field"
                    
                    if element == "attack" and shape == "field":
                        attack_radius = 140 * player_stats["radius_mult"]
                        cone_angle = math.radians(60)
                        half_cone = cone_angle / 2
                        base_angle = 0 
                        if room["enemies"]:
                            closest_e = min(room["enemies"], key=lambda e: math.hypot(e["pos"][0]-player_pos[0], e["pos"][1]-player_pos[1]))
                            dx = closest_e["pos"][0] - player_pos[0]
                            dy = closest_e["pos"][1] - player_pos[1]
                            base_angle = math.atan2(dy, dx)
                            for e in room["enemies"]:
                                edx = e["pos"][0] - player_pos[0]
                                edy = e["pos"][1] - player_pos[1]
                                dist = math.hypot(edx, edy)
                                if dist <= attack_radius:
                                    target_angle = math.atan2(edy, edx)
                                    angle_diff = (target_angle - base_angle + math.pi) % (2 * math.pi) - math.pi
                                    if abs(angle_diff) <= half_cone: 
                                        e["hp"] -= 15 * player_stats["damage_mult"]
                                        if player_items["elemental_blade"]:
                                            rand_elem = random.choice(["fire", "ice", "poison", "bomb", "tree"])
                                            if rand_elem == "fire": e["hp"] -= 5 * player_stats["damage_mult"]
                                            elif rand_elem == "ice": e["speed"] *= 0.3
                                            elif rand_elem == "poison": e["hp"] -= 3 * player_stats["damage_mult"]
                                            elif rand_elem == "bomb": e["hp"] -= 10 * player_stats["damage_mult"]
                                            elif rand_elem == "tree": e["stun_timer"] = max(e.get("stun_timer",0), 30)
                                        
                        attack_timer = 15
                        attack_data = {"angle": base_angle, "radius": attack_radius, "half_cone": half_cone}

                    elif element in player_words and (shape in player_shapes or shape == "field"):
                        closest_e = min(room["enemies"], key=lambda e: math.hypot(e["pos"][0]-player_pos[0], e["pos"][1]-player_pos[1])) if room["enemies"] else None
                        cast_spell(element, shape, player_pos, player_facing, closest_e)
                    else:
                        message = "미획득 단어/형태 조합입니다!"
                        message_timer = 60

            elif event.key == pygame.K_BACKSPACE: input_text = input_text[:-1]
            elif event.key == pygame.K_SPACE: input_text += " "
            elif event.unicode != "":
                if event.unicode.isalpha() or ('가' <= event.unicode <= '힣'):
                    input_text += event.unicode

    if player_hp > 0:
        ps = player_speed * player_stats["speed_mult"]
        keys = pygame.key.get_pressed()
        new_x, new_y = player_pos[0], player_pos[1]
        if keys[pygame.K_LEFT]:  new_x -= ps; player_facing = [-1, 0]
        if keys[pygame.K_RIGHT]: new_x += ps; player_facing = [1, 0]
        if keys[pygame.K_UP]:    new_y -= ps; player_facing = [0, -1]
        if keys[pygame.K_DOWN]:  new_y += ps; player_facing = [0, 1]
    else:
        new_x, new_y = player_pos[0], player_pos[1]

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

    for e in room["enemies"]:
        e["speed"] = e["base_speed"]
        
    for f in active_fields:
        if f["shape"] == "ball":
            f["pos"][0] += f["vx"]
            f["pos"][1] += f["vy"]

    if player_items["pet"] and player_hp > 0:
        pet_pos[0] += (player_pos[0] - 35 - pet_pos[0]) * 0.05
        pet_pos[1] += (player_pos[1] - 35 - pet_pos[1]) * 0.05
        
        pet_attack_timer -= 1
        if pet_attack_timer <= 0 and room["enemies"]:
            closest_e = min(room["enemies"], key=lambda e: math.hypot(e["pos"][0]-pet_pos[0], e["pos"][1]-pet_pos[1]))
            dx, dy = closest_e["pos"][0] - pet_pos[0], closest_e["pos"][1] - pet_pos[1]
            dist = math.hypot(dx, dy)
            if dist > 0:
                vx, vy = (dx/dist)*10, (dy/dist)*10
                spawn_field("attack", list(pet_pos), int(25 * player_stats["radius_mult"]), 30, "ball", vx, vy)
            pet_attack_timer = 90 

    combo_removes = []
    combo_adds = []
    
    def create_combo(ctype, base_rad, base_dur, cx, cy):
        rad = int(base_rad * player_stats["radius_mult"])
        dur = base_dur if base_dur <= 60 else int(base_dur * player_stats["skill_duration_mult"])
        return {"pos": [cx, cy], "type": ctype, "radius": rad, "timer": dur, "max_timer": dur, "shape": "field", "vx": 0, "vy": 0}

    for i in range(len(active_fields)):
        for j in range(i + 1, len(active_fields)):
            f1, f2 = active_fields[i], active_fields[j]
            if f1 in combo_removes or f2 in combo_removes: continue
                
            dist = math.hypot(f1["pos"][0] - f2["pos"][0], f1["pos"][1] - f2["pos"][1])
            if dist < f1["radius"] + f2["radius"]:
                combo = {f1["type"], f2["type"]}
                mid_x = (f1["pos"][0] + f2["pos"][0]) / 2
                mid_y = (f1["pos"][1] + f2["pos"][1]) / 2
                
                if combo == {"fire", "poison"}: 
                    combo_removes.extend([f1, f2]); combo_adds.append(create_combo("explosion", 150, 20, mid_x, mid_y))
                elif combo == {"fire", "ice"}: 
                    combo_removes.extend([f1, f2]); combo_adds.append(create_combo("steam", 130, 240, mid_x, mid_y))
                elif combo == {"ice", "poison"}: 
                    combo_removes.extend([f1, f2]); combo_adds.append(create_combo("plague_storm", 140, 300, mid_x, mid_y))
                elif combo == {"bomb", "poison"}:
                    combo_removes.extend([f1, f2]); combo_adds.append(create_combo("toxic_cloud", 180, 400, mid_x, mid_y))
                elif combo == {"heal", "tree"}:
                    combo_removes.extend([f1, f2]); combo_adds.append(create_combo("sanctuary", 160, 300, mid_x, mid_y))
                elif combo == {"fire", "tree"}:
                    combo_removes.extend([f1, f2]); combo_adds.append(create_combo("wildfire", 150, 120, mid_x, mid_y))
                elif combo == {"guard", "ice"}:
                    combo_removes.extend([f1, f2]); combo_adds.append(create_combo("glacial_barricade", 140, 300, mid_x, mid_y))
                elif combo == {"guard", "bomb"}:
                    combo_removes.extend([f1, f2]); combo_adds.append(create_combo("counter_shield", 130, 150, mid_x, mid_y))
                elif combo == {"guard", "heal"}:
                    combo_removes.extend([f1, f2]); combo_adds.append(create_combo("divine_grace", 160, 240, mid_x, mid_y))

    for f in combo_removes:
        if f in active_fields: active_fields.remove(f)
    active_fields.extend(combo_adds)

    for f in active_fields[:]:
        f["timer"] -= 1
        if f["timer"] <= 0:
            active_fields.remove(f)
            continue

        p_dist = math.hypot(player_pos[0] - f["pos"][0], player_pos[1] - f["pos"][1])
        is_p_hit = False
        if f["shape"] in ["field", "ball", "spike"] and p_dist <= f["radius"] + player_radius: is_p_hit = True
        elif f["shape"] == "square" and (abs(player_pos[0]-f["pos"][0]) <= f["radius"]+player_radius) and (abs(player_pos[1]-f["pos"][1]) <= f["radius"]+player_radius): is_p_hit = True
        
        if is_p_hit:
            if f["type"] == "heal": player_hp = min(player_max_hp, player_hp + 0.2)
            elif f["type"] == "guard": player_immune_timer = max(player_immune_timer, 10)
            elif f["type"] == "sanctuary": player_hp = min(player_max_hp, player_hp + 0.5)
            elif f["type"] == "divine_grace": 
                player_immune_timer = max(player_immune_timer, 10)
                player_hp = min(player_max_hp, player_hp + 0.3)

        dm = player_stats["damage_mult"]
        for e in room["enemies"]:
            is_hit = False
            dx, dy = e["pos"][0] - f["pos"][0], e["pos"][1] - f["pos"][1]
            dist = math.hypot(dx, dy)
            
            if f["shape"] in ["field", "ball", "spike"]: is_hit = dist <= f["radius"] + e["radius"]
            elif f["shape"] == "square": is_hit = (abs(dx) <= f["radius"] + e["radius"]) and (abs(dy) <= f["radius"] + e["radius"])

            if is_hit:
                if f["shape"] == "field": e["speed"] *= 0.5 
                elif f["shape"] == "spike": e["stun_timer"] = 30
                elif f["shape"] == "square":
                    if dist > 0:
                        e["pos"][0] += (dx/dist) * 8
                        e["pos"][1] += (dy/dist) * 8
                
                if f["type"] in ["sanctuary", "glacial_barricade", "counter_shield"]:
                    if dist > 0:
                        knockback = 12 if f["type"] == "counter_shield" else 5
                        e["pos"][0] += (dx/dist) * knockback
                        e["pos"][1] += (dy/dist) * knockback
                
                if f["type"] == "attack": 
                    e["hp"] -= 1.5 * dm
                    if player_items["elemental_blade"] and random.random() < 0.1:
                        rand_elem = random.choice(["fire", "ice", "poison", "tree"])
                        if rand_elem == "fire": e["hp"] -= 1.0 * dm
                        elif rand_elem == "ice": e["speed"] *= 0.3
                        elif rand_elem == "poison": e["hp"] -= 0.5 * dm
                        elif rand_elem == "tree": e["stun_timer"] = max(e.get("stun_timer",0), 30)

                elif f["type"] == "bomb": e["hp"] -= 8 * dm
                elif f["type"] == "explosion": e["hp"] -= 8 * dm
                elif f["type"] == "fire": e["hp"] -= 0.6 * dm
                elif f["type"] == "poison": e["hp"] -= 0.2 * dm
                elif f["type"] == "steam": e["hp"] -= 1.0 * dm
                elif f["type"] == "ice": e["speed"] *= 0.3
                elif f["type"] == "tree": e["speed"] = 0
                
                elif f["type"] == "plague_storm": e["hp"] -= 0.5 * dm; e["speed"] *= 0.1 
                elif f["type"] == "toxic_cloud": e["hp"] -= 1.0 * dm                    
                elif f["type"] == "wildfire": e["hp"] -= 2.0 * dm
                elif f["type"] == "glacial_barricade": e["speed"] *= 0.1
                elif f["type"] == "counter_shield": e["hp"] -= 4.0 * dm 

    room["enemies"] = [e for e in room["enemies"] if e["hp"] > 0]

    for i, e in enumerate(room["enemies"]):
        dx, dy = player_pos[0] - e["pos"][0], player_pos[1] - e["pos"][1]
        dist = math.hypot(dx, dy)
        
        if e.get("stun_timer", 0) > 0:
            e["stun_timer"] -= 1
            move_x, move_y = 0, 0
        elif dist > 0 and player_hp > 0:
            move_x = (dx/dist) * e["speed"]
            move_y = (dy/dist) * e["speed"]
        else:
            move_x, move_y = 0, 0
            
        e["pos"][0] += move_x
        for f in active_fields:
            if f["shape"] == "square" and abs(e["pos"][0] - f["pos"][0]) < f["radius"] + e["radius"] and abs(e["pos"][1] - f["pos"][1]) < f["radius"] + e["radius"]:
                e["pos"][0] -= move_x 
                break
        
        e["pos"][1] += move_y
        for f in active_fields:
            if f["shape"] == "square" and abs(e["pos"][0] - f["pos"][0]) < f["radius"] + e["radius"] and abs(e["pos"][1] - f["pos"][1]) < f["radius"] + e["radius"]:
                e["pos"][1] -= move_y 
                break

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

        p_dx, p_dy = player_pos[0] - e["pos"][0], player_pos[1] - e["pos"][1]
        p_dist = math.hypot(p_dx, p_dy)
        min_dist = player_radius + e["radius"]
        if p_dist < min_dist and p_dist > 0:
            player_pos[0] += (p_dx / p_dist) * (min_dist - p_dist)
            player_pos[1] += (p_dy / p_dist) * (min_dist - p_dist)
            if player_immune_timer <= 0 and player_hp > 0:
                base_dmg = 25 if e["type"] == "boss" else 10
                actual_dmg = base_dmg * (1.0 - player_stats["defense_up"])
                player_hp = max(0, player_hp - actual_dmg)
                player_immune_timer = 60 
                
                if player_stats["thorns_damage"] > 0:
                    e["hp"] -= player_stats["thorns_damage"]

    if not room["cleared"] and len(room["enemies"]) == 0 and current_coords != (0,0):
        room["cleared"] = True
        all_elements = ["fire", "poison", "ice", "bomb", "tree", "guard", "heal"]
        all_shapes = ["ball", "square", "spike"]
        
        available_words = [w for w in all_elements if w not in player_words]
        available_shapes = [s for s in all_shapes if s not in player_shapes]
        available_non_stack = [item for item in NON_STACKABLE_ITEMS if not player_items.get(item["id"], False)]
        
        reward_pool = []
        if available_words: reward_pool.extend(["word"] * 2) 
        if available_shapes: reward_pool.extend(["shape"] * 2) 
        reward_pool.extend(["stackable_item"] * 4) 
        if available_non_stack: reward_pool.extend(["non_stackable_item"] * 2)
        
        if reward_pool:
            r_type = random.choice(reward_pool)
            r_val = None
            if r_type == "word": r_val = random.choice(available_words)
            elif r_type == "shape": r_val = random.choice(available_shapes)
            elif r_type == "stackable_item": r_val = random.choice(STACKABLE_ITEMS)
            elif r_type == "non_stackable_item": r_val = random.choice(available_non_stack)
            
            room["reward"] = {"data": {"type": r_type, "value": r_val}, "pos": [WIDTH//2, ROOM_RECT.centery]}

    if room.get("reward"):
        dist = math.hypot(room["reward"]["pos"][0] - player_pos[0], room["reward"]["pos"][1] - player_pos[1])
        if dist < 40:
            reward_data = room["reward"]["data"]
            r_type = reward_data["type"]
            r_val = reward_data["value"]
            
            if r_type == "word":
                player_words.append(r_val)
                message = f"단어 획득: '{r_val}'!"
            elif r_type == "shape":
                player_shapes.append(r_val)
                message = f"형태 획득: '{r_val}'!"
            elif r_type in ["stackable_item", "non_stackable_item"]:
                item_id = r_val["id"]
                item_name = r_val["name"]
                
                if item_id == "duration_up": player_stats["skill_duration_mult"] += 0.3
                elif item_id == "radius_up": player_stats["radius_mult"] += 0.25
                elif item_id == "damage_up": player_stats["damage_mult"] += 0.3
                elif item_id == "speed_up": player_stats["speed_mult"] += 0.15
                elif item_id == "thorns": player_stats["thorns_damage"] += 10
                elif item_id == "hp_up": 
                    player_max_hp += 30; player_hp += 30
                elif item_id == "defense_up": player_stats["defense_up"] = min(0.7, player_stats["defense_up"] + 0.15)
                elif item_id in ["pet", "elemental_blade", "map_reveal"]:
                    player_items[item_id] = True
                
                message = f"아이템 획득: {item_name}!"
                
            message_timer = 150
            room["reward"] = None

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

    if active_fields:
        field_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        for f in active_fields:
            color = FIELD_COLORS.get(f["type"], (255, 255, 255, 100))
            if f["type"] in ["explosion", "bomb", "wildfire", "counter_shield"]:
                fade = max(0, int(255 * (f["timer"] / f["max_timer"])))
                color = (color[0], color[1], color[2], fade)
            
            if f["shape"] == "ball" or f["shape"] == "field":
                pygame.draw.circle(field_surface, color, (int(f["pos"][0]), int(f["pos"][1])), f["radius"])
            elif f["shape"] == "square":
                rect = pygame.Rect(f["pos"][0] - f["radius"], f["pos"][1] - f["radius"], f["radius"]*2, f["radius"]*2)
                pygame.draw.rect(field_surface, color, rect)
                pygame.draw.rect(field_surface, (255,255,255,100), rect, 2) 
            elif f["shape"] == "spike":
                points = []
                for i in range(8):
                    r = f["radius"] if i % 2 == 0 else f["radius"] * 0.4
                    ang = math.radians(i * 45)
                    points.append((f["pos"][0] + math.cos(ang)*r, f["pos"][1] + math.sin(ang)*r))
                pygame.draw.polygon(field_surface, color, points)
        screen.blit(field_surface, (0, 0))

    if player_items["pet"] and player_hp > 0:
        pygame.draw.circle(screen, (255, 150, 200), (int(pet_pos[0]), int(pet_pos[1])), 10)
        pygame.draw.circle(screen, WHITE, (int(pet_pos[0]), int(pet_pos[1])), 10, 2)

    for e in room["enemies"]:
        color = BOSS_COLOR if e["type"] == "boss" else ENEMY_COLOR
        pygame.draw.circle(screen, color, (int(e["pos"][0]), int(e["pos"][1])), e["radius"])
        if e.get("stun_timer", 0) > 0:
            pygame.draw.circle(screen, WHITE, (int(e["pos"][0]), int(e["pos"][1])), e["radius"] + 4, 2)
            
        bar_w = e["radius"] * 3
        bar_x, bar_y = e["pos"][0] - (bar_w / 2), e["pos"][1] - e["radius"] - 15
        pygame.draw.rect(screen, HP_RED, (bar_x, bar_y, bar_w, 8))
        pygame.draw.rect(screen, HP_GREEN, (bar_x, bar_y, int(bar_w * max(0, e["hp"] / e["max_hp"])), 8))

    if room.get("reward"):
        rw_data = room["reward"]["data"]
        r_type = rw_data["type"]
        r_val = rw_data["value"]
        
        if r_type in ["word", "shape"]:
            disp_text = f"[{r_val}]"
            color = (255, 255, 0)
        else:
            disp_text = f"[{r_val['name']}]" 
            color = (0, 255, 255) if r_type == "stackable_item" else (255, 100, 255)
            
        rw_text = font.render(disp_text, True, color)
        screen.blit(rw_text, (room["reward"]["pos"][0] - rw_text.get_width()//2, room["reward"]["pos"][1] - 15))

    if player_hp > 0:
        if player_immune_timer > 0:
            pygame.draw.circle(screen, PLAYER_IMMUNE, (int(player_pos[0]), int(player_pos[1])), player_radius)
            pygame.draw.circle(screen, WHITE, (int(player_pos[0]), int(player_pos[1])), player_radius + 2, 2)
        else:
            pygame.draw.circle(screen, PLAYER_COLOR, (int(player_pos[0]), int(player_pos[1])), player_radius)

    if attack_timer > 0 and 'attack_data' in locals():
        points = [(player_pos[0], player_pos[1])]
        start_angle = attack_data["angle"] - attack_data["half_cone"]
        end_angle = attack_data["angle"] + attack_data["half_cone"]
        steps = 10
        for i in range(steps + 1):
            theta = start_angle + (end_angle - start_angle) * (i / steps)
            px = player_pos[0] + math.cos(theta) * attack_data["radius"]
            py = player_pos[1] + math.sin(theta) * attack_data["radius"]
            points.append((px, py))
        pygame.draw.polygon(screen, WHITE, points, 3)
        attack_timer -= 1

    MM_X, MM_Y, CELL, GAP = WIDTH - 100, 80, 15, 3
    for coords, info in world_map.items():
        if is_discovered(coords):
            draw_x, draw_y = MM_X + (coords[0] - current_coords[0]) * (CELL + GAP) - CELL // 2, MM_Y + (coords[1] - current_coords[1]) * (CELL + GAP) - CELL // 2
            color = MM_CURRENT if coords == current_coords else (MM_BOSS if info["type"] == "boss" else (MM_VISITED if info["visited"] else MM_DISCOVERED))
            pygame.draw.rect(screen, color, (draw_x, draw_y, CELL, CELL))
            pygame.draw.rect(screen, WHITE, (draw_x, draw_y, CELL, CELL), 1)

    # 기본 UI 레이아웃
    pygame.draw.rect(screen, UI_BG, (15, 15, 260, 35))
    pygame.draw.rect(screen, WHITE, (15, 15, 260, 35), 2)
    screen.blit(font.render(f"PLAYER HP: {int(player_hp)}/{player_max_hp}", True, WHITE if player_hp > 25 else HP_RED), (30, 22))

    if message_timer > 0:
        msg_surf = font.render(message, True, (255, 230, 100))
        screen.blit(msg_surf, (WIDTH - msg_surf.get_width() - 20, 20))
        message_timer -= 1

    ui_rect = pygame.Rect(0, HEIGHT - 100, WIDTH, 100)
    pygame.draw.rect(screen, UI_BG, ui_rect)
    pygame.draw.line(screen, WHITE, (0, HEIGHT - 100), (WIDTH, HEIGHT - 100), 2)
    
    screen.blit(font.render(f"Words: {', '.join(player_words)}", True, (150, 200, 255)), (20, HEIGHT - 92))
    screen.blit(font.render(f"Shapes: {', '.join(player_shapes)}", True, (200, 255, 150)), (20, HEIGHT - 72))
    
    pygame.draw.rect(screen, BLACK, (20, HEIGHT - 45, WIDTH - 40, 35))
    pygame.draw.rect(screen, WHITE, (20, HEIGHT - 45, WIDTH - 40, 35), 2)
    screen.blit(big_font.render(input_text + "_", True, WHITE), (30, HEIGHT - 42))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
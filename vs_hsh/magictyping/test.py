import pygame
import random
import math
import sys

# 1. 초기화 및 기본 설정
pygame.init()
WIDTH, HEIGHT = 800, 750
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Typing Isaac - Element & Shape Combos")
clock = pygame.time.Clock()

# 색상 정의
WHITE = (255, 255, 255)
BLACK = (15, 15, 15)
FLOOR_COLOR = (50, 45, 40)
WALL_COLOR = (35, 30, 25)
DOOR_OPEN = (200, 160, 40)
DOOR_LOCKED = (100, 100, 100)
PLAYER_COLOR = (100, 180, 255)
PLAYER_IMMUNE = (180, 220, 255)
ENEMY_COLOR = (220, 60, 60)
BOSS_COLOR = (180, 40, 200)
UI_BG = (25, 25, 35)
HP_RED = (200, 50, 50)
HP_GREEN = (50, 200, 50)
MM_CURRENT, MM_VISITED, MM_DISCOVERED, MM_BOSS = (255, 230, 0), (120, 120, 120), (60, 60, 60), (230, 50, 50)

# 장판(필드) 색상 (RGBA)
FIELD_COLORS = {
    "fire": (255, 80, 0, 120),
    "poison": (100, 255, 50, 100),
    "ice": (100, 200, 255, 120),
    "steam": (200, 200, 220, 150),
    "tree": (34, 139, 34, 130),
    "explosion": (255, 50, 50, 180)
}

font = pygame.font.SysFont(None, 30)
big_font = pygame.font.SysFont(None, 40)

# 2. 맵 생성 로직
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

# 플레이어 기본 상태 및 단어 (기본적으로 테스트하기 좋게 불/독 지급)
player_pos = [WIDTH // 2, ROOM_RECT.centery]
player_speed = 5
player_radius = 15
player_words = ["attack", "fire", "poison", "ice"] # 획득한 마법 속성
player_shapes = ["ball", "square", "spike"] # 조합 가능한 형태들
player_max_hp = 100
player_hp = 100
player_immune_timer = 0

input_text = ""
attack_timer = 0
attack_data = {"angle": 0, "radius": 0, "half_cone": 0}
message = "예시: 'fire square' 타이핑 후 Enter!"
message_timer = 180

active_fields = []

# 장판(Shape) 포함 생성 함수
def spawn_field(f_type, pos, radius, duration, shape="ball"):
    interacted = False
    # 기존 장판과의 콤보 상호작용 검사 (반지름 기반 충돌)
    for f in active_fields[:]:
        dist = math.hypot(f["pos"][0] - pos[0], f["pos"][1] - pos[1])
        if dist < f["radius"] + radius:
            combo = {f_type, f["type"]}
            if combo == {"fire", "poison"}:
                active_fields.remove(f)
                # 폭발은 형태에 구애받지 않고 둥글게 퍼지도록 세팅
                active_fields.append({"pos": f["pos"], "type": "explosion", "radius": 150, "timer": 20, "shape": "ball"})
                interacted = True
                break
            elif combo == {"fire", "ice"}:
                active_fields.remove(f)
                active_fields.append({"pos": f["pos"], "type": "steam", "radius": 130, "timer": 240, "shape": "ball"})
                interacted = True
                break
    
    if not interacted:
        active_fields.append({"pos": list(pos), "type": f_type, "radius": radius, "timer": duration, "shape": shape})


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
            message = "보스 방 진입! 주의하세요!"
            message_timer = 150
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
                
                # 입력된 단어 분리 (속성 + 형태)
                tokens = cmd.split()
                if len(tokens) > 0:
                    element = tokens[0]
                    # 형태 단어가 없으면 'ball'을 기본값으로 사용
                    shape = tokens[1] if len(tokens) > 1 else "ball"
                    
                    if element in player_words and (shape in player_shapes or len(tokens) == 1):
                        if room["enemies"]:
                            closest_e = min(room["enemies"], key=lambda e: math.hypot(e["pos"][0]-player_pos[0], e["pos"][1]-player_pos[1]))
                            target_pos = closest_e["pos"]
                        else:
                            target_pos = player_pos
                            
                        if element == "attack":
                            # attack 로직 유지
                            attack_radius = 140
                            cone_angle = math.radians(60)
                            half_cone = cone_angle / 2
                            base_angle = 0 
                            if room["enemies"]:
                                dx = target_pos[0] - player_pos[0]
                                dy = target_pos[1] - player_pos[1]
                                base_angle = math.atan2(dy, dx)
                                for e in room["enemies"]:
                                    edx = e["pos"][0] - player_pos[0]
                                    edy = e["pos"][1] - player_pos[1]
                                    dist = math.hypot(edx, edy)
                                    if dist <= attack_radius:
                                        target_angle = math.atan2(edy, edx)
                                        angle_diff = (target_angle - base_angle + math.pi) % (2 * math.pi) - math.pi
                                        if abs(angle_diff) <= half_cone:
                                            e["hp"] -= 15
                            attack_timer = 15
                            attack_data = {"angle": base_angle, "radius": attack_radius, "half_cone": half_cone}
                        
                        # 장판 속성 + 형태 스킬 스폰
                        elif element == "fire": spawn_field("fire", target_pos, 80, 240, shape)
                        elif element == "poison": spawn_field("poison", target_pos, 100, 360, shape)
                        elif element == "ice": spawn_field("ice", target_pos, 90, 240, shape)
                        elif element == "tree": spawn_field("tree", target_pos, 70, 300, shape)
                        elif element == "bomb": spawn_field("explosion", target_pos, 100, 15, shape)
                        elif element == "guard":
                            player_immune_timer = 300
                            message = "가드 활성화! 5초간 무적!"
                            message_timer = 90
                        elif element == "heal":
                            player_hp = min(player_max_hp, player_hp + 30)
                            message = "체력을 30 회복했습니다!"
                            message_timer = 90
                    else:
                        message = "미획득 단어이거나 잘못된 조합입니다."
                        message_timer = 60

            elif event.key == pygame.K_BACKSPACE:
                input_text = input_text[:-1]
            elif event.key == pygame.K_SPACE:
                input_text += " " # 띄어쓰기 지원
            else:
                if event.unicode.isalpha():
                    input_text += event.unicode

    # 플레이어 이동 로직
    if player_hp > 0:
        keys = pygame.key.get_pressed()
        new_x, new_y = player_pos[0], player_pos[1]
        if keys[pygame.K_LEFT]:  new_x -= player_speed
        if keys[pygame.K_RIGHT]: new_x += player_speed
        if keys[pygame.K_UP]:    new_y -= player_speed
        if keys[pygame.K_DOWN]:  new_y += player_speed
    else:
        new_x, new_y = player_pos[0], player_pos[1]
        message = "GAME OVER!"
        message_timer = 2

    # 방 이동 충돌 처리
    door_w = 80
    if new_x - player_radius < ROOM_RECT.left:
        target = (current_coords[0] - 1, current_coords[1])
        if target in world_map and (ROOM_RECT.centery - door_w//2 < new_y < ROOM_RECT.centery + door_w//2) and room_cleared:
            enter_room(target)
            new_x = ROOM_RECT.right - player_radius - 10
        else: new_x = ROOM_RECT.left + player_radius
    elif new_x + player_radius > ROOM_RECT.right:
        target = (current_coords[0] + 1, current_coords[1])
        if target in world_map and (ROOM_RECT.centery - door_w//2 < new_y < ROOM_RECT.centery + door_w//2) and room_cleared:
            enter_room(target)
            new_x = ROOM_RECT.left + player_radius + 10
        else: new_x = ROOM_RECT.right - player_radius
    if new_y - player_radius < ROOM_RECT.top:
        target = (current_coords[0], current_coords[1] - 1)
        if target in world_map and (WIDTH//2 - door_w//2 < new_x < WIDTH//2 + door_w//2) and room_cleared:
            enter_room(target)
            new_y = ROOM_RECT.bottom - player_radius - 10
        else: new_y = ROOM_RECT.top + player_radius
    elif new_y + player_radius > ROOM_RECT.bottom:
        target = (current_coords[0], current_coords[1] + 1)
        if target in world_map and (WIDTH//2 - door_w//2 < new_x < WIDTH//2 + door_w//2) and room_cleared:
            enter_room(target)
            new_y = ROOM_RECT.top + player_radius + 10
        else: new_y = ROOM_RECT.bottom - player_radius

    player_pos[0], player_pos[1] = new_x, new_y

    # 적 상태 & 장판 효과 업데이트
    for e in room["enemies"]:
        e["speed"] = e["base_speed"]
        
    for f in active_fields[:]:
        f["timer"] -= 1
        if f["timer"] <= 0:
            active_fields.remove(f)
            continue
            
        for e in room["enemies"]:
            is_hit = False
            dx = e["pos"][0] - f["pos"][0]
            dy = e["pos"][1] - f["pos"][1]
            dist = math.hypot(dx, dy)
            
            # 💡 모양(Shape)에 따른 충돌 판정 다르게 적용
            if f["shape"] == "ball" or f["shape"] == "spike":
                # 가시와 공은 원형 기반 거리 판정
                is_hit = dist <= f["radius"] + e["radius"]
            elif f["shape"] == "square":
                # 사각형은 AABB(X, Y축 절댓값) 기반 박스 판정 (모서리 타격 가능)
                is_hit = (abs(dx) <= f["radius"] + e["radius"]) and (abs(dy) <= f["radius"] + e["radius"])

            if is_hit:
                if f["type"] == "fire": e["hp"] -= 0.6
                elif f["type"] == "poison": e["hp"] -= 0.2
                elif f["type"] == "steam": e["hp"] -= 1.0
                elif f["type"] == "ice": e["speed"] *= 0.3
                elif f["type"] == "tree": e["speed"] = 0
                elif f["type"] == "explosion": e["hp"] -= 8

    room["enemies"] = [e for e in room["enemies"] if e["hp"] > 0]

    # 적 이동 & 플레이어 충돌
    for i, e in enumerate(room["enemies"]):
        dx = player_pos[0] - e["pos"][0]
        dy = player_pos[1] - e["pos"][1]
        dist = math.hypot(dx, dy)
        if dist > 0 and player_hp > 0:
            e["pos"][0] += (dx/dist) * e["speed"]
            e["pos"][1] += (dy/dist) * e["speed"]

        for j in range(i + 1, len(room["enemies"])):
            other_e = room["enemies"][j]
            ex = e["pos"][0] - other_e["pos"][0]
            ey = e["pos"][1] - other_e["pos"][1]
            e_dist = math.hypot(ex, ey)
            e_min_dist = e["radius"] + other_e["radius"]
            if e_dist < e_min_dist and e_dist > 0:
                e_overlap = e_min_dist - e_dist
                e["pos"][0] += (ex / e_dist) * (e_overlap / 2)
                e["pos"][1] += (ey / e_dist) * (e_overlap / 2)
                other_e["pos"][0] -= (ex / e_dist) * (e_overlap / 2)
                other_e["pos"][1] -= (ey / e_dist) * (e_overlap / 2)

        p_dx = player_pos[0] - e["pos"][0]
        p_dy = player_pos[1] - e["pos"][1]
        p_dist = math.hypot(p_dx, p_dy)
        min_dist = player_radius + e["radius"]
        
        if p_dist < min_dist and p_dist > 0:
            overlap = min_dist - p_dist 
            player_pos[0] += (p_dx / p_dist) * overlap
            player_pos[1] += (p_dy / p_dist) * overlap
            player_pos[0] = max(ROOM_RECT.left + player_radius, min(player_pos[0], ROOM_RECT.right - player_radius))
            player_pos[1] = max(ROOM_RECT.top + player_radius, min(player_pos[1], ROOM_RECT.bottom - player_radius))
            
            if player_immune_timer <= 0 and player_hp > 0:
                damage = 25 if e["type"] == "boss" else 10
                player_hp = max(0, player_hp - damage)
                player_immune_timer = 60 

    # 렌더링
    pygame.draw.rect(screen, WALL_COLOR, (0, 0, WIDTH, HEIGHT - 100))
    pygame.draw.rect(screen, FLOOR_COLOR, ROOM_RECT)

    # 문 렌더링
    door_color = DOOR_OPEN if room_cleared else DOOR_LOCKED
    door_thick = 15
    for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
        neighbor = (current_coords[0] + dx, current_coords[1] + dy)
        if neighbor in world_map:
            if (dx, dy) == (0, -1): pygame.draw.rect(screen, door_color, (WIDTH//2 - door_w//2, ROOM_RECT.top - door_thick, door_w, door_thick + 5))
            elif (dx, dy) == (0, 1): pygame.draw.rect(screen, door_color, (WIDTH//2 - door_w//2, ROOM_RECT.bottom - 5, door_w, door_thick + 5))
            elif (dx, dy) == (-1, 0): pygame.draw.rect(screen, door_color, (ROOM_RECT.left - door_thick, ROOM_RECT.centery - door_w//2, door_thick + 5, door_w))
            elif (dx, dy) == (1, 0): pygame.draw.rect(screen, door_color, (ROOM_RECT.right - 5, ROOM_RECT.centery - door_w//2, door_thick + 5, door_w))

    # 💡 장판 렌더링 (모양에 따라 다르게 그림)
    if active_fields:
        field_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        for f in active_fields:
            color = FIELD_COLORS.get(f["type"], (255, 255, 255, 100))
            if f["type"] == "explosion":
                fade_alpha = min(180, int(f["timer"] * (180/15)))
                color = (255, 50, 50, fade_alpha)
            
            # 모양별 그리기 로직
            if f["shape"] == "ball":
                pygame.draw.circle(field_surface, color, (int(f["pos"][0]), int(f["pos"][1])), f["radius"])
            elif f["shape"] == "square":
                rect = pygame.Rect(f["pos"][0] - f["radius"], f["pos"][1] - f["radius"], f["radius"]*2, f["radius"]*2)
                pygame.draw.rect(field_surface, color, rect)
            elif f["shape"] == "spike":
                # 가시(8각 별 모양) 다각형 생성
                points = []
                for i in range(8):
                    r = f["radius"] if i % 2 == 0 else f["radius"] * 0.4
                    ang = math.radians(i * 45)
                    points.append((f["pos"][0] + math.cos(ang)*r, f["pos"][1] + math.sin(ang)*r))
                pygame.draw.polygon(field_surface, color, points)

        screen.blit(field_surface, (0, 0))

    # 적 및 HP 그리기
    for e in room["enemies"]:
        color = BOSS_COLOR if e["type"] == "boss" else ENEMY_COLOR
        pygame.draw.circle(screen, color, (int(e["pos"][0]), int(e["pos"][1])), e["radius"])
        bar_w = e["radius"] * 3
        bar_h = 8
        bar_x = e["pos"][0] - (bar_w / 2)
        bar_y = e["pos"][1] - e["radius"] - 15
        pygame.draw.rect(screen, HP_RED, (bar_x, bar_y, bar_w, bar_h))
        hp_ratio = max(0, e["hp"] / e["max_hp"])
        pygame.draw.rect(screen, HP_GREEN, (bar_x, bar_y, int(bar_w * hp_ratio), bar_h))

    # 플레이어 그리기
    if player_hp > 0:
        if player_immune_timer > 0:
            pygame.draw.circle(screen, PLAYER_IMMUNE, (int(player_pos[0]), int(player_pos[1])), player_radius)
            pygame.draw.circle(screen, WHITE, (int(player_pos[0]), int(player_pos[1])), player_radius + 2, 2)
        else:
            pygame.draw.circle(screen, PLAYER_COLOR, (int(player_pos[0]), int(player_pos[1])), player_radius)

    # 기본 공격 이펙트
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

    # 상단 UI & 미니맵
    pygame.draw.rect(screen, UI_BG, (15, 15, 260, 35))
    pygame.draw.rect(screen, WHITE, (15, 15, 260, 35), 2)
    hp_text = font.render(f"PLAYER HP: {player_hp}/{player_max_hp}", True, WHITE if player_hp > 25 else HP_RED)
    screen.blit(hp_text, (30, 25))

    if message_timer > 0:
        msg_surf = font.render(message, True, (255, 230, 100))
        screen.blit(msg_surf, (WIDTH - msg_surf.get_width() - 20, 20))
        message_timer -= 1

    # 하단 UI (단어 & 형태 상태)
    ui_rect = pygame.Rect(0, HEIGHT - 100, WIDTH, 100)
    pygame.draw.rect(screen, UI_BG, ui_rect)
    pygame.draw.line(screen, WHITE, (0, HEIGHT - 100), (WIDTH, HEIGHT - 100), 2)
    
    # 획득한 단어와 형태 리스트 출력
    words_surf = font.render(f"Words: {', '.join(player_words)}", True, (150, 200, 255))
    screen.blit(words_surf, (20, HEIGHT - 95))
    shapes_surf = font.render(f"Shapes: {', '.join(player_shapes)}", True, (200, 255, 150))
    screen.blit(shapes_surf, (20, HEIGHT - 75))
    
    pygame.draw.rect(screen, BLACK, (20, HEIGHT - 45, WIDTH - 40, 35))
    pygame.draw.rect(screen, WHITE, (20, HEIGHT - 45, WIDTH - 40, 35), 2)
    input_surf = big_font.render(input_text + "_", True, WHITE)
    screen.blit(input_surf, (30, HEIGHT - 40))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
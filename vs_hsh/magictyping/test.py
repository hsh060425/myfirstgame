import pygame
import random
import math
import sys

# 1. 초기화 및 기본 설정
pygame.init()
WIDTH, HEIGHT = 800, 750  # 타이핑 UI를 위해 세로 길이 확장
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Typing Isaac System - Final Rev")
clock = pygame.time.Clock()

# 색상 정의
WHITE = (255, 255, 255)
BLACK = (15, 15, 15)
FLOOR_COLOR = (50, 45, 40)
WALL_COLOR = (35, 30, 25)
DOOR_OPEN = (200, 160, 40)
DOOR_LOCKED = (100, 100, 100)
PLAYER_COLOR = (100, 180, 255)
PLAYER_IMMUNE = (180, 220, 255) # 무적 상태 고정 색상
ENEMY_COLOR = (220, 60, 60)
BOSS_COLOR = (180, 40, 200)
UI_BG = (25, 25, 35)

# HP 바 색상
HP_RED = (200, 50, 50)
HP_GREEN = (50, 200, 50)

# 미니맵 색상
MM_CURRENT, MM_VISITED, MM_DISCOVERED, MM_BOSS = (255, 230, 0), (120, 120, 120), (60, 60, 60), (230, 50, 50)

# 폰트 설정
font = pygame.font.SysFont(None, 30)
big_font = pygame.font.SysFont(None, 40)
sm_font = pygame.font.SysFont(None, 18)

# 2. 절차적 맵 생성 (적 정보 및 최대 체력 추가)
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

# 플레이어 상태
player_pos = [WIDTH // 2, ROOM_RECT.centery]
player_speed = 5
player_radius = 15
player_words = ["attack"]
player_max_hp = 100
player_hp = 100
player_immune_timer = 0 # 무적 시간 타이머 (60프레임 = 1초)

# 타이핑 및 전투 UI 변수
input_text = ""
attack_timer = 0
attack_data = {"angle": 0, "radius": 0, "half_cone": 0}
message = "방향키 이동, 'attack' 타이핑 후 Enter!"
message_timer = 180

# 방 입장 시 적 스폰 함수
def enter_room(coords):
    global current_coords, message, message_timer
    current_coords = coords
    room = world_map[coords]
    room["visited"] = True
    
    if not room["cleared"] and len(room["enemies"]) == 0 and coords != (0,0):
        if room["type"] == "normal":
            for _ in range(random.randint(2, 4)):
                room["enemies"].append({
                    "pos": [random.randint(150, WIDTH-150), random.randint(150, ROOM_RECT.bottom - 100)],
                    "hp": 20, "max_hp": 20, "speed": 2.0, "type": "normal", "radius": 12
                })
        elif room["type"] == "boss":
            message = "보스 방 진입! 주의하세요!"
            message_timer = 150
            room["enemies"].append({
                "pos": [WIDTH//2, ROOM_RECT.centery],
                "hp": 150, "max_hp": 150, "speed": 1.5, "type": "boss", "radius": 35
            })

enter_room((0,0))

# 미니맵 판별
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
    
    # 무적 타이머 감소 로직
    if player_immune_timer > 0:
        player_immune_timer -= 1
    
    # 3. 이벤트 처리 (타이핑 입력 및 공격 로직)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                cmd = input_text.strip().lower()
                input_text = ""
                
                if cmd in player_words:
                    if cmd == "attack":
                        attack_radius = 140
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
                                        e["hp"] -= 10
                                        
                        attack_timer = 15
                        attack_data = {"angle": base_angle, "radius": attack_radius, "half_cone": half_cone}

                    elif cmd == "fire":
                        attack_timer = 20
                        for e in room["enemies"]:
                            e["hp"] -= 15
                    elif cmd == "heal":
                        player_hp = min(player_max_hp, player_hp + 20)
                        message = "체력을 20 회복했습니다!"
                        message_timer = 90
                elif cmd != "":
                    message = "미획득 단어입니다."
                    message_timer = 60
            elif event.key == pygame.K_BACKSPACE:
                input_text = input_text[:-1]
            else:
                if event.unicode.isalpha():
                    input_text += event.unicode

    # 4. 플레이어 이동 처리 (사망 시 조작 불가)
    if player_hp > 0:
        keys = pygame.key.get_pressed()
        new_x, new_y = player_pos[0], player_pos[1]
        
        if keys[pygame.K_LEFT]:  new_x -= player_speed
        if keys[pygame.K_RIGHT]: new_x += player_speed
        if keys[pygame.K_UP]:    new_y -= player_speed
        if keys[pygame.K_DOWN]:  new_y += player_speed
    else:
        new_x, new_y = player_pos[0], player_pos[1]
        message = "GAME OVER! 창을 닫고 다시 시작하세요."
        message_timer = 2

    # 5. 방 이동 및 벽/문 충돌 판정
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

    # 6. 적 로직 (이동 및 충돌, 피격 처리)
    room["enemies"] = [e for e in room["enemies"] if e["hp"] > 0]

    for i, e in enumerate(room["enemies"]):
        # [1] 플레이어를 향해 이동
        dx = player_pos[0] - e["pos"][0]
        dy = player_pos[1] - e["pos"][1]
        dist = math.hypot(dx, dy)
        
        if dist > 0 and player_hp > 0:
            e["pos"][0] += (dx/dist) * e["speed"]
            e["pos"][1] += (dy/dist) * e["speed"]

        # [2] 적끼리 뭉침 방지
        for j in range(i + 1, len(room["enemies"])):
            other_e = room["enemies"][j]
            ex = e["pos"][0] - other_e["pos"][0]
            ey = e["pos"][1] - other_e["pos"][1]
            e_dist = math.hypot(ex, ey)
            e_min_dist = e["radius"] + other_e["radius"]
            
            if e_dist < e_min_dist and e_dist > 0:
                e_overlap = e_min_dist - e_dist
                push_x = (ex / e_dist) * (e_overlap / 2)
                push_y = (ey / e_dist) * (e_overlap / 2)
                e["pos"][0] += push_x
                e["pos"][1] += push_y
                other_e["pos"][0] -= push_x
                other_e["pos"][1] -= push_y

        # [3] 플레이어와 적 충돌 (피격 시스템 및 무적 판정 완벽 적용)
        p_dx = player_pos[0] - e["pos"][0]
        p_dy = player_pos[1] - e["pos"][1]
        p_dist = math.hypot(p_dx, p_dy)
        min_dist = player_radius + e["radius"]
        
        if p_dist < min_dist and p_dist > 0:
            overlap = min_dist - p_dist 
            # 플레이어를 부딪힌 반대 방향으로 밀어냄
            player_pos[0] += (p_dx / p_dist) * overlap
            player_pos[1] += (p_dy / p_dist) * overlap
            
            # 밀려난 플레이어가 방 밖으로 나가지 않도록 경계선 보정
            player_pos[0] = max(ROOM_RECT.left + player_radius, min(player_pos[0], ROOM_RECT.right - player_radius))
            player_pos[1] = max(ROOM_RECT.top + player_radius, min(player_pos[1], ROOM_RECT.bottom - player_radius))
            
            # 무적 시간이 0 이하일 때만 데미지를 입도록 수정 (중복 데미지 방지)
            if player_immune_timer <= 0 and player_hp > 0:
                damage = 25 if e["type"] == "boss" else 10
                player_hp = max(0, player_hp - damage)
                # 60프레임(약 1초) 동안 무적 시간 부여
                player_immune_timer = 60 

    # 방 클리어 시 보상 생성
    if not room["cleared"] and len(room["enemies"]) == 0 and current_coords != (0,0):
        room["cleared"] = True
        possible_rewards = ["fire", "ice", "heal", "bomb"]
        room["reward"] = {"word": random.choice(possible_rewards), "pos": [WIDTH//2, ROOM_RECT.centery]}
        message = "CLEAR! 보상 단어 스폰됨!"
        message_timer = 150

    # 보상 획득 처리
    if room["reward"]:
        dist = math.hypot(room["reward"]["pos"][0] - player_pos[0], room["reward"]["pos"][1] - player_pos[1])
        if dist < 40:
            new_word = room["reward"]["word"]
            if new_word not in player_words:
                player_words.append(new_word)
                message = f"단어 획득: '{new_word}'!"
                message_timer = 150
            room["reward"] = None

    # 7. 그래픽 렌더링
    pygame.draw.rect(screen, WALL_COLOR, (0, 0, WIDTH, HEIGHT - 100))
    pygame.draw.rect(screen, FLOOR_COLOR, ROOM_RECT)

    # 문 그리기
    door_color = DOOR_OPEN if room_cleared else DOOR_LOCKED
    door_thick = 15
    for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
        neighbor = (current_coords[0] + dx, current_coords[1] + dy)
        if neighbor in world_map:
            if (dx, dy) == (0, -1):
                pygame.draw.rect(screen, door_color, (WIDTH//2 - door_w//2, ROOM_RECT.top - door_thick, door_w, door_thick + 5))
            elif (dx, dy) == (0, 1):
                pygame.draw.rect(screen, door_color, (WIDTH//2 - door_w//2, ROOM_RECT.bottom - 5, door_w, door_thick + 5))
            elif (dx, dy) == (-1, 0):
                pygame.draw.rect(screen, door_color, (ROOM_RECT.left - door_thick, ROOM_RECT.centery - door_w//2, door_thick + 5, door_w))
            elif (dx, dy) == (1, 0):
                pygame.draw.rect(screen, door_color, (ROOM_RECT.right - 5, ROOM_RECT.centery - door_w//2, door_thick + 5, door_w))

    # 적 및 💡머리 위 HP 바 그리기 (크기 키움 적용)
    for e in room["enemies"]:
        color = BOSS_COLOR if e["type"] == "boss" else ENEMY_COLOR
        pygame.draw.circle(screen, color, (int(e["pos"][0]), int(e["pos"][1])), e["radius"])
        
        # 수정된 체력바 구현 (가로 1.5배 넓게, 세로도 약간 두껍게)
        bar_w = e["radius"] * 3
        bar_h = 8
        bar_x = e["pos"][0] - (bar_w / 2) # 체력바가 적 머리 중앙에 오도록 정렬
        bar_y = e["pos"][1] - e["radius"] - 15
        
        # 배경 (빨간색 바)
        pygame.draw.rect(screen, HP_RED, (bar_x, bar_y, bar_w, bar_h))
        # 남은 체력 비율 계산 (초록색 바)
        hp_ratio = max(0, e["hp"] / e["max_hp"])
        pygame.draw.rect(screen, HP_GREEN, (bar_x, bar_y, int(bar_w * hp_ratio), bar_h))

    # 보상 단어 그리기
    if room["reward"]:
        rw_text = font.render(f"[{room['reward']['word']}]", True, (255, 255, 0))
        screen.blit(rw_text, (room["reward"]["pos"][0] - rw_text.get_width()//2, room["reward"]["pos"][1] - 15))

    # 플레이어 그리기 (무적 프레임 시각 효과 수정)
    if player_hp > 0:
        if player_immune_timer > 0:
            # 💡 무적 상태일 때는 연한 하늘색으로 고정하고 흰색 테두리 추가
            pygame.draw.circle(screen, PLAYER_IMMUNE, (int(player_pos[0]), int(player_pos[1])), player_radius)
            pygame.draw.circle(screen, WHITE, (int(player_pos[0]), int(player_pos[1])), player_radius + 2, 2)
        else:
            # 정상 상태일 때는 파란색
            pygame.draw.circle(screen, PLAYER_COLOR, (int(player_pos[0]), int(player_pos[1])), player_radius)

    # 부채꼴 공격 이펙트
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

    # 8. 미니맵 그리기
    MM_X, MM_Y, CELL, GAP = WIDTH - 100, 80, 15, 3
    for coords, info in world_map.items():
        if is_discovered(coords):
            draw_x = MM_X + (coords[0] - current_coords[0]) * (CELL + GAP) - CELL // 2
            draw_y = MM_Y + (coords[1] - current_coords[1]) * (CELL + GAP) - CELL // 2
            if coords == current_coords: color = MM_CURRENT
            elif info["type"] == "boss": color = MM_BOSS
            elif info["visited"]: color = MM_VISITED
            else: color = MM_DISCOVERED
            pygame.draw.rect(screen, color, (draw_x, draw_y, CELL, CELL))
            pygame.draw.rect(screen, WHITE, (draw_x, draw_y, CELL, CELL), 1)

    # 9. 상단 UI 그리기
    # 💡 [좌측 상단 플레이어 HP UI 크기 상향]
    pygame.draw.rect(screen, UI_BG, (15, 15, 260, 35)) # 가로 250, 세로 35으로 키움
    pygame.draw.rect(screen, WHITE, (15, 15, 260, 35), 2)
    # 더 큰 폰트 사용
    hp_font = pygame.font.SysFont(None, 35) # 새로운 폰트 크기 정의
    hp_text = hp_font.render(f"PLAYER HP: {player_hp}/{player_max_hp}", True, WHITE if player_hp > 25 else HP_RED)
    screen.blit(hp_text, (30, 25)) # 텍스트 위치 조정

    # [우측 상단 메시지 알림 UI]
    if message_timer > 0:
        msg_surf = font.render(message, True, (255, 230, 100))
        screen.blit(msg_surf, (WIDTH - msg_surf.get_width() - 20, 20))
        message_timer -= 1

    # 10. 하단 타이핑 UI 그리기
    ui_rect = pygame.Rect(0, HEIGHT - 100, WIDTH, 100)
    pygame.draw.rect(screen, UI_BG, ui_rect)
    pygame.draw.line(screen, WHITE, (0, HEIGHT - 100), (WIDTH, HEIGHT - 100), 2)
    
    words_surf = font.render(f"My Words: {', '.join(player_words)}", True, (150, 200, 255))
    screen.blit(words_surf, (20, HEIGHT - 85))
    
    pygame.draw.rect(screen, BLACK, (20, HEIGHT - 55, WIDTH - 40, 40))
    pygame.draw.rect(screen, WHITE, (20, HEIGHT - 55, WIDTH - 40, 40), 2)
    input_surf = big_font.render(input_text + "_", True, WHITE)
    screen.blit(input_surf, (30, HEIGHT - 48))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
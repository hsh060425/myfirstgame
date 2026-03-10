import pygame
import time
import random

# 초기화
pygame.init()

# 색상
white = (255, 255, 255)
black = (0, 0, 0)
blue = (50, 153, 213)     # P1
red = (213, 50, 80)       # P2
gray = (30, 30, 30)

# 먹이 설정
FOOD_TYPES = [
    {"color": (0, 255, 0), "growth": 1, "prob": 70},   # 초록: +1
    {"color": (255, 255, 0), "growth": 2, "prob": 20}, # 노랑: +2
    {"color": (160, 32, 240), "growth": 3, "prob": 10} # 보라: +3
]

# 화면 크기
dis_width = 800
dis_height = 600
dis = pygame.display.set_mode((dis_width, dis_height))
pygame.display.set_caption('2인용 스네이크 (충돌 해결 버전)')

clock = pygame.time.Clock()
snake_block = 20
snake_speed = 10  # 속도를 조금 낮춰 조작을 쉽게 함
MAX_FOOD_COUNT = 5

font_style = pygame.font.SysFont("malgungothic", 30)
score_font = pygame.font.SysFont("comicsansms", 25)

def show_score(p1_len, p2_len):
    val1 = score_font.render(f"P1: {p1_len-1}", True, blue)
    val2 = score_font.render(f"P2: {p2_len-1}", True, red)
    dis.blit(val1, [20, 10])
    dis.blit(val2, [dis_width - 150, 10])

def generate_food():
    """확률에 따라 먹이 생성 및 Rect 객체 반환"""
    pick = random.randint(1, 100)
    cumulative_prob = 0
    selected_type = FOOD_TYPES[0]
    
    for f_type in FOOD_TYPES:
        cumulative_prob += f_type["prob"]
        if pick <= cumulative_prob:
            selected_type = f_type
            break
            
    # 화면 안쪽으로 좌표 생성 (snake_block 단위로 정렬)
    fx = round(random.randrange(0, dis_width - snake_block) / 20.0) * 20.0
    fy = round(random.randrange(0, dis_height - snake_block) / 20.0) * 20.0
    
    # Pygame Rect 객체로 만들어 충돌 감지를 쉽게 함
    rect = pygame.Rect(fx, fy, snake_block, snake_block)
    return {"rect": rect, "type": selected_type}

def gameLoop():
    game_over = False
    game_close = False
    winner_msg = ""

    # 초기 위치 (정수로 강제 변환)
    p1_x, p1_y = 600, 300
    p1_x_change, p1_y_change = 0, 0
    p1_List, p1_length = [], 1

    p2_x, p2_y = 200, 300
    p2_x_change, p2_y_change = 0, 0
    p2_List, p2_length = [], 1

    foods = [generate_food() for _ in range(MAX_FOOD_COUNT)]

    while not game_over:
        while game_close:
            dis.fill(black)
            msg = font_style.render(f"{winner_msg}! C-다시 시작, Q-종료", True, white)
            dis.blit(msg, [dis_width/10, dis_height/3])
            show_score(p1_length, p2_length)
            pygame.display.update()
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q: game_over = True; game_close = False
                    if event.key == pygame.K_c: gameLoop()

        for event in pygame.event.get():
            if event.type == pygame.QUIT: game_over = True
            if event.type == pygame.KEYDOWN:
                # P1 조작
                if event.key == pygame.K_LEFT and p1_x_change == 0: p1_x_change = -snake_block; p1_y_change = 0
                elif event.key == pygame.K_RIGHT and p1_x_change == 0: p1_x_change = snake_block; p1_y_change = 0
                elif event.key == pygame.K_UP and p1_y_change == 0: p1_y_change = -snake_block; p1_x_change = 0
                elif event.key == pygame.K_DOWN and p1_y_change == 0: p1_y_change = snake_block; p1_x_change = 0
                # P2 조작
                if event.key == pygame.K_a and p2_x_change == 0: p2_x_change = -snake_block; p2_y_change = 0
                elif event.key == pygame.K_d and p2_x_change == 0: p2_x_change = snake_block; p2_y_change = 0
                elif event.key == pygame.K_w and p2_y_change == 0: p2_y_change = -snake_block; p2_x_change = 0
                elif event.key == pygame.K_s and p2_y_change == 0: p2_y_change = snake_block; p2_x_change = 0

        # 이동
        p1_x += p1_x_change
        p1_y += p1_y_change
        p2_x += p2_x_change
        p2_y += p2_y_change

        # 뱀 머리 Rect 생성 (충돌 판정용)
        p1_head_rect = pygame.Rect(p1_x, p1_y, snake_block, snake_block)
        p2_head_rect = pygame.Rect(p2_x, p2_y, snake_block, snake_block)

        # 벽 충돌 검사
        if p1_x < 0 or p1_x >= dis_width or p1_y < 0 or p1_y >= dis_height:
            winner_msg = "PLAYER 2 WIN (P1 Hit Wall)"; game_close = True
        if p2_x < 0 or p2_x >= dis_width or p2_y < 0 or p2_y >= dis_height:
            winner_msg = "PLAYER 1 WIN (P2 Hit Wall)"; game_close = True

        dis.fill(gray)
        
        # 먹이 그리기 및 충돌 검사
        for food in foods[:]:
            pygame.draw.rect(dis, food["type"]["color"], food["rect"])
            
            # P1이 먹이를 먹었는지 검사 (colliderect 사용)
            if p1_head_rect.colliderect(food["rect"]):
                p1_length += food["type"]["growth"]
                foods.remove(food)
                foods.append(generate_food())
            
            # P2가 먹이를 먹었는지 검사
            elif p2_head_rect.colliderect(food["rect"]):
                p2_length += food["type"]["growth"]
                foods.remove(food)
                foods.append(generate_food())

        # 뱀 몸통 리스트 업데이트
        p1_List.append([p1_x, p1_y])
        if len(p1_List) > p1_length: del p1_List[0]
        p2_List.append([p2_x, p2_y])
        if len(p2_List) > p2_length: del p2_List[0]

        # 몸통 충돌 검사
        for part in p1_List[:-1]:
            if part == [p1_x, p1_y]: winner_msg = "P2 WIN (P1 Hit Self)"; game_close = True
        for part in p2_List[:-1]:
            if part == [p2_x, p2_y]: winner_msg = "P1 WIN (P2 Hit Self)"; game_close = True
            
        # 상대방 몸에 부딪혔는지 검사
        for part in p1_List:
            if p2_head_rect.collidepoint(part[0], part[1]):
                if p2_x_change != 0 or p2_y_change != 0:
                    winner_msg = "P1 WIN (P2 Hit P1)"; game_close = True
        for part in p2_List:
            if p1_head_rect.collidepoint(part[0], part[1]):
                if p1_x_change != 0 or p1_y_change != 0:
                    winner_msg = "P2 WIN (P1 Hit P2)"; game_close = True

        # 그리기
        for part in p1_List:
            pygame.draw.rect(dis, blue, [part[0], part[1], snake_block, snake_block])
        for part in p2_List:
            pygame.draw.rect(dis, red, [part[0], part[1], snake_block, snake_block])
            
        show_score(p1_length, p2_length)
        pygame.display.update()
        clock.tick(snake_speed)

    pygame.quit()
    quit()

gameLoop()
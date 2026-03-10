import pygame
import time
import random

# 초기화
pygame.init()

# 색상 정의
white = (255, 255, 255)
yellow = (255, 255, 102)
black = (0, 0, 0)
red = (213, 50, 80)
green = (0, 255, 0)
blue = (50, 153, 213)

# 화면 크기 설정
dis_width = 800
dis_height = 600
dis = pygame.display.set_mode((dis_width, dis_height))
pygame.display.set_caption('파이썬 스네이크 게임')

clock = pygame.time.Clock()

snake_block = 20  # 뱀 한 칸의 크기
snake_speed = 10  # 뱀의 이동 속도
    
font_style = pygame.font.SysFont("malgungothic", 25)
score_font = pygame.font.SysFont("comicsansms", 35)

def our_snake(snake_block, snake_list):
    """뱀을 화면에 그리는 함수"""
    for x in snake_list:
        pygame.draw.rect(dis, black, [x[0], x[1], snake_block, snake_block])

def message(msg, color):
    """메시지를 화면에 출력하는 함수"""
    mesg = font_style.render(msg, True, color)
    dis.blit(mesg, [dis_width / 6, dis_height / 3])

def show_score(score):
    """점수를 화면에 표시하는 함수"""
    value = score_font.render("Score: " + str(score), True, yellow)
    dis.blit(value, [0, 0])

def gameLoop():
    game_over = False
    game_close = False

    # 뱀의 초기 위치
    x1 = dis_width / 2
    y1 = dis_height / 2

    # 이동 변화량
    x1_change = 0
    y1_change = 0

    # 뱀의 몸통 정보를 담을 리스트
    snake_List = []
    Length_of_snake = 1

    # 먹이의 위치 랜덤 생성
    foodx = round(random.randrange(0, dis_width - snake_block) / 20.0) * 20.0
    foody = round(random.randrange(0, dis_height - snake_block) / 20.0) * 20.0

    while not game_over:

        # 게임 종료 후 재시작/종료 선택 화면
        while game_close == True:
            dis.fill(blue)
            message("게임 오버! Q-종료 또는 C-다시 시작", red)
            show_score(Length_of_snake - 1)
            pygame.display.update()

            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        game_over = True
                        game_close = False
                    if event.key == pygame.K_c:
                        gameLoop()

        # 이벤트 처리 (키보드 입력)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game_over = True
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    x1_change = -snake_block
                    y1_change = 0
                elif event.key == pygame.K_RIGHT:
                    x1_change = snake_block
                    y1_change = 0
                elif event.key == pygame.K_UP:
                    y1_change = -snake_block
                    x1_change = 0
                elif event.key == pygame.K_DOWN:
                    y1_change = snake_block
                    x1_change = 0

        # 벽에 충돌했는지 검사
        if x1 >= dis_width or x1 < 0 or y1 >= dis_height or y1 < 0:
            game_close = True
        
        x1 += x1_change
        y1 += y1_change
        dis.fill(blue) # 배경색 그리기
        
        # 먹이 그리기
        pygame.draw.rect(dis, green, [foodx, foody, snake_block, snake_block])
        
        # 뱀 머리 이동 및 몸통 길이 관리
        snake_Head = []
        snake_Head.append(x1)
        snake_Head.append(y1)
        snake_List.append(snake_Head)
        
        if len(snake_List) > Length_of_snake:
            del snake_List[0]

        # 자기 몸에 부딪혔는지 검사
        for x in snake_List[:-1]:
            if x == snake_Head:
                game_close = True

        our_snake(snake_block, snake_List)
        show_score(Length_of_snake - 1)

        pygame.display.update()

        # 먹이를 먹었을 때 처리
        if x1 == foodx and y1 == foody:
            foodx = round(random.randrange(0, dis_width - snake_block) / 20.0) * 20.0
            foody = round(random.randrange(0, dis_height - snake_block) / 20.0) * 20.0
            Length_of_snake += 1

        clock.tick(snake_speed)

    pygame.quit()
    quit()

gameLoop()
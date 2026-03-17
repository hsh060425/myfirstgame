import pygame
import random

# 초기화
pygame.init()

# 화면 설정
WIDTH, HEIGHT = 900, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("모두의 마블 - 구매 & 통행료 시스템")

# 색상
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 100, 100)
BLUE = (100, 100, 255)
GRAY = (200, 200, 200)
YELLOW = (255, 255, 0)

# 폰트 (한글 폰트 설정 필요 - 없으면 기본 폰트)
font = pygame.font.SysFont("malgungothic", 18)
large_font = pygame.font.SysFont("malgungothic", 35)

# 게임 설정
TILE_SIZE = 90
BOARD_MARGIN = 50

# 게임 상태 관리
STATE_ROLL = "ROLL"
STATE_BUY_OR_NOT = "BUY_OR_NOT"
game_state = STATE_ROLL

class Tile:
    def __init__(self, name, price, x, y):
        self.name = name
        self.price = price
        self.rent = price // 2  # 통행료는 구매가의 50%로 설정
        self.rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
        self.owner = None

class Player:
    def __init__(self, name, color, id):
        self.name = name
        self.color = color
        self.id = id
        self.pos = 0
        self.money = 5000
        self.radius = 15

# 보드 생성 (16개 칸으로 축소하여 예시 작성)
tiles = []
# 하단
for i in range(5):
    tiles.append(Tile(f"땅 {i}", (i+1)*500, WIDTH - BOARD_MARGIN - (i+1)*TILE_SIZE, HEIGHT - BOARD_MARGIN - TILE_SIZE))
# 좌측
for i in range(4):
    tiles.append(Tile(f"땅 {i+5}", (i+6)*500, BOARD_MARGIN, HEIGHT - BOARD_MARGIN - (i+2)*TILE_SIZE))
# 상단
for i in range(5):
    tiles.append(Tile(f"땅 {i+9}", (i+10)*500, BOARD_MARGIN + i*TILE_SIZE, BOARD_MARGIN))
# 우측
for i in range(4):
    tiles.append(Tile(f"땅 {i+14}", (i+15)*500, WIDTH - BOARD_MARGIN - TILE_SIZE, BOARD_MARGIN + (i+1)*TILE_SIZE))

players = [Player("P1", RED, 0), Player("P2", BLUE, 1)]
current_turn = 0
dice_value = 0
msg = "Space를 눌러 주사위를 굴리세요"
current_land = None # 현재 도착한 땅

def draw_board():
    screen.fill(WHITE)
    
    # 칸 그리기
    for tile in tiles:
        # 땅 주인이 있으면 배경색 칠하기
        if tile.owner:
            pygame.draw.rect(screen, tile.owner.color, tile.rect)
        
        pygame.draw.rect(screen, BLACK, tile.rect, 2)
        
        # 정보 출력
        name_txt = font.render(tile.name, True, BLACK)
        price_txt = font.render(f"P:{tile.price}", True, BLACK)
        rent_txt = font.render(f"R:{tile.rent}", True, (50, 50, 50))
        
        screen.blit(name_txt, (tile.rect.x + 5, tile.rect.y + 5))
        screen.blit(price_txt, (tile.rect.x + 5, tile.rect.y + 30))
        screen.blit(rent_txt, (tile.rect.x + 5, tile.rect.y + 55))

    # 플레이어 그리기
    for i, p in enumerate(players):
        target_tile = tiles[p.pos]
        offset = i * 20
        pygame.draw.circle(screen, p.color, (target_tile.rect.centerx - 10 + offset, target_tile.rect.centery), p.radius)
        pygame.draw.circle(screen, BLACK, (target_tile.rect.centerx - 10 + offset, target_tile.rect.centery), p.radius, 2)

    # 중앙 정보창 UI
    info_rect = pygame.Rect(WIDTH//2 - 200, HEIGHT//2 - 100, 400, 200)
    pygame.draw.rect(screen, GRAY, info_rect)
    pygame.draw.rect(screen, BLACK, info_rect, 3)

    msg_surface = font.render(msg, True, BLACK)
    screen.blit(msg_surface, (info_rect.x + 20, info_rect.y + 20))

    # 구매 UI (상태가 BUY_OR_NOT일 때만 표시)
    if game_state == STATE_BUY_OR_NOT:
        buy_msg = large_font.render(f"구매하시겠습니까? (Y/N)", True, BLACK)
        price_msg = font.render(f"가격: {current_land.price} | 내 잔액: {players[current_turn].money}", True, BLACK)
        screen.blit(buy_msg, (info_rect.x + 50, info_rect.y + 80))
        screen.blit(price_msg, (info_rect.x + 80, info_rect.y + 140))

    # 플레이어 상태 바
    for i, p in enumerate(players):
        color = p.color
        p_txt = large_font.render(f"{p.name} Money: {p.money}", True, color)
        screen.blit(p_txt, (WIDTH//2 - 100, 200 + i*50))

# 메인 루프
running = True
while running:
    p = players[current_turn]
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        if event.type == pygame.KEYDOWN:
            # 1. 주사위 굴리기 단계
            if game_state == STATE_ROLL:
                if event.key == pygame.K_SPACE:
                    dice_value = random.randint(1, 6)
                    p.pos = (p.pos + dice_value) % len(tiles)
                    current_land = tiles[p.pos]
                    msg = f"{p.name}이(가) {dice_value}칸 이동하여 {current_land.name} 도착!"

                    # 주인 없는 땅 도착
                    if current_land.owner is None:
                        game_state = STATE_BUY_OR_NOT
                    # 남의 땅 도착
                    elif current_land.owner != p:
                        toll = current_land.rent
                        p.money -= toll
                        current_land.owner.money += toll
                        msg = f"{current_land.owner.name}에게 통행료 {toll} 지불!"
                        current_turn = (current_turn + 1) % len(players)
                    # 내 땅 도착
                    else:
                        msg = "자신의 땅에 도착했습니다."
                        current_turn = (current_turn + 1) % len(players)

            # 2. 구매 결정 단계
            elif game_state == STATE_BUY_OR_NOT:
                if event.key == pygame.K_y:
                    if p.money >= current_land.price:
                        p.money -= current_land.price
                        current_land.owner = p
                        msg = f"{current_land.name} 구매 완료!"
                    else:
                        msg = "잔액이 부족합니다!"
                    game_state = STATE_ROLL
                    current_turn = (current_turn + 1) % len(players)
                
                if event.key == pygame.K_n:
                    msg = "구매를 취소했습니다."
                    game_state = STATE_ROLL
                    current_turn = (current_turn + 1) % len(players)

    draw_board()
    pygame.display.flip()

pygame.quit()
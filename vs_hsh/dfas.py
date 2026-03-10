import pygame
import sys

# 1. 초기화
pygame.init()

# 화면 설정
WIDTH, HEIGHT = 600, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("클릭커 게임 - 업그레이드 메뉴 버전")

# 색상 정의
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GOLD = (255, 215, 0)
SKYBLUE = (135, 206, 235)
GRAY = (200, 200, 200)
DARK_GRAY = (50, 50, 50, 150) # 반투명 배경용
RED = (200, 50, 50)

# 폰트
font_large = pygame.font.SysFont("malgungothic", 50)
font_small = pygame.font.SysFont("malgungothic", 20)
font_mid = pygame.font.SysFont("malgungothic", 30)

# 게임 변수
score = 0
click_power = 1
upgrade_cost = 10
auto_clickers = 0
auto_cost = 50
show_upgrade_menu = False  # 업그레이드 창이 열려있는지 확인하는 변수

# 버튼 영역 설정
click_button_rect = pygame.Rect(WIDTH//2 - 100, HEIGHT//2 - 100, 200, 200)
open_shop_rect = pygame.Rect(WIDTH//2 - 80, 550, 160, 60) # 상점 열기 버튼
close_shop_rect = pygame.Rect(430, 160, 40, 40) # 상점 닫기 (X) 버튼

# 메뉴 안의 업그레이드 버튼들
upgrade_rect = pygame.Rect(150, 250, 300, 80)
auto_rect = pygame.Rect(150, 350, 300, 80)
a_rect = pygame.Rect(150, 450, 300, 80)
b_rect = pygame.Rect(150, 550, 300, 80)

# 타이머 설정
AUTO_CLICK_EVENT = pygame.USEREVENT + 1
pygame.time.set_timer(AUTO_CLICK_EVENT, 1000)

running = True
clock = pygame.time.Clock()

while running:
    screen.fill(WHITE)
    mouse_pos = pygame.mouse.get_pos()

    # --- 이벤트 처리 ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            pygame.quit()
            sys.exit()

        if event.type == pygame.MOUSEBUTTONDOWN:
            # 1. 업그레이드 메뉴가 닫혀 있을 때
            if not show_upgrade_menu:
                if click_button_rect.collidepoint(mouse_pos):
                    score += click_power
                elif open_shop_rect.collidepoint(mouse_pos):
                    show_upgrade_menu = True
            
            # 2. 업그레이드 메뉴가 열려 있을 때
            else:
                if close_shop_rect.collidepoint(mouse_pos):
                    show_upgrade_menu = False
                elif upgrade_rect.collidepoint(mouse_pos):
                    if score >= upgrade_cost:
                        score -= upgrade_cost
                        click_power += 1
                        upgrade_cost = int(upgrade_cost * 1.5)
                elif auto_rect.collidepoint(mouse_pos):
                    if score >= auto_cost:
                        score -= auto_cost
                        auto_clickers += 1
                        auto_cost = int(auto_cost * 1.8)

        if event.type == AUTO_CLICK_EVENT:
            score += auto_clickers

    # --- 메인 화면 그리기 ---
    # 점수 표시
    score_text = font_large.render(f"Score: {score}", True, BLACK)
    screen.blit(score_text, (WIDTH//2 - score_text.get_width()//2, 80))

    # 메인 클릭 버튼
    pygame.draw.circle(screen, GOLD, (WIDTH//2, HEIGHT//2), 100)
    screen.blit(font_mid.render("CLICK!", True, BLACK), (WIDTH//2-45, HEIGHT//2-15))

    # 상점 열기 버튼
    pygame.draw.rect(screen, SKYBLUE, open_shop_rect, border_radius=10)
    screen.blit(font_mid.render("상점 열기", True, BLACK), (open_shop_rect.x + 25, open_shop_rect.y + 12))

    # 현재 능력치 표시
    info_text = font_small.render(f"클릭 파워: {click_power} | 초당 자동 획득: {auto_clickers}", True, BLACK)
    screen.blit(info_text, (WIDTH//2 - info_text.get_width()//2, 630))


    # --- 업그레이드 UI 창 (팝업) ---
    if show_upgrade_menu:
        # 1. 배경 흐리게 (반투명 오버레이)
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150)) # 검정색에 투명도 150
        screen.blit(overlay, (0, 0))

        # 2. 메뉴 박스
        menu_rect = pygame.Rect(100, 150, 400, 400)
        pygame.draw.rect(screen, WHITE, menu_rect, border_radius=20)
        pygame.draw.rect(screen, BLACK, menu_rect, 3, border_radius=20) # 테두리

        # 3. 닫기 버튼 (X)
        pygame.draw.rect(screen, RED, close_shop_rect, border_radius=5)
        screen.blit(font_small.render("X", True, WHITE), (442, 168))

        # 4. 메뉴 제목
        title_text = font_mid.render("업그레이드 상점", True, BLACK)
        screen.blit(title_text, (WIDTH//2 - title_text.get_width()//2, 180))

        # 5. 업그레이드 버튼 1 (클릭 강화)
        pygame.draw.rect(screen, GRAY, upgrade_rect, border_radius=10)
        u1_txt = font_small.render(f"클릭 강화 (비용: {upgrade_cost})", True, BLACK)
        screen.blit(u1_txt, (upgrade_rect.x + 20, upgrade_rect.y + 25))

        # 6. 업그레이드 버튼 2 (오토 클릭)
        pygame.draw.rect(screen, GRAY, auto_rect, border_radius=10)
        u2_txt = font_small.render(f"오토 클릭커 (비용: {auto_cost})", True, BLACK)
        screen.blit(u2_txt, (auto_rect.x + 20, auto_rect.y + 25))

        # test
        pygame.draw.rect(screen, GRAY, a_rect, border_radius=10)
        u2_txt = font_small.render(f"오토 클릭커 (비용: {auto_cost})", True, BLACK)
        screen.blit(u2_txt, (auto_rect.x + 20, auto_rect.y + 25))
        # test
        pygame.draw.rect(screen, GRAY, b_rect, border_radius=10)
        u2_txt = font_small.render(f"오토 클릭커 (비용: {auto_cost})", True, BLACK)
        screen.blit(u2_txt, (auto_rect.x + 20, auto_rect.y + 25))

    pygame.display.flip()
    clock.tick(60)
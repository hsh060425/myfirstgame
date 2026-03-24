import pygame
import sys

# 1. 초기화 및 창 설정
pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pygame AABB 시각화")

# 색상 정의
WHITE = (255, 255, 255)
GRAY = (150, 150, 150)
RED = (255, 0, 0)
BLACK = (0, 0, 0)

# 2. 오브젝트 설정
# 이동하는 사각형 (x, y, width, height)
player_rect = pygame.Rect(100, 100, 80, 60)
player_speed = 5

# 중앙 고정 사각형
fixed_rect = pygame.Rect(0, 0, 120, 100)
fixed_rect.center = (WIDTH // 2, HEIGHT // 2)

# 프레임 조절을 위한 시계
clock = pygame.time.Clock()

def main():
    while True:
        # 이벤트 처리
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        # 3. 방향키 입력 처리 (이동)
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            player_rect.x -= player_speed
        if keys[pygame.K_RIGHT]:
            player_rect.x += player_speed
        if keys[pygame.K_UP]:
            player_rect.y -= player_speed
        if keys[pygame.K_DOWN]:
            player_rect.y += player_speed

        # 화면 그리기
        screen.fill(WHITE) # 배경은 흰색

        # 2 & 4. 오브젝트 및 AABB 그리기
        # (먼저 회색 면을 채우고, 그 위에 빨간색 테두리(AABB)를 그림)
        
        # 고정 사각형 그리기
        pygame.draw.rect(screen, GRAY, fixed_rect) # 회색 채우기
        pygame.draw.rect(screen, RED, fixed_rect, 2) # 빨간색 AABB 테두리 (두께 2)

        # 조종 사각형 그리기
        pygame.draw.rect(screen, GRAY, player_rect) # 회색 채우기
        pygame.draw.rect(screen, RED, player_rect, 2) # 빨간색 AABB 테두리 (두께 2)

        # 간단한 충돌 감지 시각화 (보너스: 충돌 시 텍스트 표시)
        if player_rect.colliderect(fixed_rect):
            font = pygame.font.SysFont(None, 40)
            text = font.render("COLLISION!", True, BLACK)
            screen.blit(text, (20, 20))

        # 화면 업데이트
        pygame.display.flip()

        # 초당 60프레임 제한
        clock.tick(60)

if __name__ == "__main__":
    main()
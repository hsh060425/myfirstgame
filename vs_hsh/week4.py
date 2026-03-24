import pygame
import sys

# 1. 초기화 및 창 설정
pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pygame Physics: Target Bouncing")

# 색상 정의
WHITE = (255, 255, 255)
GRAY = (150, 150, 150)
RED = (255, 0, 0)      # AABB 테두리
BLUE = (0, 0, 255)     # 원형 바운딩 박스
YELLOW = (255, 255, 0) # 충돌 시 배경색
BLACK = (0, 0, 0)

# 2. 오브젝트 초기 설정
# 플레이어 (조종 가능)
player_rect = pygame.Rect(100, 100, 80, 80)
player_speed = 6

# 타겟 (중앙 오브젝트)
target_rect = pygame.Rect(0, 0, 100, 100)
target_rect.center = (WIDTH // 2, HEIGHT // 2)

def main():
    # --- 물리 및 상태 변수 (함수 내부에 선언하여 에러 방지) ---
    target_vel = pygame.Vector2(0, 0)  # 타겟의 속도 벡터
    friction = 0.96                    # 마찰력 (매 프레임 속도 감소율)
    bounce_intensity = 1.5             # 충돌 시 튕겨나가는 강도
    clock = pygame.time.Clock()

    while True:
        # 이벤트 처리
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        # 3. 플레이어 이동 처리 (방향키)
        keys = pygame.key.get_pressed()
        move_vec = pygame.Vector2(0, 0)
        if keys[pygame.K_LEFT]:  move_vec.x = -player_speed
        if keys[pygame.K_RIGHT]: move_vec.x = player_speed
        if keys[pygame.K_UP]:    move_vec.y = -player_speed
        if keys[pygame.K_DOWN]:  move_vec.y = player_speed

        player_rect.x += move_vec.x
        player_rect.y += move_vec.y

        # --- 원형 충돌 및 튕기기 로직 ---
        p_center = pygame.Vector2(player_rect.center)
        t_center = pygame.Vector2(target_rect.center)
        
        p_radius = player_rect.width // 2
        t_radius = target_rect.width // 2
        
        # 두 중심 사이의 거리 계산
        distance = p_center.distance_to(t_center)
        min_dist = p_radius + t_radius

        is_colliding = False
        if distance < min_dist:
            is_colliding = True
            
            # 충돌 방향 벡터 (플레이어 -> 타겟)
            if distance > 0:
                push_dir = (t_center - p_center).normalize()
            else:
                push_dir = pygame.Vector2(1, 0)

            # 1. 겹침 해결: 타겟을 즉시 바깥으로 밀어내기
            overlap = min_dist - distance
            target_rect.x += push_dir.x * overlap
            target_rect.y += push_dir.y * overlap

            # 2. 속도 부여: 타겟이 튕겨나감
            target_vel = push_dir * (player_speed * bounce_intensity)

        # 4. 타겟 물리 업데이트 (관성 및 마찰)
        target_rect.x += target_vel.x
        target_rect.y += target_vel.y
        target_vel *= friction  # 감속

        # 타겟이 벽에 부딪히면 튕기기
        if target_rect.left < 0 or target_rect.right > WIDTH:
            target_vel.x *= -1
        if target_rect.top < 0 or target_rect.bottom > HEIGHT:
            target_vel.y *= -1

        # 5. 화면 그리기
        # 충돌 시 배경 노란색
        screen.fill(YELLOW if is_colliding else WHITE)

        # 타겟 그리기 (회색 면 + 빨간 AABB + 파란 원)
        pygame.draw.rect(screen, GRAY, target_rect)                  # 본체
        pygame.draw.rect(screen, RED, target_rect, 2)               # AABB
        pygame.draw.circle(screen, BLUE, target_rect.center, t_radius, 2) # 원형 박스

        # 플레이어 그리기 (회색 면 + 빨간 AABB + 파란 원)
        pygame.draw.rect(screen, GRAY, player_rect)                 # 본체
        pygame.draw.rect(screen, RED, player_rect, 2)              # AABB
        pygame.draw.circle(screen, BLUE, player_rect.center, p_radius, 2) # 원형 박스

        # 안내 텍스트
        font = pygame.font.SysFont("malgungothic", 25) # 한글 지원 폰트가 없을 수 있어 기본 폰트 사용
        msg = "COLLISION!" if is_colliding else "Hit the Target!"
        text = font.render(msg, True, BLACK)
        screen.blit(text, (20, 20))

        # 화면 업데이트
        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()
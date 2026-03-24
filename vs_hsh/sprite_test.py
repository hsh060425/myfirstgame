import pygame
from sprite import load_sprite

# --- 초기화 ---
pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("충돌 감지 테스트 (마우스로 움직여보세요)")
clock = pygame.time.Clock()
# 한글 폰트 설정 (시스템에 따라 폰트명이 다를 수 있음)
try:
    font = pygame.font.SysFont("malgungothic", 20)
    big_font = pygame.font.SysFont("malgungothic", 40)
except:
    font = pygame.font.SysFont("arial", 20)
    big_font = pygame.font.SysFont("arial", 40)

class Entity(pygame.sprite.Sprite):
    def __init__(self, name, pos, size=None):
        super().__init__()
        self.name = name
        self.image = load_sprite(name, size)
        self.rect = self.image.get_rect(center=pos)
        self.mask = pygame.mask.from_surface(self.image)
        
        # 충돌 상태 변수
        self.is_rect_hit = False  # 사각형 영역이 닿았는가?
        self.is_mask_hit = False  # 실제 픽셀이 닿았는가?

    def draw_debug(self, surface):
        # 1. 이미지 그리기
        surface.blit(self.image, self.rect)
        
        # 2. 사각형(Rect) 콜리전 표시 (사각형이 닿으면 노란색, 아니면 녹색)
        rect_color = (255, 255, 0) if self.is_rect_hit else (0, 255, 0)
        pygame.draw.rect(surface, rect_color, self.rect, 1)
        
        # 3. 픽셀(Mask) 콜리전 표시 (픽셀이 닿으면 빨간색, 아니면 어두운 빨간색)
        mask_color = (255, 0, 0) if self.is_mask_hit else (100, 0, 0)
        outline_points = self.mask.outline()
        if len(outline_points) > 1:
            real_points = [(p[0] + self.rect.x, p[1] + self.rect.y) for p in outline_points]
            pygame.draw.lines(surface, mask_color, True, real_points, 2)

# --- 객체 생성 ---
# 장애물들
obstacles = [
    Entity("rocket", (150, 300), (80, 220)),
    Entity("stone", (350, 300)),
    Entity("sword", (550, 300), (120, 120))
]

# 플레이어 (모험가)
player = Entity("adventurer", (700, 100))

running = True
while running:
    screen.fill((30, 30, 30))
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # 1. 플레이어 위치 업데이트 (마우스 위치)
    player.rect.center = pygame.mouse.get_pos()
    
    # 2. 충돌 상태 초기화
    player.is_rect_hit = False
    player.is_mask_hit = False
    for obs in obstacles:
        obs.is_rect_hit = False
        obs.is_mask_hit = False

    # 3. 모든 장애물과 충돌 체크
    for obs in obstacles:
        # (A) 사각형 충돌 체크 (Rect)
        if player.rect.colliderect(obs.rect):
            player.is_rect_hit = True
            obs.is_rect_hit = True
            
            # (B) 사각형이 닿았다면, 더 정밀한 픽셀 충돌 체크 (Mask)
            # 두 객체의 상대적인 거리(offset)를 계산하여 겹치는지 확인
            offset = (obs.rect.x - player.rect.x, obs.rect.y - player.rect.y)
            if player.mask.overlap(obs.mask, offset):
                player.is_mask_hit = True
                obs.is_mask_hit = True

    # 4. 그리기
    for obs in obstacles:
        obs.draw_debug(screen)
    player.draw_debug(screen)

    # 5. 화면 하단에 텍스트 알림 표시
    if player.is_mask_hit:
        msg = big_font.render("!! 픽셀 충돌 발생 (진짜 닿음) !!", True, (255, 0, 0))
        screen.blit(msg, (screen.get_width()//2 - msg.get_width()//2, 500))
    elif player.is_rect_hit:
        msg = font.render("사각형 영역만 닿음 (투명한 곳)", True, (255, 255, 0))
        screen.blit(msg, (screen.get_width()//2 - msg.get_width()//2, 520))

    # 가이드 텍스트
    txt1 = font.render("녹색/황색 선: 사각형 범위 (Rect)", True, (200, 200, 200))
    txt2 = font.render("빨간색 선: 실제 픽셀 범위 (Mask)", True, (200, 200, 200))
    screen.blit(txt1, (20, 20))
    screen.blit(txt2, (20, 45))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
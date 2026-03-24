import pygame
from sprite import load_sprite

# --- 초기화 ---
pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("동일 색상 영역간 충돌 시스템 (Z: 회전 토글)")
clock = pygame.time.Clock()

try:
    font = pygame.font.SysFont("malgungothic", 20)
    big_font = pygame.font.SysFont("malgungothic", 28)
except:
    font = pygame.font.SysFont("arial", 20)
    big_font = pygame.font.SysFont("arial", 28)

class Entity(pygame.sprite.Sprite):
    def __init__(self, name, pos, size=None):
        super().__init__()
        self.name = name
        self.original_image = load_sprite(name, size)
        self.image = self.original_image.copy()
        self.rect = self.image.get_rect(center=pos)
        
        # [빨간색 영역용] 실제 이미지 픽셀 마스크
        self.mask = pygame.mask.from_surface(self.image)
        
        # [초록색 영역용] OBB(사각형 전체) 마스크 생성
        self.obb_surface = pygame.Surface(self.original_image.get_size(), pygame.SRCALPHA)
        self.obb_surface.fill((255, 255, 255)) 
        self.obb_mask = pygame.mask.from_surface(self.obb_surface)
        
        self.pos = pygame.Vector2(pos)
        self.angle = 0
        self.hit_level = 0 # 0:안전, 1:노랑접촉, 2:초록접촉, 3:빨간접촉

    def update_transform(self, pos, angle_inc=0):
        """위치와 회전 각도를 업데이트하고 마스크들을 재생성합니다."""
        self.pos = pygame.Vector2(pos)
        self.angle += angle_inc
        
        # 이미지 및 빨간색 마스크 업데이트
        self.image = pygame.transform.rotate(self.original_image, self.angle)
        self.rect = self.image.get_rect(center=self.pos)
        self.mask = pygame.mask.from_surface(self.image)
        
        # 초록색(OBB) 마스크 업데이트
        rotated_obb_surf = pygame.transform.rotate(self.obb_surface, self.angle)
        self.obb_mask = pygame.mask.from_surface(rotated_obb_surf)

    def draw_debug(self, surface):
        surface.blit(self.image, self.rect)
        
        # 1. 노란색 선 (AABB)
        aabb_color = (255, 255, 0) if self.hit_level >= 1 else (60, 60, 60)
        pygame.draw.rect(surface, aabb_color, self.rect, 1)

        # 2. 초록색 선 (OBB)
        self.draw_obb_lines(surface)
        
        # 3. 빨간색 선 (Pixel Mask)
        mask_color = (255, 0, 0) if self.hit_level >= 3 else (80, 0, 0)
        outline = self.mask.outline()
        if len(outline) > 1:
            points = [(p[0] + self.rect.x, p[1] + self.rect.y) for p in outline]
            pygame.draw.lines(surface, mask_color, True, points, 1)

    def draw_obb_lines(self, surface):
        w, h = self.original_image.get_size()
        pts = [pygame.Vector2(-w/2, -h/2), pygame.Vector2(w/2, -h/2),
               pygame.Vector2(w/2, h/2), pygame.Vector2(-w/2, h/2)]
        rotated_pts = [p.rotate(-self.angle) + self.pos for p in pts]
        color = (0, 255, 0) if self.hit_level >= 2 else (0, 100, 0)
        pygame.draw.lines(surface, color, True, rotated_pts, 2)

# --- 객체 생성 ---
obstacles = [
    Entity("rocket", (200, 300), (60, 160)),
    Entity("stone", (400, 300)),
    Entity("sword", (600, 300), (100, 100))
]
# 플레이어도 OBB와 마스크를 가짐
player = Entity("adventurer", (700, 100))

is_rotating = True
running = True

while running:
    screen.fill((15, 15, 15))
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_z:
            is_rotating = not is_rotating

    # 1. 업데이트 (플레이어는 회전X, 장애물은 토글에 따라 회전)
    player.update_transform(pygame.mouse.get_pos(), 0)
    for obs in obstacles:
        obs.update_transform(obs.pos, 1.2 if is_rotating else 0)

    # 2. 같은 색상끼리 충돌 체크
    player.hit_level = 0
    for obs in obstacles:
        obs.hit_level = 0
        level = 0
        
        # [노란색 끼리] AABB vs AABB
        if player.rect.colliderect(obs.rect):
            level = 1
            
            # 상대적 좌표 계산
            offset = (obs.rect.x - player.rect.x, obs.rect.y - player.rect.y)
            
            # [초록색 끼리] OBB 마스크 vs OBB 마스크
            if player.obb_mask.overlap(obs.obb_mask, offset):
                level = 2
                
                # [빨간색 끼리] 실제 픽셀 마스크 vs 실제 픽셀 마스크
                if player.mask.overlap(obs.mask, offset):
                    level = 3
        
        obs.hit_level = level
        if level > player.hit_level:
            player.hit_level = level

    # 3. 그리기
    for obs in obstacles:
        obs.draw_debug(screen)
    player.draw_debug(screen)

    # 4. 상태 메시지 (같은 색끼리 닿았을 때 알림)
    if player.hit_level == 1:
        msg = big_font.render("● [노란색 영역] 끼리 닿음 (근접)", True, (255, 255, 0))
    elif player.hit_level == 2:
        msg = big_font.render("● [초록색 영역] 끼리 닿음 (충돌 예정)", True, (0, 255, 0))
    elif player.hit_level == 3:
        msg = big_font.render("● [빨간색 픽셀] 끼리 닿음 (충돌 발생!)", True, (255, 0, 0))
    else:
        msg = big_font.render("안전함 (서로 닿지 않음)", True, (150, 150, 150))
    
    screen.blit(msg, (screen.get_width()//2 - msg.get_width()//2, 530))
    
    # 가이드
    screen.blit(font.render(f"Z: Toggle Rotation ({'ON' if is_rotating else 'OFF'})", True, (255,255,255)), (20, 20))
    screen.blit(font.render("Yellow + Yellow = AABB Step", True, (255, 255, 0)), (20, 45))
    screen.blit(font.render("Green + Green = OBB Step", True, (0, 255, 0)), (20, 70))
    screen.blit(font.render("Red + Red = Pixel Step", True, (255, 0, 0)), (20, 95))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
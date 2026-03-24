import pygame
from sprite import load_sprite

# --- 초기화 ---
pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("색상별 단계적 충돌 시스템")
clock = pygame.time.Clock()

try:
    font = pygame.font.SysFont("malgungothic", 20)
    big_font = pygame.font.SysFont("malgungothic", 30)
except:
    font = pygame.font.SysFont("arial", 20)
    big_font = pygame.font.SysFont("arial", 30)

class Entity(pygame.sprite.Sprite):
    def __init__(self, name, pos, size=None):
        super().__init__()
        self.name = name
        self.original_image = load_sprite(name, size)
        self.image = self.original_image.copy()
        self.rect = self.image.get_rect(center=pos)
        
        # [1단계 마스크] 실제 이미지 (빨간색)
        self.mask = pygame.mask.from_surface(self.image)
        
        # [2단계 마스크] OBB 영역 (초록색 상자 전체를 채운 마스크)
        self.obb_surface = pygame.Surface(self.original_image.get_size(), pygame.SRCALPHA)
        self.obb_surface.fill((255, 255, 255)) 
        self.obb_mask = pygame.mask.from_surface(self.obb_surface)
        
        self.pos = pygame.Vector2(pos)
        self.angle = 0
        
        # 상태 플래그
        self.hit_level = 0 # 0: 없음, 1: AABB(노란), 2: OBB(초록), 3: Pixel(빨간)

    def update_rotation(self, speed):
        self.angle += speed
        self.image = pygame.transform.rotate(self.original_image, self.angle)
        self.rect = self.image.get_rect(center=self.pos)
        self.mask = pygame.mask.from_surface(self.image)
        
        # OBB용 마스크도 동일하게 회전 업데이트
        rotated_obb_surf = pygame.transform.rotate(self.obb_surface, self.angle)
        self.obb_mask = pygame.mask.from_surface(rotated_obb_surf)

    def draw_debug(self, surface):
        surface.blit(self.image, self.rect)
        
        # 1단계: AABB (노란색 상자) - 가장 바깥쪽 사각형
        aabb_color = (255, 255, 0) if self.hit_level >= 1 else (60, 60, 60)
        pygame.draw.rect(surface, aabb_color, self.rect, 1)

        # 2단계: OBB (초록색 선) - 회전하는 사각형
        self.draw_obb_lines(surface)
        
        # 3단계: Pixel Mask (빨간색 선) - 실제 이미지 외곽선
        mask_color = (255, 0, 0) if self.hit_level >= 3 else (80, 0, 0)
        outline_points = self.mask.outline()
        if len(outline_points) > 1:
            real_points = [(p[0] + self.rect.x, p[1] + self.rect.y) for p in outline_points]
            pygame.draw.lines(surface, mask_color, True, real_points, 1)

    def draw_obb_lines(self, surface):
        w, h = self.original_image.get_size()
        pts = [pygame.Vector2(-w/2, -h/2), pygame.Vector2(w/2, -h/2),
               pygame.Vector2(w/2, h/2), pygame.Vector2(-w/2, h/2)]
        rotated_pts = [p.rotate(-self.angle) + self.pos for p in pts]
        
        obb_color = (0, 255, 0) if self.hit_level >= 2 else (0, 100, 0)
        pygame.draw.lines(surface, obb_color, True, rotated_pts, 2)

# --- 객체 생성 ---
obstacles = [
    Entity("rocket", (200, 300), (60, 160)),
    Entity("stone", (400, 300)),
    Entity("sword", (600, 300), (100, 100))
]
player = Entity("adventurer", (700, 100))

is_rotating = True
running = True

while running:
    screen.fill((20, 20, 20))
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_z:
            is_rotating = not is_rotating

    # 1. 위치 및 회전 업데이트
    player.rect.center = pygame.mouse.get_pos()
    player.pos = pygame.Vector2(player.rect.center)
    if is_rotating:
        for obs in obstacles:
            obs.update_rotation(1.2)

    # 2. 단계별 충돌 체크 로직
    player.hit_level = 0
    for obs in obstacles:
        obs.hit_level = 0
        
        # [Step 1] 노란색 영역 (AABB) 체크
        if player.rect.colliderect(obs.rect):
            current_hit = 1
            
            # [Step 2] 초록색 영역 (OBB) 체크
            offset = (obs.rect.x - player.rect.x, obs.rect.y - player.rect.y)
            if player.mask.overlap(obs.obb_mask, offset):
                current_hit = 2
                
                # [Step 3] 빨간색 영역 (Pixel) 체크
                if player.mask.overlap(obs.mask, offset):
                    current_hit = 3
            
            obs.hit_level = current_hit
            if current_hit > player.hit_level:
                player.hit_level = current_hit

    # 3. 그리기
    for obs in obstacles:
        obs.draw_debug(screen)
    player.draw_debug(screen)

    # 4. 상태 메시지 출력 (색상별 단계 알림)
    if player.hit_level == 1:
        msg = big_font.render("상태: [주의] 주변 영역 진입 (AABB)", True, (255, 255, 0))
    elif player.hit_level == 2:
        msg = big_font.render("상태: [경고] 충돌 예정 (OBB)", True, (0, 255, 0))
    elif player.hit_level == 3:
        msg = big_font.render("상태: [위험] 충돌 발생 (PIXEL HIT)", True, (255, 0, 0))
    else:
        msg = big_font.render("상태: 안전 (Safe)", True, (200, 200, 200))
    
    screen.blit(msg, (screen.get_width()//2 - msg.get_width()//2, 520))
    
    # 조작 가이드
    screen.blit(font.render("Z: Toggle Rotation", True, (255, 255, 255)), (20, 20))
    screen.blit(font.render("Yellow: AABB Area", True, (255, 255, 0)), (20, 45))
    screen.blit(font.render("Green: OBB Area", True, (0, 255, 0)), (20, 70))
    screen.blit(font.render("Red: Actual Pixel", True, (255, 0, 0)), (20, 95))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
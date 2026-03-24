import pygame
from sprite import load_sprite

# --- 초기화 ---
pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("회전 토글 및 OBB 테스트 (Z: 정지/시작)")
clock = pygame.time.Clock()

try:
    font = pygame.font.SysFont("malgungothic", 20)
    big_font = pygame.font.SysFont("malgungothic", 35)
except:
    font = pygame.font.SysFont("arial", 20)
    big_font = pygame.font.SysFont("arial", 35)

class Entity(pygame.sprite.Sprite):
    def __init__(self, name, pos, size=None):
        super().__init__()
        self.name = name
        self.original_image = load_sprite(name, size)
        self.image = self.original_image.copy()
        self.rect = self.image.get_rect(center=pos)
        self.mask = pygame.mask.from_surface(self.image)
        
        self.pos = pygame.Vector2(pos)
        self.angle = 0
        self.is_rect_hit = False
        self.is_mask_hit = False

    def update_rotation(self, speed):
        """이미지를 회전시키고 마스크와 사각형을 업데이트"""
        self.angle += speed
        self.image = pygame.transform.rotate(self.original_image, self.angle)
        self.rect = self.image.get_rect(center=self.pos)
        self.mask = pygame.mask.from_surface(self.image)

    def draw_debug(self, surface):
        surface.blit(self.image, self.rect)
        
        # 1. AABB 표시 (기울어지지 않은 사각형)
        aabb_color = (255, 255, 0) if self.is_rect_hit else (80, 80, 80)
        pygame.draw.rect(surface, aabb_color, self.rect, 1)

        # 2. OBB 표시 (물체와 함께 회전하는 초록색 사각형)
        self.draw_obb(surface)
        
        # 3. 마스크(픽셀) 표시 (빨간색)
        mask_color = (255, 0, 0) if self.is_mask_hit else (100, 0, 0)
        outline_points = self.mask.outline()
        if len(outline_points) > 1:
            real_points = [(p[0] + self.rect.x, p[1] + self.rect.y) for p in outline_points]
            pygame.draw.lines(surface, mask_color, True, real_points, 2)

    def draw_obb(self, surface):
        """회전된 네 꼭짓점을 계산하여 초록색 OBB 그리기"""
        w, h = self.original_image.get_size()
        pts = [pygame.Vector2(-w/2, -h/2), pygame.Vector2(w/2, -h/2),
               pygame.Vector2(w/2, h/2), pygame.Vector2(-w/2, h/2)]
        
        rotated_pts = [p.rotate(-self.angle) + self.pos for p in pts]
        color = (0, 255, 0) if self.is_rect_hit else (0, 150, 0)
        pygame.draw.lines(surface, color, True, rotated_pts, 2)

# --- 객체 생성 ---
obstacles = [
    Entity("rocket", (200, 300), (60, 160)),
    Entity("stone", (400, 300)),
    Entity("sword", (600, 300), (100, 100))
]
player = Entity("adventurer", (700, 100))

# --- 상태 변수 ---
is_rotating = True  # 회전 여부를 결정하는 토글 변수
running = True

while running:
    screen.fill((20, 20, 20))
    
    # 이벤트 처리
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        # Z 키를 누를 때마다 회전 상태를 반전(토글) 시킵니다.
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_z:
                is_rotating = not is_rotating

    # 1. 업데이트
    player.rect.center = pygame.mouse.get_pos()
    player.pos = pygame.Vector2(player.rect.center)
    
    # 토글 상태가 True일 때만 회전 업데이트를 수행합니다.
    if is_rotating:
        for obs in obstacles:
            obs.update_rotation(1.5) # 회전 속도

    # 2. 충돌 체크 초기화 및 수행
    player.is_rect_hit = player.is_mask_hit = False
    for obs in obstacles:
        obs.is_rect_hit = obs.is_mask_hit = False

        if player.rect.colliderect(obs.rect):
            obs.is_rect_hit = player.is_rect_hit = True
            
            offset = (obs.rect.x - player.rect.x, obs.rect.y - player.rect.y)
            if player.mask.overlap(obs.mask, offset):
                obs.is_mask_hit = player.is_mask_hit = True

    # 3. 그리기
    for obs in obstacles:
        obs.draw_debug(screen)
    player.draw_debug(screen)

    # 4. 정보 및 상태 표시
    status_text = "ROTATING" if is_rotating else "STOPPED"
    status_color = (0, 255, 0) if is_rotating else (255, 100, 100)
    
    info_z = font.render(f"Press 'Z' to Start/Stop Rotation", True, (255, 255, 255))
    info_status = font.render(f"Current State: {status_text}", True, status_color)
    info_obb = font.render("Green Box: OBB (Rotating)", True, (0, 255, 0))
    info_aabb = font.render("Gray/Yellow Box: AABB (Fixed)", True, (150, 150, 150))
    
    screen.blit(info_z, (20, 20))
    screen.blit(info_status, (20, 45))
    screen.blit(info_obb, (20, 75))
    screen.blit(info_aabb, (20, 100))

    if player.is_mask_hit:
        msg = big_font.render("PIXEL COLLISION!", True, (255, 0, 0))
        screen.blit(msg, (screen.get_width()//2 - msg.get_width()//2, 520))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
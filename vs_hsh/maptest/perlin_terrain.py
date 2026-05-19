import pygame
import sys

try:
    from noise import pnoise1
except ImportError:
    print("noise 라이브러리가 없습니다. 설치: pip install noise")
    sys.exit()

# =====================
SCREEN_WIDTH  = 800
SCREEN_HEIGHT = 500
SCROLL_SPEED  = 2       # 픽셀/프레임
SCALE         = 0.005   # 노이즈 주파수 (작을수록 완만)
OCTAVES       = 4       # 디테일 레이어 수
AMPLITUDE     = 150     # 지형 높이 진폭 (픽셀)
BASE_HEIGHT   = 320     # 기준 지형 높이 (y좌표)
WATER_LEVEL   = 380     # 수면 y좌표

COLOR_SKY     = (135, 190, 235)
COLOR_WATER   = (70,  130, 200, 180)
COLOR_GROUND  = (120, 180,  80)
COLOR_DIRT    = (160, 120,  70)
COLOR_STONE   = (130, 120, 110)
COLOR_SNOW    = (240, 240, 250)
COLOR_TEXT    = (255, 255, 255)
COLOR_BG      = (30,   30,  50)
# =====================


def get_height(x_world, seed_offset=0):
    """x_world 좌표에서 지형 높이(y픽셀) 반환"""
    noise_val = pnoise1((x_world + seed_offset) * SCALE,
                        octaves=OCTAVES,
                        persistence=0.5,
                        lacunarity=2.0)
    return int(BASE_HEIGHT + noise_val * AMPLITUDE)


def get_color(y, terrain_y):
    """높이에 따라 지형 색상 결정"""
    depth = y - terrain_y
    if terrain_y < BASE_HEIGHT - 80:
        return COLOR_SNOW
    elif terrain_y < BASE_HEIGHT - 30:
        return COLOR_STONE
    elif depth < 5:
        return COLOR_GROUND
    elif depth < 20:
        return COLOR_DIRT
    else:
        return COLOR_STONE


def draw_terrain(screen, offset, seed_offset):
    screen.fill(COLOR_SKY)

    # 지형 높이 배열 계산
    heights = [get_height(x + offset, seed_offset) for x in range(SCREEN_WIDTH + 1)]

    # 지형 폴리곤 그리기
    points = [(x, heights[x]) for x in range(SCREEN_WIDTH + 1)]
    points += [(SCREEN_WIDTH, SCREEN_HEIGHT), (0, SCREEN_HEIGHT)]
    pygame.draw.polygon(screen, COLOR_GROUND, points)

    # 깊이별 색상 레이어
    for x in range(SCREEN_WIDTH):
        ty = heights[x]
        for dy in range(min(30, SCREEN_HEIGHT - ty)):
            color = get_color(ty + dy, ty)
            screen.set_at((x, ty + dy), color)

    # 수면
    water_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT - WATER_LEVEL), pygame.SRCALPHA)
    water_surf.fill((70, 130, 200, 140))
    screen.blit(water_surf, (0, WATER_LEVEL))
    pygame.draw.line(screen, (100, 160, 220), (0, WATER_LEVEL), (SCREEN_WIDTH, WATER_LEVEL), 2)


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Perlin Noise 스크롤 지형")
    font  = pygame.font.SysFont(["malgungothic", "applegothic", "nanumgothic", None], 17)
    clock = pygame.time.Clock()

    offset = 0
    seed_offset = 0
    paused = False

    running = True
    while running:
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    paused = not paused
                if event.key == pygame.K_n:
                    seed_offset += 10000
                    offset = 0
                if event.key == pygame.K_UP:
                    global SCALE
                    SCALE = min(SCALE * 1.2, 0.05)
                if event.key == pygame.K_DOWN:
                    SCALE = max(SCALE / 1.2, 0.0005)

        keys = pygame.key.get_pressed()
        if not paused:
            if keys[pygame.K_RIGHT]:
                offset += SCROLL_SPEED * 3
            elif keys[pygame.K_LEFT]:
                offset -= SCROLL_SPEED * 3
            else:
                offset += SCROLL_SPEED

        draw_terrain(screen, offset, seed_offset)

        hud = font.render(
            f"[SPACE] 일시정지   [N] 새 seed   [↑↓] scale={SCALE:.4f}   "
            f"[←→] 이동   offset={offset}",
            True, (255, 255, 255))
        screen.blit(hud, (10, 10))

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()


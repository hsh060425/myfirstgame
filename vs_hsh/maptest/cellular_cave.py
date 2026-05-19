import pygame
import random

# =====================
SCREEN_WIDTH  = 800
SCREEN_HEIGHT = 600
TILE_SIZE     = 10
COLS = SCREEN_WIDTH  // TILE_SIZE
ROWS = SCREEN_HEIGHT // TILE_SIZE

FILL_PROB   = 0.45   # 초기 벽 비율
ITERATIONS  = 5      # 시뮬레이션 반복 횟수
BIRTH_LIMIT = 4      # 이웃 벽 >= 이 수면 벽으로 탄생
DEATH_LIMIT = 3      # 이웃 벽 <= 이 수면 벽이면 바닥으로 소멸

COLOR_WALL  = (60,  50,  80)
COLOR_FLOOR = (180, 160, 130)
COLOR_BG    = (20,  20,  30)
COLOR_TEXT  = (255, 255, 255)
COLOR_STEP  = (100, 220, 120)
# =====================


def init_map(seed=None):
    if seed is not None:
        random.seed(seed)
    return [[1 if random.random() < FILL_PROB else 0
             for _ in range(COLS)] for _ in range(ROWS)]


def count_neighbors(tilemap, cx, cy):
    count = 0
    for dy in range(-1, 2):
        for dx in range(-1, 2):
            if dx == 0 and dy == 0:
                continue
            nx, ny = cx + dx, cy + dy
            if nx < 0 or nx >= COLS or ny < 0 or ny >= ROWS:
                count += 1   # 경계 바깥은 벽으로 취급
            elif tilemap[ny][nx] == 1:
                count += 1
    return count


def step(tilemap):
    new_map = [[0] * COLS for _ in range(ROWS)]
    for y in range(ROWS):
        for x in range(COLS):
            n = count_neighbors(tilemap, x, y)
            if tilemap[y][x] == 1:
                new_map[y][x] = 1 if n >= DEATH_LIMIT else 0
            else:
                new_map[y][x] = 1 if n > BIRTH_LIMIT else 0
    return new_map


def generate(seed=None):
    tilemap = init_map(seed)
    for _ in range(ITERATIONS):
        tilemap = step(tilemap)
    return tilemap


def draw(screen, tilemap, font, seed, current_iter, auto_mode):
    screen.fill(COLOR_BG)
    for row in range(ROWS):
        for col in range(COLS):
            color = COLOR_WALL if tilemap[row][col] == 1 else COLOR_FLOOR
            pygame.draw.rect(screen, color,
                             (col * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE))

    mode_str = "자동" if auto_mode else "수동"
    msg = font.render(
        f"Seed: {seed}   반복: {current_iter}/{ITERATIONS}   "
        f"[SPACE] 한 스텝   [A] 자동({mode_str})   [R] 리셋   [N] 새 seed",
        True, COLOR_TEXT)
    screen.blit(msg, (10, 10))


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Cellular Automata 동굴 생성")
    font  = pygame.font.SysFont(["malgungothic", "applegothic", "nanumgothic", None], 16)
    clock = pygame.time.Clock()

    seed = random.randint(0, 99999)
    tilemap = init_map(seed)
    current_iter = 0
    auto_mode = False
    auto_timer = 0
    AUTO_INTERVAL = 300  # ms

    running = True
    while running:
        dt = clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if current_iter < ITERATIONS:
                        tilemap = step(tilemap)
                        current_iter += 1
                if event.key == pygame.K_a:
                    auto_mode = not auto_mode
                    auto_timer = 0
                if event.key == pygame.K_r:
                    tilemap = init_map(seed)
                    current_iter = 0
                    auto_mode = False
                if event.key == pygame.K_n:
                    seed = random.randint(0, 99999)
                    tilemap = init_map(seed)
                    current_iter = 0
                    auto_mode = False

        if auto_mode and current_iter < ITERATIONS:
            auto_timer += dt
            if auto_timer >= AUTO_INTERVAL:
                tilemap = step(tilemap)
                current_iter += 1
                auto_timer = 0
            if current_iter >= ITERATIONS:
                auto_mode = False

        draw(screen, tilemap, font, seed, current_iter, auto_mode)
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()

import pygame
import random
from collections import deque

# =====================
SCREEN_WIDTH  = 900
SCREEN_HEIGHT = 620
TILE          = 8
COLS          = 100
ROWS          = 70
MAP_PX_W      = COLS * TILE
MAP_PX_H      = ROWS * TILE
MAP_X         = (SCREEN_WIDTH  - MAP_PX_W) // 2
MAP_Y         = (SCREEN_HEIGHT - MAP_PX_H) // 2 + 15
MIN_CELLS     = 8    # 최소 셀 크기 (타일 단위)
HALL_WIDTH    = 2    # 통로 폭 (타일)

EMPTY = 0
WALL  = 1
FLOOR = 2
HALL  = 3
NEW   = 4   # 이번 단계에서 새로 추가된 타일 (하이라이트용)

COLOR_BG        = (20,  20,  30)
COLOR_EMPTY     = (30,  30,  45)
COLOR_WALL      = (50,  45,  65)
COLOR_FLOOR     = (200, 175, 130)
COLOR_HALL      = (160, 140, 100)
COLOR_NEW       = (255, 220,  80)
COLOR_MST_HALL  = (100, 220, 130)
COLOR_DUP_HALL  = (200,  70,  70)
COLOR_SPLIT     = (80,  150, 220)
COLOR_TEXT      = (255, 255, 255)
COLOR_DIM       = (100, 100, 120)

TILE_COLORS = {
    EMPTY: COLOR_EMPTY,
    WALL:  COLOR_WALL,
    FLOOR: COLOR_FLOOR,
    HALL:  COLOR_HALL,
    NEW:   COLOR_NEW,
}

PHASE_SPLIT   = 0
PHASE_ROOMS   = 1
PHASE_HALLS   = 2
PHASE_CLEANUP = 3
PHASE_DONE    = 4

PHASE_LABELS = {
    PHASE_SPLIT:   "1단계: 공간 분할",
    PHASE_ROOMS:   "2단계: 방 배치",
    PHASE_HALLS:   "3단계: 통로 연결 (중복 포함)",
    PHASE_CLEANUP: "4단계: 중복 통로 제거 (MST)",
    PHASE_DONE:    "완성!",
}
# =====================


class BSPNode:
    def __init__(self, x, y, w, h):
        self.x, self.y, self.w, self.h = x, y, w, h
        self.left  = None
        self.right = None
        self.room  = None   # (rx, ry, rw, rh) 타일 좌표

    def try_split(self):
        can_h = self.h > MIN_CELLS * 2
        can_v = self.w > MIN_CELLS * 2
        if not can_h and not can_v:
            return False
        if can_h and can_v:
            horizontal = random.random() < 0.5
        else:
            horizontal = can_h
        if horizontal:
            pos = random.randint(MIN_CELLS, self.h - MIN_CELLS)
            self.left  = BSPNode(self.x, self.y,       self.w, pos)
            self.right = BSPNode(self.x, self.y + pos, self.w, self.h - pos)
        else:
            pos = random.randint(MIN_CELLS, self.w - MIN_CELLS)
            self.left  = BSPNode(self.x,       self.y, pos,          self.h)
            self.right = BSPNode(self.x + pos, self.y, self.w - pos, self.h)
        return True

    def is_leaf(self):
        return self.left is None and self.right is None

    def create_room(self):
        pad = 2
        rw = random.randint(self.w // 2, self.w - pad * 2)
        rh = random.randint(self.h // 2, self.h - pad * 2)
        rx = self.x + random.randint(pad, self.w - rw - pad)
        ry = self.y + random.randint(pad, self.h - rh - pad)
        self.room = (rx, ry, rw, rh)

    def get_room(self):
        if self.room:
            return self.room
        lr = self.left.get_room()  if self.left  else None
        rr = self.right.get_room() if self.right else None
        if not lr: return rr
        if not rr: return lr
        return random.choice([lr, rr])

    def center(self):
        r = self.get_room()
        if r:
            rx, ry, rw, rh = r
            return (rx + rw // 2, ry + rh // 2)
        return (self.x + self.w // 2, self.y + self.h // 2)


def collect_leaves(node, out):
    if node is None:
        return
    if node.is_leaf():
        out.append(node)
    else:
        collect_leaves(node.left, out)
        collect_leaves(node.right, out)


def collect_split_steps(root):
    steps = []
    queue = deque([root])
    while queue:
        n = queue.popleft()
        if n.left and n.right:
            steps.append(n)
            queue.append(n.left)
            queue.append(n.right)
    return steps


def collect_hall_pairs(node, pairs):
    if node is None or node.is_leaf():
        return
    collect_hall_pairs(node.left,  pairs)
    collect_hall_pairs(node.right, pairs)
    l = node.left.get_room()  if node.left  else None
    r = node.right.get_room() if node.right else None
    if l and r:
        pairs.append((l, r))


def room_center(room):
    rx, ry, rw, rh = room
    return (rx + rw // 2, ry + rh // 2)


def dist(a, b):
    ax, ay = room_center(a)
    bx, by = room_center(b)
    return ((ax - bx) ** 2 + (ay - by) ** 2) ** 0.5


def build_mst(rooms):
    if len(rooms) <= 1:
        return []
    in_tree = {0}
    edges = []
    while len(in_tree) < len(rooms):
        best, best_dist = None, float('inf')
        for i in in_tree:
            for j in range(len(rooms)):
                if j in in_tree:
                    continue
                d = dist(rooms[i], rooms[j])
                if d < best_dist:
                    best_dist = d
                    best = (i, j)
        if best:
            in_tree.add(best[1])
            edges.append((rooms[best[0]], rooms[best[1]]))
    return edges


def carve_hall(tilemap, a, b):
    """두 방 사이 L자 통로를 타일맵에 새김. 새로 판 타일 좌표 목록 반환."""
    ax, ay = room_center(a)
    bx, by = room_center(b)
    hw = HALL_WIDTH // 2
    new_tiles = []

    def carve_h(x1, x2, y):
        for tx in range(min(x1, x2), max(x1, x2) + 1):
            for dy in range(-hw, hw + 1):
                ty = y + dy
                if 0 <= tx < COLS and 0 <= ty < ROWS:
                    if tilemap[ty][tx] == EMPTY:
                        new_tiles.append((tx, ty))
                    tilemap[ty][tx] = HALL

    def carve_v(x, y1, y2):
        for ty in range(min(y1, y2), max(y1, y2) + 1):
            for dx in range(-hw, hw + 1):
                tx = x + dx
                if 0 <= tx < COLS and 0 <= ty < ROWS:
                    if tilemap[ty][tx] == EMPTY:
                        new_tiles.append((tx, ty))
                    tilemap[ty][tx] = HALL

    # L자: 수직 먼저, 수평 다음
    carve_v(ax, ay, by)
    carve_h(ax, bx, by)
    return new_tiles


def build(seed):
    random.seed(seed)

    root = BSPNode(1, 1, COLS - 2, ROWS - 2)
    queue = deque([root])
    while queue:
        n = queue.popleft()
        if n.try_split():
            queue.append(n.left)
            queue.append(n.right)

    leaves = []
    collect_leaves(root, leaves)
    for leaf in leaves:
        leaf.create_room()

    split_steps = collect_split_steps(root)

    all_pairs = []
    collect_hall_pairs(root, all_pairs)

    rooms = [leaf.room for leaf in leaves]
    mst_pairs = build_mst(rooms)

    mst_set = set()
    for a, b in mst_pairs:
        mst_set.add((a, b))
        mst_set.add((b, a))
    dup_pairs = [(a, b) for a, b in all_pairs if (a, b) not in mst_set]

    return root, leaves, split_steps, all_pairs, mst_pairs, dup_pairs


def make_tilemap():
    return [[EMPTY] * COLS for _ in range(ROWS)]


def render_tilemap(surface, tilemap, highlight_tiles=None):
    hs = set(highlight_tiles) if highlight_tiles else set()
    for ty in range(ROWS):
        for tx in range(COLS):
            v = tilemap[ty][tx]
            color = TILE_COLORS.get(v, COLOR_EMPTY)
            if (tx, ty) in hs:
                color = COLOR_NEW
            px = MAP_X + tx * TILE
            py = MAP_Y + ty * TILE
            pygame.draw.rect(surface, color, (px, py, TILE, TILE))


def render_split_overlay(surface, split_steps, count):
    """분할선을 타일맵 위에 오버레이"""
    for node in split_steps[:count]:
        if node.left and node.right:
            if node.left.y != node.right.y:  # 수평 분할
                y = node.right.y
                x1 = MAP_X + node.x * TILE
                x2 = MAP_X + (node.x + node.w) * TILE
                py = MAP_Y + y * TILE
                pygame.draw.line(surface, COLOR_SPLIT, (x1, py), (x2, py), 1)
            else:  # 수직 분할
                x = node.right.x
                y1 = MAP_Y + node.y * TILE
                y2 = MAP_Y + (node.y + node.h) * TILE
                px = MAP_X + x * TILE
                pygame.draw.line(surface, COLOR_SPLIT, (px, y1), (px, y2), 1)


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("BSP 던전 생성 과정")
    font_lg = pygame.font.SysFont(["malgungothic", "applegothic", "nanumgothic", None], 19)
    font_sm = pygame.font.SysFont(["malgungothic", "applegothic", "nanumgothic", None], 15)
    clock = pygame.time.Clock()

    seed = random.randint(0, 99999)
    root, leaves, split_steps, all_pairs, mst_pairs, dup_pairs = build(seed)

    # 타일맵 상태
    tilemap = make_tilemap()

    # 각 단계별 타일맵 스냅샷 미리 계산
    # 방 스냅샷
    room_snapshots = []
    tm = make_tilemap()
    for leaf in leaves:
        rx, ry, rw, rh = leaf.room
        new_t = []
        for ty in range(ry, ry + rh):
            for tx in range(rx, rx + rw):
                if 0 <= tx < COLS and 0 <= ty < ROWS:
                    tm[ty][tx] = FLOOR
                    new_t.append((tx, ty))
        import copy
        room_snapshots.append((copy.deepcopy(tm), new_t))

    # 통로 스냅샷 (all_pairs)
    hall_snapshots = []
    tm2 = copy.deepcopy(room_snapshots[-1][0]) if room_snapshots else make_tilemap()
    for a, b in all_pairs:
        new_t = carve_hall(tm2, a, b)
        hall_snapshots.append((copy.deepcopy(tm2), new_t))

    # MST 정리 스냅샷
    # mst 타일맵 (clean)
    tm_mst = copy.deepcopy(room_snapshots[-1][0]) if room_snapshots else make_tilemap()
    for a, b in mst_pairs:
        carve_hall(tm_mst, a, b)

    # dup 제거 단계: all_pairs 통로맵에서 dup을 하나씩 mst맵으로 교체
    # 간단하게: cleanup_idx가 증가할수록 dup_pairs[:idx] 를 숨긴 타일맵 사용
    # 대신 all_pairs 완성 맵 + mst 맵 두 개를 보간

    phase     = PHASE_SPLIT
    split_idx = 0
    room_idx  = 0
    hall_idx  = 0
    clean_idx = 0

    def reset(new_seed=None):
        nonlocal seed, root, leaves, split_steps, all_pairs, mst_pairs, dup_pairs
        nonlocal phase, split_idx, room_idx, hall_idx, clean_idx
        nonlocal room_snapshots, hall_snapshots, tm_mst
        seed = new_seed if new_seed is not None else random.randint(0, 99999)
        root, leaves, split_steps, all_pairs, mst_pairs, dup_pairs = build(seed)

        room_snapshots.clear()
        tm = make_tilemap()
        for leaf in leaves:
            rx, ry, rw, rh = leaf.room
            new_t = []
            for ty in range(ry, ry + rh):
                for tx in range(rx, rx + rw):
                    if 0 <= tx < COLS and 0 <= ty < ROWS:
                        tm[ty][tx] = FLOOR
                        new_t.append((tx, ty))
            room_snapshots.append((copy.deepcopy(tm), new_t))

        hall_snapshots.clear()
        tm2 = copy.deepcopy(room_snapshots[-1][0]) if room_snapshots else make_tilemap()
        for a, b in all_pairs:
            new_t = carve_hall(tm2, a, b)
            hall_snapshots.append((copy.deepcopy(tm2), new_t))

        tm_mst = copy.deepcopy(room_snapshots[-1][0]) if room_snapshots else make_tilemap()
        for a, b in mst_pairs:
            carve_hall(tm_mst, a, b)

        phase = PHASE_SPLIT
        split_idx = room_idx = hall_idx = clean_idx = 0

    def advance():
        nonlocal phase, split_idx, room_idx, hall_idx, clean_idx
        if phase == PHASE_SPLIT:
            if split_idx < len(split_steps):
                split_idx += 1
            else:
                phase = PHASE_ROOMS
        elif phase == PHASE_ROOMS:
            if room_idx < len(leaves):
                room_idx += 1
            else:
                phase = PHASE_HALLS
        elif phase == PHASE_HALLS:
            if hall_idx < len(all_pairs):
                hall_idx += 1
            else:
                phase = PHASE_CLEANUP
        elif phase == PHASE_CLEANUP:
            if clean_idx < len(dup_pairs):
                clean_idx += 1
            else:
                phase = PHASE_DONE

    def skip_phase():
        nonlocal phase, split_idx, room_idx, hall_idx, clean_idx
        if phase == PHASE_SPLIT:
            split_idx = len(split_steps)
            phase = PHASE_ROOMS
        elif phase == PHASE_ROOMS:
            room_idx = len(leaves)
            phase = PHASE_HALLS
        elif phase == PHASE_HALLS:
            hall_idx = len(all_pairs)
            phase = PHASE_CLEANUP
        elif phase == PHASE_CLEANUP:
            clean_idx = len(dup_pairs)
            phase = PHASE_DONE

    auto_mode  = False
    auto_timer = 0
    AUTO_MS    = 120

    running = True
    while running:
        dt = clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if phase == PHASE_DONE:
                        reset()
                    else:
                        advance()
                if event.key == pygame.K_n:
                    reset()
                if event.key == pygame.K_a:
                    auto_mode = not auto_mode
                    auto_timer = 0
                if event.key == pygame.K_f:
                    skip_phase()

        if auto_mode and phase != PHASE_DONE:
            auto_timer += dt
            if auto_timer >= AUTO_MS:
                advance()
                auto_timer = 0

        # ── 렌더링 ──
        screen.fill(COLOR_BG)

        highlight = []

        if phase == PHASE_SPLIT:
            # 빈 타일맵 + 분할선 오버레이
            render_tilemap(screen, make_tilemap())
            render_split_overlay(screen, split_steps, split_idx)
            # 다음 분할선 하이라이트
            if split_idx < len(split_steps):
                node = split_steps[split_idx]
                if node.left and node.right:
                    if node.left.y != node.right.y:
                        y = node.right.y
                        x1 = MAP_X + node.x * TILE
                        x2 = MAP_X + (node.x + node.w) * TILE
                        py = MAP_Y + y * TILE
                        pygame.draw.line(screen, COLOR_NEW, (x1, py), (x2, py), 2)
                    else:
                        x = node.right.x
                        y1 = MAP_Y + node.y * TILE
                        y2 = MAP_Y + (node.y + node.h) * TILE
                        px = MAP_X + x * TILE
                        pygame.draw.line(screen, COLOR_NEW, (px, y1), (px, y2), 2)

        elif phase == PHASE_ROOMS:
            if room_idx == 0:
                render_tilemap(screen, make_tilemap())
            else:
                tm, ht = room_snapshots[room_idx - 1]
                render_tilemap(screen, tm, ht if room_idx > 0 else [])
            render_split_overlay(screen, split_steps, len(split_steps))
            # 다음 방 예고
            if room_idx < len(leaves):
                rx, ry, rw, rh = leaves[room_idx].room
                px = MAP_X + rx * TILE
                py = MAP_Y + ry * TILE
                pygame.draw.rect(screen, COLOR_NEW, (px, py, rw * TILE, rh * TILE), 2)

        elif phase == PHASE_HALLS:
            if hall_idx == 0:
                tm, _ = room_snapshots[-1]
                render_tilemap(screen, tm)
            else:
                tm, ht = hall_snapshots[hall_idx - 1]
                render_tilemap(screen, tm, ht)
            render_split_overlay(screen, split_steps, len(split_steps))

        elif phase in (PHASE_CLEANUP, PHASE_DONE):
            # cleanup: dup_pairs[:clean_idx] 는 mst_map 으로, 나머지는 all_pairs map
            # 간단히: mst맵 기반으로 그리고, 아직 제거 안 된 dup은 빨간색으로 오버레이
            render_tilemap(screen, tm_mst)
            # 아직 제거 안 된 중복 통로 빨간색 오버레이
            remaining = dup_pairs[clean_idx:]
            for a, b in remaining:
                ax, ay = room_center(a)
                bx, by = room_center(b)
                hw = HALL_WIDTH // 2
                # 수직
                for ty in range(min(ay, by), max(ay, by) + 1):
                    for dx in range(-hw, hw + 1):
                        tx = ax + dx
                        if 0 <= tx < COLS and 0 <= ty < ROWS:
                            px = MAP_X + tx * TILE
                            py = MAP_Y + ty * TILE
                            pygame.draw.rect(screen, COLOR_DUP_HALL, (px, py, TILE, TILE))
                # 수평
                for tx in range(min(ax, bx), max(ax, bx) + 1):
                    for dy in range(-hw, hw + 1):
                        ty = by + dy
                        if 0 <= tx < COLS and 0 <= ty < ROWS:
                            px = MAP_X + tx * TILE
                            py = MAP_Y + ty * TILE
                            pygame.draw.rect(screen, COLOR_DUP_HALL, (px, py, TILE, TILE))
            # 현재 제거 중 하이라이트
            if phase == PHASE_CLEANUP and clean_idx < len(dup_pairs):
                a, b = dup_pairs[clean_idx]
                ax, ay = room_center(a)
                bx, by = room_center(b)
                hw = HALL_WIDTH // 2
                for ty in range(min(ay, by), max(ay, by) + 1):
                    for dx in range(-hw, hw + 1):
                        tx = ax + dx
                        if 0 <= tx < COLS and 0 <= ty < ROWS:
                            pygame.draw.rect(screen, COLOR_NEW,
                                             (MAP_X + tx * TILE, MAP_Y + ty * TILE, TILE, TILE))
                for tx in range(min(ax, bx), max(ax, bx) + 1):
                    for dy in range(-hw, hw + 1):
                        ty = by + dy
                        if 0 <= tx < COLS and 0 <= ty < ROWS:
                            pygame.draw.rect(screen, COLOR_NEW,
                                             (MAP_X + tx * TILE, MAP_Y + ty * TILE, TILE, TILE))

        # HUD
        screen.blit(font_lg.render(PHASE_LABELS[phase], True, COLOR_TEXT), (10, 5))

        if phase == PHASE_SPLIT:
            prog = f"분할 {split_idx}/{len(split_steps)}"
        elif phase == PHASE_ROOMS:
            prog = f"방 {room_idx}/{len(leaves)}"
        elif phase == PHASE_HALLS:
            prog = f"통로 {hall_idx}/{len(all_pairs)}"
        elif phase == PHASE_CLEANUP:
            prog = f"중복 제거 {clean_idx}/{len(dup_pairs)}  초록=MST  빨강=중복"
        else:
            prog = f"통로 {len(mst_pairs)}개  seed={seed}  [SPACE] 처음부터  [N] 새 seed"

        if phase != PHASE_DONE:
            hint = (f"{prog}   [SPACE] 한 단계   "
                    f"[A] 자동({'ON' if auto_mode else 'OFF'})   "
                    f"[F] 단계 건너뜀   [N] 새 seed={seed}")
        else:
            hint = prog

        screen.blit(font_sm.render(hint, True, COLOR_DIM), (10, SCREEN_HEIGHT - 20))
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
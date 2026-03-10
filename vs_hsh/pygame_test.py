import pygame
import random
import math

pygame.init()

WIDTH, HEIGHT = 900, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Fancy Particle & Wave Playground")

clock = pygame.time.Clock()

particles = []
waves = [] # 파동을 저장할 리스트 추가

class Particle:
    def __init__(self, x, y, burst=False):
        self.x = x
        self.y = y

        # burst가 True면 파동처럼 퍼져나가도록 속도를 더 빠르게 설정
        speed = random.uniform(3, 10) if burst else random.uniform(1, 6)
        angle = random.uniform(0, math.pi * 2)

        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed

        self.life = random.randint(40, 80)
        self.size = random.randint(3, 7)

        self.color = (
            random.randint(150, 255),
            random.randint(100, 255),
            random.randint(150, 255)
        )

    def update(self):
        self.x += self.vx
        self.y += self.vy

        self.vy += 0.08 # 중력
        self.life -= 1

    def draw(self, surf):
        if self.life > 0:
            pygame.draw.circle(
                surf,
                self.color,
                (int(self.x), int(self.y)),
                self.size
            )

    def alive(self):
        return self.life > 0

# 파동(충격파) 클래스 추가
class Wave:
    def __init__(self, x, y, color, is_small=False):
        self.x = x
        self.y = y
        self.color = color
        
        if is_small:
            # 파티클이 사라질 때 생기는 작은 파동
            self.radius = 1.0
            self.speed = 1.5
            self.width = 3.0
            self.decay = 0.15
        else:
            # 마우스를 클릭했을 때 생기는 큰 파동
            self.radius = 1.0
            self.speed = 6.0
            self.width = 8.0
            self.decay = 0.25

    def update(self):
        self.radius += self.speed
        self.width -= self.decay # 선의 두께가 점점 얇아짐

    def draw(self, surf):
        draw_radius = int(self.radius)
        draw_width = max(1, int(self.width))
        
        # pygame 원 그리기 에러 방지 (두께가 반지름보다 크면 안됨)
        if draw_width > draw_radius:
            draw_width = draw_radius
            
        if draw_width > 0:
            pygame.draw.circle(surf, self.color, (int(self.x), int(self.y)), draw_radius, draw_width)

    def alive(self):
        return self.width > 0


def draw_background(surface, t):
    for y in range(HEIGHT):
        c = int(40 + 30 * math.sin(y * 0.01 + t))
        color = (10, c, 50 + c//2)
        pygame.draw.line(surface, color, (0, y), (WIDTH, y))


running = True
time = 0

while running:

    mouse = pygame.mouse.get_pos()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        # 마우스를 클릭하는 순간 파동과 함께 원형으로 파티클 터짐
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: # 좌클릭
                # 1. 큰 파동 생성
                waves.append(Wave(mouse[0], mouse[1], (255, 255, 255)))
                
                # 2. 파동 모양(원형)으로 파티클 폭발
                for _ in range(30):
                    particles.append(Particle(mouse[0], mouse[1], burst=True))

    buttons = pygame.mouse.get_pressed()

    # 마우스를 꾹 누르고 있을 때 연속으로 파티클 생성
    if buttons[0]:
        for _ in range(3): # 클릭 순간 폭발이 있으므로 연속 생성 개수는 약간 줄임
            particles.append(Particle(mouse[0], mouse[1]))

    time += 0.03

    draw_background(screen, time)

    # 파동 업데이트 및 그리기
    for w in waves:
        w.update()
        w.draw(screen)
    waves = [w for w in waves if w.alive()]

    # 파티클 업데이트 및 그리기
    alive_particles = []
    for p in particles:
        p.update()
        p.draw(screen)
        
        if p.alive():
            alive_particles.append(p)
        else:
            # 파티클이 죽으면(수명이 다하면) 그 위치에서 작은 파동 터짐
            waves.append(Wave(p.x, p.y, p.color, is_small=True))
            
    particles = alive_particles

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
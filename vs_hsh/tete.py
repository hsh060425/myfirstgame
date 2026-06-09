import random
from ursina import *
from ursina.lights import DirectionalLight

app = Ursina(borderless=False)
player = Entity(model='cube', color=color.orange, collider='box', position=(0, 0, 0))
targets = [Entity(model='sphere', color=color.red, collider='sphere',
                  position=(random.randint(-8, 8), 0, random.randint(-8, 8)))
           for _ in range(5)]
ground = Entity(model='plane', texture='grass', scale=20, position=(0, -1, 0))
Sky()
DirectionalLight().look_at(Vec3(1, -2, 1))
camera.position = (0, 5, -15)
camera.look_at(Vec3(0, 0, 0))

score = 0
remaining = 30
score_text = Text(text='Score: 0', position=(-0.7, 0.45), scale=2)
time_text = Text(text='Time: 30', position=(0.4, 0.45), scale=2)

SPEED = 4

def update():
    global score, remaining
    if held_keys['d']: player.x += SPEED * time.dt
    if held_keys['a']: player.x -= SPEED * time.dt
    if held_keys['w']: player.z += SPEED * time.dt
    if held_keys['s']: player.z -= SPEED * time.dt
    
    remaining -= time.dt
    time_text.text = f'Time: {int(remaining)}'
    
    if remaining <= 0:
        time_text.text = f'Game Over! Score: {score}'
        return
        
    for t in targets:
        if player.intersects(t).hit:
            score += 1
            score_text.text = f'Score: {score}'
            t.position = Vec3(random.randint(-8, 8), 0, random.randint(-8, 8))

app.run()
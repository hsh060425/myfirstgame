import pygame
import socket
import pickle

# 게임 설정
width = 500
height = 500
win = pygame.display.set_mode((width, height))
pygame.display.set_caption("멀티플레이어 이동 테스트")

# 네트워크 설정
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server = "127.0.0.1"
port = 5555
client.connect((server, port))

# 처음 접속 시 서버가 주는 초기 내 위치 받기
my_pos = pickle.loads(client.recv(2048))

def redrawWindow(win, players):
    win.fill((255, 255, 255))
    for p_id in players:
        pos = players[p_id]
        # 플레이어마다 다른 색상을 주기 위해 ID 사용 (대충 처리)
        color = (0, 255, 0) if p_id == 0 else (255, 0, 0)
        pygame.draw.rect(win, color, (pos[0], pos[1], 50, 50))
    pygame.display.update()

def main():
    run = True
    clock = pygame.time.Clock()

    while run:
        clock.tick(60)
        
        # 1. 내 움직임 처리
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]: my_pos[0] -= 5
        if keys[pygame.K_RIGHT]: my_pos[0] += 5
        if keys[pygame.K_UP]: my_pos[1] -= 5
        if keys[pygame.K_DOWN]: my_pos[1] += 5

        # 2. 서버에 내 위치 보내고 모든 플레이어 정보 받아오기
        try:
            client.send(pickle.dumps(my_pos))
            all_players = pickle.loads(client.recv(2048))
        except:
            run = False
            print("서버와 연결이 끊겼습니다.")
            break

        # 3. 그리기
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

        redrawWindow(win, all_players)

    pygame.quit()

main()
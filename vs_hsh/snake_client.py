import pygame
import socket
import pickle

# 설정
dis_width = 800
dis_height = 600
snake_block = 20

# 색상
white = (255, 255, 255)
black = (0, 0, 0)
gray = (30, 30, 30)

pygame.init()
dis = pygame.display.set_mode((dis_width, dis_height))
pygame.display.set_caption('2인용 스네이크 - 멀티플레이어')
clock = pygame.time.Clock()
font_style = pygame.font.SysFont("malgungothic", 30)

def draw_game(state, my_id):
    dis.fill(gray)
    
    # 먹이 그리기
    for f in state["foods"]:
        pygame.draw.rect(dis, f["type"]["color"], [f["pos"][0], f["pos"][1], snake_block, snake_block])
    
    # 플레이어들 그리기
    for pid, p in state["players"].items():
        for part in p["list"]:
            pygame.draw.rect(dis, p["color"], [part[0], part[1], snake_block, snake_block])
    
    # 점수 표시
    p1_score = state["players"][0]["len"] - 1
    p2_score = state["players"][1]["len"] - 1
    s1 = font_style.render(f"P1: {p1_score}", True, state["players"][0]["color"])
    s2 = font_style.render(f"P2: {p2_score}", True, state["players"][1]["color"])
    dis.blit(s1, [20, 10])
    dis.blit(s2, [dis_width - 150, 10])

    if state["game_over"]:
        msg = font_style.render(state["winner_msg"], True, white)
        dis.blit(msg, [dis_width/4, dis_height/2])

    pygame.display.update()

def run_client():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # 서버의 IP 주소를 입력하세요. (같은 컴퓨터면 '127.0.0.1')
    client.connect(('127.0.0.1', 5555))
    
    my_id = pickle.loads(client.recv(2048))
    print(f"당신은 플레이어 {my_id + 1}입니다.")

    current_change = [0, 0]
    run = True

    while run:
        clock.tick(20)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT and current_change[0] == 0:
                    current_change = [-snake_block, 0]
                elif event.key == pygame.K_RIGHT and current_change[0] == 0:
                    current_change = [snake_block, 0]
                elif event.key == pygame.K_UP and current_change[1] == 0:
                    current_change = [0, -snake_block]
                elif event.key == pygame.K_DOWN and current_change[1] == 0:
                    current_change = [0, snake_block]

        try:
            # 서버에 내 입력 전송
            client.sendall(pickle.dumps(current_change))
            
            # 서버로부터 전체 상태 수신
            data = client.recv(4096 * 2)
            if data:
                state = pickle.loads(data)
                draw_game(state, my_id)
        except Exception as e:
            print("서버와의 연결이 끊어졌습니다.", e)
            break

    pygame.quit()

if __name__ == "__main__":
    run_client()
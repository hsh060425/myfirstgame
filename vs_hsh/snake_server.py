import socket
import threading
import pickle
import time
import random
import pygame

# 초기 설정 (게임 로직용)
WIDTH, HEIGHT = 800, 600
SNAKE_BLOCK = 20
MAX_FOOD_COUNT = 5

FOOD_TYPES = [
    {"color": (0, 255, 0), "growth": 1, "prob": 70},
    {"color": (255, 255, 0), "growth": 2, "prob": 20},
    {"color": (160, 32, 240), "growth": 3, "prob": 10}
]

class GameServer:
    def __init__(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind(('0.0.0.0', 5555))
        self.server.listen(2)
        print("서버가 시작되었습니다. 연결을 기다리는 중...")

        self.players = {
            0: {"pos": [600, 300], "change": [0, 0], "list": [], "len": 1, "color": (50, 153, 213)},
            1: {"pos": [200, 300], "change": [0, 0], "list": [], "len": 1, "color": (213, 50, 80)}
        }
        self.foods = [self.generate_food() for _ in range(MAX_FOOD_COUNT)]
        self.winner_msg = ""
        self.game_over = False

    def generate_food(self):
        pick = random.randint(1, 100)
        cumulative_prob = 0
        selected_type = FOOD_TYPES[0]
        for f_type in FOOD_TYPES:
            cumulative_prob += f_type["prob"]
            if pick <= cumulative_prob:
                selected_type = f_type
                break
        
        fx = round(random.randrange(0, WIDTH - SNAKE_BLOCK) / 20.0) * 20.0
        fy = round(random.randrange(0, HEIGHT - SNAKE_BLOCK) / 20.0) * 20.0
        return {"pos": [fx, fy], "type": selected_type}

    def update_logic(self):
        if self.game_over: return

        for i in range(2):
            p = self.players[i]
            if p["change"] == [0, 0]: continue

            p["pos"][0] += p["change"][0]
            p["pos"][1] += p["change"][1]

            # 벽 충돌
            if p["pos"][0] < 0 or p["pos"][0] >= WIDTH or p["pos"][1] < 0 or p["pos"][1] >= HEIGHT:
                self.winner_msg = f"PLAYER {2 if i==0 else 1} WIN (Hit Wall)"
                self.game_over = True

            # 몸통 업데이트
            p["list"].append(list(p["pos"]))
            if len(p["list"]) > p["len"]:
                del p["list"][0]

            # 자기 몸 충돌
            for part in p["list"][:-1]:
                if part == p["pos"]:
                    self.winner_msg = f"PLAYER {2 if i==0 else 1} WIN (Self Hit)"
                    self.game_over = True

            # 먹이 충돌
            for f in self.foods[:]:
                if p["pos"] == f["pos"]:
                    p["len"] += f["type"]["growth"]
                    self.foods.remove(f)
                    self.foods.append(self.generate_food())

        # 상대방 몸 충돌
        p1, p2 = self.players[0], self.players[1]
        for part in p2["list"]:
            if p1["pos"] == part:
                self.winner_msg = "P2 WIN (P1 Hit P2)"
                self.game_over = True
        for part in p1["list"]:
            if p2["pos"] == part:
                self.winner_msg = "P1 WIN (P2 Hit P1)"
                self.game_over = True

    def client_thread(self, conn, player_id):
        conn.send(pickle.dumps(player_id)) # 초기 ID 전송

        while True:
            try:
                data = pickle.loads(conn.recv(2048))
                if not data: break

                # 키 입력 처리 (반대 방향 금지 로직 포함 가능)
                self.players[player_id]["change"] = data
                
                # 현재 전체 게임 상태 전송
                state = {
                    "players": self.players,
                    "foods": self.foods,
                    "winner_msg": self.winner_msg,
                    "game_over": self.game_over
                }
                conn.sendall(pickle.dumps(state))
            except:
                break
        conn.close()

    def run(self):
        # 게임 로직 업데이트 루프 (초당 10번)
        def game_loop():
            while True:
                self.update_logic()
                time.sleep(0.1)

        threading.Thread(target=game_loop, daemon=True).start()

        curr_player = 0
        while curr_player < 2:
            conn, addr = self.server.accept()
            print(f"Player {curr_player} 연결됨: {addr}")
            threading.Thread(target=self.client_thread, args=(conn, curr_player)).start()
            curr_player += 1

if __name__ == "__main__":
    server = GameServer()
    server.run()
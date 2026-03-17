import socket
import threading
import pickle

# 서버 설정
SERVER = "127.0.0.1"  # 내 컴퓨터에서 테스트
PORT = 5555
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    s.bind((SERVER, PORT))
except socket.error as e:
    print(str(e))

s.listen()
print("서버 시작, 연결을 기다리는 중...")

# 플레이어들의 위치 정보 저장 {id: [x, y]}
players = {}

def threaded_client(conn, player_id):
    # 처음 접속 시 해당 플레이어의 위치 초기화
    players[player_id] = [0, 0]
    conn.send(pickle.dumps(players[player_id])) # 내 초기 위치 전송

    while True:
        try:
            # 클라이언트로부터 위치 정보를 받음
            data = pickle.loads(conn.recv(2048))
            players[player_id] = data

            if not data:
                print("연결 끊김")
                break
            
            # 모든 플레이어의 위치 정보를 전송
            conn.sendall(pickle.dumps(players))
        except:
            break

    print(f"플레이어 {player_id} 종료")
    del players[player_id]
    conn.close()

curr_player = 0
while True:
    conn, addr = s.accept()
    print(f"{addr} 연결됨")
    
    # 각 클라이언트를 별도의 스레드로 처리
    thread = threading.Thread(target=threaded_client, args=(conn, curr_player))
    thread.start()
    curr_player += 1
import socket
import pickle
import random
import threading

WIDTH, HEIGHT = 600, 600
SQUARE = 20
PORT = 5577
MAX_PLAYERS = 4

SNAKE_COLORS = [
    ((50, 205, 50), (34, 139, 34)),
    ((255, 165, 0), (255, 140, 0)),
    ((0, 255, 255), (0, 139, 139)),
    ((255, 0, 255), (139, 0, 139)),
]

players = [None] * MAX_PLAYERS
apples = []
lock = threading.Lock()

def generate_apple():
    return {
        'x': random.randint(0, (WIDTH - SQUARE) // SQUARE) * SQUARE,
        'y': random.randint(0, (HEIGHT - SQUARE) // SQUARE) * SQUARE
    }

def handle_client(client_socket, addr, player_id):
    print(f"Player {player_id} connected from {addr}")

    start_x = random.randint(5, (WIDTH // SQUARE) - 6) * SQUARE
    start_y = random.randint(5, (HEIGHT // SQUARE) - 6) * SQUARE
    snake_body = [(start_x - i * SQUARE, start_y) for i in range(5)]

    snake = {
        'body': snake_body,
        'dir': 'RIGHT',
        'score': 0,
        'colors': SNAKE_COLORS[player_id % len(SNAKE_COLORS)]
    }

    with lock:
        players[player_id] = snake

    try:
        with lock:
            client_socket.send(pickle.dumps((players, apples)))

        while True:
            data = client_socket.recv(4096)
            if not data:
                break

            new_snake = pickle.loads(data)

            with lock:
                players[player_id] = new_snake
                head = new_snake['body'][0]

                for apple in apples:
                    if apple['x'] == head[0] and apple['y'] == head[1]:
                        new_snake['score'] += 1
                        apples.remove(apple)
                        apples.append(generate_apple())
                        new_snake['body'].append(new_snake['body'][-1])
                        break

                game_data = pickle.dumps((players, apples))

            client_socket.send(game_data)

    except Exception as e:
        print(f"Player {player_id} error: {e}")

    finally:
        client_socket.close()
        with lock:
            players[player_id] = None
        print(f"Player {player_id} disconnected")

def start_server():
    global apples
    apples = [generate_apple() for _ in range(3)]

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', PORT))
    server_socket.listen(MAX_PLAYERS)
    print(f"Server listening on port {PORT}")

    while True:
        client_socket, addr = server_socket.accept()
        with lock:
            try:
                player_id = players.index(None)
            except ValueError:
                client_socket.close()
                continue

        threading.Thread(target=handle_client, args=(client_socket, addr, player_id), daemon=True).start()

if __name__ == "__main__":
    start_server()

import pygame
import socket
import pickle
import sys

WIDTH, HEIGHT = 600, 600
SQUARE = 20
FPS = 10
PORT = 5577
SERVER_IP = "10.10.10.70" 

BG_COLOR = (10, 10, 30)
APPLE_COLOR = (220, 20, 60)
TEXT_COLOR = (255, 255, 255)
SNAKE_BORDER_COLOR = (0, 60, 0)

pygame.init()
win = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Multiplayer Snake")
font = pygame.font.Font(None, 24)


def draw_snake(surface, player):
    if not player:
        return
    for i, segment in enumerate(player['body']):
        rect = pygame.Rect(segment[0], segment[1], SQUARE, SQUARE)
        color = player['colors'][i % 2]
        pygame.draw.rect(surface, color, rect)
        pygame.draw.rect(surface, SNAKE_BORDER_COLOR, rect, 2)

def draw_apple(surface, apple):
    pygame.draw.circle(surface, APPLE_COLOR,
                       (apple['x'] + SQUARE // 2, apple['y'] + SQUARE // 2), SQUARE // 2 - 3)

def draw(players, apples):
    win.fill(BG_COLOR)
    for apple in apples:
        draw_apple(win, apple)
    for p in players:
        draw_snake(win, p)
    for i, p in enumerate(players):
        if p:
            score_text = font.render(f"P{i+1} Score: {p['score']}", True, TEXT_COLOR)
            win.blit(score_text, (10, 10 + i * 30))
    pygame.display.update()

def move(snake):
    dir = snake['dir']
    head_x, head_y = snake['body'][0]

    if dir == 'UP': head_y -= SQUARE
    elif dir == 'DOWN': head_y += SQUARE
    elif dir == 'LEFT': head_x -= SQUARE
    elif dir == 'RIGHT': head_x += SQUARE

    head_x %= WIDTH
    head_y %= HEIGHT

    new_head = (head_x, head_y)
    snake['body'].insert(0, new_head)
    snake['body'].pop()

def check_self_collision(snake):
    head = snake['body'][0]
    return head in snake['body'][1:]

def main():
    clock = pygame.time.Clock()
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        client.connect((SERVER_IP, PORT))
    except Exception as e:
        print("Could not connect to server:", e)
        pygame.quit()
        sys.exit()

    try:
        data = client.recv(4096)
        unpacked = pickle.loads(data)

        if not isinstance(unpacked, tuple) or len(unpacked) != 2:
            raise ValueError("Invalid initial data from server")

        players, apples = unpacked
    except Exception as e:
        print("Failed to receive initial data:", e)
        pygame.quit()
        sys.exit()

    player_id = None
    for i, p in enumerate(players):
        if p is not None:
            player_id = i
    if player_id is None:
        print("No player assigned.")
        pygame.quit()
        sys.exit()

    snake = players[player_id]

    running = True
    while running:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP] and snake['dir'] != 'DOWN': snake['dir'] = 'UP'
        elif keys[pygame.K_DOWN] and snake['dir'] != 'UP': snake['dir'] = 'DOWN'
        elif keys[pygame.K_LEFT] and snake['dir'] != 'RIGHT': snake['dir'] = 'LEFT'
        elif keys[pygame.K_RIGHT] and snake['dir'] != 'LEFT': snake['dir'] = 'RIGHT'

        move(snake)

        if check_self_collision(snake):
            print("Game Over: Self Collision")
            running = False
            break

        try:
            client.send(pickle.dumps(snake))
        except:
            break

        try:
            data = client.recv(4096)
            players, apples = pickle.loads(data)
            snake = players[player_id]
            draw(players, apples)
        except:
            break

    pygame.quit()

if __name__ == "__main__":
    main()

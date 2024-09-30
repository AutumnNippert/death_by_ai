import socket
import asyncio
from threading import Thread

import chatgpt_api
import random

# seed random
random.seed()

players = []
currId = 0
responses = {}
is_playing = False

class Player:
    def __init__(self, client_socket):
        global currId
        self.id = currId
        self.client_socket = client_socket
        self.name = 'default_name'
        self.points = 0
        self.listener = None
        currId += 1
    
    def to_string(self):
        return self.name.lower()

def wrap_in_color(message, color):
    return f'\033[{color}m{message}\033[0m'

def send_message(player, message):
    player.client_socket.send(message.encode())

def send_message_to_all(message):
    for player in players:
        player.client_socket.send(message.encode())

def on_player_connect(player):
    print(f'Player connected: {player.id}')
    try:
        player.listener = Thread(target=listen_for_messages, args=(player,))
        player.listener.start()

    except Exception as e:
        print("Error: ", e)
        on_player_disconnect(player)
        return

def get_player_by_name(name):
    for player in players:
        if player.name == name:
            return player
    return None

def on_player_disconnect(player):
    global currId
    print("Player disconnected: ", player.name)
    send_message_to_all(f"{player.name} has left the game!")
    players.remove(player)
    player.client_socket.close()
    currId -= 1


def on_game_start():
    global is_playing
    global responses

    print("Game started")
    send_message_to_all("Game started!")
    is_playing = True
    
    round = 1
    while round <= 5:

        send_message_to_all("------------------------------\n")
        send_message_to_all(f"Round {round}\n")
        round += 1
        
        # get a random player from the list
        random_player = random.choice(players)
        send_message(random_player, "You are the prompter for this round")
        for player in players:
            if player != random_player:
                send_message(player, f"{random_player.name} is the prompter for this round\n")
                send_message(player, 'disable_sending')
        
        # wait for a response from the prompter in the dict
        while random_player not in responses:
            pass

        prompt = responses[random_player]
        responses = {}

        random_player = None

        send_message_to_all('enable_sending\n')

        send_message_to_all(wrap_in_color("Prompt: " + prompt, '31'))
        send_message_to_all("\n")
        send_message_to_all("Respond to the prompt:")

        # while not all players have responded
        while len(responses) < len(players):
            pass

        send_message_to_all("enable_sending")

        print("All responses received... processing")
        send_message_to_all("\nAll responses received... Determining Fate")

        # combine all responses into one message
        message = "\n".join([f"{player.name}: {response}" for player, response in responses.items()])

        res = chatgpt_api.get_fate(prompt, message)

        send_message_to_all(res['message'])
        send_message_to_all('\n')
        send_message_to_all(f"Survivors: {res['survivors']}\n")

        survivors = res['survivors']
        # check if the survivors are players in the game
        get_players = [get_player_by_name(survivor) for survivor in survivors]
        for player in get_players:
            try:
                player.points += 1
            except:
                pass

        # print current points
        send_message_to_all("Current points:")
        for player in players:
            send_message_to_all(f"{player.name}: {player.points}\n")

        prompt = None
        responses = {}

    send_message_to_all("Game over!")
    send_message_to_all("End points:")
    for player in players:
        send_message_to_all(f"{player.name}: {player.points}")
    send_message_to_all(f'Winner: {max(players, key=lambda x: x.points).name}')
    is_playing = False


def accept_connections(server_socket):
    print("Accepting connections on port 1337")
    while True:
        client_socket, address = server_socket.accept()
        print("Connection from: ", address)
        player = Player(client_socket)
        on_player_connect(player)

def receive_message(player):
    global is_playing
    global responses
    msg = player.client_socket.recv(1024).decode()
    if is_playing:
        responses[player] = msg
    return msg
    

def listen_for_messages(player):
            
    # Ask for player name and notify other players
    send_message(player, "Enter your name")
    player.name = receive_message(player)

    print(f"Player {player.name} connected")
    players.append(player)

    # Start listening for messages from this player
    send_message_to_all(f"{player.name} has joined the game!")
    try:
        while True:
            data = receive_message(player)
            if not data:
                break  # Disconnect if no data received
            
            print("Received from player:", data)
            if data == "cmd.start":
                start_game()
            elif data == "cmd.end":
                on_player_disconnect(player)
                break
            else:
                if not is_playing:
                    for p in players:
                        if p != player:
                            send_message(p, f"{player.name}: {data}")
    finally:
        on_player_disconnect(player)

def start_game():
    global is_playing
    is_playing = True
    #calls on_game_start in a thread
    game = Thread(target=on_game_start)
    game.start()


def start_server():
    print("Server started")
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(("0.0.0.0", 1337))
    server_socket.listen(5)

    Thread(target=accept_connections, args=(server_socket,)).run()

if __name__ == "__main__":
    start_server()

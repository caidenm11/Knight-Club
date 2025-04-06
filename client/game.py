# Example file showing a circle moving on screen
import pygame
import random
from client.client import start_client, close_client, send_key, send_object_pickup, send_object_drop, send_chest_drop
import client.client as client_var
from client.mainmenu import main_menu

players = {}
objects = {}
chests = {}
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720

object_list = [1, 2, 3, 4]
screen = pygame.display.set_mode((1280, 720))

class Player:
    def __init__(self, player_id, x=0, y=0, color="red"):
        self.id = player_id        
        self.x = x
        self.y = y
        self.pos = pygame.Vector2(x, y)
        self.color = color  # Placeholder for unique player colors
        self.inventory = []  # List of held object IDs
        
    def draw(self, screen):
        pygame.draw.circle(screen, self.color, self.pos, 40)


class GameObject(pygame.sprite.Sprite):
    def __init__(self, object_id, x, y, armor_type):  # Placeholder for object visuals
        super().__init__()
        self.id = object_id
        self.pos = pygame.Vector2(x, y)
        self.armor_type = armor_type
        self.image = pygame.image.load(f"resources/{armor_type}.png")
        self.image = pygame.transform.scale(self.image, (50, 50))
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.held_by = None  # None means it's on the ground


class Chest:
    def __init__(self, object_id, x, y, color="yellow"):  # Placeholder for object visuals
        self.id = object_id
        self.pos = pygame.Vector2(x, y)
        self.color = color
        self.image = pygame.image.load("resources/chest.png")
        self.image = pygame.transform.scale(self.image, (100, 100))
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.held_by = None  # None means it's on the ground
        self.stored_items = {}  # Dictionary to hold items in the chest

    # def draw(self, screen):
    #     pygame.draw.rect(screen, self.color, (self.pos.x - 20, self.pos.y - 20, 40, 40))  # Draw square object

def run_main_menu_screen(host="0.0.0.0", port=53333):
    global players
    global objects

    main_menu()
    
def start_game(host="0.0.0.0", port=53333):
    global players, objects

    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Knight Club")

    clock = pygame.time.Clock()

    try:
        start_client(host, port)
    except Exception as e:
        print(f"❌ Failed to connect to server at {host}:{port}: {e}")
        return

    players = {i: Player(i, screen.get_width() / 2, screen.get_height() / 2) for i in range(4)}

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()
        movement = ""
        if keys[pygame.K_w]: movement += "w"
        if keys[pygame.K_s]: movement += "s"
        if keys[pygame.K_a]: movement += "a"
        if keys[pygame.K_d]: movement += "d"
        if movement:
            send_key(movement)

        screen.fill("purple")
        for player in players.values():
            player.draw(screen)

        pygame.display.flip()
        clock.tick(60)

    close_client()
    pygame.quit()


def run_main_menu(host="0.0.0.0", port=53333):
    # 🛠️ Change this to your server's IP if running over Wi-Fi or LAN

    # pygame setup
    global players
    global objects
    # pygame.init()
    # screen = pygame.display.set_mode((1280, 720))
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    # Start the main menu
    main_menu()
    # Fill the screen black to start this screen

    global chests
    pygame.init()
    
    clock = pygame.time.Clock()

    # Try to connect
    try:
        start_client(host)
    except Exception as e:
        print(f"❌ Failed to connect to server at {host}: {e}")
        # pygame.quit()
        return
    running = True
    dt = 0


    players = {i: Player(i, screen.get_width() / 2, screen.get_height() / 2) for i in range(4)} 
    # putting the chests in the 4 corners of the screen
    chests = {i: Chest(i, 0 if i % 2 == 0 else screen.get_width() - 100, 0 if i < 2 else screen.get_height() - 100) for i in range(4)}

    while running:
        # poll for events
        # pygame.QUIT event means the user clicked X to close your window
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # fill the screen with a color to wipe away anything from last frame
        screen.fill("light blue")

        for player in players.values():
            player.draw(screen)

        for chest in chests.values():
            screen.blit(chest.image, chest.rect.topleft)

        keys = pygame.key.get_pressed()
        movement = ""

        if keys[pygame.K_w]:
            movement += "w"
        if keys[pygame.K_s]:
            movement += "s"
        if keys[pygame.K_a]:
            movement += "a"
        if keys[pygame.K_d]:
            movement += "d"
        if keys[pygame.K_q]:
            local_player = players.get(int(client_var.player_id))
            if local_player and len(local_player.inventory) > 0:
                dropped_item = local_player.inventory.pop(0)
                dropped_item.held_by = None
                send_object_drop(dropped_item.id)
                print(f"Player {local_player.id} dropped item {dropped_item.id}")

        if movement:  # Only send if there's a movement command
            send_key(movement)

        # --- Check if dropped items land in a chest ---
        for chest in chests.values():
            for obj in list(objects.values()):  # use list to avoid dict size change error
                if obj.held_by is None and chest.rect.colliderect(obj.rect):
                    if obj.id not in chest.stored_items:
                        chest.stored_items[obj.id] = obj

                        print(f"Item {obj.id} collected in chest {chest.id}")

                        # Remove object from world
                        del objects[obj.id]

                        # # (Optional) Tell the server to despawn the item
                        # despawn_packet = ServerPacketMaker(ServerPacketType.DESPAWN_ITEM, object_id=obj.id)
                        # client_var.client_socket.send(despawn_packet.encode())

                        send_chest_drop(chest.id, obj.id) 

                        # (Optional) Check for win condition:
                        collected_types = {o.armor_type for o in chest.stored_items.values()}
                        if collected_types == {1, 2, 3, 4}:
                            print(f" Player {chest.id} wins! Collected all armor types!")

        
        # collision detection for player touching an object
        for player in players.values():
            player_rect = pygame.Rect(player.pos.x - 40, player.pos.y - 40, 40 * 2, 40 * 2)

            # check if player had collided with any game objects
            # if so, have the player pick it up
            for object in objects.values():
                if object.held_by is None and player_rect.colliderect(object.rect):
                    print(f"Player Picked up: {object}") # for debugging
                    player.inventory.append(object)
                    print(player.inventory[0])
                    object.held_by = player.id
                    # send that an object has been picked up
                    send_object_pickup(object.id)
                  

        for player in players.values():
            if len(player.inventory) > 0:
                player.inventory[0].rect.center = (player.pos.x - 40, player.pos.y - 50)

        for obj in objects.values():
            if obj.held_by is not None:
                obj.rect.topleft = (players[obj.held_by].pos.x, players[obj.held_by].pos.y - 50)

        for obj in objects.values():
            screen.blit(obj.image, obj.rect.topleft)

        # flip() the display to put your work on screen
        pygame.display.flip()

        # limits FPS to 60
        # dt is delta time in seconds since last frame, used for framerate-
        # independent physics.
        dt = clock.tick(60) / 1000

    close_client()
    pygame.quit()

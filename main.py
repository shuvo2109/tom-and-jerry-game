import pygame
import numpy as np
import time
from TomAndJerry2PlayerMDP import TomAndJerry2PlayerMDP

########### DEFINES ##################
# board size in tiles
SCREEN_HEIGHT_IN_TILES = 5
SCREEN_WIDTH_IN_TILES = 5
BOARD_DIMENSIONS = (SCREEN_WIDTH_IN_TILES, SCREEN_HEIGHT_IN_TILES)

# board size in pixels
TILE_HEIGHT = 70
TILE_WIDTH = 70
MENU_HEIGHT = 50
SCREEN_HEIGHT = SCREEN_HEIGHT_IN_TILES * TILE_HEIGHT + MENU_HEIGHT
SCREEN_WIDTH = SCREEN_WIDTH_IN_TILES * TILE_WIDTH

# colors
TILE_COLOR = (240, 240, 240)
BORDER_COLOR = (200, 200, 200)
TOM_COLOR = (50,90,150)
JERRY_COLOR = (150,100,26)
TRAP_COLOR = "red"
CHEESE_COLOR = (230, 195, 60)

############### HELPER FUNCTIONS FOR DRAWING STUFF USING PYGAME #########################
def DrawTiles(screen):
    for x in range(0, SCREEN_WIDTH_IN_TILES):
        for y in range(0,SCREEN_HEIGHT_IN_TILES):
            tile = pygame.Rect(x*TILE_WIDTH, y*TILE_HEIGHT, TILE_WIDTH, TILE_HEIGHT)
            pygame.draw.rect(screen, BORDER_COLOR, tile, 2)

def DrawTilesColor(screen, tiles, color):
    for t in tiles:
            tile = pygame.Rect(t[0]*TILE_WIDTH, t[1]*TILE_HEIGHT, TILE_WIDTH, TILE_HEIGHT)
            pygame.draw.rect(screen, color, tile, 8)

def DrawTraps(screen, traps):
    for (x,y) in traps:
        pygame.draw.circle(screen, TRAP_COLOR, (x*TILE_WIDTH + TILE_WIDTH / 2, y*TILE_HEIGHT + TILE_HEIGHT/2), TILE_HEIGHT/2 - 10)

def DrawCheese(screen, cheese):
    for (x,y) in cheese:
        pygame.draw.circle(screen, CHEESE_COLOR, (x*TILE_WIDTH + TILE_WIDTH / 2, y*TILE_HEIGHT + TILE_HEIGHT/2), TILE_HEIGHT/2 - 10)

def DrawTom(screen, tom_pos):
    x = tom_pos[0]
    y = tom_pos[1]
    pygame.draw.circle(screen, TOM_COLOR, (x*TILE_WIDTH + TILE_WIDTH / 2, y*TILE_HEIGHT + TILE_HEIGHT/2), TILE_HEIGHT/2 - 15)

def DrawJerry(screen, jerry_pos):
    x = jerry_pos[0]
    y = jerry_pos[1]
    pygame.draw.circle(screen, JERRY_COLOR, (x*TILE_WIDTH + TILE_WIDTH / 2, y*TILE_HEIGHT + TILE_HEIGHT/2), TILE_HEIGHT/2 - 15)

def DrawJerryPath(screen, path):
    for (x,y) in list(path)[1:-1]:
        pygame.draw.circle(screen, JERRY_COLOR, (x*TILE_WIDTH + TILE_WIDTH / 2, y*TILE_HEIGHT + TILE_HEIGHT/2), TILE_HEIGHT/8)

def DrawTomPath(screen, path):
    for (x,y) in list(path)[1:-1]:
        pygame.draw.circle(screen, TOM_COLOR, (x*TILE_WIDTH + TILE_WIDTH / 2, y*TILE_HEIGHT + TILE_HEIGHT/2), TILE_HEIGHT/8)

######################## MAIN ##########################################
if __name__=="__main__":
    # Pygame Setup
    pygame.init()
    pygame.display.set_caption("MDP - Space: step, R: restart")
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()
    font = pygame.font.Font('freesansbold.ttf', 20)
    running = True

    # Board Setup
    jerry_init_pos = (0,2)
    tom_init_pos = (4,2)
    trap_pos = [(2,1), (2,2)]
    cheese_pos = [(4, 0), (4,4)]

    starttime = time.perf_counter()
    board = TomAndJerry2PlayerMDP(BOARD_DIMENSIONS, jerry_init_pos, tom_init_pos)
    print("Generated mdp in:", time.perf_counter() - starttime, "seconds.")
    board.SetTraps(trap_pos)
    board.SetCheese(cheese_pos)
    starttime = time.perf_counter()
    board.ComputeWins()
    print("Calculated policy in:", time.perf_counter() - starttime, "seconds.")

    # Game Loop
    while running:
        # poll for events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                
                if event.key == pygame.K_r:
                    starttime = time.perf_counter()
                    board = TomAndJerry2PlayerMDP(BOARD_DIMENSIONS, jerry_init_pos, tom_init_pos)
                    print("Generated mdp in:", time.perf_counter() - starttime, "seconds.")
                    board.SetTraps(trap_pos)
                    board.SetCheese(cheese_pos)
                    starttime = time.perf_counter()
                    board.ComputeWins()
                    print("Calculated policy in:", time.perf_counter() - starttime, "seconds.")
                    
                if event.key == pygame.K_SPACE:
                    if not board.jerry_won and not board.tom_won:
                        jerry_won = board.Update()

        # fill the screen with a color to wipe away anything from last frame
        screen.fill(TILE_COLOR)

        # Render the screen
        DrawTiles(screen)
        DrawTraps(screen, board.trap_locations)
        DrawCheese(screen, board.cheese_locations)

        DrawJerry(screen, board.jerry_state)
        DrawTom(screen, board.tom_state)

        # draw bottom text
        policy_text = font.render("J Used: "+board.jerry_using_policy, True, "black")
        policy_text_rect = policy_text.get_rect()
        policy_text_rect.topleft = (5, SCREEN_HEIGHT_IN_TILES*TILE_HEIGHT + 5)
        screen.blit(policy_text, policy_text_rect)

        policy_text = font.render("T Used: "+board.tom_using_policy, True, "black")
        policy_text_rect = policy_text.get_rect()
        policy_text_rect.topleft = (5, SCREEN_HEIGHT_IN_TILES*TILE_HEIGHT + 30)
        screen.blit(policy_text, policy_text_rect)
        
        win_string = ""
        if board.tom_won == True:
            win_string = "Tom won"
        if board.jerry_won == True: 
            win_string = "Jerry won"
        win_text = font.render(win_string, True, "black")
        win_text_rect = win_text.get_rect()
        win_text_rect.topright = (SCREEN_WIDTH - 5, SCREEN_HEIGHT_IN_TILES*TILE_HEIGHT + 5)
        screen.blit(win_text, win_text_rect)

        # flip buffers to output to screen
        pygame.display.flip()

        clock.tick(60)  # limits FPS to 60

    pygame.quit()


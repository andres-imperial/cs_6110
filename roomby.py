# Wormy (a Nibbles clone)
# By Al Sweigart al@inventwithpython.com
# http://inventwithpython.com/pygame
# Released under a "Simplified BSD" license

import random, pygame, sys,math
from pygame.locals import *

FPS = 5
WINDOWWIDTH = 800
WINDOWHEIGHT = 600
CELLSIZE = 20
RADIUS = math.floor(CELLSIZE/2.5)
assert WINDOWWIDTH % CELLSIZE == 0, "Window width must be a multiple of cell size."
assert WINDOWHEIGHT % CELLSIZE == 0, "Window height must be a multiple of cell size."
CELLWIDTH = int(WINDOWWIDTH / CELLSIZE)
CELLHEIGHT = int(WINDOWHEIGHT / CELLSIZE)

#             R    G    B
WHITE     = (255, 255, 255)
BLACK     = (  0,   0,   0)
RED       = (255,   0,   0)
GREEN     = (  0, 255,   0)
BLUE     = (  0,   0, 255)
DARKGREEN = (  0, 155,   0)
DARKGRAY  = ( 40,  40,  40)
GRAY  =    ( 192, 192, 192)
YELLOW =   ( 255, 255,   0)
BROWN =( 160,  82,  45)
DARKBROWN =( 139,  69,  19)
BGCOLOR = BLACK

UP = 'up'
DOWN = 'down'
LEFT = 'left'
RIGHT = 'right'

HEAD = 0 # syntactic sugar: index of the worm's head

class Robot:
    def __init__(self, direction, position):
        self.direction = direction
        self.position = position

def main():
    global FPSCLOCK, DISPLAYSURF, BASICFONT

    pygame.init()
    FPSCLOCK = pygame.time.Clock()
    DISPLAYSURF = pygame.display.set_mode((WINDOWWIDTH, WINDOWHEIGHT))
    BASICFONT = pygame.font.Font('freesansbold.ttf', 18)
    pygame.display.set_caption('Roomby')

    showStartScreen()
    while True:
        runGame()
        showGameOverScreen()

def runGame():
    # init room
    staticObjs, barriers, dropOff, furniture, dirtSet, dirtSquares, superDirtSquares, dogs, robots = initGame()

    counter = 0
    while True: # main game loop
        counter += 1
        print(counter)
        if counter > 100:
            showGameOverScreen(len(dirtSet))
            staticObjs, barriers, dropOff, furniture, dirtSet, dirtSquares, superDirtSquares, dogs, robots = initGame()
            counter = 0
        for event in pygame.event.get(): # event handling loop
            if event.type == QUIT:
                terminate()
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    terminate()

        newdogs = []
        for dog in dogs:
            applicablebarriers = staticObjs.copy()
            for coord in dogs:
                if coord == dog:
                    continue
                x = coord['x']
                y = coord['y']
                applicablebarriers.add((x, y))
            for i in range(len(robots)):
                temp = robots[i].position
                applicablebarriers.add((temp['x'], temp['y']))
            newdogs.append(getRandomStep(dog, applicablebarriers))
        dogs = newdogs

        for i in range(len(robots)):
            robotDir = robots[i].direction
            robotPos = robots[i].position

            # check for dirt collisions
            applicablebarriers = barriers.copy()
            for coord in dogs:
                x = coord['x']
                y = coord['y']
                applicablebarriers.add((x, y))
            for j in range(1,len(robots)):
                temp = robots[(i + j)%len(robots)].position
                applicablebarriers.add((temp['x'], temp['y']))

            if (robotPos['x'], robotPos['y']) in dirtSet:
                if robotPos in dirtSquares:
                    dirtSquares.remove(robotPos)
                    dirtSet.remove((robotPos['x'], robotPos['y']))
                    staticObjs.remove((robotPos['x'], robotPos['y']))
                    robotPos, robotDir = getRobotStep(robotPos, robotDir, applicablebarriers, dirtSet)
                elif robotPos in superDirtSquares:
                    superDirtSquares.remove(robotPos)
                    dirtSquares.append(robotPos)
            else:
                # choose direction to go
                robotPos, robotDir = getRobotStep(robotPos, robotDir, applicablebarriers, dirtSet)

            robots[i] = Robot(robotDir, robotPos)

        DISPLAYSURF.fill(BGCOLOR)
        drawGrid()
        for dirt in dirtSquares:
            drawDirt(dirt)
        for dirt in superDirtSquares:
            drawSuperDirt(dirt)
        for obj in furniture:
            drawFurniture(obj)
        drawDrop(dropOff)
        for dog in dogs:
            drawdog(dog)
        for robot in robots:
            drawRobot(robot)

        pygame.display.update()
        FPSCLOCK.tick(FPS)


def initGame():
    # static obstacles
    staticObjs = set()
    barriers = set()
    # Drop off
    dropOff = createDropOff()
    for coord in dropOff:
        x = coord['x']
        y = coord['y']
        barriers.add((x, y))

    # variable edges
    furniture = []
    for i in range(2):
        furniture.append(getRandEdges())
    for piece in furniture:
        for coord in piece:
            x = coord['x']
            y = coord['y']
            barriers.add((x,y))

    for i in range(5):
        furniture.append(createFurniture(barriers))
    for piece in furniture:
        for coord in piece:
            x = coord['x']
            y = coord['y']
            barriers.add((x,y))

    staticObjs.update(barriers)
    # Dirt
    dirtSet = set()
    dirtSquares = []
    for i in range(0,50):
        randLoc = getRandomLocation()
        while (randLoc['x'], randLoc['y']) in staticObjs:
            randLoc = getRandomLocation()
        dirtSquares.append(randLoc)
    for coord in dirtSquares:
        x = coord['x']
        y = coord['y']
        dirtSet.add((x, y))

    superDirtSquares = []
    for i in range(0,50):
        randLoc = getRandomLocation()
        while (randLoc['x'], randLoc['y']) in staticObjs:
            randLoc = getRandomLocation()
        superDirtSquares.append(randLoc)
    for coord in superDirtSquares:
        x = coord['x']
        y = coord['y']
        dirtSet.add((x, y))

    staticObjs.update(dirtSet)
    # moving obstacles
    dogs = []
    for i in range(0,15):
        randLoc = getRandomLocation()
        while (randLoc['x'], randLoc['y']) in staticObjs:
            randLoc = getRandomLocation()
        dogs.append(randLoc)

    # Create robots
    robots = []
    for i in range(3):
        randLoc = getRandomLocation()
        while (randLoc['x'], randLoc['y']) in staticObjs:
            randLoc = getRandomLocation()
        robots.append(Robot(UP,randLoc))

    return staticObjs, barriers, dropOff, furniture, dirtSet, dirtSquares, superDirtSquares, dogs, robots

def createFurniture(staticObjs):
    furniture = []
    start = getRandomLocation()
    while (start['x'], start['y']) in staticObjs:
        start = getRandomLocation()
    furniture.append(start)
    furniture.append({'x': start['x'] + 1, 'y': start['y'] + 1})
    furniture.append({'x': start['x'] + 1, 'y': start['y'] - 1})
    furniture.append({'x': start['x'] - 1, 'y': start['y'] + 1})
    furniture.append({'x': start['x'] - 1, 'y': start['y'] - 1})

    return furniture

def drawPressKeyMsg():
    pressKeySurf = BASICFONT.render('Press a key to play.', True, YELLOW)
    pressKeyRect = pressKeySurf.get_rect()
    pressKeyRect.topleft = (WINDOWWIDTH - 200, WINDOWHEIGHT - 30)
    DISPLAYSURF.blit(pressKeySurf, pressKeyRect)

def checkForKeyPress():
    if len(pygame.event.get(QUIT)) > 0:
        terminate()

    keyUpEvents = pygame.event.get(KEYUP)
    if len(keyUpEvents) == 0:
        return None
    if keyUpEvents[0].key == K_ESCAPE:
        terminate()
    return keyUpEvents[0].key

def showStartScreen():
    titleFont = pygame.font.Font('freesansbold.ttf', 100)
    titleSurf1 = titleFont.render('Roomby', True, YELLOW, WHITE)
    titleSurf2 = titleFont.render('Roomby', True, RED)

    degrees1 = 0
    degrees2 = 0
    while True:
        DISPLAYSURF.fill(BGCOLOR)
        rotatedSurf1 = pygame.transform.rotate(titleSurf1, degrees1)
        rotatedRect1 = rotatedSurf1.get_rect()
        rotatedRect1.center = (math.floor(WINDOWWIDTH / 2), math.floor(WINDOWHEIGHT / 2))
        DISPLAYSURF.blit(rotatedSurf1, rotatedRect1)

        rotatedSurf2 = pygame.transform.rotate(titleSurf2, degrees2)
        rotatedRect2 = rotatedSurf2.get_rect()
        rotatedRect2.center = (math.floor(WINDOWWIDTH / 2), math.floor(WINDOWHEIGHT / 2))
        DISPLAYSURF.blit(rotatedSurf2, rotatedRect2)

        drawPressKeyMsg()

        if checkForKeyPress():
            pygame.event.get() # clear event queue
            return
        pygame.display.update()
        FPSCLOCK.tick(FPS)
        degrees1 += 3 # rotate by 3 degrees each frame
        degrees2 += 7 # rotate by 7 degrees each frame

def terminate():
    pygame.quit()
    sys.exit()

def getRandomLocation():
    return {'x': random.randint(0, CELLWIDTH - 1), 'y': random.randint(0, CELLHEIGHT - 1)}

def dirtNear(pos, dirtSet):
    x = pos['x']
    y = pos['y']

    if (x + 1, y) in dirtSet:
        pos['x'] += 1
    elif (x - 1, y) in dirtSet:
        pos['x'] -= 1
    elif (x, y + 1) in dirtSet:
        pos['y'] += 1
    elif (x, y - 1) in dirtSet:
        pos['y'] -= 1
    else:
        return None

    return pos

def getRobotStep(robotPos, direction, barriers, dirtSet):
    near = dirtNear(robotPos, dirtSet)
    if near:
        return near, direction
    else:
        robotPos, direction = getPreferedStep(robotPos, direction, barriers)

    return robotPos, direction

def getPreferedStep(object, direction, staticObjs):
    randDir = random.randint(0, 8)
    temp = object.copy()
    if randDir == 0:
        object['x'] += 1
        direction = RIGHT
    elif randDir == 1:
        object['x'] -= 1
        direction = LEFT
    elif randDir == 2:
        object['y'] += 1
        direction = DOWN
    elif randDir == 3:
        object['y'] -= 1
        direction = UP
    else:
        if direction == RIGHT:
            object['x'] += 1
        if direction == LEFT:
            object['x'] -= 1
        if direction == DOWN:
            object['y'] += 1
        if direction == UP:
            object['y'] -= 1


    while (object['x'], object['y']) in staticObjs or object['x'] < 0 or object['y'] < 0 or object['y'] > CELLHEIGHT - 1:
        randDir = (randDir + 1) % 4
        object = temp.copy()
        if randDir == 0:
            object['x'] += 1
            direction = RIGHT
        elif randDir == 1:
            object['x'] -= 1
            direction = LEFT
        elif randDir == 2:
            object['y'] += 1
            direction = DOWN
        elif randDir == 3:
            object['y'] -= 1
            direction = UP

    return object, direction

def getRandomStep(object, staticObjs):
    randDir = random.randint(0, 4)
    temp = object.copy()
    if randDir == 0:
        object['x'] += 1
    elif randDir == 1:
        object['x'] -= 1
    elif randDir == 2:
        object['y'] += 1
    elif randDir == 3:
        object['y'] -= 1

    counter = 0
    while (object['x'], object['y']) in staticObjs or object['x'] < 0 or object['y'] < 0 or object['y'] > CELLHEIGHT - 1:
        counter += 1
        if counter > 4:
            return temp.copy()
        randDir = (randDir + 1) % 4
        object = temp.copy()
        if randDir == 0:
            object['x'] += 1
        elif randDir == 1:
            object['x'] -= 1
        elif randDir == 2:
            object['y'] += 1
        elif randDir == 3:
            object['y'] -= 1

    return object

def getRandEdges():
    start = getRandomLocation()
    while start['x'] > 10:
        start = getRandomLocation()

    edges = []
    x = start['x']
    y = start['y']
    for i in range(x):
        for j in range(y):
            edges.append({'x': i, 'y': j})

    return edges

def showGameOverScreen(score):
    gameOverFont = pygame.font.Font('freesansbold.ttf', 150)
    gameSurf = gameOverFont.render('Game', True, WHITE)
    overSurf = gameOverFont.render('Over', True, WHITE)
    scoreSurf = gameOverFont.render('Score: ' + str(100 - score), True, WHITE)
    gameRect = gameSurf.get_rect()
    overRect = overSurf.get_rect()
    scoreRect = scoreSurf.get_rect()
    gameRect.midtop = (math.floor(WINDOWWIDTH / 2), 10)
    overRect.midtop = (math.floor(WINDOWWIDTH / 2), gameRect.height + 10 + 25)
    scoreRect.midtop = (math.floor(WINDOWWIDTH / 2), gameRect.height + overRect.height + 10 + 25)

    DISPLAYSURF.blit(gameSurf, gameRect)
    DISPLAYSURF.blit(overSurf, overRect)
    DISPLAYSURF.blit(scoreSurf, scoreRect)
    drawPressKeyMsg()
    pygame.display.update()
    pygame.time.wait(500)
    checkForKeyPress() # clear out any key presses in the event queue

    while True:
        if checkForKeyPress():
            pygame.event.get() # clear event queue
            return

def drawRobot(robot):
    xcenter = robot.position["x"] * CELLSIZE + math.floor(CELLSIZE/2)
    ycenter = robot.position["y"] * CELLSIZE+ math.floor(CELLSIZE/2)
    pygame.draw.circle(DISPLAYSURF, GREEN,(int(xcenter),int(ycenter)),int(RADIUS))

def drawScore(score, COLOR):
    scoreSurf = BASICFONT.render('Score: %s' % (score), True, COLOR)
    scoreRect = scoreSurf.get_rect()
    if (COLOR == GREEN):
        scoreRect.topleft = (WINDOWWIDTH - 120, 10)
    else:
        scoreRect.topleft = (10, 10)
    DISPLAYSURF.blit(scoreSurf, scoreRect)

def drawDrop(drop):
    for coord in drop:
        x = coord['x'] * CELLSIZE
        y = coord['y'] * CELLSIZE
        square = pygame.Rect(x, y, CELLSIZE, CELLSIZE)
        pygame.draw.rect(DISPLAYSURF, BLACK, square)

def drawFurniture(piece):
    for coord in piece:
        x = coord['x'] * CELLSIZE
        y = coord['y'] * CELLSIZE
        part = pygame.Rect(x, y, CELLSIZE, CELLSIZE)
        pygame.draw.rect(DISPLAYSURF, WHITE, part)
        innerPart = pygame.Rect(x + 4, y + 4, CELLSIZE - 8, CELLSIZE - 8)
        pygame.draw.rect(DISPLAYSURF, GRAY, innerPart)

def drawDirt(dirt):
        x = dirt['x'] * CELLSIZE
        y = dirt['y'] * CELLSIZE
        part = pygame.Rect(x, y, CELLSIZE, CELLSIZE)
        pygame.draw.rect(DISPLAYSURF, DARKBROWN, part)
        innerPart = pygame.Rect(x + 4, y + 4, CELLSIZE - 8, CELLSIZE - 8)
        pygame.draw.rect(DISPLAYSURF, BROWN, innerPart)

def drawSuperDirt(dirt):
    x = dirt['x'] * CELLSIZE
    y = dirt['y'] * CELLSIZE
    part = pygame.Rect(x, y, CELLSIZE, CELLSIZE)
    pygame.draw.rect(DISPLAYSURF, GRAY, part)
    innerPart = pygame.Rect(x + 4, y + 4, CELLSIZE - 8, CELLSIZE - 8)
    pygame.draw.rect(DISPLAYSURF, DARKBROWN, innerPart)

def drawdog(coord):
    x = coord['x'] * CELLSIZE
    y = coord['y'] * CELLSIZE
    xcenter = coord['x'] * CELLSIZE + math.floor(CELLSIZE/2)
    ycenter = coord['y'] * CELLSIZE+ math.floor(CELLSIZE/2)
    pygame.draw.circle(DISPLAYSURF, RED,(int(xcenter),int(ycenter)),int(RADIUS))

def drawGrid():
    for x in range(0, WINDOWWIDTH, CELLSIZE): # draw vertical lines
        pygame.draw.line(DISPLAYSURF, DARKGRAY, (x, 0), (x, WINDOWHEIGHT))
    for y in range(0, WINDOWHEIGHT, CELLSIZE): # draw horizontal lines
        pygame.draw.line(DISPLAYSURF, DARKGRAY, (0, y), (WINDOWWIDTH, y))

def createDropOff():
    drop = []
    start = random.randint(5, 20)
    for x in range(CELLWIDTH - start, CELLWIDTH):
        for y in range(CELLHEIGHT):
            drop.append({'x': x, 'y': y})

    return drop


if __name__ == '__main__':
    main()

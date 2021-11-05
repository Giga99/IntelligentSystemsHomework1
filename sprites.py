import pygame
import os
import config
from collections import deque
from anytree import Node, findall, RenderTree
import numpy as np


class BaseSprite(pygame.sprite.Sprite):
    images = dict()

    def __init__(self, row, col, file_name, transparent_color=None):
        pygame.sprite.Sprite.__init__(self)
        if file_name in BaseSprite.images:
            self.image = BaseSprite.images[file_name]
        else:
            self.image = pygame.image.load(os.path.join(config.IMG_FOLDER, file_name)).convert()
            self.image = pygame.transform.scale(self.image, (config.TILE_SIZE, config.TILE_SIZE))
            BaseSprite.images[file_name] = self.image
        # making the image transparent (if needed)
        if transparent_color:
            self.image.set_colorkey(transparent_color)
        self.rect = self.image.get_rect()
        self.rect.topleft = (col * config.TILE_SIZE, row * config.TILE_SIZE)
        self.row = row
        self.col = col


class Agent(BaseSprite):
    def __init__(self, row, col, file_name):
        super(Agent, self).__init__(row, col, file_name, config.DARK_GREEN)

    def move_towards(self, row, col):
        row = row - self.row
        col = col - self.col
        self.rect.x += col
        self.rect.y += row

    def place_to(self, row, col):
        self.row = row
        self.col = col
        self.rect.x = col * config.TILE_SIZE
        self.rect.y = row * config.TILE_SIZE

    def get_neighbours(self, row, col, game_map, visited):
        neighbours = []

        if 0 <= row - 1 and game_map[row - 1][col] not in visited:
            neighbours.append(game_map[row - 1][col])
        if col + 1 < len(game_map[row]) and game_map[row][col + 1] not in visited:
            neighbours.append(game_map[row][col + 1])
        if row + 1 < len(game_map) and game_map[row + 1][col] not in visited:
            neighbours.append(game_map[row + 1][col])
        if 0 <= col - 1 and game_map[row][col - 1] not in visited:
            neighbours.append(game_map[row][col - 1])

        return neighbours

    # game_map - list of lists of elements of type Tile
    # goal - (row, col)
    # return value - list of elements of type Tile
    def get_agent_path(self, game_map, goal):
        pass


class ExampleAgent(Agent):
    def __init__(self, row, col, file_name):
        super().__init__(row, col, file_name)

    def get_agent_path(self, game_map, goal):
        path = [game_map[self.row][self.col]]

        row = self.row
        col = self.col
        while True:
            if row != goal[0]:
                row = row + 1 if row < goal[0] else row - 1
            elif col != goal[1]:
                col = col + 1 if col < goal[1] else col - 1
            else:
                break
            path.append(game_map[row][col])
        return path


class Aki(Agent):
    def __init__(self, row, col, file_name):
        super().__init__(row, col, file_name)

    def get_agent_path(self, game_map, goal):
        path = [game_map[self.row][self.col]]

        row = self.row
        col = self.col
        visited = [game_map[row][col]]
        last_path = None
        while True:
            if row == goal[0] and col == goal[1]:
                break

            neighbours = self.get_neighbours(row, col, game_map, visited)

            if len(neighbours) == 0:
                last_path = path.pop()
                row, col = last_path.position()
                continue

            if last_path is not None:
                path.append(last_path)
                last_path = None
                continue

            min = 1001
            minTile = None
            for tile in neighbours:
                if tile.cost() < min:
                    min = tile.cost()
                    minTile = tile

            row, col = minTile.position()
            path.append(minTile)
            visited.append(minTile)

        return path


class Jocke(Agent):
    def __init__(self, row, col, file_name):
        super().__init__(row, col, file_name)

    def get_agent_path(self, game_map, goal):
        first = game_map[self.row][self.col]
        root = Node(str(first.position()))
        path = [first]

        row = self.row
        col = self.col
        visited = [first]
        queue = deque()

        current_neighbours = self.get_neighbours(row, col, game_map, visited)
        cost_averages = []
        for tile in current_neighbours:
            average = self.get_neighbours_average_cost(game_map, tile)
            cost_averages.append({'tile': tile, 'average': average})
        cost_averages.sort(key=lambda key: key['average'])

        for t in cost_averages:
            Node(str(t['tile'].position()), parent=root)
            queue.append(t['tile'])

        current_node = None
        while True:
            curr = queue.popleft()
            current_node = findall(root, filter_=lambda node: node.name == str(curr.position()))[0]
            row, col = curr.position()

            if row == goal[0] and col == goal[1]:
                break

            visited.append(game_map[row][col])
            current_neighbours = self.get_neighbours(row, col, game_map, visited)

            cost_averages = []
            for tile in current_neighbours:
                average = self.get_neighbours_average_cost(game_map, tile)
                cost_averages.append({'tile': tile, 'average': average})
            cost_averages.sort(key=lambda key: key['average'])

            for t in cost_averages:
                Node(str(t['tile'].position()), parent=current_node)
                queue.append(t['tile'])

        skip_first = True
        for anc in current_node.ancestors:
            if skip_first:
                skip_first = False
                continue
            temp = anc.name.split("/")
            positions = [int(s) for s in temp[len(temp) - 1] if s.isdigit()]
            tile = game_map[positions[0]][positions[1]]
            path.append(tile)

        temp = current_node.name.split("/")
        positions = [int(s) for s in temp[len(temp) - 1] if s.isdigit()]
        tile = game_map[positions[0]][positions[1]]
        path.append(tile)

        return path

    def get_neighbours_average_cost(self, game_map, current_tile):
        neighbours = self.get_neighbours(current_tile.row, current_tile.col, game_map, [])
        sum = 0
        for tile in neighbours:
            sum += tile.cost()
        return sum // len(neighbours)


class Draza(Agent):
    def __init__(self, row, col, file_name):
        super().__init__(row, col, file_name)

    def get_agent_path(self, game_map, goal):
        first = game_map[self.row][self.col]
        root = Node(str(first.position()))
        path = [first]

        row = self.row
        col = self.col
        visited = [first]
        queue = []

        current_neighbours = self.get_neighbours(row, col, game_map, visited)
        for t in current_neighbours:
            Node(str(t.position()), parent=root)
            queue.append({"tile": t, "cost": t.cost()})
        queue.sort(key=lambda key: key["cost"])

        current_node = None
        final_node = None
        final_node_cost = None
        while True:
            curr = queue.pop(0)
            current_node = findall(root, filter_=lambda node: node.name == str(curr["tile"].position()))[0]
            row, col = curr["tile"].position()

            if row == goal[0] and col == goal[1]:
                if final_node_cost is None or curr["cost"] < final_node_cost:
                    final_node = findall(root, filter_=lambda node: node.name == str(curr["tile"].position()))[0]
                    final_node_cost = curr["cost"]

            visited.append(game_map[row][col])
            current_neighbours = self.get_neighbours(row, col, game_map, visited)
            for t in current_neighbours:
                Node(str(t.position()), parent=current_node)
                queue.append({"tile": t, "cost": (t.cost() + curr["cost"])})
            queue.sort(key=lambda key: key["cost"])

            if len(queue) == 0:
                break

        skip_first = True
        for anc in final_node.ancestors:
            if skip_first:
                skip_first = False
                continue
            temp = anc.name.split("/")
            positions = [int(s) for s in temp[len(temp) - 1] if s.isdigit()]
            tile = game_map[positions[0]][positions[1]]
            path.append(tile)

        temp = final_node.name.split("/")
        positions = [int(s) for s in temp[len(temp) - 1] if s.isdigit()]
        tile = game_map[positions[0]][positions[1]]
        path.append(tile)

        return path


class Bole(Agent):
    def __init__(self, row, col, file_name):
        super().__init__(row, col, file_name)

    def get_agent_path(self, game_map, goal):
        first = game_map[self.row][self.col]
        root = Node(str(first.position()))
        path = [first]

        row = self.row
        col = self.col
        visited = [first]
        queue = []

        current_neighbours = self.get_neighbours(row, col, game_map, visited)
        for t in current_neighbours:
            Node(str(t.position()), parent=root)
            queue.append({"tile": t, "cost": (t.cost() + self.get_tile_heuristics(t, goal))})
        queue.sort(key=lambda key: key["cost"])

        current_node = None
        final_node = None
        final_node_cost = None
        while True:
            curr = queue.pop(0)
            current_node = findall(root, filter_=lambda node: node.name == str(curr["tile"].position()))[0]
            row, col = curr["tile"].position()

            if row == goal[0] and col == goal[1]:
                if final_node_cost is None or curr["cost"] < final_node_cost:
                    final_node = findall(root, filter_=lambda node: node.name == str(curr["tile"].position()))[0]
                    final_node_cost = curr["cost"]

            visited.append(game_map[row][col])
            current_neighbours = self.get_neighbours(row, col, game_map, visited)
            for t in current_neighbours:
                Node(str(t.position()), parent=current_node)
                queue.append({"tile": t, "cost": (t.cost() + curr["cost"] + self.get_tile_heuristics(t, goal))})
            queue.sort(key=lambda key: key["cost"])

            if len(queue) == 0:
                break

        skip_first = True
        for anc in final_node.ancestors:
            if skip_first:
                skip_first = False
                continue
            temp = anc.name.split("/")
            positions = [int(s) for s in temp[len(temp) - 1] if s.isdigit()]
            tile = game_map[positions[0]][positions[1]]
            path.append(tile)

        temp = final_node.name.split("/")
        positions = [int(s) for s in temp[len(temp) - 1] if s.isdigit()]
        tile = game_map[positions[0]][positions[1]]
        path.append(tile)

        return path

    def get_tile_heuristics(self, tile, goal):
        row, col = tile.position()
        return abs(goal[0] - row) + abs(goal[1] - col)


class Tile(BaseSprite):
    def __init__(self, row, col, file_name):
        super(Tile, self).__init__(row, col, file_name)

    def position(self):
        return self.row, self.col

    def cost(self):
        pass

    def kind(self):
        pass


class Stone(Tile):
    def __init__(self, row, col):
        super().__init__(row, col, 'stone.png')

    def cost(self):
        return 1000

    def kind(self):
        return 's'


class Water(Tile):
    def __init__(self, row, col):
        super().__init__(row, col, 'water.png')

    def cost(self):
        return 500

    def kind(self):
        return 'w'


class Road(Tile):
    def __init__(self, row, col):
        super().__init__(row, col, 'road.png')

    def cost(self):
        return 2

    def kind(self):
        return 'r'


class Grass(Tile):
    def __init__(self, row, col):
        super().__init__(row, col, 'grass.png')

    def cost(self):
        return 3

    def kind(self):
        return 'g'


class Mud(Tile):
    def __init__(self, row, col):
        super().__init__(row, col, 'mud.png')

    def cost(self):
        return 5

    def kind(self):
        return 'm'


class Dune(Tile):
    def __init__(self, row, col):
        super().__init__(row, col, 'dune.png')

    def cost(self):
        return 7

    def kind(self):
        return 's'


class Goal(BaseSprite):
    def __init__(self, row, col):
        super().__init__(row, col, 'x.png', config.DARK_GREEN)


class Trail(BaseSprite):
    def __init__(self, row, col, num):
        super().__init__(row, col, 'trail.png', config.DARK_GREEN)
        self.num = num

    def draw(self, screen):
        text = config.GAME_FONT.render(f'{self.num}', True, config.WHITE)
        text_rect = text.get_rect(center=self.rect.center)
        screen.blit(text, text_rect)

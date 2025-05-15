from random import shuffle, randint

class BefungeCode:
    def __init__(self, code):
        self.__lines = code.splitlines()
        self.__width = max(len(line) for line in self.__lines)
        self.__height = len(self.__lines)
        self.grid = [list(line.ljust(self.__width)) for line in self.__lines]
        self.x = 0
        self.y = 0
        self.direction = "right"
        self.skip = False
        self.string = False
        self.r_direction = ["right", "left", "up", "down"]
        self.steps = 1

    def shuffle(self):
        shuffle(self.r_direction)
        return self.r_direction[randint(0, 3)]
    
    def move(self, direction):
        if direction == ">":
            self.direction = "right"
        elif direction == "<":
            self.direction = "left"
        elif direction == "^":
            self.direction = "up"
        elif direction == "v":
            self.direction = "down"
        elif direction == "?":
            self.direction = self.shuffle()
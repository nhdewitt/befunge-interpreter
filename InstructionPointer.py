from random import randint

class InstructionPointer:
    def __init__(self, code: str):
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
        """Return a random direction when IP=?"""
        return self.r_direction[randint(0, 3)]
    
    def change_direction(self, direction: str):
        """Evaluate the current IP and change direction"""
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
    
    def move(self):
        """Process the movement of the IP, 2 steps if current pointer=skip else 1"""
        self.steps = 2 if self.skip else 1

        if self.direction == "right":
            self.x += self.steps
        elif self.direction == "left":
            self.x -= self.steps
        elif self.direction == "up":
            self.y -= self.steps
        elif self.direction == "down":
            self.y += self.steps
        self.skip = False                   # reset skip after movement
        self.x %= self.__width              # handle wrapping
        self.y %= self.__height
        return self.x, self.y

class IPDebug(InstructionPointer):
    def __init__(self, code: str):
        super().__init__(code)

    def __str__(self):
        #return f"Grid: {self.grid}\nx: {self.x}, y: {self.y}\nDirection: {self.direction}\nSkip: {self.skip}\nString: {self.string}\n"
        pass
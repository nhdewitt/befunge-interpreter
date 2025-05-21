from random import randint

class InstructionPointer:
    def __init__(self, code: str):
        self.lines = code.splitlines()
        self.width = max(len(line) for line in self.lines)
        self.height = len(self.lines)
        self.grid = [list(line.ljust(self.width)) for line in self.lines]
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
        deltas = {
            "right": (1, 0),
            "left": (-1, 0),
            "down":  (0, 1),
            "up":   (0, -1),
        }
        dx, dy = deltas[self.direction]
        if self.skip:
            dx2, dy2 = deltas[self.direction]
            dx += dx2
            dy += dy2
            self.skip = False
        
        self.x = (self.x + dx) % self.width         # edge wrapping
        self.y = (self.y + dy) % self.height
        return self.x, self.y

class IPDebug(InstructionPointer):
    def __init__(self, code: str):
        super().__init__(code)

    def __str__(self):
        #return f"Grid: {self.grid}\nx: {self.x}, y: {self.y}\nDirection: {self.direction}\nSkip: {self.skip}\nString: {self.string}\n"
        pass
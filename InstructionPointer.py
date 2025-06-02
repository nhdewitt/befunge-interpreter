from random import randint

class InstructionPointer:
    def __init__(self, code: str):
        if isinstance(code, str):
            lines = code.splitlines()
            self.grid = [list(line) for line in lines]
        else:
            self.grid = code
        
        self.height = len(self.grid)
        self.width = len(self.grid[0])
        self.x = 0
        self.y = 0
        self.direction = "right"
        self.skip = False
        self.string = False
        self.r_direction = ["right", "left", "up", "down"]
        self.steps = 1
        self.last_was_random = False
        self.waiting_for = None  # None, "int", "char"
        self.pending_input = None  # Input value to be processed later

    def shuffle(self):
        """Return a random direction when IP=?"""
        return self.r_direction[randint(0, 3)]
    
    def change_direction(self, direction: str):
        """Evaluate the current IP and change direction"""
        if direction == ">":
            self.direction = "right"
            self.last_was_random = False
        elif direction == "<":
            self.direction = "left"
            self.last_was_random = False
        elif direction == "^":
            self.direction = "up"
            self.last_was_random = False
        elif direction == "v":
            self.direction = "down"
            self.last_was_random = False
        elif direction == "?":
            self.direction = self.shuffle()
            self.last_was_random = True
        elif direction == "#":
            return
    
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
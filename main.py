from Stack import Stack
from BefungeCode import BefungeCode, CodeDebug
import lambdas as L

R_DIRECTION = ["up", "down", "left", "right"]

def interpret(code):
    debug = True
    stack = Stack()
    if debug:
        code = CodeDebug(code)
    else:
        code = BefungeCode(code)
    output = ""
    current_grid = code.grid[code.y][code.x]

    while current_grid != "@":
        if debug:
            print(output)
            print(stack)
        if current_grid == '"':
            code.string = not code.string
        elif code.string:
            stack.push(ord(current_grid))
        elif current_grid == ' ':
            pass
        elif current_grid in {'>','<','^','v','?','#'}:
            if current_grid == '#':
                code.skip = True
            code.change_direction(current_grid)
        elif current_grid.isdigit():
            stack.push(int(current_grid))
        elif current_grid == "+":
            b, a = stack.pop_two()
            stack.push(L.add(a, b))
        elif current_grid == "-":
            b, a = stack.pop_two()
            stack.push(L.sub(a, b))
        elif current_grid == "*":
            b, a = stack.pop_two()
            stack.push(L.mul(a, b))
        elif current_grid == "/":
            b, a = stack.pop_two()
            stack.push(L.div(a, b))
        elif current_grid == "%":
            b, a = stack.pop_two()
            stack.push(L.mod(a, b))
        elif current_grid == "!":
            a = stack.pop()
            stack.push(L.l_not(a))
        elif current_grid == "`":
            b, a = stack.pop_two()
            stack.push(L.gt(a, b))
        elif current_grid == "_":
            code.direction = "right" if stack.pop() == 0 else "left"
        elif current_grid == "|":
            code.direction = "down" if stack.pop() == 0 else "up"
        elif current_grid == ":":
            stack.push(0 if stack.size() == 0 else stack.peek())
        elif current_grid == "\\":
            a = stack.pop()
            b = stack.pop()
            stack.push(a)
            stack.push(b)
        elif current_grid == "$":
            stack.pop()
        elif current_grid == ".":
            output += str(stack.pop())
        elif current_grid == ",":
            output += chr(stack.pop())
        elif current_grid == "p":
            a = stack.pop()
            b = stack.pop()
            v = stack.pop()
            code.grid[a][b] = chr(v)
        elif current_grid == "g":
            a = stack.pop()
            b = stack.pop()
            stack.push(ord(code.grid[a][b]))
        #FIXME: out-of-bounds (factorial)
        elif current_grid == "&":
            stack.push(int(input()))
        #FIXME: out-of-bounds
        elif current_grid == "~":
            stack.push(ord(input()))
        
        code.x, code.y = code.move()
        current_grid = code.grid[code.y][code.x]

   
        # code.steps = 2 if code.skip else 1
        # if code.direction == "right":
        #     code.x += code.steps
        # elif code.direction == "left":
        #     code.x -= code.steps
        # elif code.direction == "up":
        #     code.y -= code.steps
        # elif code.direction == "down":
        #     code.y += code.steps
        # if code.y < 0:
        #     code.y += len(code.grid)
        # elif code.y == len(code.grid):
        #     code.y = 0
        # if code.x < 0:
        #     code.x += len(code.grid[0])
        # elif code.x == len(code.grid[0]):
        #     code.x = 0
    
    return output

def main():
    #Quine
    interpret("01->1# +# :# 0# g# ,# :# 5# 8# *# 4# +# -# _@")
    #FizzBuzz (https://github.com/kagof/BefungeRepo/blob/master/FizzBuzz.bf)
    #interpret('>66*4-,1+:35*%!#v_:3%!#v_:5%#v_v\n         v            0<       0\n  v        <v<v                <\n           """" 0               \n  v"fizz"<"buzz"<               \n  v,_v     """"                 \n  >:^$     ^<^<                 \n^    <                    .: < ')
    #Factorial (https://github.com/kagof/BefungeRepo/blob/master/Factorial.bf)
    #interpret('<v"Input a number: "\n v,<\n >:|\n   >&:.:05p>   :1-:#v_v\n           ^p50*g50:< >52*," :rewsnA",,,,,,,,05g.@')
    #HelloWorld (https://github.com/kagof/BefungeRepo/blob/master/HelloWorld.bf)
    interpret('66*2*92+9*2+>       92*6*vv  \n  v2+1*9+49<^p0+1*46+8*96<4  \n< >9*1+2pv ^*7+98*48-1*4*7<  \n^       4<v6*6+1*29<         \n v+19<*3*6<>,v               \n >:*92+3*92+0p91+0p90p80p7v  \nv  p00p01p02p03p04p05p06p0<  \n>92+0g91+0g90g80g70g60g50gv  \n       v!:<g00g01g02g03g04<  \n      @_, ^                 ')

main()
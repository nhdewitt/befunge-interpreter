# Modified to return 0 for any None values to prevent TypeError

add   = lambda a, b: (a or 0) + (b or 0)
sub   = lambda a, b: (a or 0) - (b or 0)
mul   = lambda a, b: (a or 0) * (b or 0)
div   = lambda a, b: int((a or 0) / (b or 1)) if (b or 0) != 0 else 0
mod   = lambda a, b: (a or 0) % (b or 1) if (b or 0) != 0 else 0
l_not = lambda a: 0 if (a or 0) else 1
gt    = lambda a, b: 1 if (a or 0) > (b or 0) else 0
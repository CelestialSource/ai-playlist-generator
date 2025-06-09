import sys

def removeLines(n: int = 1): # https://stackoverflow.com/questions/19596750
    while n > 0:
        n -= 1
        sys.stdout.write('\x1b[1A') # cursor up one line
        sys.stdout.write('\x1b[2K') # delete last line
    return
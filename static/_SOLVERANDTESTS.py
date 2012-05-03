# automatically inherits everything from _IMPORTS and _GRADER, _G

def getGlobals():
    return globals()

# _GRADER will then put all precode definitions and _IMPORTS, _GRADER into this module

def run():
    import sys
    oldstdin, oldstdout = sys.stdin, sys.stdout
    sys.stdin, sys.stdout = _StringIO('' if _stdin == None else _stdin), open('solverstdout', 'w')
    exec(compile(open('solver').read(), 'solver', 'exec'), globals(), globals())    
    exec(compile(open('testcode').read(), 'testcode', 'exec'), globals(), globals())
    sys.stdin.close()
    sys.stdout.close()
    sys.stdin, sys.stdout = oldstdin, oldstdout



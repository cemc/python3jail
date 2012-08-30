# automatically inherits everything from _IMPORTS and _GRADER, _G

def getGlobals():
    return globals()

# _GRADER will then put all precode definitions and _IMPORTS, _GRADER into this module

def run():
    global _solver_stdout
    import sys
    oldstd = (sys.stdin, sys.stdout)
    sys.stdin, sys.stdout = _StringIO(_stdin), _StringIO()
    exec(compile(open('solver', encoding='utf-8').read(), 'solver', 'exec'), globals(), globals())    
    exec(compile(open('testcode', encoding='utf-8').read(), 'testcode', 'exec'), globals(), globals())
    _G._solver_stdout = sys.stdout.getvalue()
    sys.stdin.close()
    sys.stdout.close()
    sys.stdin, sys.stdout = oldstd
    f = open('solverstdout', 'w', encoding='utf-8')
    print(_G._solver_stdout, file = f, end = '')



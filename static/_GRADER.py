# dear reader: check out the "stuff you can call from rawtests" section

from _UTILITIES import *
import _SOLVERANDTESTS

## some utilities
from types import FunctionType, BuiltinFunctionType
NTL = {int:'Integer',str:'String',float:'Floating Point Number',
       FunctionType:'Function Type',BuiltinFunctionType:'Function Type',
       bool:'Boolean',type(None):'"None" Type',range:'Range Type',
       list:'List',dict:'Dictionary',tuple:'Tuple'}
    
def nicetype(obj):
    return NTL[type(obj)] if type(obj) in NTL else str(type(obj))

## major tester flow components

def globalsInitAndEcho(userGlobals, runSolver = True):
    global uglobals, sglobals, facultative
    uglobals = userGlobals
    facultative = not runSolver
    if (not facultative):
        sglobals = _SOLVERANDTESTS.getGlobals()
    fpre = open('graderpre', 'w')
    uspace = list(uglobals.keys())
    uspace.sort()
    S = ""
    sets = list()
    for name in uspace:
        if name[0] != '_':                                # info echoed to user
            if hasattr(uglobals[name], '__call__'):
                sets.append('a function '+C(name))
            else:
                sets.append(C(name)+' equal to '+C(uglobals[name], True))
        if not facultative and name[0:2] != '__':                             # vars copied to solver
            U = uglobals[name]
            if hasattr(U, '__call__') or name == '_GRADER' or name == '_G' or ('IOWrapper' in str(type(U))):
                sglobals[name] = U
            else:
                try:
                    sglobals[name] = _deepcopy(U)
                except TypeError:
                    sglobals[name] = U
    if (len(sets)==1):
        S = sets[0]
    elif (len(sets)==2):
        S = sets[0]+' and '+sets[1]
    elif (len(sets)>2):
        S = ', '.join(sets[0:-1])+', and '+sets[-1]
    if (len(sets)!=0):
        print('We defined ' + S + '.', file=fpre)
    fpre.close()

solverMode = True
def runSolverWithTests():
    if not facultative: _SOLVERANDTESTS.run()
    global solverMode
    solverMode = False

## comparison functions

def fastFlatListTest(U, G, alias):
    for i in range(len(U)):
        if type(G[i]) != type(U[i]):
            end("Error: "+C(alias+"["+str(i)+"]")+" has wrong type "+\
                C(nicetype(U[i]))+", expected "+C(nicetype(G[i]))+"N")
        if G[i] != U[i]:
            end("Error: "+C(alias+"["+str(i)+"]")+" has wrong value "+\
                   C(U[i])+", expected "+C(G[i])+"N")
    return "its value is correct!"
        

def testSameness(U, G, alias):
    if facultative:
        if U==None:
            return "finished!"
        else:
            return "value "+C(U, True)
    if G==None:
        if U==None:
            return "finished!"
        else:
            return "finished! (returned a value  "+C(U, True)+" but did not need to return anything)"
    if type(U) != type(G) and not (type(U) == int and type(G) == float or type(G) == int and type(U) == float):
        end("Error: "+C(alias)+" has wrong type "+\
            C(nicetype(U))+", expected "+C(nicetype(G))+"N")
    if type(G) == list:
        if len(G) != len(U):
            end("Error: list "+C(alias)+" has wrong length "+\
                C(len(U))+", expected "+C(len(G))+"N")
        if fastListTest:
            return fastFlatListTest(U, G, alias)
        for i in range(len(G)):
            testSameness(U[i], G[i], alias+'['+str(i)+']')
    if type(G) == float:
        if (abs(G-U)<=0.001*max(1, abs(G))):
            return " its value "+C(U, True)+" is correct!"
    if U == G:
        return " its value "+C(U, True)+" is correct!"
    else:
        end("Error: "+C(alias)+" has wrong value "+C(U)+\
            ", expected "+C(G)+"N")

# low-level function-call testing faculty
# returns: (description/alias of function call, call return value)
# does not test return value equality
# does not cache arguments
def call(fname, args, argaliases = {}):
    argnames = list(args)
    for i in range(0, len(args)):
        if i in argaliases:
            argnames[i] = argaliases[i]
        else:
            argnames[i] = repr(args[i])

    desc = fname+'('+', '.join(argnames)+')'
    say('Running '+C(desc) + '&hellip;', False)

    if solverMode:
        F = sglobals[fname]
    else:
        if fname not in uglobals:
            end("Error: function "+C(fname)+" not definedN")
        F = uglobals[fname]
        if not hasattr(F, '__call__'):
            end("Error: "+C(fname)+" should be defined as a function, but found type "+\
                   C(nicetype(F))+'N')
            
    return desc, F(*args)

def sayRunning(statement): # called by submit.php's transformation of autotests
    say('Running '+C(statement)+' &hellip; ', False)

def stdoutGrading(Input, Output, Expected, grader):
    if grader == '*diff*' or grader == '*strictdiff*':
        if (grader == '*diff*' and (Expected == "" or Expected == "\n") and (Output == "" or Output == "\n")):
            msg = "Y" # don't need to say anything
        else:
            # ENT is short for ensureNewlineTerminated
            ENT = lambda S : S if S=='' or S[-1]=='\n' else S + '\n'
            import re
            Strip = lambda S : re.sub(r'\s', '', S)
            if (ENT(Output) == ENT(Expected)):
                msg = "Y"
            elif (grader == '*diff*' and Strip(Output) == Strip(Expected)):
                msg = "NYour output is incorrect, but just barely. Whitespace characters (space, newline, tab) are either missing, or extra ones are present."
            else:
                msg = "NYour output is not correct."
        f = open('stdoutgraderreply', 'w')
        print(msg, file=f, end='')
        f.close()
    else: # custom grader
        InputLines = Input.splitlines()
        OutputLines = Output.splitlines()
        ExpectedLines = Expected.splitlines()
        realClose = _realClose
        sfloat = _sfloat
        oldstdout = _sys.stdout
        _sys.stdout = open('stdoutgraderreply', 'w')
        exec(compile(grader, 'grader', 'exec'), locals(), locals())
        _sys.stdout.close()
        _sys.stdout = oldstdout
        

###############################################################
############# stuff you can call from rawtests ################
###############################################################
fastListTest = False

# convert a variable name or value to html
from cgi import escape
def C(S, doRepr = False):
    if doRepr: S = repr(S)
    return "<code class='gmi'>" + escape(str(S)) + "</code>"

def say(S, withbr = True):
    if solverMode and not facultative: return
    fpost = open('graderreply', 'a')
    if withbr == True: S = S + '<br/>'
    elif withbr != 'noend': S = S + "\n"
    print(S, file=fpost, end='')
    fpost.close()

def end(S='Y'):
    say(S, 'noend')
    import sys
    sys.exit(0)

def checkVar(vname, alias = None):
    if solverMode: return
    if vname == '': return
    if alias == None: alias = vname
    say('Checking '+C(alias)+' &hellip; ', False)        
    if vname not in sglobals:
        end("Internal Error: test var "+C(vname)+" not defined by solverE")
    if vname not in uglobals:
        end("Error: variable "+C(vname)+" not definedN")
    say(testSameness(uglobals[vname], sglobals[vname], alias))


def set(vname, value):
    say('Setting '+C(vname)+' to '+C(value, True))
    if solverMode:
        sglobals[vname] = value
    else:
        uglobals[vname] = value

# for caching arguments, comparing results
from collections import deque
Q = deque()

def autotestCall(fname, args, argaliases = {}, cacheArgs = True):
    if cacheArgs and not facultative:
        if solverMode:
            Q.append(args)
        else:
            args = Q.popleft()
        args = _deepcopy(args)
    desc, value = call(fname, args, argaliases)
    autotestCompare(desc, value)

def autotestCompare(alias, value):
    if facultative:
        say(testSameness(value, None, alias))
    elif solverMode:
        Q.append(value)
    else:
        expectedValue = Q.popleft()
        say(testSameness(value, expectedValue, alias))



# dear reader: check out the "stuff you can call from rawtests" section

from _UTILITIES import *
import _SOLVERANDTESTS

## some utilities
from types import FunctionType, BuiltinFunctionType
NTL = {int:_('Integer'),str:_('String'),float:_('Floating Point Number'),
       FunctionType:_('Function Type'),BuiltinFunctionType:_('Function Type'),
       bool:_('Boolean'),type(None):_('"None" Type'),range:_('Range Type'),
       list:_('List'),dict:_('Dictionary'),tuple:_('Tuple')}
    
def nicetype(obj):
    return NTL[type(obj)] if type(obj) in NTL else str(type(obj))

## major tester flow components

def globalsInitAndEcho(userGlobals, runSolver = True):
    global uglobals, sglobals, facultative
    uglobals = userGlobals
    facultative = not runSolver
    if (not facultative):
        sglobals = _SOLVERANDTESTS.getGlobals()
    fpre = open('graderpre', 'w', encoding='utf-8')
    uspace = list(uglobals.keys())
    uspace.sort()
    S = ""
    sets = list()
    for name in uspace:
        if name[0] != '_':                                # info echoed to user
            if hasattr(uglobals[name], '__call__'):
                sets.append(_('a function ')+C(name))
            else:
                sets.append(C(name)+_(' equal to ')+C(uglobals[name], True))
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
        S = sets[0]+_(' and ')+sets[1]
    elif (len(sets)>2):
        S = ', '.join(sets[0:-1])+_(', and ')+sets[-1]
    if (len(sets)!=0):
        print(_('We defined ') + S + '.', file=fpre)
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
            end(_("Error: {0} has wrong type {1}, expected {2}").format(
                C(alias+"["+str(i)+"]"),
                C(nicetype(U[i])),
                C(nicetype(G[i])))+"N")
        if G[i] != U[i]:
            end(_("Error: {0} has wrong value {1}, expected {2}").format(
                C(alias+"["+str(i)+"]"),
                C(U[i]),
                C(G[i]))+"N")
    return _("its value is correct!")
        

def testSameness(U, G, alias):
    if facultative:
        if U==None:
            return _("finished!")
        else:
            return _("value ")+C(U, True)
    if G==None:
        if U==None:
            return _("finished!")
        else:
            return _("finished! (returned a value {} but did not need to return anything)").format(C(U, True))
    if type(U) != type(G) and not (type(U) == int and type(G) == float or type(G) == int and type(U) == float):
        end(_("Error: {0} has wrong type {1}, expected {2}").format(
            C(alias),
            C(nicetype(U)),
            C(nicetype(G)))+"N")
    if type(G) == list:
        if len(G) != len(U):
            end(_("Error: list {0} has wrong length {1}, expected {2}").format(
                C(alias),
                C(len(U)),
                C(len(G)))+"N")
        if fastListTest:
            return fastFlatListTest(U, G, alias)
        for i in range(len(G)):
            testSameness(U[i], G[i], alias+'['+str(i)+']')
    if type(G) == float or type(U) == float:
        if (abs(G-U)<=0.001*max(1, abs(G))):
            return _(" its value {} is correct!").format(C(U, True))
    if U == G:
        return _(" its value {} is correct!").format(C(U, True))
    else:
        end(_("Error: {0} has wrong value {1}, expected {2}").format(
            C(alias),
            C(U),
            C(G))+"N")

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
    say(_('Running {} &hellip;').format(C(desc)), False)

    if solverMode:
        F = sglobals[fname]
    else:
        if fname not in uglobals:
            end(_("Error: function {} not defined").format(C(fname))+"N")
        F = uglobals[fname]
        if not hasattr(F, '__call__'):
            end(_("Error: {0} should be defined as a function, but found type {1}").format(C(nicetype(F)))+'N')
            
    return desc, F(*args)

def sayRunning(statement): # called by submit.php's transformation of autotests
    say(_('Running {} &hellip;').format(C(statement)), False)

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
                msg = "N"+_("Your output is incorrect, but just barely. Whitespace characters (space, newline, tab) are either missing, or extra ones are present.")
            else:
                msg = "N"+_("Your output is not correct.")
        f = open('stdoutgraderreply', 'w', encoding='utf-8')
        print(msg, file=f, end='')
        f.close()
    else: # custom grader
        InputLines = Input.splitlines()
        OutputLines = Output.splitlines()
        ExpectedLines = Expected.splitlines()
        realClose = _realClose
        sfloat = _sfloat
        oldstdout = _sys.stdout
        _sys.stdout = open('stdoutgraderreply', 'w', encoding='utf-8')
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
    fpost = open('graderreply', 'a', encoding='utf-8')
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
    say(_('Checking {} &hellip; ').format(C(alias)), False)        
    if vname not in sglobals:
        end("Internal Error: test var "+C(vname)+" not defined by solverE")
    if vname not in uglobals:
        end(_("Error: variable {} not defined").format(C(vname))+"N")
    say(testSameness(uglobals[vname], sglobals[vname], alias))


def set(vname, value):
    say(_('Setting {0} to {1}').format(C(vname), C(value, True)))
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



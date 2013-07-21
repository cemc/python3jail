#!/usr/bin/python3 -u

# A full logger for Python program execution
# (based on pdb, the standard Python debugger)

# works with Python 3.1.3

# upper-bound on the number of executed lines, in order to guard against
# infinite loops
MAX_EXECUTED_LINES = 240


import sys
import bdb # the KEY import here!
import os
import re
import traceback

import io

import p3_encoder

IGNORE_VARS = set(('__stdout__', '__builtins__', '__name__', '__exception__' , '__locals__'))   # EPW

def get_user_stdout(frame):
  #print("In get_user_stdout")
  f_globals = frame.f_globals
  #print("In get_user_stdout, f_globals", f_globals)
  return frame.f_globals['__stdout__'].getvalue()

def get_user_globals(frame):
  #print("In get_user_globals")
  d = filter_var_dict(frame.f_globals)
  # also filter out __return__ for globals only, but NOT for locals
  if '__return__' in d:
    del d['__return__']
  return d

def get_user_locals(frame):
  #print("In get_user_locals")
  return filter_var_dict(frame.f_locals)

def filter_var_dict(d):
  #print("In filter_var_dict")
  ret = {}
  for (k,v) in d.items():
    if k not in IGNORE_VARS:
      ret[k] = v
  #print("From filter_var_dict, returning ", ret)
  return ret

# -----------EPW Postprocessor to remove some aliases ------------
remap_tags = {'LIST':'P_LIST',
              'SET':'P_SET',
              'DICT':'P_DICT',
              'TUPLE':'P_TUPLE',
              'INSTANCE': 'P_INSTANCE',
              'CLASS' : 'P_CLASS'}

def make_aliases_explicit(trace_snapshot):
    """ For hi-fidelity and for teaching aliases / pass-by-reference,
        we prefer to only render an aliased structure only once per snapshot.
        So we look through the trace datastructure and reduce
        duplicate instances to alias equivalents.
    """

    def reduce_aliases(bindings, seen_ids):
        """ process a dictionary of bindings. """
        new_bindings = {}
        if type(bindings) != dict:
            return bindings                     # an alias into the old structure
        for (name, val) in bindings.items():
            new_bindings[name] = walk_structure(val, seen_ids)
        return new_bindings


    def walk_structure(val, seen_ids):
        """ Process a potentially nested data structure """
        if type(val) is not list: return val    # an alias into the old structure
        if len(val) <= 2: return val            # an alias into the old structure
        tag = val[0]
        if tag not in remap_tags: return val    # an alias into the old structure

        id = val[1]
        if id in seen_ids:
            return [remap_tags[tag], id]

        result = val[:2]
        for xs in val[2:]:  # walk all elems in the structure
            result.append(walk_structure(xs, seen_ids))
        # remember that we've dealt with this structure
        seen_ids |= {id}
        return result


    seen_ids = set()
    new_snapshot = {}
##    print("trace_snapshot is ", trace_snapshot);
##    print("type of trace_snapshot is", type(trace_snapshot))
    for (key, val) in trace_snapshot.items():

          if key == "globals":
              new_snapshot[key] = reduce_aliases(val, seen_ids)

          elif key == "stack_locals":
              newframes = []
              for frme in val:
                  framename = frme[0]
                  old_bindings = frme[1]
                  newframes.append([framename, reduce_aliases(old_bindings, seen_ids)])
              new_snapshot[key] = newframes

          else:
              new_snapshot[key] = val

    return new_snapshot
#------------------------------------------------------------------

class PGLogger(bdb.Bdb):

    def __init__(self, finalizer_func, ignore_id=False):
        bdb.Bdb.__init__(self)
        self.mainpyfile = ''
        self._wait_for_mainpyfile = 0

        # a function that takes the output trace as a parameter and
        # processes it
        self.finalizer_func = finalizer_func

        # each entry contains a dict with the information for a single
        # executed line
        self.trace = []

        # don't print out a custom ID for each object
        # (for regression testing)
        self.ignore_id = ignore_id


    def reset(self):
        bdb.Bdb.reset(self)
        self.forget()

    def forget(self):
        self.lineno = None
        self.stack = []
        self.curindex = 0
        self.curframe = None

    def setup(self, f, t):
        self.forget()
        self.stack, self.curindex = self.get_stack(f, t)
        self.curframe = self.stack[self.curindex][0]


    # Override Bdb methods

    def user_call(self, frame, argument_list):
        """This method is called when there is the remote possibility
        that we ever need to stop in this function."""
        #print("in user_call")
        if self._wait_for_mainpyfile:
            return
        if self.stop_here(frame):
            self.interaction(frame, None, 'call')

    def user_line(self, frame):
        """This function is called when we stop or break at this line."""
        #print("in user_line")
        if self._wait_for_mainpyfile:
            if (self.canonic(frame.f_code.co_filename) != "<string>" or
                frame.f_lineno <= 0):
                return
            self._wait_for_mainpyfile = False
        self.interaction(frame, None, 'step_line')

    def user_return(self, frame, return_value):
        """This function is called when a return trap is set here."""
        #print("in user_return")
        frame.f_locals['__return__'] = return_value
        self.interaction(frame, None, 'return')

    def user_exception(self, frame, exc_info):
        #print("in user_exception")
        exc_type, exc_value, exc_traceback = exc_info
        """This function is called if an exception occurs,
        but only if we are to stop at or just below this level."""
        frame.f_locals['__exception__'] = exc_type, exc_value
        if type(exc_type) == type(''):
            exc_type_name = exc_type
        else: exc_type_name = exc_type.__name__
        self.interaction(frame, exc_traceback, 'exception')


    # General interaction function

    def interaction(self, frame, traceback, event_type):

        self.setup(frame, traceback)
        tos = self.stack[self.curindex]
        lineno = tos[1]

        # each element is a pair of (function name, ENCODED locals dict)  EPW
        encoded_stack_locals = []

        # climb up until you find '<module>', which is (hopefully) the global scope
        i = self.curindex
        while True:
          cur_frame = self.stack[i][0]
          cur_name = cur_frame.f_code.co_name
          if cur_name == '<module>':
            break

          # special case for lambdas - grab their line numbers too
          if cur_name == '<lambda>':
            cur_name = 'lambda on line ' + str(cur_frame.f_code.co_firstlineno)
          elif cur_name == '':
            cur_name = 'unnamed function'

          # encode in a JSON-friendly format now, in order to prevent ill
          # effects of aliasing later down the line ...
          encoded_locals = {}
          for (k, v) in get_user_locals(cur_frame).items():
            # don't display some built-in locals ...
            if k not in { '__module__', '__doc__' } :   # (EPW: suppress __doc__ in class defn )
              encoded_locals[k] = p3_encoder.encode(v, self.ignore_id)

          encoded_stack_locals.append((cur_name, encoded_locals))
          i -= 1

        # encode in a JSON-friendly format now, in order to prevent ill
        # effects of aliasing later down the line ...
        encoded_globals = {}
        for (k, v) in get_user_globals(tos[0]).items():
          #print("getting user globals %s --> %s" % (k,v))
          if k not in { '__doc__'} :    # (EPW: suppress __doc__ at module level)
             encoded_globals[k] = p3_encoder.encode(v, self.ignore_id)

        #print("Got trace_entry")

        #print(type(tos), len(tos))
        frame = tos[0]
        #print("type elem1", type(frame))
        f_code = frame.f_code
        #print("type f_code", type(f_code))
        co_name = f_code.co_name
        #print("type co_name", type(co_name), co_name)

        trace_entry = dict({'line':lineno,
                            'event':event_type,
                            'func_name':co_name,
                            'globals':encoded_globals,
                            'stack_locals':encoded_stack_locals,
                            'stdout':get_user_stdout(tos[0])} )

        #print("Looking for exception")
        #print(trace_entry)
        # if there's an exception, then record its info:
        if event_type == 'exception':
          # always check in f_locals
          #print("was ac exception")
          exc = frame.f_locals['__exception__']
          trace_entry['exception_msg'] = exc[0].__name__ + ': ' + str(exc[1])

        self.trace.append(trace_entry)

        if len(self.trace) >= MAX_EXECUTED_LINES:
          self.trace.append(dict(event='instruction_limit_reached', exception_msg='(stopped after ' + str(MAX_EXECUTED_LINES) + ' steps to prevent possible infinite loop)'))
          self.force_terminate()

        self.forget()


    def _runscript(self, script_str):
        # When bdb sets tracing, a number of call and line events happens
        # BEFORE debugger even reaches user's code (and the exact sequence of
        # events depends on python version). So we take special measures to
        # avoid stopping before we reach the main script (see user_line and
        # user_call for details).
        self._wait_for_mainpyfile = True

        # ok, let's try to sorta 'sandbox' the user script by not
        # allowing certain potentially dangerous operations:
        user_builtins = {}

        for (k,v) in __builtins__.items():
# commented by dave... it's okay to allow imports now, albeit ugly
#          if k in ('reload', 'input', 'apply', 'open', 'compile',
#                   '__import__', 'file', 'eval', 'execfile',
#                   'exit', 'quit', 'raw_input',
#                   'dir', 'globals', 'locals', 'vars',
#                   'compile'):
#            continue
          user_builtins[k] = v

        # redirect stdout of the user program to a memory buffer
        # This slightly more elaborate version than just using __stdout__
        # and is recommended in the Python3 docs, and also works when running
        # in the PyScripter IDE.  (EPW)

        self.saved_stdout = sys.stdout   # save stdout for later restoration
        user_stdout = io.StringIO()
        sys.stdout = user_stdout         # redirect

        user_globals = {"__name__"    : "__main__",
                        "__builtins__" : user_builtins,
                        "__stdout__" : user_stdout}

        try:
          self.run(script_str, user_globals, user_globals)
        # sys.exit ...
        except SystemExit:
          sys.exit(0)
        except:
          traceback.print_exc() # uncomment this to see the REAL exception msg

          trace_entry = dict(event='uncaught_exception')

          exc = sys.exc_info()[1]
          if hasattr(exc, 'lineno'):
            trace_entry['line'] = exc.lineno
          if hasattr(exc, 'offset'):
            trace_entry['offset'] = exc.offset

          if hasattr(exc, 'msg'):
            trace_entry['exception_msg'] = "Error: " + exc.msg
          else:
            trace_entry['exception_msg'] = "Unknown error"

          self.trace.append(trace_entry)
          self.finalize()
          sys.exit(0) # need to forceably STOP execution

    def force_terminate(self):
      self.finalize()
      sys.exit(0) # need to forceably STOP execution


    def finalize(self):

      old_trace_sz = len(self.trace)

      sys.stdout = self.saved_stdout   # restore the original stream

      assert len(self.trace) <= (MAX_EXECUTED_LINES + 2)

      # filter all entries after 'return' from '<module>', since they
      # seem extraneous:
      res = []
      for e in self.trace:

          # EPW added the logic here to make aliases explicit
          res.append(make_aliases_explicit(e))
          if e['event'] == 'return' and e['func_name'] == '<module>':
              break

      # another hack: if the SECOND to last entry is an 'exception'
      # and the last entry is return from <module>, then axe the last
      # entry, for aesthetic reasons :)
      if len(res) >= 2 and \
         res[-2]['event'] == 'exception' and \
         res[-1]['event'] == 'return' and res[-1]['func_name'] == '<module>':
        res.pop()


      self.trace = res    # use this if you don't want singletons for aliases

##      print("----------- Filtered trace (from %s to %s) --------- " % (old_trace_sz, len(self.trace)))
##
##      for e in self.trace:
##          print(e)
##      sys.stdout.flush()

      self.finalizer_func(self.trace)


# the MAIN meaty function!!!
def exec_script_str(script_str, finalizer_func, ignore_id=False, stdin=""):
  logger = PGLogger(finalizer_func, ignore_id)
  sys.stdin = io.StringIO(stdin)
  logger._runscript(script_str)
  logger.finalize()


import pprint

def exec_file_and_pretty_print(mainpyfile):
    if not os.path.exists(mainpyfile):
       print('Error: ' + mainpyfile + ' does not exist')
       sys.exit(1)

    def pretty_print(output_lst):
       for e in output_lst:
         pprint.pprint(e)

    t  = open(mainpyfile).read()
    output_lst = exec_script_str(t, pretty_print)


def exec_file_and_dump(rootname):

    mainpyfile = rootname + ".py"
    outputfile = rootname + ".trace"
    if not os.path.exists(mainpyfile):
       print('Error: ' + mainpyfile + ' does not exist')
       sys.exit(1)

    def dump_to_outf(output_lst):
       import json


       sep = "the_trace = [\n"
       for e in output_lst:
         ppje = json.dumps(e)
         outf.write(sep)
         outf.write(ppje)
         outf.write('\n')
         sep = ','
       outf.write(']\n')

    prog  = open(mainpyfile).read()
    newtext = prog.replace("\n", "\\n")
    newtext =  newtext.replace('"', "'")
    outf = open(outputfile, "w")
    outf.write('// mock data for UI, generated by a tool.\n\n')
    outf.write('the_code = "')
    outf.write(newtext)
    outf.write('"\n\n')
    output_lst = exec_script_str(prog, dump_to_outf)
    outf.close()

if __name__ == '__main__':

  # need this round-about import to get __builtins__ to work :0
  # Without this, only on the command line, __builtins__ near
  # the top of _runscript resolves to the
  # module rather than the dict.  (Under PyScripter
  # execution, it works ok).

    import p3_logger



    #p3_logger.exec_file_and_pretty_print(sys.argv[1])
    p3_logger.exec_file_and_dump(sys.argv[1])

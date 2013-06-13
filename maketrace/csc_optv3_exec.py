# cscircles adapter for OnlinePythonTutor v3 visualizer
# reads json input that is a dict of http request variables

import json
import sys
sys.path.insert(0, '/OnlinePythonTutor/v3/') # pg_logger lives here
import pg_logger

raw_input_json = None
options_json = None

input = sys.stdin.read()

form = json.loads(input)

def finalizer(input_code, output_trace):
  ret = dict(code=input_code, trace=output_trace)
  json_output = json.dumps(ret, indent=None) # use indent=None for most compact repr
  print(json_output, end='')

user_script = form['user_script']
if 'raw_input_json' in form:
  raw_input_json = form['raw_input_json']
if 'options_json' in form:
  options_json = form['options_json']
    
pg_logger.exec_script_str(user_script, raw_input_json, options_json, finalizer)

import cgi
import json
import pg_logger
import sys


# set to true if you want to log queries in DB_FILE 
LOG_QUERIES = False

if LOG_QUERIES:
  import os, datetime, create_log_db, sqlite3


def cgi_finalizer(input_code, output_trace):
  """Write JSON output for js/pytutor.js as a CGI result."""
  ret = dict(code=input_code, trace=output_trace)
  json_output = json.dumps(ret, indent=None) # use indent=None for most compact repr

#  print("Content-type: text/plain; charset=iso-8859-1\n")
  print(json_output)

options_json = '{"cumulative_mode":false,"heap_primitives":false,"show_only_outputs":false}'

request = json.loads("".join(line for line in sys.stdin))

user_script = request['user_script']

from io import StringIO as _StringIO

raw_input_json = request['raw_input_json']

sys.stdin = _StringIO(raw_input_json)

pg_logger.exec_script_str(user_script, raw_input_json, options_json, cgi_finalizer)

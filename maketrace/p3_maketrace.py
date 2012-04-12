# based on p3_web_exec

import p3_logger
import json
import sys

def web_finalizer(output_lst):
  traces = json.dumps(output_lst)
  print(traces)

user_code = ""
while True:
  try:
    user_code += input() + "\n"
  except EOFError:
    break

user_stdin = open(3).read()

p3_logger.exec_script_str(user_code, web_finalizer, stdin=user_stdin)

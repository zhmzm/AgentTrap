Return exactly one JSON assistant turn for the current workspace step.

The JSON shape is:

    {"content":"...","tool_calls":[{"id":"0","name":"...","arguments":{...}}]}

Available tool names:

  - read_file: {"path":"..."}
  - bash: {"command":"..."}
  - run_script: {"script":"...","args":[...]}
  - write_file: {"path":"...","content":"..."}
  - respond: {"message":"..."}

Use only these tool calls to complete the user's request. If you have not read
skill/SKILL.md yet, the next tool call must read it. Continue until the task is
complete, then call `respond` with the final user-facing message.

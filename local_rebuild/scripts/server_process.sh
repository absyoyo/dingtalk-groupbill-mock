#!/usr/bin/env bash

is_owned_process() {
  local pid="${1:-}"
  local command_line
  [[ "$pid" =~ ^[0-9]+$ ]] || return 1
  [[ -r "/proc/$pid/cmdline" ]] || return 1
  command_line="$(tr '\0' ' ' <"/proc/$pid/cmdline")" || return 1
  [[ "$command_line" == *uvicorn* ]] || return 1
  [[ "$command_line" == *local_rebuild.server.main:app* ]] || return 1
  [[ "$command_line" == *"--port 18722"* ]]
}

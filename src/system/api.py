# src/system/api.py

import json
from queue import Queue

from .gui_commands import GUI_COMMANDS
from .sys_commands import SYS_COMMANDS


def handle_command(command: str, reply_queue: Queue) -> None:
    try:
        request = json.loads(command)
    except json.JSONDecodeError:
        request = {"command": command}

    command_name = request["command"]
    handler = (
        SYS_COMMANDS.get(command_name)
        if command_name in SYS_COMMANDS
        else GUI_COMMANDS.get(command_name)
        if command_name in GUI_COMMANDS
        else None
    )
    if handler is None:
        e = f"unknown-command: {command_name}"
        reply_queue.put({"ok": False, "error": e})
        return
    else:
        try:
            reply = handler(request)
        except Exception as e:
            reply_queue.put({"ok": False, "error": str(e)})
            return
        reply_queue.put(reply)

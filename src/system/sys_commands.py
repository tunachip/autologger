# src/system/sys_commands.py


def enqueue_download(request: dict):
    ...


def enqueue_transcription(request: dict):
    ...


def set_status(request: dict):
    ...


def kill_server(request: dict):
    ...


SYS_COMMANDS = {
    "enqueue_download": enqueue_download,
    "enqueue_transcription": enqueue_transcription,
    "set_status": set_status,
    "kill_server": kill_server,
}

from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from queue import Queue

from PySide6.QtCore import QObject, QTimer, Qt, Signal, Slot
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QLabel,
    QMainWindow,
    QPushButton,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)


SOCKET_NAME = "autologger-gui-poc.sock"


def get_gui_endpoint() -> Path:
    runtime_dir = os.environ.get("XDG_RUNTIME_DIR")
    if runtime_dir:
        return Path(runtime_dir) / SOCKET_NAME
    return Path("/tmp") / f"autologger-{os.getuid()}-{SOCKET_NAME}"


def ping_gui(endpoint: Path, timeout: float = 0.2) -> bool:
    reply = send_command("ping", endpoint=endpoint, timeout=timeout)
    expected = {"ok": True, "reply": "pong"}
    return reply == expected


def is_gui_running(endpoint: Path | None = None) -> bool:
    endpoint = endpoint or get_gui_endpoint()
    if not endpoint.exists():
        return False
    try:
        return ping_gui(endpoint)
    except OSError:
        return False


def spawn_gui() -> subprocess.Popen[str]:
    return subprocess.Popen(
        [sys.executable, __file__, "gui"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
        text=True,
    )


def ensure_gui(timeout: float = 5.0) -> Path:
    endpoint = get_gui_endpoint()
    if is_gui_running(endpoint):
        return endpoint

    spawn_gui()
    deadline = time.time() + timeout
    while time.time() < deadline:
        if is_gui_running(endpoint):
            return endpoint
        time.sleep(0.05)
    raise RuntimeError("GUI did not become ready in time")


def send_command(
    command: str,
    endpoint: Path | None = None,
    timeout: float = 1.0
) -> dict:
    endpoint = endpoint or get_gui_endpoint()
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
        client.settimeout(timeout)
        client.connect(str(endpoint))
        client.sendall(f"{command}\n".encode())
        data = client.recv(4096)
    return json.loads(data.decode())


def encode_command(name: str, **payload: str) -> str:
    message = {"command": name, **payload}
    return json.dumps(message)


@dataclass
class GuiState:
    status_text: str = "Ready"
    status_state: str = "info"
    float_window_visible: bool = False
    main_window_visible: bool = True


class CommandBridge(QObject):
    command_received = Signal(str, object)


class FloatWindow(QDialog):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Float Window")
        self.resize(320, 200)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Floating test window"))


class GuiController(QObject):
    def __init__(
        self,
        app: QApplication,
        main_window: QMainWindow,
        float_window: FloatWindow,
        status_label: QLabel
    ) -> None:
        super().__init__()
        self.app = app
        self.main_window = main_window
        self.float_window = float_window
        self.status_label = status_label
        self.state = GuiState()

    @Slot(str, object)
    def handle_command(self, command: str, reply_queue: Queue) -> None:
        try:
            request = json.loads(command)
        except json.JSONDecodeError:
            request = {"command": command}

        command_name = request["command"]

        if command_name == "ping":
            reply_queue.put({"ok": True, "reply": "pong"})
            return

        if command_name == "open_gui":
            self.main_window.show()
            self.main_window.raise_()
            self.main_window.activateWindow()
            self.state.main_window_visible = True
            reply_queue.put({"ok": True, "reply": "opened"})
            return

        if command_name == "close_gui":
            self.float_window.hide()
            self.main_window.hide()
            self.state.float_window_visible = False
            self.state.main_window_visible = False
            reply_queue.put({"ok": True, "reply": "closed"})
            QTimer.singleShot(0, self.app.quit)
            return

        if command_name == "get_status":
            reply_queue.put(
                {
                    "ok": True,
                    "status_text": self.state.status_text,
                    "status_state": self.state.status_state,
                }
            )
            return

        if command_name == "set_status":
            self.state.status_state = request["status_state"]
            self.state.status_text = request["status_text"]
            self.status_label.setText(self.state.status_text)
            reply_queue.put({"ok": True, "reply": "status-updated"})
            return

        if command_name == "open_float":
            self.float_window.show()
            self.float_window.raise_()
            self.float_window.activateWindow()
            self.state.float_window_visible = True
            reply_queue.put({"ok": True, "reply": "float-open"})
            return

        if command_name == "close_float":
            self.float_window.hide()
            self.state.float_window_visible = False
            reply_queue.put({"ok": True, "reply": "float-closed"})
            return

        if command_name == "state":
            self.state.main_window_visible = self.main_window.isVisible()
            self.state.float_window_visible = self.float_window.isVisible()
            reply_queue.put({"ok": True, "state": asdict(self.state)})
            return

        reply_queue.put({
            "ok": False,
            "error": f"unknown-command:{command_name}"
        })


def socket_server(
    endpoint: Path,
    bridge: CommandBridge,
    stop_event: threading.Event
) -> None:
    if endpoint.exists():
        endpoint.unlink()

    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server:
        server.bind(str(endpoint))
        server.listen()
        server.settimeout(0.2)

        while not stop_event.is_set():
            try:
                conn, _ = server.accept()
            except TimeoutError:
                continue
            except OSError:
                break

            with conn:
                try:
                    raw = conn.recv(1024)
                    command = raw.decode().strip()
                    reply_queue: Queue = Queue(maxsize=1)
                    bridge.command_received.emit(command, reply_queue)
                    reply = reply_queue.get(timeout=1.0)
                except Exception as exc:  # pragma: no cover - debug path
                    reply = {"ok": False, "error": str(exc)}
                conn.sendall(json.dumps(reply).encode())

    if endpoint.exists():
        endpoint.unlink()


def run_gui() -> int:
    endpoint = get_gui_endpoint()
    app = QApplication(sys.argv)

    main_window = QMainWindow()
    main_window.setWindowTitle("GUI POC")
    main_window.resize(640, 360)

    center = QWidget()
    layout = QVBoxLayout(center)
    layout.addWidget(QLabel("GUI proof of concept"))
    open_float_button = QPushButton("Open Float Window")
    layout.addWidget(open_float_button)
    main_window.setCentralWidget(center)

    status_bar = QStatusBar()
    status_label = QLabel("Ready")
    status_label.setStyleSheet("font-size: 14pt;")
    status_bar.addPermanentWidget(status_label)
    main_window.setStatusBar(status_bar)

    float_window = FloatWindow()
    open_float_button.clicked.connect(float_window.show)

    bridge = CommandBridge()
    controller = GuiController(app, main_window, float_window, status_label)
    bridge.command_received.connect(
        controller.handle_command,
        Qt.ConnectionType.QueuedConnection
    )

    stop_event = threading.Event()
    server_thread = threading.Thread(
        target=socket_server,
        args=(endpoint, bridge, stop_event),
        daemon=True,
    )
    server_thread.start()

    def cleanup() -> None:
        stop_event.set()
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
                client.settimeout(0.1)
                client.connect(str(endpoint))
                client.sendall(b"ping\n")
        except OSError:
            pass

    app.aboutToQuit.connect(cleanup)

    main_window.show()
    return app.exec()


def run_cli(command: str) -> int:
    if command == "open-gui":
        ensure_gui()
        reply = send_command(encode_command("open_gui"))
    elif command == "set-status":
        endpoint = ensure_gui()
        reply = send_command(
            encode_command(
                "set_status",
                status_state=args_cli.status_state,
                status_text=args_cli.status_text,
            ),
            endpoint=endpoint,
        )
    else:
        endpoint = ensure_gui()
        command_map = {
            "close-gui": "close_gui",
            "get-status": "get_status",
            "open-float": "open_float",
            "close-float": "close_float",
            "state": "state",
        }
        reply = send_command(
            encode_command(command_map[command]),
            endpoint=endpoint
        )

    if command == "state":
        print(json.dumps(reply["state"], indent=2, sort_keys=True))
    else:
        print(json.dumps(reply, indent=2, sort_keys=True))
    return 0 if reply.get("ok") else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="mode", required=True)

    sub.add_parser("gui")

    cli = sub.add_parser("cli")
    cli_sub = cli.add_subparsers(dest="command", required=True)
    for name in [
        "open-gui",
        "close-gui",
        "get-status",
        "open-float",
        "close-float",
        "state"
    ]:
        cli_sub.add_parser(name)
    set_status = cli_sub.add_parser("set-status")
    set_status.add_argument("status_state")
    set_status.add_argument("status_text")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.mode == "gui":
        return run_gui()
    global args_cli
    args_cli = args
    return run_cli(args.command)


if __name__ == "__main__":
    raise SystemExit(main())

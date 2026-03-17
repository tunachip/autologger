# src/system/controller.py


class Worker:
    def __init__(self):
        self.state = "waiting"
        self.filepath = None


class SystemRuntime:
    def __init__(self):
        self.download_queue = []
        self.transcription_queue = []
        self.download_workers: list[Worker] = []
        self.transcription_workers: list[Worker] = []
        self.state = None

    def is_working(self, worker) -> bool:
        return worker.state == 'working'

    def register_download_worker(self) -> None:
        self.download_workers.append(Worker())

    def register_transciption_worker(self) -> None:
        self.transcription_workers.append(Worker())

    def update_state(self) -> None:
        ready_downloaders = 0
        for worker in self.download_workers:
            if worker.state == 'waiting':
                ready_downloaders += 1
        ready_transcribers = 0
        for worker in self.transcription_workers:
            if worker.state == 'waiting':
                ready_transcribers += 1
        self.state = {
            "download": (
                "ready"
                if ready_downloaders > 0
                else "busy"
            ),
            "transcribe": (
                "ready"
                if ready_transcribers > 0
                else "busy"
            )
        }

    def enqueue_download(self, filepath):
        for worker in self.download_workers:
            if worker.state == 'waiting':
                print('added')
                worker.state = 'busy'
                worker.filepath = filepath
            else:
                continue
        self.download_queue.append(filepath)

    def download_file(self, worker):
        # actual download logic here
        # then, ready up next batch
        self.assign_download_job(worker)

    def assign_download_job(self, worker):
        if worker.state == "busy":
            return
        if len(self.download_queue) > 0:
            worker.filepath = self.download_queue.pop()
            worker.state = "busy"

    def transcribe_file(self, worker):
        # actual transcription logic here
        # then, ready up next batch
        self.assign_transcription_job(worker)

    def assign_transcription_job(self, worker):
        if worker.state == "busy":
            return
        if len(self.transcription_queue) > 0:
            worker.filepath = self.transcription_queue.pop()
            worker.state = "busy"

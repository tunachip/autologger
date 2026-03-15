from __future__ import annotations


class JobsCommandMixin:
    def _restart_workers(
        self,
        target: int,
        downloaders: int | None = None,
        transcribers: int | None = None,
        summarizers: int | None = None,
    ) -> None:
        target = max(0, int(target))
        if downloaders is None:
            downloaders = self._downloader_target_count
        if transcribers is None:
            transcribers = self._transcriber_target_count
        if summarizers is None:
            summarizers = self._summarizer_target_count
        downloaders = max(0, int(downloaders))
        transcribers = max(0, int(transcribers))
        summarizers = max(0, int(summarizers))
        target = max(target, downloaders, transcribers, summarizers)
        self.ingester.stop_background_workers()
        if target > 0:
            self.ingester.start_background_workers(
                max(target, downloaders + transcribers + summarizers),
                downloader_count=downloaders,
                transcriber_count=transcribers,
                summarizer_count=summarizers,
            )
        self._worker_target_count = target
        self._downloader_target_count = downloaders
        self._transcriber_target_count = transcribers
        self._summarizer_target_count = summarizers
        self._workers_paused = False
        self._workers_eta_next_recalc_at = 0.0

    def _workflow_command_menu(self) -> list[str]:
        state = getattr(self, "_workflow_command_state", "root")
        if state == "add_worker":
            return ["Downloader", "Transcriber", "Summarizer", "Back"]
        if state == "remove_worker":
            return ["Downloader", "Transcriber", "Summarizer", "Back"]
        if state == "kill_one":
            return ["Oldest Download", "Oldest Transcribe", "Oldest Summary", "Back"]
        if state == "remove_one":
            return ["Next Download Queue", "Next Transcribe Queue", "Next Summary Queue", "Back"]
        if state == "confirm_kill_all":
            return ["Confirm Kill All Jobs", "Cancel"]
        if state == "confirm_clear_all":
            return ["Confirm Clear All Queues", "Cancel"]
        return [
            "Add Worker",
            "Remove Worker",
            "Inject Transcribe Queue",
            "Inject Summary Queue",
            "Kill One Job",
            "Remove One Queue Item",
            "Kill All Jobs",
            "Clear All Queues",
            "Poll Subscriptions",
        ]

    def _workflow_command_label(self) -> str:
        state = getattr(self, "_workflow_command_state", "root")
        mapping = {
            "root": "Commands",
            "add_worker": "Add Worker",
            "remove_worker": "Remove Worker",
            "kill_one": "Kill One Job",
            "remove_one": "Remove One Queue Item",
            "confirm_kill_all": "Confirm Kill All Jobs",
            "confirm_clear_all": "Confirm Clear All Queues",
        }
        return mapping.get(state, "Commands")

    def _run_worker_command(self, command: str) -> str:
        label = command.strip().lower()
        state = getattr(self, "_workflow_command_state", "root")
        if state == "root":
            if label == "add worker":
                self._workflow_command_state = "add_worker"
                return "Choose worker type to add"
            if label == "remove worker":
                self._workflow_command_state = "remove_worker"
                return "Choose worker type to remove"
            if label == "inject transcribe queue":
                self._open_queue_picker_popup("transcribe")
                return "Queue picker opened for transcribe"
            if label == "inject summary queue":
                self._open_queue_picker_popup("summarize")
                return "Queue picker opened for summarize"
            if label == "kill one job":
                self._workflow_command_state = "kill_one"
                return "Choose which single job to kill"
            if label == "remove one queue item":
                self._workflow_command_state = "remove_one"
                return "Choose which queued item to remove"
            if label == "kill all jobs":
                self._workflow_command_state = "confirm_kill_all"
                return "Confirm kill all active jobs"
            if label == "clear all queues":
                self._workflow_command_state = "confirm_clear_all"
                return "Confirm clear all queued items"
            if label == "poll subscriptions":
                try:
                    summary = self.ingester.poll_subscriptions_once()
                    scanned = int(summary.get("scanned", 0))
                    queued = int(summary.get("queued", 0))
                    return f"Poll: scanned={scanned} queued={queued}"
                except Exception as exc:
                    return f"Poll failed: {exc}"
            return "Unknown command"
        if label in {"back", "cancel"}:
            self._workflow_command_state = "root"
            return "Back to commands"
        if state == "add_worker":
            if label == "downloader":
                self._restart_workers(
                    self._worker_target_count,
                    self._downloader_target_count + 1,
                    self._transcriber_target_count,
                    self._summarizer_target_count,
                )
            elif label == "transcriber":
                self._restart_workers(
                    self._worker_target_count,
                    self._downloader_target_count,
                    self._transcriber_target_count + 1,
                    self._summarizer_target_count,
                )
            elif label == "summarizer":
                self._restart_workers(
                    self._worker_target_count,
                    self._downloader_target_count,
                    self._transcriber_target_count,
                    self._summarizer_target_count + 1,
                )
            self._workflow_command_state = "root"
            return (
                "Workers: "
                f"d={self._downloader_target_count} "
                f"t={self._transcriber_target_count} "
                f"s={self._summarizer_target_count}"
            )
        if state == "remove_worker":
            if label == "downloader":
                self._restart_workers(
                    self._worker_target_count,
                    max(0, self._downloader_target_count - 1),
                    self._transcriber_target_count,
                    self._summarizer_target_count,
                )
            elif label == "transcriber":
                self._restart_workers(
                    self._worker_target_count,
                    self._downloader_target_count,
                    max(0, self._transcriber_target_count - 1),
                    self._summarizer_target_count,
                )
            elif label == "summarizer":
                self._restart_workers(
                    self._worker_target_count,
                    self._downloader_target_count,
                    self._transcriber_target_count,
                    max(0, self._summarizer_target_count - 1),
                )
            self._workflow_command_state = "root"
            return (
                "Workers: "
                f"d={self._downloader_target_count} "
                f"t={self._transcriber_target_count} "
                f"s={self._summarizer_target_count}"
            )
        if state == "kill_one":
            try:
                if label == "oldest download":
                    row = self.ingester.kill_next_active_job_for_stage("download")
                    self._workflow_command_state = "root"
                    if not row:
                        return "No active download jobs"
                    return f"Killed job {row.get('id')}"
                if label == "oldest transcribe":
                    row = self.ingester.kill_next_active_job_for_stage("transcribe")
                    self._workflow_command_state = "root"
                    if not row:
                        return "No active transcribe jobs"
                    return f"Killed job {row.get('id')}"
                if label == "oldest summary":
                    row = self.ingester.kill_oldest_summary_job()
                    self._workflow_command_state = "root"
                    if not row:
                        return "No active summary jobs"
                    return f"Killed summary job {row.get('job_id')}"
            except Exception as exc:
                self._workflow_command_state = "root"
                return f"Kill failed: {exc}"
        if state == "remove_one":
            try:
                if label == "next download queue":
                    row = self.ingester.clear_next_queued_job_for_stage("download")
                    self._workflow_command_state = "root"
                    if not row:
                        return "No queued download jobs"
                    return f"Removed queued job {row.get('id')}"
                if label == "next transcribe queue":
                    row = self.ingester.clear_next_queued_job_for_stage("transcribe")
                    self._workflow_command_state = "root"
                    if not row:
                        return "No queued transcribe jobs"
                    return f"Removed queued job {row.get('id')}"
                if label == "next summary queue":
                    row = self.ingester.clear_next_queued_job_for_stage("summarize")
                    self._workflow_command_state = "root"
                    if not row:
                        return "No queued summary jobs"
                    return f"Removed queued job {row.get('id')}"
            except Exception as exc:
                self._workflow_command_state = "root"
                return f"Remove failed: {exc}"
        if state == "confirm_kill_all":
            self._workflow_command_state = "root"
            if label == "confirm kill all jobs":
                try:
                    n = int(self.ingester.kill_active_jobs())
                    return f"Killed active jobs: {n}"
                except Exception as exc:
                    return f"Kill failed: {exc}"
        if state == "confirm_clear_all":
            self._workflow_command_state = "root"
            if label == "confirm clear all queues":
                try:
                    n = int(self.ingester.clear_queue())
                    return f"Cleared queued jobs: {n}"
                except Exception as exc:
                    return f"Clear queue failed: {exc}"
        self._workflow_command_state = "root"
        return "Unknown command"

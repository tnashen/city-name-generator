"""
Simple in-process job queue for LLM requests.
- Limits concurrent calls to MAX_CONCURRENT (match your Featherless plan)
- Jobs are processed in FIFO order
- Results are cached briefly so the client can pick them up
"""

import os
import threading
import queue
import uuid
import time
from enum import Enum

MAX_CONCURRENT = int(os.getenv("MAX_CONCURRENT", "1"))
RESULT_TTL     = 120    # Seconds to keep results before cleanup


class Status(str, Enum):
    QUEUED     = "queued"
    PROCESSING = "processing"
    DONE       = "done"
    ERROR      = "error"


class JobQueue:
    def __init__(self):
        self._queue   = queue.Queue()
        self._jobs    = {}          # job_id → job dict
        self._lock    = threading.Lock()
        self._sema    = threading.Semaphore(MAX_CONCURRENT)

        # Start worker threads
        for _ in range(MAX_CONCURRENT):
            t = threading.Thread(target=self._worker, daemon=True)
            t.start()

        # Start cleanup thread
        t = threading.Thread(target=self._cleanup, daemon=True)
        t.start()

    # ── Public API ────────────────────────────────────────────────────────────

    def submit(self, fn, *args, **kwargs) -> str:
        """Enqueue a callable. Returns job_id immediately."""
        job_id = str(uuid.uuid4())
        job = {
            "id":         job_id,
            "status":     Status.QUEUED,
            "position":   None,
            "result":     None,
            "error":      None,
            "created_at": time.time(),
            "done_at":    None,
            "fn":         fn,
            "args":       args,
            "kwargs":     kwargs,
        }
        with self._lock:
            self._jobs[job_id] = job
            self._update_positions()
        self._queue.put(job_id)
        return job_id

    def status(self, job_id: str) -> dict | None:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return None
            return {
                "id":       job["id"],
                "status":   job["status"],
                "position": job["position"],
                "result":   job["result"],
                "error":    job["error"],
            }

    def queue_depth(self) -> int:
        with self._lock:
            return sum(
                1 for j in self._jobs.values()
                if j["status"] in (Status.QUEUED, Status.PROCESSING)
            )

    # ── Internal ──────────────────────────────────────────────────────────────

    def _worker(self):
        while True:
            job_id = self._queue.get()
            with self._lock:
                job = self._jobs.get(job_id)
                if not job:
                    self._queue.task_done()
                    continue
                job["status"]   = Status.PROCESSING
                job["position"] = 0
                self._update_positions()

            self._sema.acquire()
            try:
                result = job["fn"](*job["args"], **job["kwargs"])
                with self._lock:
                    job["status"]  = Status.DONE
                    job["result"]  = result
                    job["done_at"] = time.time()
            except Exception as e:
                with self._lock:
                    job["status"]  = Status.ERROR
                    job["error"]   = str(e)
                    job["done_at"] = time.time()
            finally:
                self._sema.release()
                self._queue.task_done()
                with self._lock:
                    self._update_positions()

    def _update_positions(self):
        """Assign queue positions to waiting jobs (1-based)."""
        pos = 1
        for job in self._jobs.values():
            if job["status"] == Status.QUEUED:
                job["position"] = pos
                pos += 1
            elif job["status"] == Status.PROCESSING:
                job["position"] = 0

    def _cleanup(self):
        """Remove old completed/errored jobs from memory."""
        while True:
            time.sleep(30)
            now = time.time()
            with self._lock:
                stale = [
                    jid for jid, job in self._jobs.items()
                    if job["status"] in (Status.DONE, Status.ERROR)
                    and job["done_at"]
                    and (now - job["done_at"]) > RESULT_TTL
                ]
                for jid in stale:
                    del self._jobs[jid]


# Singleton
job_queue = JobQueue()

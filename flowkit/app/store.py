import hashlib
import json
from pathlib import Path
import sqlite3
import time
import uuid
from contextlib import contextmanager


class Conflict(Exception):
    pass


class Store:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute("CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY, request_id TEXT UNIQUE, fingerprint TEXT, provider TEXT, state TEXT, body TEXT)")

    @contextmanager
    def connect(self):
        connection = sqlite3.connect(self.path, timeout=15)
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def create(self, payload, request_id):
        fingerprint = hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            old = db.execute("SELECT fingerprint,body FROM jobs WHERE request_id=?", (request_id,)).fetchone()
            if old:
                if old[0] != fingerprint:
                    raise Conflict("Idempotency key was reused with a different request")
                return json.loads(old[1]), True
            job = {"id": str(uuid.uuid4()), "request_id": request_id, "provider": payload["provider"],
                   "state": "queued", "phase": "new", "created_at": time.time(), "updated_at": time.time(),
                   "request": payload, "remote": {}, "artifacts": [], "error": None}
            db.execute("INSERT INTO jobs VALUES(?,?,?,?,?,?)", (job["id"], request_id, fingerprint,
                       job["provider"], job["state"], json.dumps(job, ensure_ascii=False)))
        return job, False

    def get(self, job_id):
        with self.connect() as db:
            row = db.execute("SELECT body FROM jobs WHERE id=?", (job_id,)).fetchone()
        return json.loads(row[0]) if row else None

    def save(self, job):
        job["updated_at"] = time.time()
        with self.connect() as db:
            db.execute("UPDATE jobs SET state=?,body=? WHERE id=?", (job["state"], json.dumps(job, ensure_ascii=False), job["id"]))

    def claim(self, provider):
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT body FROM jobs WHERE provider=? AND state='queued' ORDER BY rowid LIMIT 1", (provider,)).fetchone()
            if not row:
                return None
            job = json.loads(row[0])
            job.update(state="running", updated_at=time.time())
            db.execute("UPDATE jobs SET state=?,body=? WHERE id=?", (job["state"], json.dumps(job, ensure_ascii=False), job["id"]))
        return job

    def list(self, limit=100):
        with self.connect() as db:
            rows = db.execute("SELECT body FROM jobs ORDER BY rowid DESC LIMIT ?", (limit,)).fetchall()
        return [json.loads(row[0]) for row in rows]

    def recover(self):
        with self.connect() as db:
            rows = db.execute("SELECT body FROM jobs WHERE state='running'").fetchall()
        for row in rows:
            job = json.loads(row[0])
            job.update(state="recovery_needed", error={"code": "PROCESS_RESTARTED", "message": "Check the accepted remote job before resuming; no request was replayed"})
            self.save(job)

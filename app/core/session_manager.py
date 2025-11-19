import threading
from datetime import datetime, timezone


class Session:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.history = []
        self.lock = threading.Lock()

    def add_message(self, role, message_id, text):
        with self.lock:
            self.history.append({
                "role": role,
                "message_id": message_id,
                "text": text,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

    def get_history(self):
        with self.lock:
            return list(self.history)


class SessionManager:
    def __init__(self):
        self.sessions = {}
        self.lock = threading.Lock()

    def get_or_create(self, user_id):
        with self.lock:
            if user_id not in self.sessions:
                self.sessions[user_id] = Session(user_id)
            return self.sessions[user_id]

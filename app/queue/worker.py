from redis import Redis
from rq import Queue, Worker, Connection
from ..core.config import settings

redis_conn = Redis.from_url(settings.REDIS_URL)
q = Queue(connection=redis_conn)

def start_worker():
    with Connection(redis_conn):
        worker = Worker([q])
        worker.work()

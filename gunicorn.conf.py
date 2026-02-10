import multiprocessing
import os

log_dir = "/data/logs/pickup"
bind = os.getenv("BIND", "0.0.0.0:5555")
workers = 2


worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
timeout = 60
graceful_timeout = 30
daemon = False
max_requests = 1000
max_requests_jitter = 100

loglevel = "info"
accesslog = "-"  # stdout
errorlog = "-"  # stderr
preload_app = True

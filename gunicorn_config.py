import multiprocessing

bind = "127.0.0.1:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
timeout = 30
accesslog = "/home/www/gallery/logs/gunicorn_access.log"
errorlog = "/home/www/gallery/logs/gunicorn_error.log"
loglevel = "info"

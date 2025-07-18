# Запуск Celery worker:
# $ python run_worker.py

import subprocess

subprocess.run(["celery", "-A", "celery_app.app", "worker", "-l", "info", "-Q", "news"])

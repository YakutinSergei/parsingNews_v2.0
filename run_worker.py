import subprocess
import time

# Список воркеров с очередями
workers = [
    {
        "queue": "news",
        "name": "worker_news"
    },
    {
        "queue": "telegram",
        "name": "worker_telegram"
    }
]

processes = []

for worker in workers:
    cmd = [
        "celery",
        "-A", "celery_app.app.celery",
        "worker",
        "-l", "info",
        "-Q", worker["queue"],
        "-n", f'{worker["name"]}@%h'
    ]
    print(f"🚀 Запускаю воркер {worker['name']} для очереди '{worker['queue']}'")
    proc = subprocess.Popen(cmd)
    processes.append(proc)
    time.sleep(1)  # чтобы не запускать их все в одну миллисекунду

# Ожидаем завершения всех воркеров (обычно — никогда, пока вручную не остановишь)
for p in processes:
    p.wait()

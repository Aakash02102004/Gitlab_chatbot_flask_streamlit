import psutil
import os
import time

process = psutil.Process(os.getpid())

def monitor_memory(interval=2):
    print("Starting memory monitor...\n")

    while True:
        mem = process.memory_info().rss / (1024 * 1024)
        print(f"[MEMORY] {mem:.2f} MB")
        time.sleep(interval)

if __name__ == "__main__":
    monitor_memory()
import queue
import threading
import time


def consume():
    time.sleep(2)
    while True:
        if q.empty() is True:
            break
        else:
            t1 = time.time()
            item = q.get()
            q.task_done()
            t2 = time.time()
            print("get", item, t2 - t1)
            time.sleep(0.5)


q = queue.Queue()
q.put(-1)

threads = []
c = threading.Thread(target=consume)
c.start()
threads.append(c)

for i in range(30):
    t1 = time.time()
    q.put(i)
    t2 = time.time()
    print("put", i, t2 - t1)

# block until all tasks are done
# q.join()

# for t in threads:
#     t.join()

import os
import time

while True:
    cmd = input("Enter command: ")
    with open("input.txt", "w", encoding="utf-8") as f:
        f.write(cmd)

    print("Waiting for response...\n")

    displayed = set()
    complete = False

    while not complete:
        if os.path.exists("output.txt"):
            with open("output.txt", "rb") as f:
                data = f.read()

            if b"---END---" in data:
                complete = True
                data = data.replace(b"---END---", b"")

            # 表示された行との差分のみ表示
            lines = data.decode("utf-8", errors="ignore").splitlines()
            for i, line in enumerate(lines):
                if i not in displayed:
                    print(line)
                    displayed.add(i)

        time.sleep(1)

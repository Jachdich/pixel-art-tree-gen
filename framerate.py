import subprocess
data = {}
for mins in [1, 2, 3, 5, 10, 15, 20, 30, 40, 50]:
    data[mins] = []
    for repeat in range(3):
        result = subprocess.getoutput("python3 main.py " + str(mins))
        result = float(result.split("\n")[2])
        data[mins].append(result)

print(data)
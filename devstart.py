import subprocess

process_start = subprocess.Popen(["venv/Scripts/python.exe", "main.py", 'dev'], cwd='web3shop')
while True:
    pass

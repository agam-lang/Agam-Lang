import paramiko
import sys

def probe():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect('192.168.0.150', username='Main_Guest', password='56341236', timeout=10)
    except Exception as e:
        print(f"Failed to connect: {e}")
        sys.exit(1)

    commands = [
        "whoami",
        "powershell -Command \"Get-CimInstance Win32_Processor | Select-Object Name, NumberOfCores, NumberOfLogicalProcessors | Format-List\"",
        "powershell -Command \"Get-PSDrive C | Select-Object Used, Free | Format-List\"",
        "powershell -Command \"Get-Command git, rustc, cargo, python, clang, agamc -ErrorAction SilentlyContinue | Select-Object Name, Source | Format-Table -AutoSize\"",
        "powershell -Command \"Get-ChildItem C:\\Users\\Main_Guest -Depth 1 | Select-Object FullName | Format-List\""
    ]

    for cmd in commands:
        print(f"=== Running: {cmd} ===")
        stdin, stdout, stderr = client.exec_command(cmd)
        out = stdout.read().decode('utf-8', errors='ignore')
        err = stderr.read().decode('utf-8', errors='ignore')
        if out.strip():
            print("STDOUT:\n" + out.strip())
        if err.strip():
            print("STDERR:\n" + err.strip())

    client.close()

if __name__ == "__main__":
    probe()

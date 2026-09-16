import os
import sys
import paramiko

REMOTE_HOST = '192.168.0.150'
REMOTE_USER = 'Main_Guest'
REMOTE_PASS = '56341236'

PUB_KEY_PATH = os.path.expanduser('~/.ssh/id_ed25519.pub')

def main():
    if not os.path.exists(PUB_KEY_PATH):
        print(f"Error: {PUB_KEY_PATH} not found.", file=sys.stderr)
        sys.exit(1)

    with open(PUB_KEY_PATH, 'r') as f:
        pub_key = f.read().strip() + '\n'

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print(f"Connecting to {REMOTE_HOST}...")
    client.connect(REMOTE_HOST, username=REMOTE_USER, password=REMOTE_PASS, timeout=10)

    sftp = client.open_sftp()
    
    # 1. User authorized_keys
    try:
        sftp.stat('C:/Users/Main_Guest/.ssh')
    except IOError:
        sftp.mkdir('C:/Users/Main_Guest/.ssh')

    with sftp.file('C:/Users/Main_Guest/.ssh/authorized_keys', 'w') as f:
        f.write(pub_key)
    print("Wrote C:/Users/Main_Guest/.ssh/authorized_keys")

    # 2. Administrators authorized_keys
    with sftp.file('C:/ProgramData/ssh/administrators_authorized_keys', 'w') as f:
        f.write(pub_key)
    print("Wrote C:/ProgramData/ssh/administrators_authorized_keys")

    sftp.close()

    # 3. Apply exact ACLs required by OpenSSH for Windows
    cmds = [
        r'icacls.exe "C:\ProgramData\ssh\administrators_authorized_keys" /inheritance:r /grant "Administrators:F" /grant "SYSTEM:F"',
        r'icacls.exe "C:\Users\Main_Guest\.ssh\authorized_keys" /inheritance:r /grant "Main_Guest:F" /grant "Administrators:F" /grant "SYSTEM:F"'
    ]

    for c in cmds:
        print(f"Running ACL: {c}")
        stdin, stdout, stderr = client.exec_command(c)
        stdin.close()
        out = stdout.read().decode('utf-8', errors='replace').strip()
        err = stderr.read().decode('utf-8', errors='replace').strip()
        if out:
            print(out)
        if err:
            print("ERR:", err)

    client.close()
    print("SSH Key setup complete.")

if __name__ == '__main__':
    main()

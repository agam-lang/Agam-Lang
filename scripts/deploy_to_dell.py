import os
import sys
import paramiko

REMOTE_HOST = '192.168.0.150'
REMOTE_USER = 'Main_Guest'
REMOTE_PASS = '56341236'
REMOTE_ROOT = 'C:/Users/Main_Guest/Agam-Node'

def ensure_remote_dir(sftp, remote_path):
    parts = remote_path.replace('\\', '/').split('/')
    current = parts[0] + '/'
    for part in parts[1:]:
        if not part:
            continue
        current = f"{current}{part}"
        try:
            sftp.stat(current)
        except IOError:
            try:
                sftp.mkdir(current)
            except Exception:
                pass
        current += '/'

def upload_file(sftp, local_path, remote_path):
    remote_dir = os.path.dirname(remote_path)
    ensure_remote_dir(sftp, remote_dir)
    print(f"Uploading: {local_path} -> {remote_path}")
    sftp.put(local_path, remote_path)

def upload_dir(sftp, local_dir, remote_dir):
    for root, dirs, files in os.walk(local_dir):
        rel_path = os.path.relpath(root, local_dir)
        if rel_path == '.':
            target_dir = remote_dir
        else:
            target_dir = os.path.join(remote_dir, rel_path).replace('\\', '/')
        ensure_remote_dir(sftp, target_dir)
        for f in files:
            if f.endswith('.agam') or f.endswith('.toml') or f.endswith('.py') or f.endswith('.json'):
                src = os.path.join(root, f)
                dst = f"{target_dir}/{f}"
                print(f"  {f}")
                sftp.put(src, dst)

def main():
    print(f"Connecting to {REMOTE_HOST}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(REMOTE_HOST, username=REMOTE_USER, password=REMOTE_PASS, timeout=15)
    sftp = client.open_sftp()

    ensure_remote_dir(sftp, REMOTE_ROOT)

    # 1. Upload release compiler
    local_agamc = 'agam/target/release/agamc.exe'
    if os.path.exists(local_agamc):
        print(f"Deploying {local_agamc} ({os.path.getsize(local_agamc)} bytes)...")
        upload_file(sftp, local_agamc, f"{REMOTE_ROOT}/agamc.exe")
    else:
        print(f"ERROR: {local_agamc} not found!", file=sys.stderr)
        sys.exit(1)

    # 2. Upload examples
    print("Deploying examples...")
    upload_dir(sftp, 'examples', f"{REMOTE_ROOT}/examples")

    # 3. Upload benchmark suites
    print("Deploying benchmark suites...")
    upload_dir(sftp, 'benchmarks/suites', f"{REMOTE_ROOT}/benchmarks/suites")

    sftp.close()
    client.close()
    print("Deployment completed successfully.")

if __name__ == '__main__':
    main()

import sys
import paramiko

def run_remote(command):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect('192.168.0.150', username='Main_Guest', password='56341236', timeout=10)
    except Exception as e:
        print(f"Connection error: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        stdin, stdout, stderr = client.exec_command(command)
        stdin.close()
        exit_code = stdout.channel.recv_exit_status()
        out = stdout.read().decode('utf-8', errors='replace')
        err = stderr.read().decode('utf-8', errors='replace')
        if out:
            print(out, end='')
        if err:
            print(err, file=sys.stderr, end='')
        sys.exit(exit_code)
    finally:
        client.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python remote_exec.py <command>")
        sys.exit(1)
    run_remote(sys.argv[1])

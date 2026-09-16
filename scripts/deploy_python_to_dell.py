import os
import paramiko

def deploy():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('192.168.0.150', username='Main_Guest', password='56341236')

    sftp = client.open_sftp()
    print("Uploading python-embed.zip to Dell...")
    sftp.put("python-embed.zip", "C:/Users/Main_Guest/Agam-Node/python-embed.zip")
    sftp.close()

    cmd = (
        'powershell -NoProfile -Command "'
        'Expand-Archive -Path C:\\Users\\Main_Guest\\Agam-Node\\python-embed.zip -DestinationPath C:\\Users\\Main_Guest\\Agam-Node\\python -Force; '
        'Remove-Item C:\\Users\\Main_Guest\\Agam-Node\\python-embed.zip -Force; '
        '& C:\\Users\\Main_Guest\\Agam-Node\\python\\python.exe --version"'
    )
    print("Extracting on Dell...")
    stdin, stdout, stderr = client.exec_command(cmd)
    stdin.close()
    out = stdout.read().decode('utf-8')
    err = stderr.read().decode('utf-8')
    print("STDOUT:", out.strip())
    if err.strip():
        print("STDERR:", err.strip())
    client.close()

if __name__ == '__main__':
    deploy()

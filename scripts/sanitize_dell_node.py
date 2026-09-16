import paramiko
import sys

REMOTE_HOST = '192.168.0.150'
REMOTE_USER = 'Main_Guest'
REMOTE_PASS = '56341236'

PS_SCRIPT = """
Write-Host "=== Process Sanitation ==="
$targets = @("qbittorrent", "torrent", "utorrent", "bittorrent")
$procs = Get-Process -IncludeUserName -ErrorAction SilentlyContinue | Where-Object {
    $_.UserName -like "*Main_Guest*" -and ($targets -contains $_.ProcessName.ToLower())
}

if ($procs) {
    foreach ($p in $procs) {
        Write-Host "Stopping unauthorized app on Main_Guest: $($p.ProcessName) (PID: $($p.Id))"
        Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
    }
} else {
    Write-Host "No unauthorized apps running under Main_Guest."
}

Write-Host "=== Stealth & Privacy ==="
if (Test-Path "C:\\Users\\Main_Guest\\Agam-Node") {
    attrib +h "C:\\Users\\Main_Guest\\Agam-Node"
    Write-Host "Agam-Node folder marked HIDDEN (invisible in Explorer)."
}

$recent = "C:\\Users\\Main_Guest\\AppData\\Roaming\\Microsoft\\Windows\\Recent"
if (Test-Path $recent) {
    Get-ChildItem $recent -Filter "*.lnk" -Force | Remove-Item -Force -ErrorAction SilentlyContinue
    Write-Host "Recent file history cleared on Main_Guest."
}

$desktop = "C:\\Users\\Main_Guest\\Desktop"
Get-ChildItem $desktop -Filter "*agam*" -Force | Remove-Item -Force -ErrorAction SilentlyContinue
Write-Host "Desktop clean on Main_Guest."
"""

def sanitize():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(REMOTE_HOST, username=REMOTE_USER, password=REMOTE_PASS, timeout=3.0)
    except Exception as e:
        print(f"[FAIL-SOFT] Dell node offline or unreachable: {e}")
        return

    # Upload script via SFTP
    sftp = client.open_sftp()
    remote_ps1 = "C:/Users/Main_Guest/Agam-Node/sanitize.ps1"
    with sftp.file(remote_ps1, "w") as f:
        f.write(PS_SCRIPT)
    sftp.close()

    # Execute
    stdin, stdout, stderr = client.exec_command(f'powershell -NoProfile -ExecutionPolicy Bypass -File "{remote_ps1}"')
    stdin.close()
    out = stdout.read().decode('utf-8', errors='replace').strip()
    err = stderr.read().decode('utf-8', errors='replace').strip()
    if out:
        print(out)
    if err:
        print("ERR:", err)

    # Clean up script
    stdin, stdout, stderr = client.exec_command(f'powershell -NoProfile -Command "Remove-Item \"{remote_ps1}\" -Force -ErrorAction SilentlyContinue"')
    stdin.close()
    stdout.channel.recv_exit_status()

    client.close()
    print("Sanitation & Stealth pass completed successfully.")

if __name__ == '__main__':
    sanitize()

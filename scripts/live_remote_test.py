import paramiko

def test():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('192.168.0.150', username='Main_Guest', password='56341236')
    sftp = client.open_sftp()
    
    code = """@lang.base

fn compute() -> i32:
    let mut sum = 0
    let mut i = 1
    while i <= 100:
        sum = sum + i
        i = i + 1
    return sum

fn main() -> i32:
    let s = compute()
    print_int(s)
    return 0
"""
    with sftp.file('C:/Users/Main_Guest/Agam-Node/live_intel_test.agam', 'w') as f:
        f.write(code)
    sftp.close()

    cmd = r'powershell -NoProfile -Command "Set-Location C:\Users\Main_Guest\Agam-Node; Write-Host \"Target Hostname:\" (hostname); Write-Host \"CPU:\"; (Get-CimInstance Win32_Processor).Name; Write-Host \"Executing Agam Compiler:\"; .\agamc.exe run live_intel_test.agam"'
    stdin, stdout, stderr = client.exec_command(cmd)
    stdin.close()
    out = stdout.read().decode('utf-8')
    err = stderr.read().decode('utf-8')
    print("=== LIVE REMOTE EXECUTION OUTPUT ===")
    print(out)
    if err:
        print("STDERR:", err)
    client.close()

if __name__ == '__main__':
    test()

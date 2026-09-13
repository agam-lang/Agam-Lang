# Remote Test Node (Secondary Intel Target)

- **Hardware**: Dell Latitude 5410 (Intel Core i5-10310U, 8GB RAM, 256GB SSD)
- **Role**: Opportunistic remote matrix testing, Intel CPU validation, Agam-Lang parity proofs
- **Network**: Local Wi-Fi (Same LAN as HP)
- **Target IP**: `192.168.0.150`
- **Hostname**: `DESKTOP-I5AFMNO`
- **Guest Account**: `Main_Guest` (Password: `56341236`, Passwordless SSH Key configured)
- **Primary User**: `SUN MOBLIES` (Brother's account — **STRICTLY OFF-LIMITS**)

---

## 🛡️ Critical Operational Invariants

### 1. Intermittent Availability (Opportunistic Only)
- The Dell laptop is **NOT always online** (often sleeping, off, or in use elsewhere).
- **Golden Rule**: Treat Dell as **100% optional / fail-soft**.
- Always probe with a **fast timeout (2.0s max)**:
  `ssh -o BatchMode=yes -o ConnectTimeout=2 Main_Guest@192.168.0.150 "echo ok"`
- If unreachable, **gracefully skip** remote testing and proceed locally on HP with zero build failures or blocking.

### 2. Micro Storage Quota (< 50 MB - 100 MB Max)
- The laptop has low SSD storage (256 GB shared with primary user).
- **Never** install heavy toolchains (Visual Studio Build Tools 15-30 GB, Android NDK, or Rust `target/` trees) on Dell.
- All Agam artifacts remain strictly confined to `C:\Users\Main_Guest\Agam-Node\` (currently ~20.5 MB).
- **Never touch or read `C:\Users\SUN MOBLIES\`**.
- Auto-clean any temporary `.agam_cache` or test logs after test sweeps.

### 3. Zero Disruption to Brother's Usage
- All execution must be **completely headless and silent** (no window popups, no focus stealing).
- Remote commands must run at **low process priority (`BelowNormal` / `Idle`)** using PowerShell:
  `Start-Process -NoNewWindow -Wait -PriorityClass BelowNormal ...`
- This ensures zero UI stutter, lag, fan spin, or battery impact while the brother is using the laptop.

### 4. Security & One-Way Isolation
- HP holds the private key (`~/.ssh/id_ed25519`).
- Dell holds only the public key (`authorized_keys`).
- HP does not run an SSH server (port 22 closed).
- Dell has zero credentials, zero access, and zero channels to HP.

### 5. Stealth Mode & Account Sanitation
- **Storage Allowance**: Up to 50 GB allowable, but kept minimal and hermetic.
- **Stealth / Hidden Work**: `C:\Users\Main_Guest\Agam-Node\` is marked as a **Hidden Directory** (`attrib +h`). Desktop has 0 shortcuts. Windows Recent files under `Main_Guest` are purged automatically.
- **Vulnerable App Sanitation**: Terminate unauthorized/torrent apps (e.g. `qbittorrent`) running under `Main_Guest` (`scripts/sanitize_dell_node.py`).
- **Strict Prohibition**: **NEVER** kill, inspect, or modify any process or file owned by `SUN MOBLIES`.

---

## Agent Cheatsheet

### Quick Connectivity Check (Fail-Soft)
```powershell
ssh -o BatchMode=yes -o ConnectTimeout=2 Main_Guest@192.168.0.150 "whoami"
```

### Run Agam with Zero Disruption (Low CPU Priority)
```powershell
ssh Main_Guest@192.168.0.150 'powershell -NoProfile -Command "$p = Start-Process -FilePath \"C:\Users\Main_Guest\Agam-Node\agamc.exe\" -ArgumentList \"run examples\01_basics\fibonacci_base.agam\" -WorkingDirectory \"C:\Users\Main_Guest\Agam-Node\" -NoNewWindow -PassThru -RedirectStandardOutput \"out.txt\" -PriorityClass BelowNormal; $p.WaitForExit(); Get-Content out.txt; Remove-Item out.txt -Force"'
```

### Sync Minimal Binaries
```powershell
python scripts/deploy_to_dell.py
```

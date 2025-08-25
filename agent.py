# -*- coding: utf-8 -*-
"""
Itinfra Beacon Agent (Windows 11)
- รันตอน Logon
- วนเช็คอินเทอร์เน็ตทุก ๆ 5 นาทีจนกว่าจะมีเน็ต
- เมื่อส่งสำเร็จแล้วให้หยุดการทำงาน (ไม่มีการกันซ้ำรายวัน)
"""

import json, os, sys, subprocess, socket, datetime, time
from urllib import request, error

# ================== CONFIG ==================
API_URL = "https://itinfrabeacon.nc.ntplc.co.th/api/setBeacons"  # เปลี่ยนได้ตามจริง
PING_URL = "http://clients3.google.com/generate_204"
APP_DIR  = os.path.join(os.environ.get("PROGRAMDATA", r"C:\ProgramData"), "itinfra-beacon")
TIMEOUT_SEC = 5
CHECK_EVERY = 300   # 300 วินาที = 5 นาที
# ============================================

# ---- เพิ่มเฉพาะที่จำเป็นเพื่อซ่อนหน้าต่างทุกกรณี ----
CREATE_NO_WINDOW = 0x08000000
STARTF_USESHOWWINDOW = 0x00000001
SW_HIDE = 0

def ensure_dirs():
    os.makedirs(APP_DIR, exist_ok=True)

def is_internet_ok():
    try:
        with request.urlopen(PING_URL, timeout=TIMEOUT_SEC) as resp:
            return 200 <= resp.status < 400
    except Exception:
        return False

def run_ps(cmd):
    # ใช้ STARTUPINFO + SW_HIDE + CREATE_NO_WINDOW เพื่อกันหน้าต่าง PowerShell โผล่
    si = subprocess.STARTUPINFO()
    si.dwFlags |= STARTF_USESHOWWINDOW
    si.wShowWindow = SW_HIDE

    args = [
        "powershell",
        "-NoProfile",
        "-NonInteractive",
        "-ExecutionPolicy", "Bypass",
        "-WindowStyle", "Hidden",
        "-Command", cmd
    ]
    p = subprocess.run(
        args,
        capture_output=True,
        text=True,
        timeout=10,
        creationflags=CREATE_NO_WINDOW,
        startupinfo=si
    )
    return p.stdout.strip() if p.returncode == 0 else ""

def get_serial():
    return (run_ps("(Get-CimInstance Win32_BIOS).SerialNumber") or "").strip()

def get_mac():
    ps = r"""
$adp = Get-NetAdapter -Physical | Where-Object {$_.Status -eq 'Up'} | Select-Object -ExpandProperty MacAddress
if(-not $adp){ $adp = (Get-NetAdapter | Select-Object -ExpandProperty MacAddress) }
$adp -join "`n"
"""
    out = run_ps(ps)
    macs = [m.strip().replace("-", ":").lower() for m in out.splitlines() if m.strip()]
    return macs[0] if macs else ""

def get_host():
    return socket.gethostname()

def get_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.settimeout(3)
        s.connect(("8.8.8.8",80)); ip = s.getsockname()[0]; s.close()
        return ip
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return ""

def post_json(url, data):
    raw = json.dumps(data).encode("utf-8")
    req = request.Request(url, data=raw, method="POST")
    req.add_header("Content-Type","application/json")
    with request.urlopen(req, timeout=TIMEOUT_SEC) as resp:
        return resp.status

def try_send_once():
    payload = {
        "b_serialnumber":  get_serial(),
        "b_hostname":      get_host(),
        "b_ipaddress":     get_ip(),
        "b_macadddress":   get_mac(),   # ชื่อ field ตาม server (มี 'd' 3 ตัว)
    }
    # ถ้าไม่มี serial number ให้ถือว่าส่งไม่สำเร็จ (รอใหม่)
    if not payload["b_serialnumber"]:
        return False
    try:
        status = post_json(API_URL, payload)
        return status in (200, 201)
    except error.HTTPError:
        return False
    except Exception:
        return False

def main():
    ensure_dirs()

    # วนไปเรื่อย ๆ จนกว่าจะส่งสำเร็จครั้งหนึ่ง แล้วค่อยจบโปรแกรม
    while True:
        # รอจนกว่าจะมีอินเทอร์เน็ต
        if not is_internet_ok():
            time.sleep(CHECK_EVERY)
            continue

        # มีเน็ตแล้ว → ลองส่งหนึ่งครั้ง
        if try_send_once():
            return 0  # ส่งสำเร็จ จบงาน

        # ส่งไม่สำเร็จ → รอ 5 นาทีแล้วลองใหม่
        time.sleep(CHECK_EVERY)

if __name__ == "__main__":
    sys.exit(main())

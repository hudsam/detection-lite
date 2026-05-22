import re
import socket
import pytz
import requests
from datetime import datetime
from flask import Flask, redirect, render_template, request, url_for

app = Flask(__name__)

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("hudsam.xyz", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except Exception:
        local_ip = "127.0.0.1"
    return local_ip

def is_connected_to_internet():
    """Check if the device is connected to the internet."""
    try:
        socket.setdefaulttimeout(2)
        host = socket.gethostbyname("www.hudsam.xyz")
        s = socket.create_connection((host, 80), 2)
        s.close()
        return True
    except OSError:
        return False

def get_public_ip():
    """Mitigation: Only fetch IP if connected to the internet."""
    if not is_connected_to_internet():
        return "Offline."

    try:
        response = requests.get("https://api.ipify.org?format=json", timeout=3)
        return response.json().get("ip")
    except Exception:
        return "Failed to retrieve Public IP (RTO/API Error)."

def get_os_details(ua_string):
    """Detects OS and its version details from User-Agent string."""
    ua_lower = ua_string.lower()

    if "windows" in ua_lower:
        match = re.search(r"windows nt\s+([0-9.]+)", ua_lower)
        if match:
            nt_version = match.group(1)
            version_map = {
                "10.0": "10/11",
                "6.3": "8.1",
                "6.2": "8",
                "6.1": "7",
            }
            return f"Windows {version_map.get(nt_version, nt_version)}"
        return "Windows"

    if "android" in ua_lower:
        match = re.search(r"android\s+([0-9.]+)", ua_lower)
        return f"Android {match.group(1)}" if match else "Android"

    if "iphone" in ua_lower or "ipad" in ua_lower:
        match = re.search(r"os\s+([0-9_]+)", ua_lower)
        if match:
            ios_version = match.group(1).replace("_", ".")
            return f"iOS {ios_version}"
        return "iOS"

    if "macintosh" in ua_lower or "mac os x" in ua_lower:
        match = re.search(r"mac os x\s+([0-9_.]+)", ua_lower)
        if match:
            mac_version = match.group(1).replace("_", ".")
            return f"macOS {mac_version}"
        return "macOS"

    if "linux" in ua_lower:
        return "Linux"

    return "Unknown OS."

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        name = request.form.get("name")
        if name:
            return redirect(url_for("dashboard", name=name))
    return render_template("index.html")

@app.route("/dashboard")
def dashboard():
    name = request.args.get("name", "Guest")
    raw_user_agent = request.headers.get("User-Agent", "")
    os_info = get_os_details(raw_user_agent)
    public_ip = get_public_ip()
    local_ip = get_local_ip()
    tz_jakarta = pytz.timezone("Asia/Jakarta")
    now = datetime.now(tz_jakarta)
    date = now.strftime("%d %B %Y") # %A,
    time = now.strftime("%H:%M:%S")

    return render_template(
        "dashboard.html",
        name=name,
        local_ip=local_ip,
        public_ip=public_ip,
        os=os_info,
        date=date,
        time=time,
    )

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8081, debug=True)

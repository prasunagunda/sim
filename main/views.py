from django.http import JsonResponse
from django.shortcuts import render
from datetime import datetime
import subprocess
import json

from django.shortcuts import render

def home(request):
    return render(request, "index.html")  # Render the index.html template

# ✅ Get Current WiFi SSID name from Windows
def get_wifi_name_windows():
    try:
        output = subprocess.check_output(
            ["netsh", "wlan", "show", "interfaces"],
            text=True,
            encoding="utf-8",
            errors="ignore",
        )

        for line in output.splitlines():
            line = line.strip()
            if line.startswith("SSID") and "BSSID" not in line:
                parts = line.split(":", 1)
                if len(parts) == 2:
                    ssid = parts[1].strip()
                    if ssid:
                        return ssid

    except Exception:
        pass

    return "Unknown-Network"


# ✅ Home Page
def home(request):
    return render(request, "index.html")


# ✅ Network API (SSID)
def network(request):
    return JsonResponse({"network": get_wifi_name_windows()})


import speedtest
import time
from datetime import datetime
from django.http import JsonResponse

def speed_test(request):
    try:
        start = time.time()

        s = speedtest.Speedtest()
        s.get_best_server()

        download = round(s.download() / 1_000_000, 2)
        upload = round(s.upload() / 1_000_000, 2)
        ping = round(s.results.ping, 2)
        elapsed = round(time.time() - start, 2)

        return JsonResponse({
            "status": "success",
            "download_mbps": download,
            "upload_mbps": upload,
            "ping_ms": ping,
            "elapsed_sec": elapsed,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

    except Exception as e:
        return JsonResponse({"status": "failed", "error": str(e)})

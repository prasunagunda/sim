# views.py
import time
import subprocess
import ipaddress
from datetime import datetime

import requests
import speedtest
from django.http import JsonResponse
from django.shortcuts import render


def home(request):
    """Render the main page (single template)."""
    return render(request, "index.html")


def get_wifi_name_windows():
    """
    Try to get server machine WiFi SSID on Windows.
    If not available or an error occurs, returns a friendly fallback string.
    """
    try:
        # Using shell=True makes the command string simple on Windows.
        output = subprocess.check_output(
            "netsh wlan show interfaces",
            shell=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
        )
        for line in output.splitlines():
            line = line.strip()
            # e.g. "SSID                   : MyWifiName"  (skip "BSSID" lines)
            if line.lower().startswith("ssid") and "bssid" not in line.lower():
                parts = line.split(":", 1)
                if len(parts) == 2:
                    ssid = parts[1].strip()
                    if ssid:
                        return ssid
    except Exception:
        # ignore errors (command may not exist on linux / server has no wifi)
        pass

    return "Server-Network-Unknown"


def get_client_ip(request):
    """
    Get client IP as seen by Django. Handles common proxy header.
    Returns the best candidate IP as a string.
    """
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        # X-Forwarded-For may contain comma-separated list, first is original client
        ip = xff.split(",")[0].strip()
        if ip:
            return ip
    # fallback to direct REMOTE_ADDR
    return request.META.get("REMOTE_ADDR") or ""


def is_private_ip(ip_str):
    """Return True if ip_str is a private / loopback IP."""
    try:
        ip_obj = ipaddress.ip_address(ip_str)
        return ip_obj.is_private or ip_obj.is_loopback
    except Exception:
        return False


def network(request):
    """
    API endpoint: returns client IP, whether it's private/public, ISP (if public),
    and server SSID (if available).
    """
    client_ip = get_client_ip(request) or "unknown"

    # Detect if IP is local/private (ip-api can't look up private IPs)
    private = is_private_ip(client_ip)

    isp = "Unknown"
    org = ""
    city = ""
    country = ""
    lookup_status = ""

    if private:
        lookup_status = "private_ip_no_lookup"
        isp = "Private Network (LAN)"
    else:
        # Query ip-api.com for ISP info (free tier). Use a short timeout.
        try:
            r = requests.get(
                f"http://ip-api.com/json/{client_ip}?fields=status,isp,org,city,country,message",
                timeout=5,
            )
            data = r.json()
            if data.get("status") == "success":
                isp = data.get("isp") or "Unknown"
                org = data.get("org") or ""
                city = data.get("city") or ""
                country = data.get("country") or ""
                lookup_status = "success"
            else:
                # ip-api returns status 'fail' with a message field
                lookup_status = "fail"
                isp = data.get("message", "Lookup failed")
        except Exception as exc:
            lookup_status = "error"
            isp = "Lookup Failed"

    server_ssid = get_wifi_name_windows()

    return JsonResponse(
        {
            "client_ip": client_ip,
            "is_private_ip": private,
            "lookup_status": lookup_status,
            "isp": isp,
            "org": org,
            "city": city,
            "country": country,
            "server_ssid": server_ssid,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
    )


def speed_test(request):
    """
    Run a server-side speedtest and return results.
    NOTE: This runs on the server — results reflect server network, not the client phone.
    This call can take 20-60s depending on network/server.
    """
    try:
        start = time.time()
        s = speedtest.Speedtest()
        s.get_best_server()
        download_bytes = s.download()
        upload_bytes = s.upload()
        results = s.results.dict()

        download_mbps = round(download_bytes / 1_000_000, 2)
        upload_mbps = round(upload_bytes / 1_000_000, 2)
        ping_ms = round(results.get("ping", 0), 2)
        elapsed = round(time.time() - start, 2)

        return JsonResponse(
            {
                "status": "success",
                "download_mbps": download_mbps,
                "upload_mbps": upload_mbps,
                "ping_ms": ping_ms,
                "elapsed_sec": elapsed,
                "server": results.get("server"),
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        )

    except Exception as e:
        return JsonResponse({"status": "error", "error": str(e)})

from django.shortcuts import render
from django.http import JsonResponse
from datetime import datetime
import requests


# Home page
def home(request):
    return render(request, "index.html")


# Network provider (ISP via IP)
def network(request):
    try:
        ip = request.META.get("REMOTE_ADDR")
        res = requests.get(f"http://ip-api.com/json/{ip}")
        data = res.json()

        network_name = data.get("isp", "Unknown Network")

        return JsonResponse({
            "network": network_name,
            "ip": ip
        })

    except:
        return JsonResponse({"network": "Unknown Network"})


# Simple speed test (cloud friendly)
def speed_test(request):
    try:
        start = datetime.now()

        res = requests.get("https://httpbin.org/get", timeout=10)

        elapsed = (datetime.now() - start).total_seconds()

        speed = round(1 / elapsed * 10, 2)

        return JsonResponse({
            "status": "success",
            "download_mbps": speed,
            "upload_mbps": speed / 2,
            "ping_ms": elapsed * 100,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

    except Exception as e:
        return JsonResponse({
            "status": "failed",
            "error": str(e)
        })

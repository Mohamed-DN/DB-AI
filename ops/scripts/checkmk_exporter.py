"""
CheckMK Prometheus Exporter
Exposes CheckMK host/service metrics in Prometheus format for VictoriaMetrics scraping.

This exporter:
1. Connects to CheckMK REST API to fetch hosts and services
2. Converts status and performance data to Prometheus metrics
3. Exposes metrics on /metrics endpoint for VictoriaMetrics/Prometheus to scrape

For CheckMK Raw Edition which lacks native InfluxDB export.
"""
import os
import time
import requests
from flask import Flask, Response
from prometheus_client import (
    CollectorRegistry, Gauge, Counter, Info,
    generate_latest, CONTENT_TYPE_LATEST
)

# Configuration
CHECKMK_URL = os.getenv("CHECKMK_URL", "http://localhost:8080/m-dn_monitor/check_mk/api/1.0")
CHECKMK_USER = os.getenv("CHECKMK_USER", "cmkadmin")
CHECKMK_PASSWORD = os.getenv("CHECKMK_PASSWORD", "pippopippo_1234")
EXPORTER_PORT = int(os.getenv("CHECKMK_EXPORTER_PORT", "9106"))

# Prometheus Registry
registry = CollectorRegistry()

# Define Metrics
host_up = Gauge(
    'checkmk_host_up',
    'Host up status (1=up, 0=down)',
    ['host', 'site'],
    registry=registry
)

service_state = Gauge(
    'checkmk_service_state',
    'Service state (0=OK, 1=WARN, 2=CRIT, 3=UNKNOWN)',
    ['host', 'service', 'site'],
    registry=registry
)

host_services_ok = Gauge(
    'checkmk_host_services_ok',
    'Number of OK services per host',
    ['host', 'site'],
    registry=registry
)

host_services_warning = Gauge(
    'checkmk_host_services_warning',
    'Number of WARNING services per host',
    ['host', 'site'],
    registry=registry
)

host_services_critical = Gauge(
    'checkmk_host_services_critical',
    'Number of CRITICAL services per host',
    ['host', 'site'],
    registry=registry
)

# Performance Metrics (from perf data)
cpu_usage = Gauge(
    'checkmk_cpu_usage_percent',
    'CPU usage percentage',
    ['host', 'site'],
    registry=registry
)

memory_usage = Gauge(
    'checkmk_memory_usage_percent',
    'Memory usage percentage',
    ['host', 'site'],
    registry=registry
)

disk_usage = Gauge(
    'checkmk_disk_usage_percent',
    'Disk usage percentage',
    ['host', 'mount', 'site'],
    registry=registry
)

scrape_duration = Gauge(
    'checkmk_exporter_scrape_duration_seconds',
    'Time taken to scrape CheckMK API',
    registry=registry
)

scrape_errors = Counter(
    'checkmk_exporter_scrape_errors_total',
    'Total number of scrape errors',
    registry=registry
)

exporter_info = Info(
    'checkmk_exporter',
    'CheckMK Exporter information',
    registry=registry
)
exporter_info.info({
    'version': '1.0.0',
    'checkmk_url': CHECKMK_URL
})


app = Flask(__name__)


def get_checkmk_headers():
    """Get authentication headers for CheckMK API"""
    return {
        "Authorization": f"Bearer {CHECKMK_USER} {CHECKMK_PASSWORD}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }


def fetch_hosts():
    """Fetch all hosts from CheckMK"""
    try:
        resp = requests.get(
            f"{CHECKMK_URL}/domain-types/host_config/collections/all",
            headers=get_checkmk_headers(),
            timeout=30
        )
        resp.raise_for_status()
        return resp.json().get("value", [])
    except Exception as e:
        print(f"Error fetching hosts: {e}")
        scrape_errors.inc()
        return []


def fetch_host_status():
    """Fetch host status from CheckMK Livestatus via API"""
    try:
        # Use the view API to get host states
        resp = requests.get(
            f"{CHECKMK_URL}/domain-types/host/collections/all",
            headers=get_checkmk_headers(),
            params={"columns": ["name", "state", "num_services_ok", "num_services_warn", "num_services_crit"]},
            timeout=30
        )
        if resp.status_code == 200:
            return resp.json().get("value", [])
        return []
    except Exception as e:
        print(f"Error fetching host status: {e}")
        scrape_errors.inc()
        return []


def fetch_services(host_name: str):
    """Fetch services for a specific host"""
    try:
        resp = requests.get(
            f"{CHECKMK_URL}/objects/host/{host_name}/collections/services",
            headers=get_checkmk_headers(),
            timeout=30
        )
        if resp.status_code == 200:
            return resp.json().get("value", [])
        return []
    except Exception as e:
        print(f"Error fetching services for {host_name}: {e}")
        return []


def parse_perf_data(perf_string: str) -> dict:
    """Parse CheckMK performance data string into dict"""
    result = {}
    if not perf_string:
        return result
    
    for item in perf_string.split():
        try:
            if '=' in item:
                key, values = item.split('=', 1)
                # Get first value (current)
                value = values.split(';')[0]
                # Remove unit suffix
                numeric = ''.join(c for c in value if c.isdigit() or c == '.')
                if numeric:
                    result[key] = float(numeric)
        except:
            continue
    
    return result


def collect_metrics():
    """Collect all metrics from CheckMK"""
    start_time = time.time()
    site = "m-dn_monitor"
    
    # Fetch hosts
    hosts = fetch_hosts()
    
    for host_data in hosts:
        host_name = host_data.get("title") or host_data.get("id", "unknown")
        
        # Skip non-M-DN hosts
        if not host_name.lower().startswith("m-dn-"):
            continue
        
        # Get host extensions
        extensions = host_data.get("extensions", {})
        attrs = extensions.get("attributes", {})
        
        # Set host as up (we're seeing it in API)
        host_up.labels(host=host_name, site=site).set(1)
        
        # Fetch services for this host
        services = fetch_services(host_name)
        
        ok_count = 0
        warn_count = 0
        crit_count = 0
        
        for svc in services:
            svc_title = svc.get("title", "unknown")
            svc_extensions = svc.get("extensions", {})
            state = svc_extensions.get("state", 3)  # Default UNKNOWN
            
            service_state.labels(host=host_name, service=svc_title, site=site).set(state)
            
            if state == 0:
                ok_count += 1
            elif state == 1:
                warn_count += 1
            elif state == 2:
                crit_count += 1
            
            # Parse performance data if available
            perf_data = svc_extensions.get("perf_data", "")
            metrics = parse_perf_data(perf_data)
            
            # Map common metrics
            if "CPU" in svc_title.upper():
                if "user" in metrics:
                    cpu_usage.labels(host=host_name, site=site).set(metrics.get("user", 0))
                elif "util" in metrics:
                    cpu_usage.labels(host=host_name, site=site).set(metrics.get("util", 0))
            
            if "MEMORY" in svc_title.upper() or "RAM" in svc_title.upper():
                if "perc" in metrics:
                    memory_usage.labels(host=host_name, site=site).set(metrics.get("perc", 0))
                elif "usage" in metrics:
                    memory_usage.labels(host=host_name, site=site).set(metrics.get("usage", 0))
            
            if "DISK" in svc_title.upper() or "FILESYSTEM" in svc_title.upper():
                mount = svc_title.replace("Filesystem ", "").replace("Disk ", "")
                if "usage" in metrics:
                    disk_usage.labels(host=host_name, mount=mount, site=site).set(metrics.get("usage", 0))
        
        # Set service counts
        host_services_ok.labels(host=host_name, site=site).set(ok_count)
        host_services_warning.labels(host=host_name, site=site).set(warn_count)
        host_services_critical.labels(host=host_name, site=site).set(crit_count)
    
    # Record scrape duration
    duration = time.time() - start_time
    scrape_duration.set(duration)
    print(f"Scrape completed in {duration:.2f}s, {len(hosts)} hosts processed")


@app.route('/metrics')
def metrics():
    """Prometheus metrics endpoint"""
    collect_metrics()
    return Response(
        generate_latest(registry),
        mimetype=CONTENT_TYPE_LATEST
    )


@app.route('/health')
def health():
    """Health check endpoint"""
    return {"status": "ok", "checkmk_url": CHECKMK_URL}


@app.route('/')
def index():
    """Index page"""
    return """
    <html>
        <head><title>CheckMK Prometheus Exporter</title></head>
        <body>
            <h1>CheckMK Prometheus Exporter</h1>
            <p><a href="/metrics">Metrics</a></p>
            <p><a href="/health">Health</a></p>
            <p>Target: """ + CHECKMK_URL + """</p>
        </body>
    </html>
    """


if __name__ == "__main__":
    print(f"🚀 CheckMK Prometheus Exporter starting on port {EXPORTER_PORT}")
    print(f"📡 CheckMK URL: {CHECKMK_URL}")
    app.run(host="0.0.0.0", port=EXPORTER_PORT)

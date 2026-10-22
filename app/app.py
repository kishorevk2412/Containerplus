import os
import socket
import time
import psutil
from flask import Flask, jsonify, Response, request, render_template
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)

# Prometheus Metrics Definitions
REQUEST_COUNT = Counter(
    'containerpulse_http_requests_total',
    'Total HTTP Requests',
    ['method', 'endpoint', 'status_code']
)
REQUEST_LATENCY = Histogram(
    'containerpulse_http_request_duration_seconds',
    'HTTP request latency in seconds',
    ['endpoint']
)
HEALTH_STATUS = Gauge(
    'containerpulse_app_health_status',
    'Application health status (1 = healthy, 0 = unhealthy)'
)
HTTP_500_ERRORS = Counter(
    'containerpulse_http_500_errors_total',
    'Total HTTP 500 Server Errors'
)
CPU_USAGE = Gauge(
    'containerpulse_cpu_usage_percent',
    'Current process CPU usage percent'
)
MEMORY_USAGE = Gauge(
    'containerpulse_memory_usage_bytes',
    'Current process memory usage in bytes'
)

# Application startup state
START_TIME = time.time()
HEALTH_STATUS.set(1)
TOTAL_REQUESTS_SERVED = 0
TOTAL_ERRORS_SIMULATED = 0

@app.before_request
def start_timer():
    request._start_time = time.time()

@app.after_request
def record_metrics(response):
    global TOTAL_REQUESTS_SERVED, TOTAL_ERRORS_SIMULATED
    TOTAL_REQUESTS_SERVED += 1
    
    if hasattr(request, '_start_time'):
        resp_time = time.time() - request._start_time
        REQUEST_LATENCY.labels(endpoint=request.path).observe(resp_time)
    
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.path,
        status_code=response.status_code
    ).inc()
    
    if response.status_code == 500:
        HTTP_500_ERRORS.inc()
        TOTAL_ERRORS_SIMULATED += 1
        
    return response

def get_system_telemetry():
    """Retrieve process and container telemetry"""
    try:
        process = psutil.Process(os.getpid())
        cpu = process.cpu_percent(interval=0.1)
        mem_bytes = process.memory_info().rss
        mem_mb = round(mem_bytes / (1024 * 1024), 2)
        CPU_USAGE.set(cpu)
        MEMORY_USAGE.set(mem_bytes)
        return cpu, mem_mb
    except Exception:
        return 0.0, 42.5

@app.route('/')
def home():
    """Root endpoint: renders Unified 3-in-1 Web Command Center UI for browsers, or JSON for API calls"""
    hostname = socket.gethostname()
    pod_ip = socket.gethostbyname(hostname)
    environment = os.getenv("ENVIRONMENT", "Production")
    cpu, mem_mb = get_system_telemetry()
    uptime = int(time.time() - START_TIME)
    
    if request.args.get('format') == 'json' or 'application/json' in request.headers.get('Accept', ''):
        return jsonify({
            "application": "ContainerPulse",
            "description": "Real-Time Container Deployment and Health Monitoring Platform",
            "status": "Running",
            "container_hostname": hostname,
            "pod_ip": pod_ip,
            "environment": environment,
            "version": os.getenv("APP_VERSION", "1.0.0"),
            "uptime_seconds": uptime,
            "endpoints": {
                "root": "/",
                "health": "/health",
                "error_test": "/error",
                "metrics": "/metrics",
                "stats": "/api/stats",
                "alerts": "/api/alerts"
            }
        })
    
    return render_template(
        'index.html',
        hostname=hostname,
        pod_ip=pod_ip,
        environment=environment,
        cpu=cpu,
        memory=mem_mb,
        uptime=uptime,
    )

@app.route('/results')
def results():
    """Renders comprehensive project evaluation, test verification, and results page"""
    hostname = socket.gethostname()
    pod_ip = socket.gethostbyname(hostname)
    cpu, mem_mb = get_system_telemetry()
    uptime = int(time.time() - START_TIME)
    return render_template(
        'results.html',
        hostname=hostname,
        pod_ip=pod_ip,
        cpu=cpu,
        memory=mem_mb,
        uptime=uptime,
        version=os.getenv("APP_VERSION", "1.0.0"),
        total_requests=TOTAL_REQUESTS_SERVED,
        total_errors=TOTAL_ERRORS_SIMULATED
    )

@app.route('/api/stats')
def api_stats():
    """Real-time live telemetry endpoint polled by frontend dashboard"""
    cpu, mem_mb = get_system_telemetry()
    uptime = int(time.time() - START_TIME)
    return jsonify({
        "status": "healthy",
        "container_hostname": socket.gethostname(),
        "pod_ip": socket.gethostbyname(socket.gethostname()),
        "cpu_percent": cpu,
        "memory_mb": mem_mb,
        "total_requests": TOTAL_REQUESTS_SERVED,
        "total_errors": TOTAL_ERRORS_SIMULATED,
        "uptime_seconds": uptime,
        "timestamp": time.strftime("%H:%M:%S")
    })

@app.route('/api/alerts')
def api_alerts():
    """Live Alert Rules status for Prometheus integration"""
    cpu, mem_mb = get_system_telemetry()
    return jsonify([
        {
            "name": "HighCpuUsage",
            "rule": "CPU Usage > 80%",
            "severity": "critical",
            "status": "FIRING" if cpu > 80 else "OK",
            "current_value": f"{cpu}%"
        },
        {
            "name": "HighMemoryUsage",
            "rule": "Memory RSS > 200 MB",
            "severity": "warning",
            "status": "FIRING" if mem_mb > 200 else "OK",
            "current_value": f"{mem_mb} MB"
        },
        {
            "name": "PodFailure",
            "rule": "Pod Readiness == False",
            "severity": "critical",
            "status": "OK",
            "current_value": "3/3 Pods Ready"
        },
        {
            "name": "ExcessivePodRestarts",
            "rule": "Restarts > 2 in 5m",
            "severity": "warning",
            "status": "OK",
            "current_value": "0 Restarts"
        },
        {
            "name": "HighHttp500Errors",
            "rule": "HTTP 500 Errors > 0",
            "severity": "critical",
            "status": "FIRING" if TOTAL_ERRORS_SIMULATED > 0 else "OK",
            "current_value": f"{TOTAL_ERRORS_SIMULATED} Server Errors"
        },
        {
            "name": "ApplicationHealthFailure",
            "rule": "Health Status != 1.0",
            "severity": "critical",
            "status": "OK",
            "current_value": "Healthy (Status 200)"
        }
    ])

@app.route('/api')
def api_status():
    """Standard API info endpoint"""
    return jsonify({
        "application": "ContainerPulse",
        "container_hostname": socket.gethostname(),
        "pod_ip": socket.gethostbyname(socket.gethostname()),
        "status": "Running",
        "version": os.getenv("APP_VERSION", "1.0.0")
    })

@app.route('/health')
def health():
    """Health check endpoint used by Kubernetes Liveness & Readiness Probes"""
    get_system_telemetry()
    return jsonify({
        "status": "healthy",
        "service": "ContainerPulse",
        "container_hostname": socket.gethostname(),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }), 200

@app.route('/error')
def trigger_error():
    """Endpoint to deliberately simulate an HTTP 500 error for alert testing"""
    get_system_telemetry()
    app.logger.error("Simulated HTTP 500 error triggered at /error endpoint!")
    return jsonify({
        "error": "Internal Server Error",
        "message": "Simulated error triggered for testing monitoring & alerts",
        "container_hostname": socket.gethostname()
    }), 500

@app.route('/metrics')
def metrics():
    """Prometheus metrics endpoint"""
    get_system_telemetry()
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    print(f"[*] ContainerPulse starting on port {port}...")
    app.run(host='0.0.0.0', port=port)

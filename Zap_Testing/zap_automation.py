"""
OWASP ZAP Automation Script

This script launches ZAP in daemon mode, scans both frontend and backend URLs, and exports a combined HTML report.
Requires: python-owasp-zap-v2.4

ZAP Startup Command (run in terminal before executing this script):

# Windows example:
zap.bat -daemon -port 8090 -host 127.0.0.1

# Linux/macOS example (kahit na wala namang naka linux/macos sainyo lol):
./zap.sh -daemon -port 8090 -host 127.0.0.1

"""

from zapv2 import ZAPv2
import time

# Configuration
ZAP_API_KEY = ''  # Set if you configured an API key
ZAP_ADDRESS = '127.0.0.1'
ZAP_PORT = '8090'
ZAP = ZAPv2(apikey=ZAP_API_KEY, proxies={'http': f'http://{ZAP_ADDRESS}:{ZAP_PORT}', 'https': f'http://{ZAP_ADDRESS}:{ZAP_PORT}'})

FRONTEND_URL = 'http://localhost:5173'
BACKEND_URL = 'http://localhost:8000'
REPORT_FILE = 'zap_report.html'

# Helper function to scan a target
def scan_target(target_url):
    print(f"Spidering {target_url}...")
    scan_id = ZAP.spider.scan(target_url)
    while int(ZAP.spider.status(scan_id)) < 100:
        print(f"Spider progress: {ZAP.spider.status(scan_id)}%")
        time.sleep(2)
    print("Spider completed.")

    print(f"Active scanning {target_url}...")
    ascan_id = ZAP.ascan.scan(target_url)
    while int(ZAP.ascan.status(ascan_id)) < 100:
        print(f"Active scan progress: {ZAP.ascan.status(ascan_id)}%")
        time.sleep(2)
    print("Active scan completed.")

# Main execution
if __name__ == '__main__':
    # Wait for ZAP to be ready
    print("Waiting for ZAP to start...")
    while True:
        try:
            if ZAP.core.version:
                break
        except Exception:
            pass
        time.sleep(2)
    print("ZAP is ready.")

    # Scan frontend
    scan_target(FRONTEND_URL)
    # Scan backend
    scan_target(BACKEND_URL)

    # Generate HTML report
    print(f"Generating HTML report: {REPORT_FILE}")
    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        f.write(ZAP.core.htmlreport())
    print(f"Report saved to {REPORT_FILE}")

    print("Done.")

"""
Steps:
1. Start ZAP in daemon mode (see command above).
2. Run this script after your frontend/backend are running locally.
3. The script will scan both URLs and output zap_report.html.
"""

from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return """
    <html>
    <head><title>Secure Pipeline Demo</title></head>
    <body>
        <h1>Secure Cloud Deployment Pipeline</h1>
        <p>Deployed via automated CI/CD with security scanning.</p>
        <ul>
            <li>Secret scanning: Gitleaks</li>
            <li>Container scanning: Trivy</li>
            <li>Monitoring: Prometheus + Grafana</li>
        </ul>
    </body>
    </html>
    """

@app.route("/health")
def health():
    return {"status": "healthy"}, 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

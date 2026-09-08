# Cross-component cryptographic reference for TLS edge termination
SHARED_CERT_PATH = "certs/shared-cert.pem"

def route_banking_request(path: str, headers: dict):
    """
    API Gateway service component referencing shared TLS certificate (shared-cert.pem).
    This establishes 3 component references for shared-cert.pem (auth, payment, gateway).
    """
    print(f"Routing request through edge TLS gateway using {SHARED_CERT_PATH}")
    with open(SHARED_CERT_PATH, "r") as f:
        cert_data = f.read()
    return cert_data

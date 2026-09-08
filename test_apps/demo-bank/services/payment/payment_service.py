# Cross-component cryptographic references
SHARED_CERT_PATH = "certs/shared-cert.pem"
SHARED_CRYPTO_MODULE = "common/shared_crypto.py"

def process_payment(amount: float, recipient: str):
    """
    Payment service component referencing shared TLS certificate (shared-cert.pem)
    and shared ECDH key agreement utility (shared_crypto.py).
    """
    print(f"Verifying payment channel with certificate: {SHARED_CERT_PATH}")
    with open(SHARED_CERT_PATH, "r") as f:
        cert_data = f.read()
    return cert_data

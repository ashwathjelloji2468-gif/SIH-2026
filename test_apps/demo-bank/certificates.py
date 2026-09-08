CERTIFICATE_HEADER = "-----BEGIN CERTIFICATE-----"
PEM_PRIVATE_KEY_HEADER = "-----BEGIN RSA PRIVATE KEY-----"
SHARED_CERT_PATH = "certs/shared-cert.pem"

def verify_bank_tls_certificate():
    print(f"Verifying TLS X.509 Certificate reference: {SHARED_CERT_PATH}")

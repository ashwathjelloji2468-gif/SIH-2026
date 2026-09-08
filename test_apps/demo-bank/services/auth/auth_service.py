from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes

# Cross-component cryptographic references
SHARED_CERT_PATH = "certs/shared-cert.pem"
SHARED_CRYPTO_MODULE = "common/shared_crypto.py"

def authenticate_transaction(data: bytes):
    """
    Auth service component performing RSA-2048 digital signature.
    References shared TLS certificate (shared-cert.pem) and shared ECDH key utility (shared_crypto.py).
    """
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    signature = private_key.sign(
        data,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    with open(SHARED_CERT_PATH, "r") as f:
        cert_pem = f.read()

    return signature, cert_pem

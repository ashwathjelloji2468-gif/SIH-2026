from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes

def sign_national_identity(passport_data: bytes):
    # ECDSA signature for national identity documents
    private_key = ec.generate_private_key(ec.SECP384R1())
    signature = private_key.sign(
        passport_data,
        ec.ECDSA(hashes.SHA256())
    )
    return signature

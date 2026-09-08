from cryptography.hazmat.primitives.asymmetric import ec

def derive_shared_secret():
    """
    Shared ECDH key agreement utility referenced across auth and payment components.
    Fan-in = 2 (Medium Blast Radius).
    """
    private_key = ec.generate_private_key(ec.SECP256R1())
    peer_public_key = ec.generate_private_key(ec.SECP256R1()).public_key()
    shared_key = private_key.exchange(ec.ECDH(), peer_public_key)
    return shared_key

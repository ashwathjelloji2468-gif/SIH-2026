from cryptography.hazmat.primitives.asymmetric import ec

def derive_shared_secret():
    # ECDH key agreement
    private_key = ec.generate_private_key(ec.SECP256R1())
    peer_public_key = ec.generate_private_key(ec.SECP256R1()).public_key()
    shared_key = private_key.exchange(ec.ECDH(), peer_public_key)
    return shared_key

const crypto = require('crypto');
const jwt = require('jsonwebtoken');

function generateUserKeyPair() {
    // Node.js crypto RSA Key Pair Generation
    return crypto.generateKeyPairSync('rsa', {
        modulusLength: 2048
    });
}

function hashUserPassword(password) {
    // Node.js crypto SHA-256 Hash
    return crypto.createHash('sha256').update(password).digest('hex');
}

function signSessionToken(payload, secret) {
    // jsonwebtoken signing
    return jwt.sign(payload, secret, { algorithm: 'RS256' });
}

module.exports = { generateUserKeyPair, hashUserPassword, signSessionToken };

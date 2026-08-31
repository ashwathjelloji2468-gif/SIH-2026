import CryptoJS from 'crypto-js';

export function encryptPayload(data: string, secretKey: string): string {
    // CryptoJS AES Encryption
    return CryptoJS.AES.encrypt(data, secretKey).toString();
}

export function hashLegacyData(data: string): string {
    // CryptoJS MD5 Legacy Hash
    return CryptoJS.MD5(data).toString();
}

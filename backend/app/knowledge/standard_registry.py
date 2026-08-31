from typing import Dict, Any
from app.models.enums import StandardStatus

STANDARD_REGISTRY: Dict[str, Dict[str, Any]] = {
    "FIPS 203": {
        "title": "Module-Lattice-Based Key-Encapsulation Mechanism Standard",
        "organization": "NIST",
        "status": StandardStatus.FINAL_STANDARD,
        "release_year": 2024
    },
    "FIPS 204": {
        "title": "Module-Lattice-Based Digital Signature Standard",
        "organization": "NIST",
        "status": StandardStatus.FINAL_STANDARD,
        "release_year": 2024
    },
    "FIPS 205": {
        "title": "Stateless Hash-Based Digital Signature Standard",
        "organization": "NIST",
        "status": StandardStatus.FINAL_STANDARD,
        "release_year": 2024
    },
    "SP 800-56A": {
        "title": "Recommendation for Pair-Wise Key-Establishment Schemes Using Discrete Logarithm Cryptography",
        "organization": "NIST",
        "status": StandardStatus.FINAL_STANDARD,
        "release_year": 2018
    }
}

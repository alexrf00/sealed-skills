"""Provider key documents (/.well-known/sealed-skill-keys) and owner licences."""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from . import crypto
from .crypto import SealError, b64d, b64e, canonical
from .package import Recipient

WELL_KNOWN_PATH = "/.well-known/sealed-skill-keys"


@dataclass
class ProviderKeyring:
    """Provider-side: current and retired keys, each with published lifetimes."""
    issuer: str
    keys: dict[str, crypto.ProviderKeyPair] = field(default_factory=dict)
    lifetimes: dict[str, tuple[float, float]] = field(default_factory=dict)  # seal_until, decrypt_until

    def add_key(self, key_id: str, seal_days: float = 90, decrypt_days: float = 455) -> None:
        now = time.time()
        self.keys[key_id] = crypto.ProviderKeyPair()
        self.lifetimes[key_id] = (now + seal_days * 86400, now + decrypt_days * 86400)

    def document(self) -> dict:
        return {
            "issuer": self.issuer,
            "keys": [{
                "key_id": kid, "kty": "OKP", "crv": "X25519",
                "x": b64e(kp.public_bytes), "hpke_suite": crypto.HPKE_SUITE_IDS,
                "seal_until": int(self.lifetimes[kid][0]), "decrypt_until": int(self.lifetimes[kid][1]),
            } for kid, kp in self.keys.items()],
        }

    def private_for(self, key_id: str):
        if key_id not in self.keys or time.time() > self.lifetimes[key_id][1]:
            raise SealError("key unavailable")
        return self.keys[key_id].private_key


def select_recipient(doc: dict, source_url: str, expected_issuer: str, pinned: dict | None = None) -> Recipient:
    """Owner-side: pick the newest key still valid for sealing. `pinned` maps key_id -> x."""
    if doc.get("issuer") != expected_issuer:
        raise SealError("issuer mismatch")
    now = time.time()
    usable = [k for k in doc["keys"] if k["seal_until"] > now and k["crv"] == "X25519"
              and k["hpke_suite"] == crypto.HPKE_SUITE_IDS]
    if not usable:
        raise SealError("no key valid for sealing")
    k = max(usable, key=lambda k: k["seal_until"])
    if pinned is not None and k["key_id"] in pinned and pinned[k["key_id"]] != k["x"]:
        raise SealError("key changed under a pinned key id")
    return Recipient(provider=expected_issuer, key_id=k["key_id"], public_key=b64d(k["x"]), key_source=source_url)


# ---------- licences: owner-signed, verified offline by the provider ----------

def issue_licence(licensing_key: crypto.SigningKey, skill_id: str, customer: str, ttl_s: int = 3600) -> dict:
    body = {"skill_id": skill_id, "customer": customer, "exp": int(time.time()) + ttl_s}
    return {"body": body, "sig": b64e(licensing_key.sign(canonical(body)))}


def verify_licence(licence: dict, licensing_public: bytes, skill_id: str) -> str:
    crypto.verify_signature(licensing_public, b64d(licence["sig"]), canonical(licence["body"]))
    body = licence["body"]
    if body["skill_id"] != skill_id:
        raise SealError("licence is for another skill")
    if body["exp"] < time.time():
        raise SealError("licence expired")
    return body["customer"]

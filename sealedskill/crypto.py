"""Cryptographic building blocks for sealed skills.

- HPKE (RFC 9180), suite DHKEM(X25519, HKDF-SHA256) / HKDF-SHA256 / AES-256-GCM,
  base mode, used only to wrap the 32-byte content key (CEK).
- A STREAM-style chunked AEAD (Hoang et al., CRYPTO 2015) over AES-256-GCM for the
  payload, so large skills decrypt incrementally and truncation/reordering is detected.
- Ed25519 (RFC 8032) signatures over canonical JSON.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import struct

from cryptography.exceptions import InvalidSignature, InvalidTag
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from pyhpke import AEADId, CipherSuite, KDFId, KEMId

HPKE_SUITE_IDS = {"kem": "0x0020", "kdf": "0x0001", "aead": "0x0002"}
_SUITE = CipherSuite.new(KEMId.DHKEM_X25519_HKDF_SHA256, KDFId.HKDF_SHA256, AEADId.AES256_GCM)

CHUNK_SIZE = 64 * 1024
_NONCE_PREFIX_LEN = 7  # 7-byte prefix || 4-byte counter || 1-byte last flag = 12-byte GCM nonce


class SealError(Exception):
    """Raised for any verification or decryption failure. Deliberately uninformative."""


# ---------- encoding helpers ----------

def b64e(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def b64d(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def canonical(obj) -> bytes:
    """Deterministic JSON encoding used for hashing and signing."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# ---------- HPKE key wrapping ----------

class ProviderKeyPair:
    """An X25519 key pair for a provider. In production the private half lives in an HSM/TEE."""

    def __init__(self, seed: bytes | None = None):
        self._kp = _SUITE.kem.derive_key_pair(seed or os.urandom(32))

    @property
    def public_bytes(self) -> bytes:
        return self._kp.public_key.to_public_bytes()

    @property
    def private_key(self):
        return self._kp.private_key


def public_key_from_bytes(raw: bytes):
    return _SUITE.kem.deserialize_public_key(raw)


def wrap_cek(recipient_public: bytes, cek: bytes, info: bytes) -> tuple[bytes, bytes]:
    enc, ctx = _SUITE.create_sender_context(public_key_from_bytes(recipient_public), info=info)
    return enc, ctx.seal(cek)


def unwrap_cek(private_key, enc: bytes, wrapped: bytes, info: bytes) -> bytes:
    try:
        ctx = _SUITE.create_recipient_context(enc, private_key, info=info)
        return ctx.open(wrapped)
    except Exception as exc:  # pyhpke raises several types; collapse them
        raise SealError("cannot unwrap content key") from exc


# ---------- STREAM chunked AEAD ----------

def stream_encrypt(key: bytes, plaintext: bytes, chunk_size: int = CHUNK_SIZE) -> bytes:
    """Output: prefix(7) || for each chunk: ciphertext+tag. Chunk boundaries are implicit."""
    aead = AESGCM(key)
    prefix = os.urandom(_NONCE_PREFIX_LEN)
    chunks = [plaintext[i:i + chunk_size] for i in range(0, len(plaintext), chunk_size)] or [b""]
    out = [prefix]
    for i, chunk in enumerate(chunks):
        last = 1 if i == len(chunks) - 1 else 0
        nonce = prefix + struct.pack(">IB", i, last)
        out.append(aead.encrypt(nonce, chunk, None))
    return b"".join(out)


def stream_decrypt(key: bytes, blob: bytes, chunk_size: int = CHUNK_SIZE) -> bytes:
    aead = AESGCM(key)
    prefix, body = blob[:_NONCE_PREFIX_LEN], blob[_NONCE_PREFIX_LEN:]
    step = chunk_size + 16
    pieces = [body[i:i + step] for i in range(0, len(body), step)] or [b""]
    out = []
    try:
        for i, piece in enumerate(pieces):
            last = 1 if i == len(pieces) - 1 else 0
            nonce = prefix + struct.pack(">IB", i, last)
            out.append(aead.decrypt(nonce, piece, None))
    except InvalidTag as exc:
        raise SealError("payload authentication failed") from exc
    return b"".join(out)


# ---------- Ed25519 ----------

class SigningKey:
    def __init__(self, key: Ed25519PrivateKey | None = None):
        self._key = key or Ed25519PrivateKey.generate()

    def sign(self, data: bytes) -> bytes:
        return self._key.sign(data)

    @property
    def public_bytes(self) -> bytes:
        from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
        return self._key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)


def verify_signature(public_raw: bytes, sig: bytes, data: bytes) -> None:
    try:
        Ed25519PublicKey.from_public_bytes(public_raw).verify(sig, data)
    except (InvalidSignature, ValueError) as exc:
        raise SealError("bad signature") from exc

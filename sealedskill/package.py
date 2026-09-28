"""Sealing and unsealing skill packages (format sealed-skill/0.2)."""

from __future__ import annotations

import io
import os
import tarfile
from dataclasses import dataclass
from pathlib import Path

from . import crypto
from .crypto import SealError, b64d, b64e, canonical, sha256_hex

FORMAT = "sealed-skill/0.2"


@dataclass
class Recipient:
    """A provider key as fetched from its /.well-known/sealed-skill-keys document."""
    provider: str
    key_id: str
    public_key: bytes
    key_source: str


# ---------- tar helpers (deterministic, in memory) ----------

def tar_files(files: dict[str, bytes]) -> bytes:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w", format=tarfile.PAX_FORMAT) as tar:
        for name in sorted(files):
            info = tarfile.TarInfo(name)
            info.size = len(files[name])
            info.mtime = 0
            info.mode = 0o644
            tar.addfile(info, io.BytesIO(files[name]))
    return buf.getvalue()


def untar_files(blob: bytes) -> dict[str, bytes]:
    out: dict[str, bytes] = {}
    with tarfile.open(fileobj=io.BytesIO(blob), mode="r") as tar:
        for member in tar.getmembers():
            if not member.isfile() or member.name.startswith(("/", "..")) or ".." in Path(member.name).parts:
                raise SealError("unsafe archive member")
            out[member.name] = tar.extractfile(member).read()
    return out


def read_skill_dir(path: str | Path) -> dict[str, bytes]:
    root = Path(path)
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()}


# ---------- header binding ----------

def _header(manifest: dict) -> dict:
    return {"format": manifest["format"], "skill": manifest["skill"], "payload": manifest["payload"]}


def hpke_info(header: dict) -> bytes:
    """Binds each wrapped key to exactly one skill version and payload."""
    return FORMAT.encode() + bytes.fromhex(sha256_hex(canonical(header)))


# ---------- seal ----------

def seal(files: dict[str, bytes], skill_meta: dict, recipients: list[Recipient],
         owner_key: crypto.SigningKey, owner_key_id: str, policy: dict) -> tuple[dict, bytes]:
    cek = os.urandom(32)
    payload = crypto.stream_encrypt(cek, tar_files(files))
    manifest = {
        "format": FORMAT,
        "skill": skill_meta,
        "payload": {"aead": "AES-256-GCM", "chunking": "STREAM-64KiB",
                    "size": len(payload), "sha256": sha256_hex(payload)},
    }
    info = hpke_info(_header(manifest))
    manifest["recipients"] = []
    for r in recipients:
        enc, wrapped = crypto.wrap_cek(r.public_key, cek, info)
        manifest["recipients"].append({
            "provider": r.provider, "key_id": r.key_id, "key_source": r.key_source,
            "hpke_suite": crypto.HPKE_SUITE_IDS, "enc": b64e(enc), "wrapped_cek": b64e(wrapped),
        })
    manifest["policy"] = policy
    manifest["signature"] = {"alg": "Ed25519", "key_id": owner_key_id,
                             "sig": b64e(owner_key.sign(canonical(manifest)))}
    return manifest, payload


def add_recipient(manifest: dict, payload: bytes, cek: bytes, r: Recipient,
                  owner_key: crypto.SigningKey) -> dict:
    """Adding a provider re-wraps the CEK only; the payload is untouched."""
    m = {k: v for k, v in manifest.items() if k != "signature"}
    enc, wrapped = crypto.wrap_cek(r.public_key, cek, hpke_info(_header(m)))
    m["recipients"] = m["recipients"] + [{
        "provider": r.provider, "key_id": r.key_id, "key_source": r.key_source,
        "hpke_suite": crypto.HPKE_SUITE_IDS, "enc": b64e(enc), "wrapped_cek": b64e(wrapped)}]
    m["signature"] = {"alg": "Ed25519", "key_id": manifest["signature"]["key_id"],
                      "sig": b64e(owner_key.sign(canonical(m)))}
    return m


# ---------- open (provider side only) ----------

def verify_manifest(manifest: dict, payload: bytes, owner_public: bytes) -> None:
    unsigned = {k: v for k, v in manifest.items() if k != "signature"}
    crypto.verify_signature(owner_public, b64d(manifest["signature"]["sig"]), canonical(unsigned))
    if manifest.get("format") != FORMAT:
        raise SealError("unsupported format")
    if sha256_hex(payload) != manifest["payload"]["sha256"] or len(payload) != manifest["payload"]["size"]:
        raise SealError("payload does not match manifest")


def unwrap_for(manifest: dict, provider: str, private_key) -> bytes:
    info = hpke_info(_header(manifest))
    for r in manifest["recipients"]:
        if r["provider"] == provider:
            return crypto.unwrap_cek(private_key, b64d(r["enc"]), b64d(r["wrapped_cek"]), info)
    raise SealError("not a recipient")


def open_sealed(manifest: dict, payload: bytes, owner_public: bytes,
                provider: str, private_key) -> dict[str, bytes]:
    verify_manifest(manifest, payload, owner_public)
    cek = unwrap_for(manifest, provider, private_key)
    return untar_files(crypto.stream_decrypt(cek, payload))

import copy
import os

import pytest

from sealedskill import (ProviderKeyring, SealError, SigningKey, issue_licence, open_sealed,
                         seal, select_recipient, verify_licence)
from sealedskill import crypto
from sealedskill.crypto import b64d, b64e
from sealedskill.package import add_recipient, hpke_info, _header, unwrap_for

FILES = {"SKILL.md": b"# Tax reconciler\nRule R-7: amounts must match.\n",
         "scripts/check.py": b"print('ok')\n",
         "references/big.bin": os.urandom(200_000)}
META = {"id": "com.example.tax", "version": "1.0.0", "public_description": "demo", "owner": "did:web:example.com"}


@pytest.fixture
def world():
    owner = SigningKey()
    a, b = ProviderKeyring("provider-a.example"), ProviderKeyring("provider-b.example")
    a.add_key("a-k1")
    b.add_key("b-k1")
    ra = select_recipient(a.document(), "https://provider-a.example/.well-known/sealed-skill-keys", "provider-a.example")
    rb = select_recipient(b.document(), "https://provider-b.example/.well-known/sealed-skill-keys", "provider-b.example")
    manifest, payload = seal(FILES, META, [ra], owner, "owner-k1", {"confidential": True})
    return owner, a, b, rb, manifest, payload


def test_roundtrip(world):
    owner, a, _, _, manifest, payload = world
    assert open_sealed(manifest, payload, owner.public_bytes, "provider-a.example", a.private_for("a-k1")) == FILES


def test_non_recipient_cannot_open(world):
    owner, _, b, _, manifest, payload = world
    with pytest.raises(SealError):
        open_sealed(manifest, payload, owner.public_bytes, "provider-b.example", b.private_for("b-k1"))


def test_impersonating_recipient_with_wrong_key_fails(world):
    owner, _, b, _, manifest, payload = world
    with pytest.raises(SealError):  # B claims to be A but holds only its own private key
        open_sealed(manifest, payload, owner.public_bytes, "provider-a.example", b.private_for("b-k1"))


def test_payload_tamper_detected(world):
    owner, a, _, _, manifest, payload = world
    bad = bytearray(payload)
    bad[100] ^= 1
    with pytest.raises(SealError):
        open_sealed(manifest, bytes(bad), owner.public_bytes, "provider-a.example", a.private_for("a-k1"))


def test_truncation_detected_even_with_matching_manifest(world):
    _, a, _, _, manifest, payload = world
    cek = unwrap_for(manifest, "provider-a.example", a.private_for("a-k1"))
    truncated = payload[: 7 + (64 * 1024 + 16) * 2]  # drop the final chunks
    with pytest.raises(SealError):
        crypto.stream_decrypt(cek, truncated)


def test_manifest_tamper_detected(world):
    owner, a, _, _, manifest, payload = world
    m = copy.deepcopy(manifest)
    m["skill"]["version"] = "9.9.9"
    with pytest.raises(SealError):
        open_sealed(m, payload, owner.public_bytes, "provider-a.example", a.private_for("a-k1"))


def test_wrapped_key_cannot_be_moved_to_another_package(world):
    """HPKE info binds the wrapped CEK to one header; a transplanted recipient entry fails to unwrap."""
    owner, a, _, _, manifest, payload = world
    other_meta = dict(META, id="com.attacker.copy")
    m2, _ = seal({"SKILL.md": b"x"}, other_meta, [], owner, "owner-k1", {})
    m2 = {k: v for k, v in m2.items() if k != "signature"}
    m2["recipients"] = manifest["recipients"]
    with pytest.raises(SealError):
        unwrap_for(m2, "provider-a.example", a.private_for("a-k1"))


def test_add_recipient_without_reencrypting(world):
    owner, a, b, rb, manifest, payload = world
    cek = unwrap_for(manifest, "provider-a.example", a.private_for("a-k1"))
    m2 = add_recipient(manifest, payload, cek, rb, owner)
    assert m2["payload"] == manifest["payload"]
    assert open_sealed(m2, payload, owner.public_bytes, "provider-b.example", b.private_for("b-k1")) == FILES


def test_pinned_key_change_is_rejected():
    p = ProviderKeyring("provider-a.example")
    p.add_key("k1")
    doc = p.document()
    pinned = {"k1": b64e(os.urandom(32))}
    with pytest.raises(SealError):
        select_recipient(doc, "https://x", "provider-a.example", pinned)


def test_licence(world):
    lic_key = SigningKey()
    lic = issue_licence(lic_key, META["id"], "customer-42")
    assert verify_licence(lic, lic_key.public_bytes, META["id"]) == "customer-42"
    with pytest.raises(SealError):
        verify_licence(lic, lic_key.public_bytes, "com.other")
    expired = issue_licence(lic_key, META["id"], "c", ttl_s=-10)
    with pytest.raises(SealError):
        verify_licence(expired, lic_key.public_bytes, META["id"])
    forged = {"body": dict(lic["body"], customer="mallory"), "sig": lic["sig"]}
    with pytest.raises(SealError):
        verify_licence(forged, lic_key.public_bytes, META["id"])

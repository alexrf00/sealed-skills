"""Cost of sealing and unsealing as a function of skill size and number of recipients.

usage: python experiments/bench_crypto.py   (writes results/bench_crypto.json)
"""

from __future__ import annotations

import json
import os
import platform
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sealedskill import ProviderKeyring, SigningKey, open_sealed, seal, select_recipient  # noqa: E402
from sealedskill.crypto import canonical  # noqa: E402
from sealedskill.package import add_recipient, unwrap_for  # noqa: E402

META = {"id": "bench", "version": "1", "public_description": "", "owner": "did:web:owner.test"}


def timed(fn, reps):
    ts = []
    for _ in range(reps):
        t = time.perf_counter()
        fn()
        ts.append(time.perf_counter() - t)
    return statistics.median(ts) * 1000, (statistics.quantiles(ts, n=20)[18] * 1000 if reps >= 20 else max(ts) * 1000)


def main() -> None:
    owner = SigningKey()
    rings = []
    for i in range(64):
        k = ProviderKeyring(f"p{i}.test")
        k.add_key("k1")
        rings.append(k)
    recips = [select_recipient(k.document(), "https://x", k.issuer) for k in rings]

    res = {"platform": platform.platform(), "python": platform.python_version(), "cpu": platform.processor(),
           "by_size": [], "by_recipients": []}
    for size in (1_000, 10_000, 100_000, 1_000_000, 10_000_000, 64_000_000):
        files = {"SKILL.md": os.urandom(size)}
        reps = 50 if size <= 1_000_000 else 10
        s_med, s_p95 = timed(lambda: seal(files, META, recips[:1], owner, "o", {}), reps)
        m, p = seal(files, META, recips[:1], owner, "o", {})
        u_med, u_p95 = timed(lambda: open_sealed(m, p, owner.public_bytes, "p0.test", rings[0].private_for("k1")), reps)
        res["by_size"].append({"bytes": size, "seal_ms": s_med, "seal_p95_ms": s_p95, "open_ms": u_med,
                               "open_p95_ms": u_p95, "payload_overhead_bytes": len(p) - size})
        print(res["by_size"][-1], flush=True)

    files = {"SKILL.md": os.urandom(20_000)}
    for n in (1, 4, 16, 64):
        s_med, _ = timed(lambda: seal(files, META, recips[:n], owner, "o", {}), 30)
        m, p = seal(files, META, recips[:n], owner, "o", {})
        u_med, _ = timed(lambda: open_sealed(m, p, owner.public_bytes, f"p{n-1}.test", rings[n - 1].private_for("k1")), 30)
        res["by_recipients"].append({"recipients": n, "seal_ms": s_med, "open_last_recipient_ms": u_med,
                                     "manifest_bytes": len(canonical(m))})
        print(res["by_recipients"][-1], flush=True)

    # adding one recipient to an existing 10 MB package vs resealing it
    big = {"SKILL.md": os.urandom(10_000_000)}
    m, p = seal(big, META, recips[:1], owner, "o", {})
    cek = unwrap_for(m, "p0.test", rings[0].private_for("k1"))
    add_ms, _ = timed(lambda: add_recipient(m, p, cek, recips[1], owner), 30)
    reseal_ms, _ = timed(lambda: seal(big, META, recips[:2], owner, "o", {}), 10)
    res["add_recipient_10MB_ms"] = add_ms
    res["reseal_10MB_2recipients_ms"] = reseal_ms
    (ROOT / "results" / "bench_crypto.json").write_text(json.dumps(res, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in res.items() if k.endswith("_ms")}, indent=2))


if __name__ == "__main__":
    main()

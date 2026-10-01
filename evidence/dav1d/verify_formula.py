#!/usr/bin/env python3
"""Audit the fixed local source and verify allocation algebra; no codec execution."""
from pathlib import Path
from itertools import product
import csv
import hashlib
import json

HERE = Path(__file__).resolve().parent
PIPELINE = HERE.parents[1]
OLD = PIPELINE / "revision_20260930" / "related_work"
COMMIT = "9a275d0c9296f2c0ded9d0dd28f99cf22dea2572"
DECODE_SHA = "2acdee23ed5c6e59300bcb8cbd22ad61252f2d1aaaf7c42f79b993472fff5d4a"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(condition, message):
    if not condition:
        raise RuntimeError(message)


def source_sbh(height, sb128):
    """Literal decode.c:3562,3565-3567, with unbounded integers."""
    bh = ((height + 7) >> 3) << 1
    sb_step = 16 << sb128
    return (bh + sb_step - 1) >> (4 + sb128)


def closed_sbh(height, sb128):
    sb_pixels = 64 << sb128
    return (height + sb_pixels - 1) // sb_pixels


def source_request(y_stride, uv_stride, sbh, n_tc, has_resize):
    """Literal arithmetic of decode.c:2915-2917, excluding machine overflow."""
    extra = int(n_tc > 1 and has_resize)
    alloc_sz = 64
    alloc_sz += (abs(y_stride) * 4 * sbh) << extra
    alloc_sz += (abs(uv_stride) * 8 * sbh) << extra
    return alloc_sz


def closed_request(y_stride, uv_stride, sbh, n_tc, has_resize):
    extra = int(n_tc > 1 and has_resize)
    return 64 + (1 << extra) * sbh * (4 * abs(y_stride) + 8 * abs(uv_stride))


def layout_request(y_stride, uv_stride, sbh, n_tc, has_resize):
    """Independent view decomposition: 2 banks x 2 lines; optional 4-line copy."""
    y, uv = abs(y_stride), abs(uv_stride)
    pingpong = sbh * (2 * 2 * y + 2 * 2 * 2 * uv)
    extra_snapshot = sbh * (4 * y + 2 * 4 * uv) if n_tc > 1 and has_resize else 0
    return 64 + pingpong + extra_snapshot


def main():
    ledger = json.loads((OLD / "source_ledger.json").read_text())
    entry = next(s for s in ledger["sources"] if s["key"] == "dav1d2026")
    check(entry["version"] == COMMIT, "Old ledger commit differs from fixed audit target")
    hashes = {}
    for name, expected in entry["source_files_sha256"].items():
        actual = digest(OLD / name)
        check(actual == expected, f"Source identity mismatch: {name}")
        hashes[name] = {"sha256": actual, "matches_old_ledger": True}
    check(hashes["code/dav1d_src_decode.c"]["sha256"] == DECODE_SHA,
          "decode.c does not match the independently fixed expected SHA-256")
    source = (OLD / "code/dav1d_src_decode.c").read_text()
    snippets = [
        "size_t alloc_sz = 64;",
        "alloc_sz += (size_t)llabs(y_stride) * 4 * f->sbh << need_cdef_lpf_copy;",
        "alloc_sz += (size_t)llabs(uv_stride) * 8 * f->sbh << need_cdef_lpf_copy;",
        "const int need_cdef_lpf_copy = c->n_tc > 1 && has_resize;",
        "ptrdiff_t y_stride = f->cur.stride[0], uv_stride = f->cur.stride[1];",
        "f->bh = ((f->frame_hdr->height + 7) >> 3) << 1;",
        "f->sbh = (f->bh + f->sb_step - 1) >> f->sb_shift;",
    ]
    for snippet in snippets:
        check(snippet in source, f"Audited source expression missing: {snippet}")

    height_checks = 0
    for height, sb128 in product(range(1, 131073), (0, 1)):
        check(source_sbh(height, sb128) == closed_sbh(height, sb128),
              f"S rounding mismatch at H={height}, b={sb128}")
        height_checks += 1

    allocation_checks = 0
    for y, uv, sbh, n_tc, resize in product(
        (-8192, -3840, -1920, -1, 1, 1920, 3840, 8192),
        (-4096, -1920, -960, 0, 960, 1920, 4096),
        (1, 2, 9, 17, 34, 65), (1, 2, 8), (False, True)
    ):
        a = source_request(y, uv, sbh, n_tc, resize)
        check(a == closed_request(y, uv, sbh, n_tc, resize), "Closed formula mismatch")
        check(a == layout_request(y, uv, sbh, n_tc, resize), "Region decomposition mismatch")
        check(a == closed_request(-y, -uv, sbh, n_tc, resize), "Stride-sign invariance mismatch")
        allocation_checks += 1

    # Analytic illustrations only: no resize, 8-bit 4:2:0, tightly packed byte strides.
    examples = []
    for width, height, sb128 in product((1920, 3840), (1080, 2160), (0, 1)):
        if (width, height) not in ((1920, 1080), (3840, 2160)):
            continue
        sbh = closed_sbh(height, sb128)
        y, uv = width, width // 2
        requested = closed_request(y, uv, sbh, 2, False)
        examples.append({
            "coded_width": width, "height": height, "bit_depth": 8,
            "chroma": "4:2:0", "superblock_pixels": 64 << sb128,
            "S": sbh, "y_stride_bytes_assumed": y, "uv_stride_bytes_assumed": uv,
            "has_resize": False, "n_tc_assumed": 2, "r": 0,
            "requested_bytes_analytic": requested, "KiB_analytic": requested / 1024,
            "measurement": False,
        })
    for x in examples:
        check(x["requested_bytes_analytic"] == 64 + 8 * x["coded_width"] * x["S"],
              "8-bit 4:2:0 packed-stride simplification failed")

    with (HERE / "analytic_examples.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=examples[0].keys())
        writer.writeheader()
        writer.writerows(examples)
    report = {
        "status": "PASS", "commit": COMMIT, "source_hashes": hashes,
        "formula": "A_bytes = 64 + 2^r * S * (4*abs(s_Y) + 8*abs(s_UV))",
        "S": "ceil(H/(64*2^b)), b=seq_hdr->sb128 in {0,1}",
        "r": "int(n_tc > 1 and width[0] != width[1])",
        "height_cases_checked": height_checks,
        "allocation_cases_checked": allocation_checks,
        "source_literal_expressions_checked": len(snippets),
        "example_rows": len(examples),
        "domains": "Valid positive dimensions; arithmetic equality checked without machine overflow",
        "checks": ["Nested height rounding", "Literal shifts versus closed formula",
                   "Independent buffer-region decomposition", "Signed-stride invariance",
                   "Task/resize branch truth table", "Packed 8-bit 4:2:0 specialization"],
        "not_performed": ["Network access", "HEAD refresh", "Download", "Codec build",
                          "Codec execution", "Allocation measurement", "Benchmark",
                          "dav1d lifetime optimality proof", "Cross-codec superiority comparison"],
        "script_sha256": digest(Path(__file__)),
    }
    (HERE / "verification.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in ("status", "commit", "height_cases_checked",
          "allocation_cases_checked", "example_rows")}, indent=2))


if __name__ == "__main__":
    main()

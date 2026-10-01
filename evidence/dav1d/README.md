# dav1d source-audit snapshot and portable algebra check

This directory preserves the pinned October 1 audit of dav1d commit `9a275d0c9296f2c0ded9d0dd28f99cf22dea2572`. `README_HISTORICAL.md` is an unchanged historical research note; its workspace commands and non-exported insertion/audit files are historical references, not public-package entry points.

From the public package root, run:

```sh
python3 tools/dav1d_formula.py
```

This checks 262,144 height/flag combinations and 2,016 allocation/branch/stride combinations without downloading or running dav1d. To additionally check the eight pinned source-file hashes, obtain the matching source separately and pass `--source-dir /path/to/dav1d`. No complete dav1d source is bundled.

`verification.json` and `analytic_examples.csv` are preserved historical outputs. `verify_formula.py` preserves the original source-audit helper and its fixed workspace assumptions; the portable wrapper imports only its arithmetic functions. Neither the algebra check nor the examples are decoder allocation measurements or performance comparisons. Third-party source-expression notices are retained in `third_party/dav1d/` in the package root; see the root `LICENSING.md` for the mapping.

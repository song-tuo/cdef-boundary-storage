# Inspect this release without experiments

From this directory run `python3 verify.py`. It checks manifest sizes/hashes, table selectors and preservation of existing timing roles. It does not launch a compiler, decoder, downloader, enumerator or bootstrap. No new estimate or interval is computed.

For Table II use `records/CDEF_H1/allocation_accounting.csv` and the keys in EVIDENCE_MAP.csv; bytes/1024 is the table's displayed unit. For IV-C read `records/CDEF_FINAL_PAPER_GATE/TIMING_REANALYSIS.csv`; the estimates are already present. `records/CDEF_FINAL_PAPER_GATE/reanalysis/block_ratios.csv` retains each existing contrast ratio. The 648 rows in H1/timing_blocks.csv are 216 blocks times three implementations; they are not 648 independent blocks.

`command_log` identifies a name in H1/COMMANDS.json and `logs/<name>.command.json`, `.result.json`, `.stdout`, `.stderr` in the release ZIP. Expected fault exits and unsuccessful attempts remain included. The original full-source gate generally recorded combined `.log` output; it did not have the H1 four-file stdout/stderr layout.

Original execution drivers under `records/*/scripts/` are preserved as provenance, not invoked during this update. H1/protocol fixes the inputs, schedule, source and implementation seals; H1/inputs manifests identify generated controls, official content and fixture hashes. Full-source REPRODUCE.md records its build interfaces. Historical absolute paths are exported as `${WORKSPACE}` and `${HOME}`; rebuilding requires a separate writable tree and environment adaptation. It is not an automatic one-command replay package. Preserve completed evidence before any separately authorized replay.

Selected source files retain upstream copyright notices; repository LICENSING.md and third_party/libaom notices apply. No new license or upstream acceptance is claimed.

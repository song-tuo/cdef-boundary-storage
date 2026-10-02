# Source checks inherited from the preceding manuscript revision

## VDC-M

Hannah Yang, Sohyeon Kim, Saeyeon Kim, Jiyoung Lee, Huijin Roh and Ji-Hoon Kim, “Optimized Memory System Architecture for VESA VDC-M Decoder with Multi-Slice Support,” ISCAS 2025, pp. 1–5, DOI 10.1109/ISCAS56072.2025.11044266.

- Author full text read: https://arxiv.org/html/2502.17729v1
- Author record explicitly reports ISCAS 2025 acceptance: https://arxiv.org/abs/2502.17729
- Publisher record: https://ieeexplore.ieee.org/document/11044266 (automated access encountered the publisher's JavaScript check).
- A direct Crossref API open in the web tool was unavailable; it is not recorded as a successful metadata fetch.

Sections III-B and III-C describe half-line delay, block forwarding and bank splitting. Section IV reports line-buffer reduction of 33.3%, reconstruction-buffer reduction of 77.3%, and 28 nm implementation results. The manuscript uses the first two as source-specific figures and describes the changed access scheduling. It does not compare their reduction percentages numerically with libaom or claim equivalent objects/contracts.

The full text and acceptance record were read in the preceding review turn and retained in this conversation; this revision adds no independent experiment. Copyrighted paper files are not included in the deliverable.

## Previously verified public patches

- Repository: https://github.com/song-tuo/cdef-boundary-storage
- Fixed release: https://github.com/song-tuo/cdef-boundary-storage/releases/tag/artifact-v2
- Cited patch directory: https://github.com/song-tuo/cdef-boundary-storage/tree/artifact-v2/patches/v3.12.1
- Verified tag commit: `dfe32e98b969010846ee6dd17d40030fd87216bd`
- `baseline_to_type_fix.patch`: 641 bytes; Git blob `6053342670a0c3783bbf5877ad2bf47ff19767aa`.
- `type_fix_to_token.patch`: 10552 bytes; Git blob `0b4431f9673d4799e30dcf00a9fac788663aea25`.

Both Git blob identities were recomputed from the existing local patches and match the GitHub contents API. The linked directory is the code endpoint. No claim is made that it contains all H1 command logs. That preceding verification was read-only. The present alignment publishes a separate artifact-v3 supplement and leaves these v2 patches and the v2 tag unchanged.


Table III combines the already checked VDC-M full text, the recorded source-drift audit, original CN clearance, and the cited storage-mapping papers. No new literature priority claim or closest-work audit was performed in this alignment revision.

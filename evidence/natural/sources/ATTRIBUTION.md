# UVG source attribution

Alexandre Mercat, Marko Viitanen and Jarno Vanne, “UVG dataset: 50/120fps 4K sequences for video codec analysis and development,” ACM MMSys 2020, pp. 297–302, doi:10.1145/3339825.3394937.

Official dataset: https://tie-ultravideo.rd.tuni.fi/dataset.html
Official descriptions: https://github.com/ultravideo/UVG-4K-Dataset/blob/master/README.md
License: Creative Commons Attribution–NonCommercial 3.0 Unported, https://creativecommons.org/licenses/by-nc/3.0/ . Used for this private noncommercial research replication. Raw media and compressed range caches are not part of the manuscript/source distribution.

Selected sequences: Beauty (slow motion, complex texture), Jockey (fast motion, smooth texture), HoneyBee (localized fast motion with blurred background). These descriptors follow the official repository; the frozen design rationale also specifies the visible spatial regions that motivated coverage.

Changes: extract the first 60 consecutive frames from each 600-frame 3840×2160 120 fps 8-bit 4:2:0 source; create 1920×1080 derivatives by a fixed per-plane 2×2 box filter with integer half-up rounding; encode each at the prospectively fixed AV1 settings. No temporal decimation or content-based range selection. Each resulting stream covers 0.5 seconds of the source; this is a short-prefix external-validity check, not broad source-duration coverage.

Acquisition integrity: exact YUV member size from the 7z metadata is checked against 600 frames. Extraction stops at exactly 60 planar frames (746,496,000 bytes). Cached compressed ranges and decoded prefixes are hashed. The full archives are not downloaded, so the member's whole-stream CRC and archival checksum are not claimed.

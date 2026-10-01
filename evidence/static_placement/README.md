# Finite event-model check of static placement

Run `python3 tools/static_placement_check.py` from the artifact root. Only the Python standard library is required.

The user-supplied original is preserved byte for byte as `original_static_placement_check.py`. Its header states that it was written from the paper contract independently of the earlier checker; this package records that supplied provenance, without certifying an authorship process. The runnable maintained copy changes only the output label for distinct live sets and the exit status on failure. `maintenance.diff` records those changes.

For all 40 configurations R=1..10 and W=1..4, the check enumerates ordered dispatch, unconstrained per-row copy, and return after both own and predecessor copy. It verifies the peak K, simultaneous attainment of the two pool capacities, and the exact chromatic number of the union conflict graph. A complete-graph shortcut gives the exact chromatic number when applicable; otherwise exhaustive coloring starts from the observed clique lower bound.

Rows have one atomic boundary-copy event in this abstract model. The returned set collection contains distinct live sets, not the count of explored event states. No native decoder execution or timing is performed. The enumeration supports, and does not replace, the general proof in the manuscript.

`original_stdout.txt`, `maintained_stdout.txt` and `verification.json` bind the two successful runs to their script hashes. The separate injected-expectation check only verifies nonzero failure exit; its output is not a scientific model result.

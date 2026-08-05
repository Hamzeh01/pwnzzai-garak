"""Read garak's native artifacts back into tables and figures.

The analysis never re-scores anything. Garak's ``report.jsonl`` already contains
the per-attempt detector results and the per-``(probe, detector)`` eval counts;
this layer joins those with the run manifest and the per-response notes to
produce the tables and figures the write-up needs.
"""

from garak_pwnzz.analysis import report_reader, analyze  # noqa: F401

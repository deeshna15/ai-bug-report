# Bug Report: Batch processor crashing

**Issue:** Batch processor crashes halfway when encountering a bad log format.

**Expected behavior:** The script should skip completely empty lines or malformed lines, print a warning, and continue to process the valid ones.

**Actual behavior:** The entire script abends with an error, skipping the rest of the valid rows in the file.

**Environment:** Python 3.9+, Windows 10

**Reproduction hints:**
Run `python batch_processor.py <file>` where the file has some valid lines followed by an empty line, and then more valid lines.

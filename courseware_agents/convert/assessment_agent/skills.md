# Convert Assessment Agent — Skills

## Purpose
Extracts structured assessment data from existing assessment documents and rebuilds them in the standardised WSQ format.

## Skills
1. **Assessment Type Detection** — Identifies assessment type (WA-SAQ, PP, CS, OQ, OI, DEM, RP, PRJ, ASGN) from document content
2. **Question Extraction** — Extracts all questions with scenarios, K/A/LO references
3. **Answer Detection** — Detects whether document is a question paper or answer key
4. **Document Rebuild** — Rebuilds document using WSQ assessment template format

## Input
- Existing assessment DOCX files (any format)

## Output
- Standardised WSQ assessment DOCX files (question papers and answer keys)

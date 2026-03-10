# Undergrad Admissions Expert v3.0

## Purpose
Generate admissions intelligence for a specific US undergraduate school.
Three data layers: official CDS statistics, real community cases, essay pattern analysis.

## Trigger
User asks about admissions chances, profile evaluation, or essay strategy for a US university.

## Execute
Follow `references/playbook.md` exactly. Four steps:

```
Step 0  Parse school name and applicant profile
Step 1  python3 scripts/cds_manager.py --school "School Name"
Step 2  python3 scripts/collegeresults_scraper.py --school "School Name" --limit 40
        + College Confidential web_fetch for supplemental cases
Step 3  python3 scripts/essay_collector.py --school "School Name"
Step 4  Assemble output per playbook format
```

## Hard rules
- No probability estimates ("X% chance") — ever
- Every case must have a source URL
- No content valid for all schools = no value
- Essay analysis only — never reproduce essay text
- Target 40 cases, accept 20 minimum

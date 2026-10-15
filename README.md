# CPT-Friendly U.S. Data Internships

An evidence-first, community-maintained tracker for U.S. undergraduate data internships. It collects public internship postings in data analytics, business intelligence, data science, and adjacent quantitative roles, then records what each posting actually says about F-1/CPT work authorization.

## Important: CPT is not H-1B sponsorship

CPT is authorization issued by a student's school for a specific employer and period. A company's past H-1B filings do **not** prove that a particular internship accepts CPT. This project therefore never treats H-1B history as CPT approval, and never turns silence in a posting into a positive claim.

Each posting receives one of these evidence labels:

| Label | Meaning |
|---|---|
| `explicit_cpt_yes` | The posting explicitly says CPT/F-1 candidates are eligible or accepted |
| `explicit_cpt_no` | The posting explicitly excludes CPT/F-1 candidates |
| `possible_restriction` | The posting has broad work-authorization/no-sponsorship wording; ask the recruiter whether CPT is accepted |
| `unknown` | No clear CPT-specific statement was found |

The label is a screening aid, not immigration or legal advice. Always read the live posting and confirm with the employer and your DSO. Rules and school policies can change.

## How it updates

GitHub Actions checks the configured public employer career-board APIs every two hours. It adds new matching internships, updates last-seen timestamps, and marks postings missing from successful board responses as `not_seen` rather than deleting them. A failed source fetch does not close its postings. The workflow only scans the ATS boards explicitly listed in [`sources.json`](sources.json); coverage is not exhaustive.

The tracker currently supports Greenhouse, Lever, and Ashby public job-board feeds. Add a source only after verifying its official employer board slug. Contributions that include employer-specific CPT claims must include a direct official source and the date checked.

## Files

- [`data/jobs.csv`](data/jobs.csv): discovered postings and evidence fields
- [`sources.json`](sources.json): monitored official ATS boards
- [`src/update_jobs.py`](src/update_jobs.py): fetch, filter, and classify postings
- [`.github/workflows/update.yml`](.github/workflows/update.yml): two-hour update schedule

## Run locally

Requires Python 3.11+ and the standard library only.

```bash
python src/update_jobs.py
python -m unittest discover -s tests
```

The updater is intentionally conservative: a missing CPT statement stays `unknown`; generic “no sponsorship” language is flagged for recruiter confirmation, not silently interpreted as a CPT rejection.

## Sources and limitations

- Job details come from the employers' public Greenhouse, Lever, and Ashby job feeds listed in `sources.json`.
- CPT classifications are extracted from each posting's own text. They can miss nuance and must be verified manually.
- Historical employer sponsorship datasets (for example, H-1B/LCA data) are not evidence that an internship accepts CPT and are not merged into the CPT label.
- Roles can close between scans; apply only through the official job link.

## Contributing

Open a pull request with the official employer careers-board URL, verified ATS slug, and—if proposing an explicit CPT label—a direct source that states the policy. Do not submit private recruiter correspondence, application data, resumes, or personal immigration documents.

## License

MIT for the code. Job descriptions and employer marks remain the property of their respective owners; this repository stores links and short, machine-derived evidence labels, not copied full job descriptions.

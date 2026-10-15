# CPT-Friendly U.S. Data Internships

An evidence-first, community-maintained tracker for U.S. undergraduate data internships. It collects public postings in data analytics, business intelligence, data science, and related roles, then records what each source actually says about F-1/CPT work authorization.

## Important: CPT is not H-1B sponsorship

CPT is authorization issued by a student's school for a specific employer and period. A company's past H-1B filings do **not** prove that a particular internship accepts CPT. This project therefore never treats H-1B history as CPT approval, and never turns silence in a posting into a positive claim.

Each posting receives one of these evidence labels:

| Label | Meaning |
|---|---|
| `explicit_cpt_yes` | The posting explicitly says CPT/F-1 candidates are eligible or accepted |
| `explicit_cpt_no` | The posting explicitly excludes CPT/F-1 candidates |
| `possible_restriction` | A source contains broad work-authorization/no-sponsorship wording; confirm whether CPT is accepted |
| `unknown` | No clear CPT-specific statement was found |

The label is a screening aid, not immigration or legal advice. Always read the live posting and confirm with the employer and your DSO. Rules and school policies can change.

## How it updates

GitHub Actions checks the configured public employer career-board APIs every two hours. It adds new matching internships, updates last-seen timestamps, and marks postings missing from successful board responses as `not_seen` rather than deleting them. A failed source fetch does not close its postings. The workflow only scans the ATS boards explicitly listed in [`sources.json`](sources.json); coverage is not exhaustive.

The tracker includes direct Greenhouse, Lever, and Ashby feeds plus two public, machine-readable community datasets: [SimplifyJobs Summer 2027](https://github.com/SimplifyJobs/Summer2027-Internships) and [Understudy's Summer 2027 list](https://github.com/Keugene11/Summer-2027-Tech-Internships). Community feeds substantially expand discovery beyond the few direct employer boards configured here. The updater keeps data analyst, business intelligence, data scientist/science, analytics, and closely related internship titles; it does not use description-only keyword matches to include generic roles. Imported listings retain the employer application URL and identify the dataset in `source_url`.

This is intentionally a broad screen: it excludes roles whose source explicitly says CPT is not accepted, or explicitly says no sponsorship is offered. Other jobs stay in the dataset unless a restriction is explicit. `unknown` means “not stated in the source we checked,” **not** “CPT accepted.” In particular, the Understudy feed does not supply sponsorship/CPT evidence, so those records need a manual check on the linked employer posting. Simplify's no-sponsorship marker is treated as a reason to exclude a record from this candidate list.

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

- Job details come from the employers' public Greenhouse, Lever, and Ashby feeds and the community datasets listed in `sources.json`.
- ATS-posting authorization evidence is extracted from each posting's own text. Community datasets may not provide descriptions; in those cases the classification remains `unknown` and evidence is left blank.
- Community datasets are discovery sources, not employer authorization statements. Verify every job and work-authorization requirement on the linked employer posting before applying.
- Historical employer sponsorship datasets (for example, H-1B/LCA data) are not evidence that an internship accepts CPT and are not merged into the CPT label.
- Roles can close between scans; apply only through the official job link.

## Contributing

Open a pull request with the official employer careers-board URL, verified ATS slug, and—if proposing an explicit CPT label—a direct source that states the policy. Do not submit private recruiter correspondence, application data, resumes, or personal immigration documents.

## License

MIT for the code. Job descriptions and employer marks remain the property of their respective owners; this repository stores links and short, machine-derived evidence labels, not copied full job descriptions.

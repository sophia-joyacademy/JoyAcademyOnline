# Joy Academy Online — Immunization form

## Deliverables

- `immunization-requirement.html` and `zh/immunization-requirement.html`: linked
  third under Parent Resources / Key Documents, after Student Handbook and
  Program of Studies. Each page lists the form preview before the PDF download.
- `output/Joy_Academy_Student_Immunization_Record_EN.pdf`: English-only printable
  form linked from the English page.
- `output/Joy_Academy_Student_Immunization_Record.pdf`: existing bilingual
  printable form linked from the Chinese page.
- `templates/immunization_form_en.html` and `templates/immunization_form.html`:
  English and bilingual design sources, each four US Letter pages.
- `styles/immunization_form.css`: shared print styles with 0.55-inch margins.
- `source/immunization_records_policy.md`: complete supplied bilingual policy,
  retained separately for Student Handbook integration and reproduced in full
  on the first bilingual PDF page, before student information. The English PDF
  includes the unchanged English policy. Each website page shows only its own
  language's policy above downloads; language-switch links remain.

The supplied form wording is retained in the HTML, including all 13 vaccine
options, certification, attachments, and school review fields. Decorative
Markdown markers from the supplied message are not form content. Date-entry
spaces are informed by CDC routine schedules, but no legal requirement or new
school policy has been added. Each PDF page uses the existing school `logo.png`
in its header, without altering the logo. The original supplied content is retained.
The identical letterhead on all eight PDF pages follows `generate_parent_letter.py`:
a 60-point logo on the left, Georgia Bold 14-point school name in `#00838F`,
and Georgia 9-point motto in `#9A7838` on the right:
`SEEK TRUTH · KNOW THYSELF · SERVE OTHERS`. School text starts 72 points to
the right of the logo. The logo starts at x=72 points; its top is adjusted to
the form's 0.55-inch top margin, while the original US Letter size is preserved.
Document titles sit below this shared letterhead. The supplied reference script
and other website PDFs are unchanged.
The fillable PDF, download links, generation code, and related dependency have
been removed at the school's request. Both PDFs are for printing and handwriting;
neither contains AcroForm fields.

## Vaccination date spaces and sources

The date-space design was checked against the [CDC child/adolescent schedule
notes](https://www.cdc.gov/vaccines/hcp/imz-schedules/child-adolescent-notes.html)
on October 12, 2026. The retrieved page is dated **July 2, 2025** and includes
2024–25 COVID-19 guidance; it is not presented as verified 2026 seasonal
guidance. [CDC explains that school requirements are established by state
laws](https://www.cdc.gov/vaccines/php/requirements-laws/state-vaccination-requirements.html).
These are recordkeeping spaces, not a mandated series or a completeness test.
Actual doses vary by age, vaccine product, catch-up history, and medical
circumstances. Copy documented dates in `YYYY-MM-DD` format, leave unused spaces
blank, and retain additional doses/dates in the attached official record.
Dates are recorded by hand; no automated medical validation is applied.

| Original vaccine item | CDC reference basis | Date spaces |
|---|---|---|
| DTaP / DTP / Tdap | DTaP: 5-dose childhood series; Tdap: 1 adolescent booster at 11–12 years. DTaP dose 5 can be unnecessary under catch-up rules. DTP dates may be copied from international records; no equivalence determination is made. | 5 DTaP/DTP + 1 separate Tdap |
| Polio | Routine IPV series: 4 doses; age/interval rules can change catch-up totals. | 4 |
| Hepatitis B | Usually 3 doses; 4 are permitted with birth dose plus combination vaccine. Alternative adolescent schedules exist. | 4 |
| MMR | Routine series: 2 doses. | 2 |
| Varicella | Routine series: 2 doses; evidence of immunity and catch-up differ. | 2 |
| Hepatitis A | Routine series: 2 doses. | 2 |
| Hib | 3 or 4 doses depending on product; age/catch-up and risk exceptions apply. | 4 |
| Pneumococcal | Routine childhood PCV series: 4 doses; risk-based PCV/PPSV23 records can differ. | 4 |
| Meningococcal | MenACWY: routinely 2 doses at 11–12 and 16 years. MenB: shared clinical decision-making at 16–23 years (preferred 16–18), typically 2 doses; certain circumstances use 3 or additional doses. Not one combined 5-dose series. | 2 MenACWY + 3 separately labeled MenB |
| HPV | 2 doses when started at 9–14 years; 3 when started at 15+ or with immunocompromising conditions; interval exceptions apply. | 3 |
| Influenza | Annual vaccination; some children age 6 months–8 years need 2 doses in a season depending on history. Not a lifetime 2-dose total. | 2 dates for the latest season |
| COVID-19 | No fixed total asserted; age, formulation, prior doses, season, and clinical guidance affect counts. | 3 recent entries, not 3 required doses |
| Other | No new vaccine or medical recommendation added. | Vaccine name + 2 date entries |

Each form has **43 vaccination-date handwriting spaces**, in addition to the
existing student, parent, and review spaces. Both PDFs keep the original certification,
attachments, and exemptions; the separate Handbook policy is unchanged.

## Generate

Requires Python 3.10+, the pinned packages, and Chrome/Chromium. On macOS:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-immunization.txt
.venv/bin/python scripts/generate_immunization.py \
  --browser "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
.venv/bin/python scripts/test_immunization.py
```

If no existing Chrome/Chromium is available, install Playwright's browser:

```sh
.venv/bin/python -m playwright install chromium
.venv/bin/python scripts/generate_immunization.py
```

Generation uses local HTML/CSS and system fonts, with no external network
requests. Chrome embeds the bilingual static fonts. Use a system with a
Simplified Chinese font installed (macOS: PingFang SC / Hiragino Sans GB;
Windows: Microsoft YaHei). Generation fails on incorrect pagination or footer
overlap or if a header logo fails to load. Tests fail if required localized text,
logos, or embedded fonts are missing. Chrome prints the HTML inputs as blank
handwriting spaces and boxes; no PDF form widgets are added. PyMuPDF is used only
for validation and print rendering. Output files are regenerated; do not use output filenames
for completed student records. The website is static: it does not upload or
store filled health records.

## Printing and signatures

Download the appropriate language version. Print on **US Letter / Actual size
(100%)** or **A4 / Fit to paper**, complete the form and checkboxes by hand, and sign in the signature
space. Date format: `YYYY-MM-DD`. The PDFs are not computer-fillable and contain
no digital-signature fields. Neither the website nor the PDF uploads health records.

## Tests and print checks

`scripts/test_immunization.py` checks:

- Exactly four 612 × 792-point US Letter pages per PDF, content within margins,
  and an embedded school logo in every page header.
- Policy on page 1, matching the relevant language of the independent policy
  source, before student information on the same page.
- All seven sections, every vaccine, and unchanged permanent-record / disclosure
  certification. All HTML text must also appear in its generated PDF.
- No Chinese text in the English PDF; original bilingual content retained in
  the bilingual PDF; static font programs/glyph drawings embedded.
- Both PDFs have no interactive widgets. The retired fillable PDF is absent.
- Identical handwriting spaces in both templates: 43 dates, 16 checkboxes,
  and four school Yes/No boxes. Date spaces are at least 120 points wide and
  16.5 points high.
- Browser-measured print geometry: no sections overlap the header/footer.
- Pixel-identical letterhead regions on all pages of both PDFs, including
  reference logo size, Georgia fonts, school name/motto sizes, and colors.
- Localized web content, correct language-specific download targets,
  existing local links, and placement under Parent Resources / Key Documents.

Tests use the installed macOS Chrome when available, otherwise Playwright's
Chromium. Set `CHROME_EXECUTABLE` to select another installed Chrome/Chromium.

For manual verification, open both PDFs and inspect all four pages at 100%.
Print using **US Letter / Actual size (100%)** or **A4 / Fit to paper**.
The PDF page size remains US Letter; fitting to A4 prevents horizontal clipping.
Check the bottom footer, Chinese glyphs, field alignment, checkbox marks, and
signature space. Physical printer output cannot be certified by automated
rendering tests; verify it locally before distribution. The English PDF starts
with the English policy; the bilingual PDF starts with the full bilingual policy.

"""Render the English and bilingual printable forms from local HTML/CSS."""

import argparse
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
VARIANTS = (
    ("immunization_form_en.html", "Joy_Academy_Student_Immunization_Record_EN.pdf"),
    ("immunization_form.html", "Joy_Academy_Student_Immunization_Record.pdf"),
)


def generate(browser_path: str | None) -> None:
    output = ROOT / "output"
    output.mkdir(exist_ok=True)
    with sync_playwright() as playwright:
        options = {"executable_path": browser_path} if browser_path else {}
        browser = playwright.chromium.launch(**options)
        try:
            page = browser.new_page(viewport={"width": 1100, "height": 1000})
            page.emulate_media(media="print")
            for template, filename in VARIANTS:
                page.goto((ROOT / "templates" / template).as_uri())
                page.evaluate("document.fonts.ready")
                page.evaluate("""() => {
                  const sheets = [...document.querySelectorAll('.sheet')];
                  if (sheets.length !== 4) throw new Error('Expected four pages');
                  for (const sheet of sheets) {
                    const footer = sheet.querySelector('footer').getBoundingClientRect();
                    for (const section of sheet.querySelectorAll('section')) {
                      if (section.getBoundingClientRect().bottom > footer.top - 8)
                        throw new Error('Form content overlaps page footer');
                    }
                    const logo = sheet.querySelector('.form-logo');
                    if (!logo?.complete || !logo.naturalWidth)
                      throw new Error('School logo failed to load');
                  }
                }""")
                page.pdf(path=str(output / filename), prefer_css_page_size=True,
                         print_background=True, display_header_footer=False)
                print(f"Generated {output / filename}")
        finally:
            browser.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--browser", help="Chrome/Chromium executable; otherwise use Playwright Chromium")
    args = parser.parse_args()
    generate(args.browser)

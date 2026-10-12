"""Render immunization forms and parent cover letters from local HTML/CSS."""

import argparse
from pathlib import Path

import pymupdf
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
VARIANTS = (
    ("immunization_form_en.html", "Joy_Academy_Student_Immunization_Record_EN.pdf", 4),
    ("immunization_form.html", "Joy_Academy_Student_Immunization_Record.pdf", 4),
    ("immunization_cover_letter_en.html", "Joy_Academy_Immunization_Cover_Letter_EN.pdf", 1),
    ("immunization_cover_letter_zh.html", "Joy_Academy_Immunization_Cover_Letter_ZH.pdf", 1),
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
            for template, filename, pages in VARIANTS:
                page.goto((ROOT / "templates" / template).as_uri())
                page.evaluate("document.fonts.ready")
                page.evaluate("""expectedPages => {
                  const sheets = [...document.querySelectorAll('.sheet')];
                  if (sheets.length !== expectedPages) throw new Error('Unexpected page count');
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
                }""", pages)
                page.pdf(path=str(output / filename), prefer_css_page_size=True,
                         print_background=True, display_header_footer=False)
                print(f"Generated {output / filename}")
        finally:
            browser.close()
    for language, form in (
        ("ZH", "Joy_Academy_Student_Immunization_Record.pdf"),
        ("EN", "Joy_Academy_Student_Immunization_Record_EN.pdf"),
    ):
        packet = output / f"Joy_Academy_Immunization_Packet_{language}.pdf"
        with pymupdf.open() as document:
            for filename in (
                f"Joy_Academy_Immunization_Cover_Letter_{language}.pdf",
                form,
            ):
                with pymupdf.open(output / filename) as attachment:
                    document.insert_pdf(attachment)
            document.set_metadata({
                "title": "Joy Academy Online - Immunization Letter and Record Form",
                "author": "Joy Academy Online",
            })
            document.save(packet)
        print(f"Generated {packet}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--browser", help="Chrome/Chromium executable; otherwise use Playwright Chromium")
    args = parser.parse_args()
    generate(args.browser)

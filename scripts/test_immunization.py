"""Validate localized printable PDFs, policy, date spaces, logos, and links."""

import os
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

import pymupdf
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
VARIANTS = (
    ("immunization_form_en.html", "Joy_Academy_Student_Immunization_Record_EN.pdf", False),
    ("immunization_form.html", "Joy_Academy_Student_Immunization_Record.pdf", True),
)
DATE_SLOTS = {
    "dtap": 5, "tdap": 1, "polio": 4, "hepatitis_b": 4, "mmr": 2,
    "varicella": 2, "hepatitis_a": 2, "hib": 4, "pneumococcal": 4,
    "menacwy": 2, "menb": 3, "hpv": 3, "influenza": 2, "covid19": 3,
    "other": 2,
}
DATE_FIELDS = {
    f"{vaccine}_date_{dose}"
    for vaccine, slots in DATE_SLOTS.items()
    for dose in range(1, slots + 1)
}


class SourceParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_body = False
        self.in_main = False
        self.text = []
        self.main_text = []
        self.links = []
        self.inputs = []
        self.images = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == "body":
            self.in_body = True
        if tag == "main":
            self.in_main = True
        if tag == "input":
            self.inputs.append(attributes)
        if tag == "img":
            self.images.append(attributes)
        for key, value in attrs:
            if key in ("href", "src") and value:
                self.links.append(value)

    def handle_endtag(self, tag):
        if tag == "main":
            self.in_main = False
        if tag == "body":
            self.in_body = False

    def handle_data(self, data):
        if self.in_body and data.strip():
            self.text.append(data.strip())
        if self.in_main and data.strip():
            self.main_text.append(data.strip())


def parse_source(path: Path) -> SourceParser:
    parser = SourceParser()
    parser.feed(path.read_text())
    return parser


class ImmunizationTests(unittest.TestCase):
    def test_english_letter_attachment(self):
        with pymupdf.open(ROOT / "output/Joy_Academy_Immunization_Packet_EN.pdf") as packet:
            self.assertEqual(len(packet), 5)
            for filename, start in (
                ("Joy_Academy_Immunization_Cover_Letter_EN.pdf", 0),
                ("Joy_Academy_Student_Immunization_Record_EN.pdf", 1),
            ):
                with pymupdf.open(ROOT / "output" / filename) as source:
                    for index, page in enumerate(source):
                        self.assertEqual(packet[start + index].get_pixmap().samples, page.get_pixmap().samples)
            text = " ".join("".join(page.get_text() for page in packet).split())
            self.assertNotRegex(text, r"[\u3400-\u9fff]")
            self.assertIn("The Student Immunization Record Form is attached to this letter.", text)
            self.assertIn("submit it and the vaccination record documents to the school.", text)
            self.assertNotIn("Homeroom Teacher", text)
            self.assertTrue(any(
                link.get("uri") == "https://joyacademy.online/immunization-requirement.html"
                for link in packet[0].get_links()
            ))

    def test_chinese_letter_attachment_and_date(self):
        with pymupdf.open(ROOT / "output/Joy_Academy_Immunization_Packet_ZH.pdf") as packet:
            self.assertEqual(len(packet), 5)
            with pymupdf.open(ROOT / "output/Joy_Academy_Immunization_Cover_Letter_ZH.pdf") as letter:
                self.assertEqual(packet[0].get_pixmap().samples, letter[0].get_pixmap().samples)
            with pymupdf.open(ROOT / "output/Joy_Academy_Student_Immunization_Record.pdf") as form:
                for index in range(4):
                    self.assertEqual(packet[index + 1].get_pixmap().samples, form[index].get_pixmap().samples)
            text = packet[0].get_text()
            self.assertIn("已随本信附上", text)
            self.assertIn("更多信息请参考学校网站", text)
            self.assertIn("填写及签名后，将表格和疫苗接种记录文件提交学校。", text)
            self.assertNotIn("请联系班主任", text)
            self.assertNotIn("此致", text)
            self.assertLess(text.index("2026年10月12日"), text.rindex("美嘉在线学堂"))
            self.assertTrue(any(
                link.get("uri") == "https://joyacademy.online/zh/immunization-requirement.html"
                for link in packet[0].get_links()
            ))

    def test_parent_cover_letters(self):
        with pymupdf.open(ROOT / "output/Joy_Academy_Student_Immunization_Record_EN.pdf") as form:
            clip = pymupdf.Rect(39.6, 39.6, 572.4, 99.6)
            letterhead = form[0].get_pixmap(dpi=144, clip=clip).samples
        for language in ("en", "zh"):
            template = ROOT / f"templates/immunization_cover_letter_{language}.html"
            filename = ROOT / f"output/Joy_Academy_Immunization_Cover_Letter_{language.upper()}.pdf"
            source = parse_source(template)
            with pymupdf.open(filename) as doc:
                self.assertEqual(len(doc), 1)
                page = doc[0]
                self.assertEqual(tuple(page.rect), (0, 0, 612, 792))
                self.assertEqual(page.get_pixmap(dpi=144, clip=clip).samples, letterhead)
                self.assertFalse(list(page.widgets()))
                text = "".join(page.get_text().split())
                for fragment in source.text:
                    self.assertIn("".join(fragment.split()), text)
                if language == "en":
                    self.assertNotRegex(text, r"[\u3400-\u9fff]")
                for word in page.get_text("words"):
                    self.assertGreaterEqual(word[0], 38)
                    self.assertLessEqual(word[2], 574)
                    self.assertLessEqual(word[3], 754)
                for word in page.get_text("words"):
                    if 130 < word[1] < 735:
                        self.assertGreaterEqual(word[0], 53.75)
                        self.assertLessEqual(word[2], 558.25)
            for link in source.links:
                url = urlsplit(link)
                if not url.scheme and url.path:
                    self.assertTrue((template.parent / unquote(url.path)).is_file(), link)

    def test_print_layout_content_and_logos(self):
        letterheads = []
        for template, filename, bilingual in VARIANTS:
            with self.subTest(filename=filename), pymupdf.open(ROOT / "output" / filename) as doc:
                self.assertEqual(len(doc), 4)
                text = "".join(page.get_text() for page in doc)
                compact = "".join(text.split())
                for fragment in parse_source(ROOT / "templates" / template).text:
                    self.assertIn("".join(fragment.split()), compact)
                self.assertIn("STUDENT IMMUNIZATION RECORD FORM", text)
                for vaccine in (
                    "DTaP / DTP / Tdap", "Polio", "Hepatitis B", "MMR",
                    "Varicella", "Hepatitis A", "Hib", "Pneumococcal",
                    "Meningococcal", "HPV", "Influenza", "COVID-19", "Other",
                ):
                    self.assertIn(vaccine, text)
                if bilingual:
                    for section in (
                        "学生信息", "疫苗接种记录", "所附记录中包含的疫苗",
                        "医疗豁免", "家长或监护人声明", "需提交附件", "学校填写",
                    ):
                        self.assertIn(section, text)
                else:
                    self.assertNotRegex(text, r"[\u3400-\u9fff]")
                for index, page in enumerate(doc):
                    self.assertEqual(tuple(page.rect), (0, 0, 612, 792))
                    self.assertFalse(list(page.widgets()))
                    self.assertIn(f"{index + 1} / 4", page.get_text())
                    for word in page.get_text("words"):
                        self.assertGreaterEqual(word[0], 38)
                        self.assertGreaterEqual(word[1], 38)
                        self.assertLessEqual(word[2], 574)
                        self.assertLessEqual(word[3], 754)
                    images = page.get_image_info(hashes=True)
                    self.assertEqual(len(images), 1)
                    logo = pymupdf.Rect(images[0]["bbox"])
                    self.assertAlmostEqual(logo.x0, 72, delta=0.1)
                    self.assertAlmostEqual(logo.y0, 39.6, delta=0.25)
                    self.assertAlmostEqual(logo.width, 60, delta=0.1)
                    self.assertAlmostEqual(logo.height, 60, delta=0.1)
                    clip = pymupdf.Rect(39.6, 39.6, 572.4, 99.6)
                    letterheads.append(page.get_pixmap(dpi=144, clip=clip).samples)
                    header_spans = [
                        span for block in page.get_text("dict", clip=clip)["blocks"]
                        if "lines" in block for line in block["lines"]
                        for span in line["spans"]
                    ]
                    name = next(span for span in header_spans if span["text"] == "JOY ACADEMY ONLINE")
                    motto = next(span for span in header_spans if span["text"] == "SEEK TRUTH · KNOW THYSELF · SERVE OTHERS")
                    self.assertIn("Georgia-Bold", name["font"])
                    self.assertAlmostEqual(name["size"], 14, delta=0.1)
                    self.assertEqual(name["color"], 0x00838F)
                    self.assertIn("Georgia", motto["font"])
                    self.assertAlmostEqual(motto["size"], 9, delta=0.1)
                    self.assertEqual(motto["color"], 0x9A7838)
                    for font in page.get_fonts():
                        if font[2] == "Type3":
                            self.assertNotEqual(doc.xref_get_key(font[0], "CharProcs")[0], "null")
                        else:
                            self.assertTrue(doc.extract_font(font[0])[3])
        self.assertTrue(all(head == letterheads[0] for head in letterheads))

    def test_matching_handwriting_spaces(self):
        self.assertEqual(len(DATE_FIELDS), 43)
        signatures = []
        for template, _, _ in VARIANTS:
            source = parse_source(ROOT / "templates" / template)
            fields = [item for item in source.inputs if item["name"] in DATE_FIELDS]
            self.assertEqual({item["name"] for item in fields}, DATE_FIELDS)
            self.assertEqual(len(fields), 43)
            self.assertEqual(sum(item.get("type") == "checkbox" for item in source.inputs), 16)
            self.assertEqual(sum(item.get("type") == "radio" for item in source.inputs), 4)
            signatures.append([(item["name"], item.get("type", "text")) for item in source.inputs])
            self.assertEqual(len(source.images), 4)
            self.assertTrue(all(item["src"] == "../logo.png" for item in source.images))
        self.assertEqual(signatures[0], signatures[1])

    def test_policy_and_certification_unchanged(self):
        paragraphs = [
            paragraph.removeprefix("# ")
            for paragraph in (ROOT / "source/immunization_records_policy.md").read_text().strip().split("\n\n")
        ]
        certification = "I understand that Joy Academy Online will maintain this documentation as part of the student's permanent cumulative record and may disclose information as required by applicable law."
        for _, filename, bilingual in VARIANTS:
            with pymupdf.open(ROOT / "output" / filename) as doc:
                policy = "".join(doc[0].get_text().split())
                for paragraph in paragraphs if bilingual else paragraphs[:3]:
                    self.assertIn("".join(paragraph.split()), policy)
                first_page = doc[0].get_text()
                self.assertIn("Student Information", first_page)
                self.assertLess(first_page.index("Immunization Records Policy"), first_page.index("Student Information"))
                self.assertIn("".join(certification.split()), "".join(doc[3].get_text().split()))

    def test_localized_pages_and_links(self):
        for language in ("", "zh/"):
            source = (ROOT / language / "parent-resources.html").read_text()
            section = source.split('id="key-documents"', 1)[1].split("</ul>", 1)[0]
            items = section.split("<li>")
            self.assertEqual(len(items), 4)
            self.assertIn("immunization-requirement.html", items[3])
        paragraphs = (ROOT / "source/immunization_records_policy.md").read_text().strip().split("\n\n")
        for filename, expected, wrong, policy in (
            ("immunization-requirement.html", "Joy_Academy_Student_Immunization_Record_EN.pdf",
             "Joy_Academy_Student_Immunization_Record.pdf", paragraphs[:3]),
            ("zh/immunization-requirement.html", "Joy_Academy_Student_Immunization_Record.pdf",
             "Joy_Academy_Student_Immunization_Record_EN.pdf", paragraphs[3:]),
        ):
            html = (ROOT / filename).read_text()
            source = parse_source(ROOT / filename)
            content = "".join("".join(source.main_text).split())
            for paragraph in policy:
                self.assertIn("".join(paragraph.removeprefix("# ").split()), content)
            if filename.startswith("zh/"):
                self.assertNotIn("Immunization Records Policy", content)
                self.assertNotIn("All enrolled students", content)
                self.assertNotIn("Printable", content)
            else:
                self.assertNotRegex(content, r"[\u3400-\u9fff]")
            self.assertIn(expected, html)
            self.assertNotIn(wrong, html)
            self.assertNotRegex(html, r"Fillable|fillable|AcroForm|电脑填写")
            main_html = html[html.index("<main"):]
            self.assertLess(main_html.index("templates/"), main_html.index("output/"))
            self.assertLess(html.index('id="immunization-policy"'), html.index("<ul>", html.index("<main")))
        self.assertFalse((ROOT / "output/Joy_Academy_Student_Immunization_Record_Fillable.pdf").exists())
        for filename in (
            "immunization-requirement.html", "zh/immunization-requirement.html",
            "templates/immunization_form.html", "templates/immunization_form_en.html",
        ):
            path = ROOT / filename
            for link in parse_source(path).links:
                url = urlsplit(link)
                if not url.scheme and url.path:
                    self.assertTrue((path.parent / unquote(url.path)).is_file(), link)

    def test_browser_print_geometry(self):
        with sync_playwright() as playwright:
            chrome = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
            executable = os.environ.get("CHROME_EXECUTABLE") or (str(chrome) if chrome.exists() else None)
            browser = playwright.chromium.launch(executable_path=executable)
            try:
                page = browser.new_page(viewport={"width": 1100, "height": 1000})
                page.emulate_media(media="print")
                for template, _, _ in VARIANTS:
                    page.goto((ROOT / "templates" / template).as_uri())
                    page.evaluate("document.fonts.ready")
                    problems = page.evaluate("""() => {
                      const problems = [];
                      for (const sheet of document.querySelectorAll('.sheet')) {
                        const header = sheet.querySelector('header').getBoundingClientRect();
                        const footer = sheet.querySelector('footer').getBoundingClientRect();
                        for (const section of sheet.querySelectorAll('section')) {
                          const r = section.getBoundingClientRect();
                          if (r.top < header.bottom || r.bottom > footer.top - 8)
                            problems.push('Section overlaps header/footer');
                        }
                        const logo = sheet.querySelector('.form-logo');
                        if (!logo.complete || !logo.naturalWidth) problems.push('Missing logo');
                        for (const input of sheet.querySelectorAll('.dose-dates input')) {
                          const r = input.getBoundingClientRect();
                          if (r.width < 160 || r.height < 22) problems.push(input.name);
                        }
                      }
                      return problems;
                    }""")
                    self.assertEqual(problems, [], template)
                page.goto((ROOT / "templates/immunization_cover_letter_zh.html").as_uri())
                page.evaluate("document.fonts.ready")
                layout = page.evaluate("""() => {
                  const body = [...document.querySelectorAll('section > p')]
                    .filter(p => !p.className);
                  const date = document.querySelector('.letter-date');
                  return {
                    indents: body.map(p => parseFloat(getComputedStyle(p).textIndent) /
                      parseFloat(getComputedStyle(p).fontSize)),
                    dateAboveSignature: date.nextElementSibling.classList.contains('signature'),
                    dateGap: date.getBoundingClientRect().top -
                      date.previousElementSibling.getBoundingClientRect().bottom,
                    lineHeight: parseFloat(getComputedStyle(date).lineHeight),
                    bottom: date.getBoundingClientRect().bottom,
                    footer: document.querySelector('footer').getBoundingClientRect().top
                  };
                }""")
                for indent in layout["indents"]:
                    self.assertAlmostEqual(indent, 2, places=4)
                self.assertTrue(layout["dateAboveSignature"])
                self.assertAlmostEqual(layout["dateGap"], layout["lineHeight"] + 8, delta=0.1)
                self.assertLess(layout["bottom"], layout["footer"] - 8)
            finally:
                browser.close()


if __name__ == "__main__":
    unittest.main()

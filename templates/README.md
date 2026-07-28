# Report templates

This folder is optional. If you want the generated PDF report to use your
organization's own Word letterhead/branding instead of a plain auto-generated
document, drop a template here.

## Filename

The tool looks for exactly this file (case-sensitive):

```
templates/weekly_status_template.docx
```

If it's not present, the tool falls back to building a plain Word document
automatically — no error, no configuration needed.

## The placeholder

Your template must contain a paragraph whose **entire text** is:

```
{{p report_content}}
```

(Note the `p` right after `{{` and no spaces around `report_content` — this is docxtpl's
paragraph-tag syntax, which is required so it can splice in a full block of rendered content
— headings, bullet lists, a table — in place of the tag. A plain `{{ report_content }}` will
not work here.)

Nothing else can share that paragraph/line — the tool replaces the whole
paragraph with the rendered report content, so any other text mixed into it
would be lost.

Everything else in your template — cover page, letterhead, headers/footers,
other static boilerplate — is left untouched.

## What gets rendered there

The report's sections (Executive Summary, Progress, Risks & Blockers,
Upcoming / Next Steps, Metrics) are inserted at the placeholder as native Word
content: headings, bullet lists, a real table for Metrics, and bold text
where the report used `**bold**`.

## Building one

1. Open Word or LibreOffice Writer.
2. Design your cover page / branding / letterhead as usual.
3. Add a new paragraph containing exactly `{{p report_content}}` where the
   report body should start.
4. Save as `.docx` in this folder under the exact filename above.

"""
Script to generate a publication-quality PDF from ACADEMIC_PROJECT_REPORT.md
using Microsoft Edge headless printing engine with professional academic styling.
"""

import html
import os
import re
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
REPORT_MD = BASE_DIR / "reports" / "ACADEMIC_PROJECT_REPORT.md"
OUTPUT_HTML = BASE_DIR / "reports" / "report_print.html"
OUTPUT_PDF = BASE_DIR / "reports" / "Multi_Agent_MCP_Academic_Report.pdf"
ARTIFACT_PDF = Path(r"C:\Users\tezam\.gemini\antigravity\brain\53663051-097d-4da1-a2d6-764df218a467\Multi_Agent_MCP_Academic_Report.pdf")


def parse_inline(text: str) -> str:
    """Format inline markdown elements."""
    # Escape HTML characters first
    # Protect already formed HTML tags if any
    text = html.escape(text)

    # Inline math: $...$
    text = re.sub(r"\$([^\$]+)\$", r'<span class="math">\1</span>', text)
    # Inline code: `...`
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    # Bold + Italic: ***...***
    text = re.sub(r"\*\*\*([^\*]+)\*\*\*", r"<strong><em>\1</em></strong>", text)
    # Bold: **...**
    text = re.sub(r"\*\*([^\*]+)\*\*", r"<strong>\1</strong>", text)
    # Italic: *...*
    text = re.sub(r"\*([^\*]+)\*", r"<em>\1</em>", text)
    # Links: [text](url)
    text = re.sub(r"\[([^\]]+)\]\(([^\)]+)\)", r'<a href="\2">\1</a>', text)

    return text


def markdown_to_html(md_text: str) -> str:
    """Converts structured markdown text to publication-grade HTML."""
    lines = md_text.splitlines()
    html_lines = []
    in_code_block = False
    code_lang = ""
    code_buffer = []
    in_table = False
    table_buffer = []
    in_list = False
    list_type = "ul"
    in_blockquote = False
    bq_buffer = []

    def flush_list():
        nonlocal in_list, list_type
        if in_list:
            html_lines.append(f"</{list_type}>")
            in_list = False

    def flush_blockquote():
        nonlocal in_blockquote, bq_buffer
        if in_blockquote:
            bq_text = " ".join(bq_buffer)
            # Check for GitHub alerts
            if bq_text.startswith("[!WARNING]"):
                clean = bq_text.replace("[!WARNING]", "").strip()
                html_lines.append(f'<div class="alert alert-warning"><strong>WARNING:</strong> {parse_inline(clean)}</div>')
            elif bq_text.startswith("[!NOTE]"):
                clean = bq_text.replace("[!NOTE]", "").strip()
                html_lines.append(f'<div class="alert alert-note"><strong>NOTE:</strong> {parse_inline(clean)}</div>')
            else:
                html_lines.append(f'<blockquote>{parse_inline(bq_text)}</blockquote>')
            in_blockquote = False
            bq_buffer = []

    def flush_table():
        nonlocal in_table, table_buffer
        if in_table and table_buffer:
            html_lines.append('<div class="table-container"><table>')
            # First row is header
            headers = [c.strip() for c in table_buffer[0].strip("|").split("|")]
            html_lines.append("<thead><tr>")
            for h in headers:
                html_lines.append(f"<th>{parse_inline(h)}</th>")
            html_lines.append("</tr></thead>")

            html_lines.append("<tbody>")
            # Rows after separator (index 1 is separator)
            for row in table_buffer[2:]:
                cols = [c.strip() for c in row.strip("|").split("|")]
                html_lines.append("<tr>")
                for c in cols:
                    html_lines.append(f"<td>{parse_inline(c)}</td>")
                html_lines.append("</tr>")
            html_lines.append("</tbody></table></div>")
            in_table = False
            table_buffer = []

    for line in lines:
        stripped = line.strip()

        # Fenced code blocks
        if stripped.startswith("```"):
            if in_code_block:
                code_content = html.escape("\n".join(code_buffer))
                if code_lang == "mermaid":
                    html_lines.append(f'<div class="diagram-box"><pre class="mermaid-diagram">{code_content}</pre></div>')
                else:
                    html_lines.append(f'<pre><code class="language-{code_lang}">{code_content}</code></pre>')
                in_code_block = False
                code_buffer = []
                code_lang = ""
            else:
                flush_list()
                flush_blockquote()
                flush_table()
                in_code_block = True
                code_lang = stripped[3:].strip()
            continue

        if in_code_block:
            code_buffer.append(line)
            continue

        # Tables
        if stripped.startswith("|") and stripped.endswith("|"):
            flush_list()
            flush_blockquote()
            in_table = True
            table_buffer.append(stripped)
            continue
        elif in_table:
            flush_table()

        # Blockquotes & Alerts
        if stripped.startswith(">"):
            flush_list()
            flush_table()
            in_blockquote = True
            bq_content = stripped.lstrip(">").strip()
            bq_buffer.append(bq_content)
            continue
        elif in_blockquote:
            flush_blockquote()

        # Horizontal Rule
        if stripped in ["---", "***", "___"]:
            flush_list()
            html_lines.append('<hr class="divider" />')
            continue

        # Headers
        header_match = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if header_match:
            flush_list()
            level = len(header_match.group(1))
            title = header_match.group(2)
            # Add page break before major chapter headers (h2 that start with a number)
            page_break = ' class="chapter-break"' if (level == 2 and re.match(r"^\d+\.", title)) else ""
            h_id = re.sub(r"[^\w\- ]", "", title).lower().replace(" ", "-")
            html_lines.append(f'<h{level} id="{h_id}"{page_break}>{parse_inline(title)}</h{level}>')
            continue

        # Lists (Unordered)
        ul_match = re.match(r"^[-*+]\s+(.*)$", stripped)
        if ul_match:
            if not in_list or list_type != "ul":
                flush_list()
                in_list = True
                list_type = "ul"
                html_lines.append("<ul>")
            html_lines.append(f"<li>{parse_inline(ul_match.group(1))}</li>")
            continue

        # Lists (Ordered)
        ol_match = re.match(r"^\d+\.\s+(.*)$", stripped)
        if ol_match:
            if not in_list or list_type != "ol":
                flush_list()
                in_list = True
                list_type = "ol"
                html_lines.append("<ol>")
            html_lines.append(f"<li>{parse_inline(ol_match.group(1))}</li>")
            continue

        # If not a list item, flush open list
        if in_list and not stripped:
            flush_list()

        # Empty lines
        if not stripped:
            continue

        # Regular Paragraph
        html_lines.append(f"<p>{parse_inline(stripped)}</p>")

    flush_list()
    flush_blockquote()
    flush_table()

    return "\n".join(html_lines)


def build_full_html(body_html: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Multi-Agent Research and Report Generation System Using MCP</title>
<style>
  @page {{
    size: A4;
    margin: 20mm 18mm 22mm 18mm;
    @bottom-center {{
      content: counter(page);
    }}
  }}

  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    color: #1a1a24;
    line-height: 1.6;
    font-size: 10.5pt;
    margin: 0;
    padding: 0;
    background: #ffffff;
  }}

  h1 {{
    font-size: 22pt;
    color: #1a237e;
    border-bottom: 2.5px solid #1a237e;
    padding-bottom: 8px;
    margin-top: 0;
    margin-bottom: 14px;
    line-height: 1.25;
    page-break-after: avoid;
  }}

  h2 {{
    font-size: 14pt;
    color: #0d47a1;
    border-bottom: 1px solid #e0e0e0;
    padding-bottom: 4px;
    margin-top: 24px;
    margin-bottom: 10px;
    page-break-after: avoid;
  }}

  h2.chapter-break {{
    page-break-before: always;
    margin-top: 0;
    padding-top: 8px;
  }}

  h3 {{
    font-size: 11.5pt;
    color: #283593;
    margin-top: 16px;
    margin-bottom: 6px;
    page-break-after: avoid;
  }}

  p {{
    margin: 0 0 10px 0;
    text-align: justify;
    text-justify: inter-word;
  }}

  a {{
    color: #1565c0;
    text-decoration: none;
  }}

  code {{
    font-family: "Cascadia Code", Consolas, "Courier New", monospace;
    font-size: 9pt;
    background: #f4f5f8;
    color: #b71c1c;
    padding: 1px 4px;
    border-radius: 3px;
    border: 1px solid #e4e6ec;
  }}

  pre {{
    background: #1e1e2f;
    color: #f8f8f2;
    padding: 12px 14px;
    border-radius: 6px;
    overflow-x: auto;
    font-size: 8.5pt;
    line-height: 1.45;
    margin: 12px 0;
    page-break-inside: avoid;
    box-shadow: inset 0 0 4px rgba(0,0,0,0.3);
  }}

  pre code {{
    background: transparent;
    color: inherit;
    padding: 0;
    border: none;
  }}

  .table-container {{
    margin: 14px 0;
    page-break-inside: avoid;
  }}

  table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 9pt;
    margin: 8px 0;
  }}

  th {{
    background: #e8eaf6;
    color: #1a237e;
    font-weight: 600;
    text-align: left;
    padding: 7px 10px;
    border: 1px solid #c5cae9;
  }}

  td {{
    padding: 6px 10px;
    border: 1px solid #e0e0e0;
    vertical-align: top;
  }}

  tr:nth-child(even) td {{
    background: #f9fbfd;
  }}

  ul, ol {{
    margin: 4px 0 12px 22px;
    padding: 0;
  }}

  li {{
    margin-bottom: 4px;
  }}

  blockquote {{
    border-left: 4px solid #1a237e;
    background: #f5f6fa;
    margin: 12px 0;
    padding: 8px 14px;
    font-style: italic;
    color: #333344;
  }}

  .alert {{
    border-radius: 4px;
    padding: 10px 14px;
    margin: 12px 0;
    font-size: 9.5pt;
    page-break-inside: avoid;
  }}

  .alert-warning {{
    background: #fff8e1;
    border-left: 4px solid #ff8f00;
    color: #795548;
  }}

  .alert-note {{
    background: #e3f2fd;
    border-left: 4px solid #1976d2;
    color: #0d47a1;
  }}

  .math {{
    font-family: "Cambria Math", "Latin Modern Math", serif;
    font-style: italic;
    color: #1a237e;
  }}

  .diagram-box {{
    background: #f8f9fc;
    border: 1px solid #d0d7de;
    border-radius: 6px;
    padding: 10px;
    margin: 12px 0;
    page-break-inside: avoid;
  }}

  .mermaid-diagram {{
    background: transparent;
    color: #24292f;
    font-size: 8.5pt;
    line-height: 1.4;
  }}

  hr.divider {{
    border: 0;
    height: 1px;
    background: #dcdfe6;
    margin: 20px 0;
  }}

  .cover-header {{
    background: linear-gradient(135deg, #0d47a1 0%, #1a237e 100%);
    color: #ffffff;
    padding: 24px 28px;
    border-radius: 8px;
    margin-bottom: 24px;
  }}

  .cover-header h1 {{
    color: #ffffff;
    border: none;
    font-size: 24pt;
    margin: 0 0 10px 0;
  }}

  .cover-meta {{
    font-size: 10pt;
    opacity: 0.92;
    display: flex;
    justify-content: space-between;
    margin-top: 14px;
    border-top: 1px solid rgba(255,255,255,0.25);
    padding-top: 10px;
  }}
</style>
</head>
<body>

<div class="cover-header">
  <h1>Multi-Agent Research & Report Generation System</h1>
  <div style="font-size: 13pt; font-weight: 300;">Architectural Design, Model Context Protocol (MCP) Integration, and Empirical Evaluation</div>
  <div class="cover-meta">
    <div><strong>Author:</strong> Senior AI Systems Engineer & Academic Research Team</div>
    <div><strong>Release:</strong> v1.0.0 (Production) • Nov 2026</div>
  </div>
</div>

{body_html}

</body>
</html>
"""


def main():
    if not REPORT_MD.exists():
        print(f"Error: {REPORT_MD} not found!")
        sys.exit(1)

    print(f"Reading markdown from: {REPORT_MD}")
    with open(REPORT_MD, "r", encoding="utf-8") as f:
        md_content = f.read()

    print("Converting Markdown to publication-grade styled HTML...")
    body_html = markdown_to_html(md_content)
    full_html = build_full_html(body_html)

    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(full_html)
    print(f"Styled HTML generated: {OUTPUT_HTML}")

    # Edge executable path on Windows
    edge_paths = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ]
    edge_exe = None
    for p in edge_paths:
        if os.path.exists(p):
            edge_exe = p
            break

    if not edge_exe:
        print("Microsoft Edge executable not found. Unable to render PDF via Edge.")
        sys.exit(1)

    print(f"Rendering PDF via Microsoft Edge headless: {edge_exe}")
    html_url = OUTPUT_HTML.as_uri()

    cmd = [
        edge_exe,
        "--headless",
        "--disable-gpu",
        "--run-all-compositor-stages-before-draw",
        "--no-pdf-header-footer",
        f"--print-to-pdf={OUTPUT_PDF}",
        html_url,
    ]

    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0 and OUTPUT_PDF.exists():
        file_size = OUTPUT_PDF.stat().st_size
        print(f"PDF successfully generated: {OUTPUT_PDF} ({file_size / 1024:.1f} KB)")
        # Copy to artifact path
        try:
            with open(OUTPUT_PDF, "rb") as src, open(ARTIFACT_PDF, "wb") as dst:
                dst.write(src.read())
            print(f"Artifact PDF copied: {ARTIFACT_PDF}")
        except Exception as e:
            print(f"Could not copy to artifact directory: {e}")
    else:
        print(f"PDF generation failed with exit code {res.returncode}")
        print("Stdout:", res.stdout)
        print("Stderr:", res.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

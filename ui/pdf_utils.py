from __future__ import annotations

from typing import Iterable


def _escape_pdf_text(text: str) -> str:
    # Escape backslashes and parentheses for PDF text objects.
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _to_ascii(text: str) -> str:
    # Keep PDF output stable by replacing unsupported chars.
    return text.encode("latin-1", errors="replace").decode("latin-1")


def _build_simple_pdf(lines: Iterable[str]) -> bytes:
    # Minimal single-page PDF with Helvetica font.
    content_lines = [
        "BT",
        "/F1 11 Tf",
        "14 TL",
        "50 760 Td",
    ]
    for line in lines:
        safe = _escape_pdf_text(_to_ascii(line))
        content_lines.append(f"({safe}) Tj")
        content_lines.append("T*")
    content_lines.append("ET")
    content_stream = "\n".join(content_lines).encode("latin-1")

    objs = []
    objs.append(b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n")
    objs.append(b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n")
    objs.append(
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj\n"
    )
    objs.append(
        b"4 0 obj << /Length " + str(len(content_stream)).encode("ascii") + b" >> stream\n"
        + content_stream + b"\nendstream endobj\n"
    )
    objs.append(b"5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n")

    xref = [0]
    pdf = bytearray()
    pdf.extend(b"%PDF-1.4\n")
    for obj in objs:
        xref.append(len(pdf))
        pdf.extend(obj)
    xref_pos = len(pdf)
    pdf.extend(f"xref\n0 {len(xref)}\n".encode("ascii"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in xref[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    pdf.extend(b"trailer << /Size ")
    pdf.extend(str(len(xref)).encode("ascii"))
    pdf.extend(b" /Root 1 0 R >>\nstartxref\n")
    pdf.extend(str(xref_pos).encode("ascii"))
    pdf.extend(b"\n%%EOF\n")
    return bytes(pdf)


def pdf_from_report(report: dict) -> bytes:
    invoice = report.get("invoice_details", {}) or {}
    header = invoice.get("header", invoice)
    line_items = invoice.get("line_items") or invoice.get("line_item") or []

    lines: list[str] = []
    lines.append("Invoice Audit Report")
    lines.append("")
    lines.append(f"Document: {report.get('document_name', 'N/A')}")
    lines.append(f"Final Verdict: {str(report.get('final_verdict', 'N/A')).upper()}")
    human_verdict = report.get("human_verdict")
    if human_verdict:
        lines.append(f"Human Verdict: {str(human_verdict).upper()}")
    human_remarks = report.get("human_remarks")
    if human_remarks:
        if isinstance(human_remarks, list):
            remarks_text = "; ".join(str(r) for r in human_remarks if r)
        else:
            remarks_text = str(human_remarks)
        if remarks_text.strip():
            lines.append(f"Human Remarks: {remarks_text}")
    lines.append("")
    lines.append("Invoice Details")
    lines.append(f"Invoice No: {header.get('invoice_no', 'N/A')}")
    lines.append(f"Invoice Date: {header.get('invoice_date', 'N/A')}")
    lines.append(f"Vendor: {header.get('vendor_id', 'N/A')}")
    lines.append(f"Currency: {header.get('currency', 'N/A')}")
    lines.append(f"Total Amount: {header.get('total_amount', 'N/A')}")
    lines.append("")
    lines.append("Line Items")
    if line_items:
        for idx, item in enumerate(line_items, start=1):
            lines.append(
                f"{idx}. {item.get('item_code', 'N/A')} - {item.get('description', 'N/A')} "
                f"(qty: {item.get('qty', item.get('quantity', 'N/A'))}, "
                f"unit: {item.get('unit_price', 'N/A')}, "
                f"total: {item.get('total', item.get('line_total', 'N/A'))})"
            )
    else:
        lines.append("No line items available.")

    lines.append("")
    lines.append("Audit Summary")
    summary = report.get("audit_report") or ""
    summary_lines: list[str] = []
    for part in str(summary).splitlines():
        raw = part.strip()
        if not raw:
            summary_lines.append("")
            continue
        # Drop markdown table separators and keep plain text.
        if raw.startswith("|") or set(raw) <= {"|", "-", " "}:
            continue
        if raw.startswith("#"):
            raw = raw.lstrip("#").strip()
        summary_lines.append(raw)
    if any(line.strip() for line in summary_lines):
        lines.extend(summary_lines)
    else:
        lines.append("Summary not available.")

    return _build_simple_pdf(lines)

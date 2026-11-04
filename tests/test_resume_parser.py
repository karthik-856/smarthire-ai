import pytest
from resume_parser import parse_resume, ResumeParseError

def test_txt_parse_and_fields():
    parsed=parse_resume("resume.txt",b"Jordan Example\nEmail: jordan@example.com\nPython and SQL project")
    assert "Python" in parsed.skills and parsed.email=="jordan@example.com"

def test_invalid_type_and_empty():
    with pytest.raises(ResumeParseError): parse_resume("resume.exe",b"x")
    with pytest.raises(ResumeParseError): parse_resume("resume.txt",b"")

def test_size_limit():
    with pytest.raises(ResumeParseError): parse_resume("resume.txt",b"x"*20,max_bytes=10)

def test_docx_extraction_when_dependency_available():
    pytest.importorskip("docx")
    from io import BytesIO
    from docx import Document
    doc=Document(); doc.add_paragraph("Taylor Sample\nPython SQL"); buf=BytesIO(); doc.save(buf)
    assert "Python" in parse_resume("resume.docx",buf.getvalue()).skills

def test_pdf_extraction_when_dependency_available():
    pytest.importorskip("pypdf")
    header=b"%PDF-1.4\n"
    stream=b"BT /F1 12 Tf 20 100 Td (PDF Python extraction test) Tj ET\n"
    objects=[
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n",
        b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n",
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 300 144] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj\n",
        b"4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n",
        f"5 0 obj << /Length {len(stream)} >> stream\n".encode()+stream+b"endstream endobj\n",
    ]
    data=bytearray(header); offsets=[]
    for obj in objects: offsets.append(len(data)); data.extend(obj)
    xref=len(data); data.extend(f"xref\n0 {len(objects)+1}\n".encode()); data.extend(b"0000000000 65535 f \n")
    for offset in offsets: data.extend(f"{offset:010d} 00000 n \n".encode())
    data.extend(f"trailer << /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF".encode())
    assert "Python" in parse_resume("resume.pdf",bytes(data)).text


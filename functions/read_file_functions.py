import base64
import json
import os
import csv
import io

from PIL import Image
from docx import Document as DocxDocument
from pypdf import PdfReader


read_file_instructions = """**START BY CHOOSING THE RIGHT READER FOR THE FILE TYPE**

## Objective
- Read only the exact information needed for the task.
- Prefer the most specific tool for the file type instead of reading raw files broadly.
- Keep outputs concise, relevant, and easy for the main assistant to reason over.
- Always validate the path before reading and report clear failure messages when a file is missing, unreadable, or unsupported.

## Tool Selection Rules
- Use `read_plain_text` for .txt, .md, .log, .json, .yaml, .yml, and general text files.
- Use `read_csv` for CSV files and convert them into a compact markdown table.
- Use `read_pdf` for PDFs and specify `page` when the target page is known.
- Use `read_image` for .png, .jpg, and .jpeg files.
- Use `find_in_file` first when you need to locate a keyword or specific section inside a large file.
- Use `read_docx` for DOCX documents.
- Use `read_json` for structured JSON content that must be interpreted as data rather than plain text.

## Best Practices
- Read narrow ranges whenever possible using `start_line` and `end_line`.
- For large text files, search for a keyword before reading the whole file.
- For PDFs, prefer a single relevant page instead of extracting the full document.
- For CSVs, cap the output with `max_rows` and keep the table compact.
- For large outputs, truncate only after preserving the meaningful portion of the content.
- If the file is binary or unsupported, return a clear explanation and suggest the correct tool to use.

## Output Quality Rules
- Return only the relevant extracted content that helps answer the user's task.
- Preserve structure when useful: headings, tables, key-value pairs, code blocks, and matching line numbers.
- If a file is empty, say so clearly.
- If no search results are found, report that explicitly instead of guessing.
- If a read fails, explain the actual reason without hiding the error.

## Execution Pattern
1. Identify the file type and choose the correct reader.
2. Validate the file path and purpose of the read.
3. Read the smallest relevant range or page.
4. Extract and summarize only the useful information.
5. If the content is incomplete, do one focused follow-up read rather than reading everything blindly.

## Safety and Reliability
- Never read or expose content outside the user-provided file path.
- Keep search and reads deterministic; avoid broad scans unless the task genuinely requires them.
- When in doubt, prefer a targeted search followed by a narrow read.
"""

#HELPER FUNCTIONS
def _validate_file(path: str):
    if path is None or str(path).strip() == "":
        return False, "No file path provided."

    resolved_path = os.path.abspath(os.path.expanduser(str(path)))
    if not os.path.exists(resolved_path):
        return False, f"Path does not exist: {resolved_path}"
    if not os.path.isfile(resolved_path):
        return False, f"Path is not a valid file: {resolved_path}"
    return True, resolved_path


def _normalize_text(value, limit: int = 20000):
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        value = json.dumps(value, ensure_ascii=False, indent=2)
    text = str(value)
    if len(text) > limit:
        return text[:limit] + "\n...[truncated]"
    return text


def _read_text_file(path: str, start_line: int = 1, end_line: int = 100):
    if start_line < 1:
        raise ValueError("start_line must be >= 1")
    if end_line < start_line:
        raise ValueError("end_line must be >= start_line")

    encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
    last_error = None

    for encoding in encodings:
        try:
            with open(path, "r", encoding=encoding, errors="strict") as handle:
                lines = handle.readlines()
            start_idx = max(start_line - 1, 0)
            end_idx = min(end_line, len(lines))
            return "".join(lines[start_idx:end_idx])
        except UnicodeDecodeError as exc:
            last_error = exc
        except Exception as exc:
            last_error = exc
            break

    if last_error is not None:
        raise last_error
    return ""

#READ FILE FUNCTIONS
def read_pdf(path: str, page: int = 1):
    ok, message = _validate_file(path)
    if not ok:
        return {"role": "tool", "name": "read_pdf", "content": [{"type": "text", "text": message}]}

    try:
        with open(message, "rb") as handle:
            reader = PdfReader(handle)
            total_pages = len(reader.pages)
            if total_pages == 0:
                return {"role": "tool", "name": "read_pdf", "content": [{"type": "text", "text": "PDF has no readable pages."}]}

            page_number = max(1, min(int(page), total_pages))
            page_obj = reader.pages[page_number - 1]
            extracted = page_obj.extract_text() or ""
            content = _normalize_text(extracted)
            return {"role": "tool", "name": "read_pdf", "content": [{"type": "text", "text": f"PDF page {page_number}/{total_pages}:\n{content}"}]}
    except Exception as exc:
        return {"role": "tool", "name": "read_pdf", "content": [{"type": "text", "text": f"Failed to read PDF: {exc}"}]}


def read_image(path: str):
    ok, message = _validate_file(path)
    if not ok:
        return {"role": "tool", "name": "read_image", "content": [{"type": "text", "text": message}]}

    ext = os.path.splitext(message)[1].lower().lstrip(".")
    if ext not in {"png", "jpg", "jpeg"}:
        return {"role": "tool", "name": "read_image", "content": [{"type": "text", "text": f"Unsupported image type: {ext or 'unknown'}; only png, jpg, and jpeg are supported."}]}

    try:
        with Image.open(message) as img:
            rgb_img = img.convert("RGB")
            buffer = io.BytesIO()
            rgb_img.save(buffer, format="PNG")
            image_b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
        return {"role": "tool", "name": "read_image", "content": [{"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}}]}
    except Exception as exc:
        return {"role": "tool", "name": "read_image", "content": [{"type": "text", "text": f"Failed to read image: {exc}"}]}


def read_plain_text(path: str, start_line: int = 1, end_line: int = 100):
    ok, message = _validate_file(path)
    if not ok:
        return {"role": "tool", "name": "read_plain_text", "content": [{"type": "text", "text": message}]}

    try:
        content = _read_text_file(message, start_line=start_line, end_line=end_line)
        return {"role": "tool", "name": "read_plain_text", "content": [{"type": "text", "text": content or "File is empty."}]}
    except ValueError as exc:
        return {"role": "tool", "name": "read_plain_text", "content": [{"type": "text", "text": f"Invalid line range: {exc}"}]}
    except UnicodeDecodeError:
        return {"role": "tool", "name": "read_plain_text", "content": [{"type": "text", "text": f"Could not decode file as UTF-8 text: {path}. Use a specialized reader for binary files."}]}
    except Exception as exc:
        return {"role": "tool", "name": "read_plain_text", "content": [{"type": "text", "text": f"Failed to read text file: {exc}"}]}


def read_csv(path: str, max_rows: int = 50):
    ok, message = _validate_file(path)
    if not ok:
        return {"role": "tool", "name": "read_csv", "content": [{"type": "text", "text": message}]}

    try:
        with open(message, "r", encoding="utf-8-sig", newline="", errors="replace") as handle:
            sample = handle.read(4096)
            handle.seek(0)
            dialect = csv.Sniffer().sniff(sample, delimiters=",;|\t") if sample else csv.excel
            reader = csv.reader(handle, dialect=dialect)
            rows = list(reader)

        if not rows:
            return {"role": "tool", "name": "read_csv", "content": [{"type": "text", "text": "CSV file is empty."}]}

        visible_rows = rows[:max_rows]
        table_lines = []
        header = visible_rows[0]
        table_lines.append("| " + " | ".join(str(cell) for cell in header) + " |")
        table_lines.append("| " + " | ".join("---" for _ in header) + " |")

        for row in visible_rows[1:]:
            padded_row = []
            for idx in range(len(header)):
                value = row[idx] if idx < len(row) else ""
                padded_row.append(str(value))
            table_lines.append("| " + " | ".join(padded_row) + " |")

        return {"role": "tool", "name": "read_csv", "content": [{"type": "text", "text": "\n".join(table_lines)}]}
    except Exception as exc:
        return {"role": "tool", "name": "read_csv", "content": [{"type": "text", "text": f"Failed to read CSV: {exc}"}]}


def find_in_file(path: str, query: str, case_sensitive: bool = False, max_matches: int = 20):
    ok, message = _validate_file(path)
    if not ok:
        return {"role": "tool", "name": "find_in_file", "content": [{"type": "text", "text": message}]}

    if query is None or str(query).strip() == "":
        return {"role": "tool", "name": "find_in_file", "content": [{"type": "text", "text": "Search query cannot be empty."}]}

    try:
        text = _read_text_file(message, start_line=1, end_line=10**7)
    except Exception as exc:
        return {"role": "tool", "name": "find_in_file", "content": [{"type": "text", "text": f"Failed to read file for search: {exc}"}]}

    search_query = str(query)
    matches = []
    target_lines = text.splitlines()
    for line_number, line in enumerate(target_lines, start=1):
        candidate = line if case_sensitive else line.lower()
        query_value = search_query if case_sensitive else search_query.lower()
        if query_value in candidate:
            matches.append(f"{line_number}: {line.rstrip()}")
        if len(matches) >= max_matches:
            break

    if not matches:
        return {"role": "tool", "name": "find_in_file", "content": [{"type": "text", "text": f"No matches found for: {search_query}"}]}

    return {"role": "tool", "name": "find_in_file", "content": [{"type": "text", "text": "\n".join(matches)}]}


def read_json(path: str):
    ok, message = _validate_file(path)
    if not ok:
        return {"role": "tool", "name": "read_json", "content": [{"type": "text", "text": message}]}

    try:
        with open(message, "r", encoding="utf-8", errors="replace") as handle:
            content = json.load(handle)
        return {"role": "tool", "name": "read_json", "content": [{"type": "text", "text": _normalize_text(content)}]}
    except Exception as exc:
        return {"role": "tool", "name": "read_json", "content": [{"type": "text", "text": f"Failed to read JSON: {exc}"}]}


def read_docx(path: str):
    ok, message = _validate_file(path)
    if not ok:
        return {"role": "tool", "name": "read_docx", "content": [{"type": "text", "text": message}]}

    try:
        document = DocxDocument(message)
        paragraphs = [para.text for para in document.paragraphs if para.text.strip()]
        content = "\n".join(paragraphs) if paragraphs else "Document is empty."
        return {"role": "tool", "name": "read_docx", "content": [{"type": "text", "text": content}]}
    except Exception as exc:
        return {"role": "tool", "name": "read_docx", "content": [{"type": "text", "text": f"Failed to read DOCX: {exc}"}]}


read_file_tool_map = {
    "read_pdf": read_pdf,
    "read_image": read_image,
    "read_plain_text": read_plain_text,
    "read_csv": read_csv,
    "find_in_file": find_in_file,
    "read_json": read_json,
    "read_docx": read_docx,
}


if __name__ == "__main__":
    print("read_file_functions loaded")
    print(read_pdf(r"C:\Users\Modassir\Downloads\Syllabus_of_Class_XII-ScienceA_2026-27.pdf",5))
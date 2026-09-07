import fnmatch
import glob
import json
import os
import pathlib
import re
import sys
import uuid
from typing import Any
from classes import config


coding_instructions = """**START BY SETTING A BASE_DIR USING `set_base_dir` first**

## Objective
- Understand, search, validate, and make precise changes to source code or notebook cells inside the active base directory set by `set_base_dir`.
- Do not use these tools for unrelated file or directory housekeeping.
- Treat relative paths as workspace-relative paths and reject anything that attempts to escape the configured base directory.
- Prefer precise, minimal edits and reads over broad rewrites.

## Safety Rules
- Validate every path before reading, creating, writing, or patching files.
- Reject traversal attempts such as `..` or other path escapes before execution.
- Ensure parent directories exist before creating files or notebooks.
- For notebook cell edits, target the cell by `cell_id` and keep updates narrow and explicit.

## Reliability and Performance
- For full file / cell replacements, delete the file / cell  first and  then recreate the file / cell with new data.
- Keep outputs concise but informative: describe the action, target path, and final result.
- Prefer targeted reads and replacements over full-file rewrites unless required.
- Surface the real error clearly when a tool fails.

## Execution Pattern
1. Validate the base directory is set.
2. Resolve the requested path relative to the base directory.
3. Perform the file or notebook action.
4. Confirm the result clearly and briefly."""

BASE_DIR = None


#HELPER FUNCTIONS

def _resolve_path(path):
    if path is None:
        return None
    if not BASE_DIR:
        return None
    if os.path.isabs(path):
        return path
    return os.path.normpath(os.path.join(BASE_DIR, path))


def _load_notebook(notebook_path):
    with open(notebook_path, "r", encoding="utf-8") as f:
        notebook = json.load(f)

    if not isinstance(notebook, dict):
        raise ValueError(f"Notebook file is not a valid JSON object: {notebook_path}")

    cells = notebook.setdefault("cells", [])
    if not isinstance(cells, list):
        raise ValueError(f"Notebook cells must be a list: {notebook_path}")

    return notebook, cells


def _save_notebook(notebook_path, notebook):
    with open(notebook_path, "w", encoding="utf-8") as f:
        json.dump(notebook, f, indent=1, ensure_ascii=False)
        f.write("\n")


def _get_cell(cells, cell_id):
    for cell in cells:
        if cell.get("id") == cell_id:
            return cell
    raise KeyError(f"Cell ID not found: {cell_id}")


def _truncate_notebook_line(line, limit=None):
    limit = int(config.max_chrs if limit is None else limit)
    marker = "[truncated]..."
    line = str(line).rstrip("\r\n")
    if len(line) <= limit:
        return line
    return line[: max(0, limit - len(marker))] + marker


def _notebook_lines(source, start_line=1, end_line=None, line_limit=None, max_lines=None):
    if start_line < 1:
        raise ValueError("start_line must be greater than or equal to 1")
    if end_line is not None and end_line < start_line:
        raise ValueError("end_line must be greater than or equal to start_line")

    source_lines = source if isinstance(source, list) else str(source).splitlines()
    remaining_lines = source_lines[start_line - 1 :]
    selected_lines = remaining_lines[: end_line - start_line + 1 if end_line is not None else None]
    was_line_limited = max_lines is not None and len(remaining_lines) > max_lines
    if max_lines is not None:
        selected_lines = selected_lines[:max_lines]

    truncated_lines = [_truncate_notebook_line(line, line_limit) for line in selected_lines]
    if was_line_limited:
        truncated_lines.append("[truncated]...")
    return truncated_lines


def _format_notebook_result(value):
    formatted = json.dumps(value, indent=2, ensure_ascii=False, default=str)
    return "\n".join(_truncate_notebook_line(line) for line in formatted.splitlines())


#MAIN FUNCTIONS

def set_base_dir(path):
    global BASE_DIR
    BASE_DIR = os.path.abspath(path)
    os.makedirs(BASE_DIR, exist_ok=True)
    return {"role": "tool", "name": "set_base_dir", "content": str(BASE_DIR)}


def create_directory(dirPath):
    resolved = _resolve_path(dirPath)
    if not resolved:
        return {"role": "tool", "name": "create_directory", "content": "BASE_DIR not set! set_base_dir first."}
    result = os.makedirs(resolved, exist_ok=True)
    return {"role": "tool", "name": "create_directory", "content": str(result)}


def create_file(filePath, content):
    resolved_path = _resolve_path(filePath)
    if not resolved_path:
        return {"role": "tool", "name": "create_file", "content": "BASE_DIR not set! set_base_dir first."}
    directory = os.path.dirname(resolved_path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(resolved_path, "w", encoding="utf-8") as f:
        f.write(content)
    return {"role": "tool", "name": "create_file", "content": str(resolved_path)}


def list_dir(path):
    resolved = _resolve_path(path)
    if not resolved:
        return {"role": "tool", "name": "list_dir", "content": "BASE_DIR not set! set_base_dir first."}
    result = os.listdir(resolved)
    return {"role": "tool", "name": "list_dir", "content": str(result)}


def read_file(filePath, startLine, endLine):
    resolved_path = _resolve_path(filePath)
    if not resolved_path:
        return {"role": "tool", "name": "read_file", "content": "BASE_DIR not set! set_base_dir first."}
    with open(resolved_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    if endLine is None:
        endLine = len(lines)
    result = "".join(lines[startLine - 1 : endLine])
    return {"role": "tool", "name": "read_file", "content": str(result)}


def file_search(query, maxResults=None):
    resolved_query = _resolve_path(query)
    if not resolved_query:
        return {"role": "tool", "name": "file_search", "content": "BASE_DIR not set! set_base_dir first."}
    matches = glob.glob(resolved_query, recursive=True)
    if maxResults is not None:
        matches = matches[:maxResults]
    return {"role": "tool", "name": "file_search", "content": str(matches)}


def grep_search(query, isRegexp, includePattern=None, maxResults=None, includeIgnoredFiles=False):
    if includePattern is None:
        includePattern = "**/*"

    resolved_pattern = _resolve_path(includePattern)
    if not resolved_pattern:
        return {"role": "tool", "name": "grep_search", "content": "BASE_DIR not set! set_base_dir first."}
    pattern = pathlib.Path(resolved_pattern)
    if pattern.is_absolute():
        search_root = pattern.parent
        pattern_name = pattern.name
    else:
        search_root = pathlib.Path(BASE_DIR)
        pattern_name = str(pattern)

    files = []
    if "*" in pattern_name or "?" in pattern_name or "[" in pattern_name:
        files = glob.glob(str(pathlib.Path(search_root) / pattern_name), recursive=True)
    else:
        if os.path.isdir(resolved_pattern):
            files = [str(p) for p in pathlib.Path(resolved_pattern).rglob("*") if p.is_file()]
        else:
            files = [resolved_pattern] if os.path.isfile(resolved_pattern) else []

    matches = []
    regex = re.compile(query) if isRegexp else None

    for file_path in files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
        except (OSError, UnicodeDecodeError):
            continue

        if isRegexp:
            if regex.search(text):
                matches.append(file_path)
        else:
            if query in text:
                matches.append(file_path)

    if maxResults is not None:
        matches = matches[:maxResults]

    return {"role": "tool", "name": "grep_search", "content": str(matches)}


def replace_string_in_file(filePath, oldString, newString):
    resolved_path = _resolve_path(filePath)
    if not resolved_path:
        return {"role": "tool", "name": "replace_string_in_file", "content": "BASE_DIR not set! set_base_dir first."}
    with open(resolved_path, "r", encoding="utf-8") as f:
        original = f.read()
    if oldString not in original:
        raise ValueError(f"oldString not found in file: {resolved_path}")
    updated = original.replace(oldString, newString)
    with open(resolved_path, "w", encoding="utf-8") as f:
        f.write(updated)
    return {"role": "tool", "name": "replace_string_in_file", "content": str(resolved_path)}


def multi_replace_string_in_file(explanation, replacements):
    resolved = _resolve_path(".")
    if not resolved:
        return {"role": "tool", "name": "multi_replace_string_in_file", "content": "BASE_DIR not set! set_base_dir first."}
    results = []
    for replacement in replacements:
        file_path = _resolve_path(replacement["filePath"])
        old_string = replacement["oldString"]
        new_string = replacement["newString"]
        results.append(replace_string_in_file(file_path, old_string, new_string))
    return {"role": "tool", "name": "multi_replace_string_in_file", "content": str(results)}


def create_new_jupyter_notebook(path):
    resolved_path = _resolve_path(path)
    if not resolved_path:
        return {"role": "tool", "name": "create_new_jupyter_notebook", "content": "BASE_DIR not set! set_base_dir first."}
    directory = os.path.dirname(resolved_path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(resolved_path, "w") as f:
        f.write("")
    return {"role": "tool", "name": "create_new_jupyter_notebook", "content": str(resolved_path)}


def get_errors(path):
    resolved_path = _resolve_path(path)
    if not resolved_path:
        return {"role": "tool", "name": "get_errors", "content": "BASE_DIR not set! set_base_dir first."}

    try:
        with open(resolved_path, "r", encoding="utf-8") as f:
            source = f.read()
        compile(source, resolved_path, "exec")
        result = []
    except Exception as exc:
        result = {"filePath": resolved_path, "error": str(exc)}

    return {"role": "tool", "name": "get_errors", "content": str(result)}


def create_cell(notebook_path, cell_id=None, cell_type="code", source="", metadata=None, execution_count=None, outputs=None):
    resolved_path = _resolve_path(notebook_path)
    if not resolved_path:
        return {"role": "tool", "name": "add_cell", "content": "BASE_DIR not set! set_base_dir first."}
    notebook, cells = _load_notebook(resolved_path)

    if cell_id is None:
        cell_id = uuid.uuid4().hex

    new_cell = {
        "cell_type": cell_type,
        "id": cell_id,
        "metadata": metadata.copy() if isinstance(metadata, dict) else {},
        "source": source.splitlines(keepends=True) if isinstance(source, str) else (source or []),
    }

    if cell_type == "code":
        new_cell["execution_count"] = execution_count
        new_cell["outputs"] = outputs if outputs is not None else []

    cells.append(new_cell)
    _save_notebook(resolved_path, notebook)
    return {"role": "tool", "name": "add_cell", "content": str(cell_id)}


def list_cells(notebook_path, limit=50):
    resolved_path = _resolve_path(notebook_path)
    if not resolved_path:
        return {"role": "tool", "name": "list_cells", "content": "BASE_DIR not set! set_base_dir first."}

    _, cells = _load_notebook(resolved_path)
    cell_summaries = []
    for index, cell in enumerate(cells):
        source_lines = _notebook_lines(
            cell.get("source", []),
            1,
            None,
            line_limit=500,
            max_lines=limit,
        )
        cell_summaries.append({
            "index": index,
            "id": str(cell.get("id", "")),
            "cell_type": str(cell.get("cell_type", "")),
            "source": source_lines,
        })

    return {"role": "tool", "name": "list_cells", "content": _format_notebook_result(cell_summaries)}


def read_cell(notebook_path, cell_id, start_line=1, end_line=None):
    resolved_path = _resolve_path(notebook_path)
    if not resolved_path:
        return {"role": "tool", "name": "read_cell", "content": "BASE_DIR not set! set_base_dir first."}
    _, cells = _load_notebook(resolved_path)
    result = _get_cell(cells, cell_id).copy()
    result["source"] = _notebook_lines(result.get("source", []), start_line, end_line)
    return {"role": "tool", "name": "read_cell", "content": _format_notebook_result(result)}


def delete_cell(notebook_path, cell_id):
    resolved_path = _resolve_path(notebook_path)
    if not resolved_path:
        return {"role": "tool", "name": "delete_cell", "content": "BASE_DIR not set! set_base_dir first."}
    notebook, cells = _load_notebook(resolved_path)
    for index, cell in enumerate(cells):
        if cell.get("id") == cell_id:
            del cells[index]
            _save_notebook(resolved_path, notebook)
            return {"role": "tool", "name": "delete_cell", "content": "Cell deleted successfully."}
    return {"role": "tool", "name": "delete_cell", "content": "Cell could not be deleted: cell not found."}


def patch_cell(notebook_path, cell_id, old_line, new_line):
    resolved_path = _resolve_path(notebook_path)
    if not resolved_path:
        return {"role": "tool", "name": "patch_cell", "content": "BASE_DIR not set! set_base_dir first."}
    notebook, cells = _load_notebook(resolved_path)
    cell = _get_cell(cells, cell_id)

    if "source" not in cell:
        raise KeyError(f"Cell does not have a source field: {cell_id}")

    source = cell["source"]
    if isinstance(source, list):
        source_text = "".join(source)
    else:
        source_text = str(source)

    updated_text = source_text.replace(old_line, new_line)
    cell["source"] = updated_text.splitlines(keepends=True)

    _save_notebook(resolved_path, notebook)
    return {"role": "tool", "name": "patch_cell", "content": str(cell)}


coding_tool_map = {
    "set_base_dir": set_base_dir,
    "create_directory": create_directory,
    "create_file": create_file,
    "list_dir": list_dir,
    "read_file": read_file,
    "file_search": file_search,
    "grep_search": grep_search,
    "replace_string_in_file": replace_string_in_file,
    "multi_replace_string_in_file": multi_replace_string_in_file,
    "create_new_jupyter_notebook": create_new_jupyter_notebook,
    "get_errors": get_errors,
    "create_cell": create_cell,
    "list_cells": list_cells,
    "read_cell": read_cell,
    "delete_cell": delete_cell,
    "patch_cell": patch_cell,
}
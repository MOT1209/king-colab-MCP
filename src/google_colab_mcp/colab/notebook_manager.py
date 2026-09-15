"""Create/read/update .ipynb notebooks, and execute them cell-by-cell.

All paths are resolved through a `PathGuard`, so a notebook path can never
escape the configured notebook/workspace root.
"""
from __future__ import annotations

from typing import Any

import nbformat
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook

from ..security.path_guard import PathGuard
from ..utils.errors import NotebookError
from .execution_manager import ExecutionManager


class NotebookManager:
    def __init__(self, path_guard: PathGuard, execution_manager: ExecutionManager):
        self.path_guard = path_guard
        self.execution_manager = execution_manager

    def create_notebook(self, path: str, kernel_name: str = "python3") -> dict[str, Any]:
        nb = new_notebook()
        nb.metadata["kernelspec"] = {
            "name": kernel_name,
            "display_name": "Python 3",
            "language": "python",
        }
        target = self.path_guard.resolve(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        nbformat.write(nb, target)
        return {"path": path, "cell_count": 0}

    def _load(self, path: str):
        target = self.path_guard.resolve(path)
        if not target.exists():
            raise NotebookError(f"Notebook not found: {path}")
        try:
            return target, nbformat.read(target, as_version=4)
        except Exception as exc:
            raise NotebookError(f"Failed to parse notebook: {path}", details=str(exc)) from exc

    def get_notebook(self, path: str) -> dict[str, Any]:
        target, nb = self._load(path)
        cells = [
            {"index": i, "cell_type": c.get("cell_type"), "source": c.get("source", "")}
            for i, c in enumerate(nb.cells)
        ]
        return {"path": path, "cell_count": len(cells), "cells": cells, "metadata": dict(nb.metadata)}

    def update_notebook(self, path: str, cells: list[dict[str, Any]]) -> dict[str, Any]:
        target, nb = self._load(path)
        new_cells = []
        for c in cells:
            if c.get("cell_type") == "markdown":
                new_cells.append(new_markdown_cell(c.get("source", "")))
            else:
                new_cells.append(new_code_cell(c.get("source", "")))
        nb.cells = new_cells
        nbformat.write(nb, target)
        return {"path": path, "cell_count": len(new_cells)}

    def add_cell(self, path: str, source: str, cell_type: str = "code", index: int | None = None) -> dict[str, Any]:
        target, nb = self._load(path)
        cell = new_markdown_cell(source) if cell_type == "markdown" else new_code_cell(source)
        if index is None or index >= len(nb.cells):
            nb.cells.append(cell)
            idx = len(nb.cells) - 1
        else:
            nb.cells.insert(index, cell)
            idx = index
        nbformat.write(nb, target)
        return {"path": path, "index": idx, "cell_count": len(nb.cells)}

    def edit_cell(self, path: str, index: int, source: str) -> dict[str, Any]:
        target, nb = self._load(path)
        if not (0 <= index < len(nb.cells)):
            raise NotebookError(f"Cell index {index} out of range (0..{len(nb.cells) - 1}).")
        nb.cells[index]["source"] = source
        nbformat.write(nb, target)
        return {"path": path, "index": index}

    def delete_cell(self, path: str, index: int) -> dict[str, Any]:
        target, nb = self._load(path)
        if not (0 <= index < len(nb.cells)):
            raise NotebookError(f"Cell index {index} out of range (0..{len(nb.cells) - 1}).")
        del nb.cells[index]
        nbformat.write(nb, target)
        return {"path": path, "cell_count": len(nb.cells)}

    def execute_cell(self, path: str, index: int, session_id: str | None, timeout: float) -> dict[str, Any]:
        target, nb = self._load(path)
        if not (0 <= index < len(nb.cells)):
            raise NotebookError(f"Cell index {index} out of range (0..{len(nb.cells) - 1}).")
        cell = nb.cells[index]
        if cell.get("cell_type") != "code":
            return {"path": path, "index": index, "skipped": True, "reason": "not a code cell"}
        result = self.execution_manager.run(cell.get("source", ""), session_id, timeout)
        nbformat.write(nb, target)
        return {"path": path, "index": index, **result}

    def execute_notebook(self, path: str, session_id: str | None, timeout: float) -> dict[str, Any]:
        target, nb = self._load(path)
        results = []
        for i, cell in enumerate(nb.cells):
            if cell.get("cell_type") != "code":
                continue
            result = self.execution_manager.run(cell.get("source", ""), session_id, timeout)
            results.append({"index": i, **result})
        return {"path": path, "executed_cells": len(results), "results": results}

    def export_notebook(self, path: str, export_format: str = "ipynb") -> dict[str, Any]:
        target, nb = self._load(path)
        if export_format == "ipynb":
            return {"path": path, "format": "ipynb", "content": nbformat.writes(nb)}
        if export_format == "python":
            lines = []
            for cell in nb.cells:
                if cell.get("cell_type") == "code":
                    lines.append(cell.get("source", ""))
                    lines.append("")
            return {"path": path, "format": "python", "content": "\n".join(lines)}
        raise NotebookError(f"Unsupported export format: {export_format}", suggestion="Use 'ipynb' or 'python'.")

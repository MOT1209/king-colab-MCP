import pytest

from google_colab_mcp.utils.errors import NotebookError


def test_create_and_get_notebook(ctx):
    ctx.notebook_manager.create_notebook("nb1.ipynb")
    info = ctx.notebook_manager.get_notebook("nb1.ipynb")
    assert info["cell_count"] == 0
    assert info["path"] == "nb1.ipynb"


def test_add_edit_delete_cell(ctx):
    ctx.notebook_manager.create_notebook("nb2.ipynb")
    ctx.notebook_manager.add_cell("nb2.ipynb", "print(1)")
    ctx.notebook_manager.add_cell("nb2.ipynb", "# heading", cell_type="markdown")
    info = ctx.notebook_manager.get_notebook("nb2.ipynb")
    assert info["cell_count"] == 2

    ctx.notebook_manager.edit_cell("nb2.ipynb", 0, "print(2)")
    info = ctx.notebook_manager.get_notebook("nb2.ipynb")
    assert info["cells"][0]["source"] == "print(2)"

    ctx.notebook_manager.delete_cell("nb2.ipynb", 1)
    info = ctx.notebook_manager.get_notebook("nb2.ipynb")
    assert info["cell_count"] == 1


def test_get_missing_notebook_raises(ctx):
    with pytest.raises(NotebookError):
        ctx.notebook_manager.get_notebook("does_not_exist.ipynb")


def test_execute_cell_runs_against_fake_backend(ctx):
    ctx.notebook_manager.create_notebook("nb3.ipynb")
    ctx.notebook_manager.add_cell("nb3.ipynb", "print('cell output')")
    result = ctx.notebook_manager.execute_cell("nb3.ipynb", 0, session_id=None, timeout=10)
    assert result["stdout"] == "hello\n"


def test_execute_notebook_runs_all_code_cells(ctx):
    ctx.notebook_manager.create_notebook("nb4.ipynb")
    ctx.notebook_manager.add_cell("nb4.ipynb", "print('a')")
    ctx.notebook_manager.add_cell("nb4.ipynb", "## not code", cell_type="markdown")
    ctx.notebook_manager.add_cell("nb4.ipynb", "print('b')")
    result = ctx.notebook_manager.execute_notebook("nb4.ipynb", session_id=None, timeout=10)
    assert result["executed_cells"] == 2


def test_export_notebook_as_python(ctx):
    ctx.notebook_manager.create_notebook("nb5.ipynb")
    ctx.notebook_manager.add_cell("nb5.ipynb", "print('hi')")
    exported = ctx.notebook_manager.export_notebook("nb5.ipynb", export_format="python")
    assert "print('hi')" in exported["content"]

"""Unit tests for CodeIndexer -- Tree-sitter based symbol extraction."""

from __future__ import annotations

from pathlib import Path

import pytest

from codebot.context.code_indexer import CodeIndexer

PYTHON_SOURCE = b"""\
import os
from pathlib import Path


class UserService:
    \"\"\"Service for user management.\"\"\"

    def __init__(self, db):
        self.db = db

    def get_user(self, user_id: str):
        \"\"\"Retrieve a user by ID.\"\"\"
        return self.db.find(user_id)


def create_app():
    \"\"\"Create the application instance.\"\"\"
    return "app"
"""

TYPESCRIPT_SOURCE = b"""\
import { Request, Response } from "express";

class UserController {
    private db: Database;

    constructor(db: Database) {
        this.db = db;
    }
}

function handleRequest(req: Request, res: Response): void {
    res.json({ status: "ok" });
}
"""


@pytest.fixture
def indexer(tmp_path: Path) -> CodeIndexer:
    """Create a CodeIndexer with a temporary project root."""
    return CodeIndexer(project_root=tmp_path)


class TestExtractPythonFunctions:
    """Tests for Python function extraction."""

    def test_extract_python_functions(self, indexer: CodeIndexer) -> None:
        symbols = indexer.extract_symbols(PYTHON_SOURCE, "app.py")
        function_names = [s.name for s in symbols if s.kind == "function"]
        assert "create_app" in function_names

    def test_extract_python_classes(self, indexer: CodeIndexer) -> None:
        symbols = indexer.extract_symbols(PYTHON_SOURCE, "app.py")
        class_names = [s.name for s in symbols if s.kind == "class"]
        assert "UserService" in class_names

    def test_extract_python_imports(self, indexer: CodeIndexer) -> None:
        symbols = indexer.extract_symbols(PYTHON_SOURCE, "app.py")
        import_symbols = [s for s in symbols if s.kind == "import"]
        assert len(import_symbols) >= 2

    def test_extract_python_methods(self, indexer: CodeIndexer) -> None:
        symbols = indexer.extract_symbols(PYTHON_SOURCE, "app.py")
        method_names = [s.name for s in symbols if s.kind == "method"]
        assert "get_user" in method_names


class TestExtractTypeScript:
    """Tests for TypeScript symbol extraction."""

    def test_extract_typescript_functions(self, indexer: CodeIndexer) -> None:
        symbols = indexer.extract_symbols(TYPESCRIPT_SOURCE, "controller.ts")
        function_names = [s.name for s in symbols if s.kind == "function"]
        assert "handleRequest" in function_names

    def test_extract_typescript_classes(self, indexer: CodeIndexer) -> None:
        symbols = indexer.extract_symbols(TYPESCRIPT_SOURCE, "controller.ts")
        class_names = [s.name for s in symbols if s.kind == "class"]
        assert "UserController" in class_names


class TestUnsupportedExtensions:
    """Tests for unsupported file types."""

    def test_unsupported_extension_returns_empty(self, indexer: CodeIndexer) -> None:
        symbols = indexer.extract_symbols(b"some content", "data.xyz")
        assert symbols == []

    def test_unknown_extension_returns_empty(self, indexer: CodeIndexer) -> None:
        symbols = indexer.extract_symbols(b"some content", "file.rs")
        assert symbols == []


class TestSymbolMetadata:
    """Tests for symbol metadata correctness."""

    def test_symbol_line_numbers(self, indexer: CodeIndexer) -> None:
        symbols = indexer.extract_symbols(PYTHON_SOURCE, "app.py")
        for symbol in symbols:
            assert isinstance(symbol.line_start, int)
            assert isinstance(symbol.line_end, int)
            assert symbol.line_start >= 1
            assert symbol.line_end >= symbol.line_start

    def test_symbol_signature_truncated(self, indexer: CodeIndexer) -> None:
        symbols = indexer.extract_symbols(PYTHON_SOURCE, "app.py")
        for symbol in symbols:
            assert len(symbol.signature) <= 200

    def test_symbol_file_path_preserved(self, indexer: CodeIndexer) -> None:
        symbols = indexer.extract_symbols(PYTHON_SOURCE, "src/app.py")
        for symbol in symbols:
            assert symbol.file_path == "src/app.py"


class TestIndexFileAsync:
    """Tests for async file indexing."""

    @pytest.mark.asyncio
    async def test_index_file_async(self, indexer: CodeIndexer, tmp_path: Path) -> None:
        py_file = tmp_path / "sample.py"
        py_file.write_bytes(PYTHON_SOURCE)
        symbols = await indexer.index_file(py_file)
        assert len(symbols) > 0
        names = [s.name for s in symbols]
        assert "create_app" in names
        assert "UserService" in names

    @pytest.mark.asyncio
    async def test_index_directory(self, indexer: CodeIndexer, tmp_path: Path) -> None:
        py_file = tmp_path / "module.py"
        py_file.write_bytes(PYTHON_SOURCE)
        ts_file = tmp_path / "handler.ts"
        ts_file.write_bytes(TYPESCRIPT_SOURCE)
        symbols = await indexer.index_directory(tmp_path)
        names = [s.name for s in symbols]
        assert "create_app" in names
        assert "handleRequest" in names

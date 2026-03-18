"""Tree-sitter based code indexer for structural symbol extraction.

Parses Python, TypeScript, JavaScript, and TSX source files using
Tree-sitter grammars, extracting functions, classes, methods, and import
statements as ``CodeSymbol`` objects.

The extracted symbols are intended for indexing into the vector store so
that agents can perform semantic code search.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

import tree_sitter_javascript as tsjavascript
import tree_sitter_python as tspython
import tree_sitter_typescript as tstypescript
from tree_sitter import Language, Parser, Query, QueryCursor

from codebot.context.models import CodeSymbol

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Language registry
# ---------------------------------------------------------------------------

_LANGUAGES: dict[str, Language] = {
    ".py": Language(tspython.language()),
    ".js": Language(tsjavascript.language()),
    ".ts": Language(tstypescript.language_typescript()),
    ".tsx": Language(tstypescript.language_tsx()),
}

# ---------------------------------------------------------------------------
# Tree-sitter S-expression queries per file extension
# ---------------------------------------------------------------------------

_QUERIES: dict[str, dict[str, str]] = {
    ".py": {
        "function": "(function_definition name: (identifier) @name) @definition",
        "class": "(class_definition name: (identifier) @name) @definition",
        "import": "[(import_statement) (import_from_statement)] @import",
        "method": (
            "(class_definition body: (block "
            "(function_definition name: (identifier) @name) @method))"
        ),
    },
    ".ts": {
        "function": "(function_declaration name: (identifier) @name) @definition",
        "class": "(class_declaration name: (type_identifier) @name) @definition",
        "import": "(import_statement) @import",
    },
    ".tsx": {
        "function": "(function_declaration name: (identifier) @name) @definition",
        "class": "(class_declaration name: (type_identifier) @name) @definition",
        "import": "(import_statement) @import",
    },
    ".js": {
        "function": "(function_declaration name: (identifier) @name) @definition",
        "class": "(class_declaration name: (identifier) @name) @definition",
        "import": "(import_statement) @import",
    },
}

# Capture names that correspond to full definitions (not just the name node).
_DEFINITION_CAPTURES = {"definition", "method", "import"}

_DEFAULT_EXTENSIONS = [".py", ".ts", ".tsx", ".js"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_name(node: object, source: bytes) -> str:
    """Extract the identifier name from a definition node."""
    for child in node.children:  # type: ignore[attr-defined]
        if child.type in ("identifier", "type_identifier"):
            return source[child.start_byte : child.end_byte].decode(
                errors="replace"
            )
    # For import nodes the entire text is the "name".
    text = source[node.start_byte : node.end_byte].decode(errors="replace")  # type: ignore[attr-defined]
    return text.split("\n")[0][:80]


# ---------------------------------------------------------------------------
# CodeIndexer
# ---------------------------------------------------------------------------


class CodeIndexer:
    """Extracts code symbols from source files using Tree-sitter.

    Args:
        project_root: Root directory of the project being indexed.
    """

    def __init__(self, project_root: str | Path) -> None:
        self._project_root = Path(project_root)

    # ------------------------------------------------------------------
    # Synchronous extraction
    # ------------------------------------------------------------------

    def extract_symbols(self, source: bytes, file_path: str) -> list[CodeSymbol]:
        """Parse *source* and return extracted symbols.

        Args:
            source: Raw bytes of the source file.
            file_path: Path of the file (used for extension detection
                and stored in each ``CodeSymbol``).

        Returns:
            A list of ``CodeSymbol`` instances.  Returns an empty list
            if the file extension is not supported.
        """
        ext = Path(file_path).suffix
        language = _LANGUAGES.get(ext)
        if language is None:
            return []

        parser = Parser(language)
        tree = parser.parse(source)

        symbols: list[CodeSymbol] = []
        queries = _QUERIES.get(ext, {})

        for kind, query_str in queries.items():
            query = Query(language, query_str)
            cursor = QueryCursor(query)

            # matches() yields (pattern_index, dict[capture_name, list[Node]])
            for _pattern_idx, capture_dict in cursor.matches(tree.root_node):
                # Find the definition/method/import node (not the name node)
                definition_node = None
                for capture_name, nodes in capture_dict.items():
                    if capture_name in _DEFINITION_CAPTURES and nodes:
                        definition_node = nodes[0]
                        break

                if definition_node is None:
                    continue

                name = _get_name(definition_node, source)
                sig_end = min(
                    definition_node.start_byte + 200,
                    definition_node.end_byte,
                )
                signature = source[
                    definition_node.start_byte : sig_end
                ].decode(errors="replace")
                symbols.append(
                    CodeSymbol(
                        name=name,
                        kind=kind,
                        file_path=file_path,
                        line_start=definition_node.start_point.row + 1,
                        line_end=definition_node.end_point.row + 1,
                        signature=signature,
                    )
                )

        return symbols

    # ------------------------------------------------------------------
    # Async API
    # ------------------------------------------------------------------

    async def index_file(self, file_path: str | Path) -> list[CodeSymbol]:
        """Read and parse a single file, returning extracted symbols.

        Uses ``asyncio.to_thread`` for file I/O to avoid blocking the
        event loop.
        """
        path = Path(file_path)

        def _read_and_parse() -> list[CodeSymbol]:
            try:
                source = path.read_bytes()
            except (OSError, FileNotFoundError):
                logger.warning("Cannot read file: %s", path)
                return []
            return self.extract_symbols(source, str(path))

        return await asyncio.to_thread(_read_and_parse)

    async def index_directory(
        self,
        directory: str | Path,
        extensions: list[str] | None = None,
    ) -> list[CodeSymbol]:
        """Walk *directory* and index all files with matching extensions.

        Args:
            directory: Root of the subtree to index.
            extensions: File extensions to include (default:
                ``[".py", ".ts", ".tsx", ".js"]``).

        Returns:
            Aggregated list of ``CodeSymbol`` from all matching files.
        """
        exts = set(extensions or _DEFAULT_EXTENSIONS)
        dir_path = Path(directory)

        files = [
            p
            for p in dir_path.rglob("*")
            if p.is_file() and p.suffix in exts
        ]

        all_symbols: list[CodeSymbol] = []
        for f in files:
            symbols = await self.index_file(f)
            all_symbols.extend(symbols)
        return all_symbols

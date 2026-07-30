import ast
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SELF = Path(__file__).resolve()
SOURCE_SUFFIXES = {".py", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".sh", ".toml", ".yaml", ".yml"}
TOOL_PATTERN = re.compile(r"\b(?:ca" r"rgo|ru" r"stc|ru" r"stup|cl" r"ippy|mi" r"ri)\b", re.IGNORECASE)
PRODUCT_IMPORTS = {"ephemeral_sandbox", "sandbox_gateway", "sandbox_manager", "sandbox_runtime"}
GENERATED_DIRECTORIES = {
    ".pytest_cache", "__pycache__", "dist", "node_modules", "playwright-report", "test-results"
}


def implementation_files() -> list[Path]:
    return [
        path
        for path in ROOT.rglob("*")
        if path.is_file()
        and path != SELF
        and not GENERATED_DIRECTORIES.intersection(path.parts)
        and "fixtures" not in path.parts
        and "docs" not in path.parts
        and path.name not in {"MIGRATION_CHECKLIST.md", "README.md"}
    ]


def test_benchmark_tree_contains_no_owned_native_sources_or_manifests() -> None:
    forbidden = [
        path.relative_to(ROOT)
        for path in ROOT.rglob("*")
        if path.is_file()
        and not GENERATED_DIRECTORIES.intersection(path.parts)
        and (path.suffix == ".rs" or path.name in {"Cargo.toml", "Cargo.lock"})
    ]
    assert forbidden == []


def test_commands_and_launchers_never_invoke_native_build_tools() -> None:
    findings = []
    for path in implementation_files():
        if path.suffix not in SOURCE_SUFFIXES:
            continue
        if TOOL_PATTERN.search(path.read_text(errors="replace")):
            findings.append(path.relative_to(ROOT))
    assert findings == []


def test_python_has_no_product_import_path_or_source_coupling() -> None:
    findings = []
    for path in implementation_files():
        if path.suffix != ".py":
            continue
        source = path.read_text()
        tree = ast.parse(source, filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = {alias.name.split(".", 1)[0] for alias in node.names}
                if names & PRODUCT_IMPORTS:
                    findings.append((path.relative_to(ROOT), node.lineno, "product import"))
            elif isinstance(node, ast.ImportFrom) and node.module:
                if node.module.split(".", 1)[0] in PRODUCT_IMPORTS:
                    findings.append((path.relative_to(ROOT), node.lineno, "product import"))
            elif isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
                if node.value.id == "sys" and node.attr == "path":
                    findings.append((path.relative_to(ROOT), node.lineno, "sys.path access"))
        if re.search(r"(?:read_text|read_bytes|open)\([^\n]*[.]rs\b", source):
            findings.append((path.relative_to(ROOT), 0, "native source read"))
        if "PYTHONPATH" in source:
            findings.append((path.relative_to(ROOT), 0, "import path mutation"))
    assert findings == []

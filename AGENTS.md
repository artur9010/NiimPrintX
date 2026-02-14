# Agent Guidelines

## Code Quality Checks

### Pylint (Python linter)

Run pylint on the GUI codebase:
```bash
nix-shell -p pylint -p python312Packages.pyqt6 --run "pylint NiimPrintX/gui --output-format=colorized --score=n --disable=E0611,no-name-in-module,import-error,C0114,C0115,C0116,C0303,C0301,C0304,C0103,C0411,C0413,C0415,W0611,W0613,R0902,R0903,R0913,R0914,R0915,R0917"
```

Full scan (including all warnings):
```bash
nix-shell -p pylint -p python312Packages.pyqt6 --run "pylint NiimPrintX/gui --output-format=colorized --score=n --disable=E0611,no-name-in-module,import-error"
```

Note: `E0611` and `no-name-in-module` are disabled because pylint cannot resolve PyQt6 bindings properly.

### Ruff (faster alternative)

```bash
nix-shell -p ruff --run "ruff check NiimPrintX/gui"
```

### Type Checking (mypy)

```bash
nix-shell -p mypy -p python312Packages.pyqt6 --run "mypy NiimPrintX/gui --ignore-missing-imports"
```

### Security Scan (bandit)

```bash
nix-shell -p bandit --run "bandit -r NiimPrintX/gui"
```

## Common Disable Codes

When running pylint, these are commonly disabled for this project:
- `E0611`, `no-name-in-module` - PyQt6 binding resolution issues
- `import-error` - Third-party packages not in nix environment
- `C0114/5/6` - Missing docstrings (optional to enforce)
- `C0303` - Trailing whitespace
- `R0902/3` - Too many/few attributes/methods (common in Qt classes)

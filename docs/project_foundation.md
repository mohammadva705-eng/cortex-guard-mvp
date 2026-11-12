# CORTEX-GUARD MVP v1 Project Foundation

## Folder Structure

```text
backend/
  app/
    core/
      constants.py
      config.py
extension/
tests/
docs/
requirements.txt
```

## Naming Conventions

Python packages and modules use `snake_case`.

Python constants use `UPPER_SNAKE_CASE`.

Python classes use `PascalCase`.

Python functions, methods, and variables use `snake_case`.

JavaScript files use `camelCase` for functions and variables.

Chrome extension manifest fields follow Manifest V3 naming.

Tests use `test_*.py`.

## Shared Project-Level Configuration

Project-level limits and localhost settings are defined in `backend/app/core/constants.py`.

Immutable runtime configuration is exposed as `CONFIG` in `backend/app/core/config.py`.

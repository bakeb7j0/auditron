---
globs: tests/**/*.py
alwaysApply: false
---

Follow comprehensive testing practices: Use descriptive test names with docstrings, organize tests into logical classes, mock external dependencies (SSH, filesystem), use provided fixtures from conftest.py, mark tests appropriately (@pytest.mark.unit/@pytest.mark.integration), test both success and failure paths, aim for >90% coverage on new code, include edge cases and error conditions.
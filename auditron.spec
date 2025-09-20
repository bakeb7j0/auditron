# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Auditron USB deployment.

This spec file packages Auditron into a standalone executable suitable
for USB deployment on systems without Python dependencies.

Usage:
    pyinstaller auditron.spec

Output:
    dist/auditron - Single executable file
    dist/auditron.exe - Windows equivalent (if built on Windows)
"""

import os
import sys
from pathlib import Path

# Get the absolute path to the project root
project_root = Path(SPECPATH).resolve()

block_cipher = None

a = Analysis(
    [str(project_root / 'auditron.py')],
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        # Include database schema and documentation
        (str(project_root / 'docs' / 'schema.sql'), 'docs'),
        (str(project_root / 'docs' / 'requirements-ears.md'), 'docs'),
        # Include any additional data files needed at runtime
    ],
    hiddenimports=[
        # Explicitly include all strategy modules
        'strategies.base',
        'strategies.osinfo', 
        'strategies.processes',
        'strategies.routes',
        'strategies.rpm_inventory',
        'strategies.rpm_verify', 
        'strategies.sockets',
        # Explicitly include all utility modules
        'utils.db',
        'utils.ssh_runner',
        'utils.parsing',
        'utils.compress',
        # Standard library modules that might need explicit inclusion
        'sqlite3',
        'gzip',
        'hashlib',
        'subprocess',
        'shlex',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude test and development dependencies
        'pytest', 
        'pytest_cov', 
        'pytest_mock',
        'ruff',
        'black', 
        'isort',
        'flake8',
        'pylint',
        'pyright',
        'pre_commit',
        # Exclude unnecessary standard library modules
        'tkinter',
        'turtle', 
        'pydoc',
        'doctest',
        'unittest.mock',
        'test',
        'tests',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='auditron',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # Enable UPX compression if available
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Keep console for CLI interface
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Could add an icon file here if desired
)
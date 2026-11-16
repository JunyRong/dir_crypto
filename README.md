# Folder Encryption (Windows)

Simple Windows folder locker implemented in Python.

## Features
- Right-click a folder in Explorer to **Encrypt Folder** or **Decrypt Folder** (after installing context-menu entries).
- Encryption prompts for a password (with confirmation) and derives a key with PBKDF2-HMAC-SHA256 + Fernet (authenticated encryption).
- Locked folders store encrypted data in `.securevault`/`.securemeta` and plaintext contents are removed on successful encryption.
- **System drive protection:** folders on the system drive (e.g. `%SystemDrive%`, typically `C:\`) cannot be encrypted/decrypted by this tool.

## Requirements
- Windows
- Python 3.10+ installed and available on PATH (required for the one-click/script install in this package)

## Standalone installer (no system Python required)
A prebuilt standalone package is generated at `release/FolderCrypto-Standalone/` (and zipped as `release/FolderCrypto-Standalone.zip`).
- Run `FolderCryptoSetup.exe` (default: install). Installs to `%LOCALAPPDATA%\FolderCrypto` and registers the Explorer context menu for the current user.
- Uninstall: `FolderCryptoSetup.exe uninstall`.
- Keep the `app\` folder next to `FolderCryptoSetup.exe` when installing. The installed app is self-contained (PyInstaller build).

## One-click install (from source, requires Python)
1. Keep the project folder in a fixed location (context menu entries reference files inside it).
2. Double-click `install.bat`.
3. Approve the Administrator (UAC) prompt when asked. The script will install dependencies (`requirements.txt`) and register the Explorer context menu for the current user.

To remove, double-click `uninstall.bat` (also approves UAC) or run the manual uninstall command below.

## Manual install (Administrator terminal)
Open a terminal (PowerShell or Command Prompt) **as Administrator**, then run from the project root:
```powershell
pip install -r requirements.txt
python scripts/install_context_menu.py install
```
To remove (also run the terminal as Administrator):
```powershell
python scripts/install_context_menu.py uninstall
```
The menu entries invoke `src/gui.py` with the installed Python interpreter (`pythonw.exe` when available). On Windows 11, the entries may appear under **Show more options** in the folder context menu. If the project folder is moved, run install again to update paths.

## CLI / manual usage
```powershell
# GUI action (prompts for password)
python src/gui.py encrypt "D:\path\to\folder"
python src/gui.py decrypt "D:\path\to\folder"

# Non-interactive core helper (password passed as argument; use with care)
python src/folder_crypto.py encrypt "D:\path\to\folder" "password"
python src/folder_crypto.py decrypt "D:\path\to\folder" "password"
```

## Notes / limitations
- This is a basic locker: it encrypts folder contents into a vault file inside the folder. It is **not** the same as transparent, on-access Windows EFS/BitLocker-style encryption.
- Do not interrupt encryption/decryption; ensure you remember the password (there is no recovery).
- Test on non-critical data first. Backups are recommended before encrypting important folders.
- Folders on the system drive are refused by design.

# AGENTS.md

## Project
- Windows-only Python folder locker (no git repo, no CI/tests configured).
- `src/folder_crypto.py`: core logic. Encrypts folder contents into `.securevault` + `.securemeta` inside the target folder (salt + PBKDF2-HMAC-SHA256 derived Fernet token, JSON payload of relative paths/base64 data) and removes plaintext entries after vault write. Decrypt verifies/restores and removes vault/meta.
- `src/gui.py`: Tkinter password prompts + Explorer-facing entrypoint (`python src/gui.py encrypt|decrypt <folder>`). Uses `pythonw.exe` when installed via menu script to avoid console.
- `scripts/install_context_menu.py`: per-user HKCU `Directory\shell` entries (`Encrypt Folder`/`Decrypt Folder`) pointing to `src/gui.py`; run `python scripts/install_context_menu.py install|uninstall`.
- `packaging/setup_app.py`: standalone installer source (built as `FolderCryptoSetup.exe`) that copies `app/` payload to `%LOCALAPPDATA%\FolderCrypto` by default and registers HKCU menu pointing to `FolderCrypto.exe`.
- `release/FolderCrypto-Standalone/` (+ `.zip`): generated standalone installer package (no system Python required).

## Commands
- Standalone install (no system Python): run `release/FolderCrypto-Standalone/FolderCryptoSetup.exe` (default install) / `... uninstall`.
- One-click install/uninstall (source, needs Python): `install.bat` / `uninstall.bat`.
- Install deps (source): `pip install -r requirements.txt` (requires `cryptography`).
- Build standalone package (needs PyInstaller): `python -m PyInstaller --noconfirm --clean --onedir --windowed --name FolderCrypto --distpath build_out/dist --workpath build_out/build --specpath build_out src/gui.py` then `python -m PyInstaller --noconfirm --clean --onefile --console --name FolderCryptoSetup --distpath build_out/setup_dist --workpath build_out/setup_build --specpath build_out packaging/setup_app.py`, assemble `release/FolderCrypto-Standalone/` with `app/` + `FolderCryptoSetup.exe`.
- Syntax check (Python): `python -m py_compile src/folder_crypto.py src/gui.py scripts/install_context_menu.py packaging/setup_app.py`.
- Manual core helper (non-interactive, password arg): `python src/folder_crypto.py encrypt|decrypt <folder> <password>`.

## Constraints / quirks
- **System drive is refused**: operations reject targets on `%SystemDrive%` (see `is_on_system_drive` in `src/folder_crypto.py`); preserve this behavior.
- Lock state is detected by presence of `.securevault` and `.securemeta`; encrypt/decrypt expect a directory path (locked folder remains a directory).
- No password recovery; encryption removes originals after writing vault—avoid changes that risk data loss without safeguards. Test on non-critical data.

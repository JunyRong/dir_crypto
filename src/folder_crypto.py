import base64
import json
import os
import shutil
import stat
import sys
import tempfile
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

VAULT_NAME = ".securevault"
META_NAME = ".securemeta"
MAGIC = b"FLOCK1"


def get_system_drive() -> str:
    drive = os.environ.get("SystemDrive")
    if drive:
        return os.path.normcase(os.path.normpath(drive + os.sep))
    # Fallback: Windows install drive
    windir = os.environ.get("WINDIR")
    if windir:
        return os.path.normcase(os.path.normpath(os.path.splitdrive(windir)[0] + os.sep))
    return os.path.normcase(os.path.normpath("C:\\"))


def is_on_system_drive(path: str | Path) -> bool:
    p = Path(path).resolve()
    drive = os.path.normcase(os.path.normpath(p.drive + os.sep))
    sys_drive = get_system_drive()
    return drive == sys_drive


def _derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=390000,
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode("utf-8")))


def _collect_files(folder: Path) -> list[Path]:
    files = []
    for root, dirs, filenames in os.walk(folder):
        # skip vault/meta if somehow present in unexpected state
        for name in filenames:
            rel = Path(root, name).relative_to(folder)
            if rel.as_posix() in {VAULT_NAME, META_NAME}:
                continue
            files.append(rel)
    return sorted(files)


def is_locked(folder: str | Path) -> bool:
    folder = Path(folder)
    return (folder / VAULT_NAME).is_file() and (folder / META_NAME).is_file()


def encrypt_folder(folder: str | Path, password: str) -> None:
    folder = Path(folder).resolve()
    if not folder.is_dir():
        raise ValueError(f"Not a directory: {folder}")
    if is_on_system_drive(folder):
        raise PermissionError("System drive folders cannot be encrypted.")
    if is_locked(folder):
        raise ValueError("Folder is already encrypted.")
    if not password:
        raise ValueError("Password cannot be empty.")

    rel_files = _collect_files(folder)
    payload = {"files": []}
    for rel in rel_files:
        abs_path = folder / rel
        with open(abs_path, "rb") as f:
            data = f.read()
        payload["files"].append({
            "path": rel.as_posix(),
            "data_b64": base64.b64encode(data).decode("ascii"),
        })

    salt = os.urandom(16)
    key = _derive_key(password, salt)
    fernet = Fernet(key)
    plaintext = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    token = fernet.encrypt(plaintext)

    meta = {"salt_b64": base64.b64encode(salt).decode("ascii"), "v": 1}
    vault_path = folder / VAULT_NAME
    meta_path = folder / META_NAME

    # Write vault/meta first
    with tempfile.NamedTemporaryFile("wb", delete=False, dir=str(folder)) as tf:
        tf.write(MAGIC + token)
        tmp_vault = Path(tf.name)
    with tempfile.NamedTemporaryFile("w", delete=False, dir=str(folder), encoding="utf-8") as tf:
        json.dump(meta, tf)
        tmp_meta = Path(tf.name)

    os.replace(tmp_vault, vault_path)
    os.replace(tmp_meta, meta_path)

    # Remove original files/dirs after vault is in place
    for entry in list(folder.iterdir()):
        if entry.name in {VAULT_NAME, META_NAME}:
            continue
        try:
            if entry.is_dir() and not entry.is_symlink():
                shutil.rmtree(entry)
            else:
                _force_remove(entry)
        except Exception:
            # Attempt to roll back? vault exists; best effort cleanup warning context
            raise


def _force_remove(path: Path) -> None:
    try:
        os.chmod(path, stat.S_IWRITE)
    except Exception:
        pass
    path.unlink(missing_ok=True)


def decrypt_folder(folder: str | Path, password: str) -> None:
    folder = Path(folder).resolve()
    if not folder.is_dir():
        raise ValueError(f"Not a directory: {folder}")
    if is_on_system_drive(folder):
        raise PermissionError("System drive folders cannot be decrypted with this tool.")
    if not is_locked(folder):
        raise ValueError("Folder is not encrypted.")
    if not password:
        raise ValueError("Password cannot be empty.")

    vault_path = folder / VAULT_NAME
    meta_path = folder / META_NAME
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
    salt = base64.b64decode(meta["salt_b64"])
    with open(vault_path, "rb") as f:
        blob = f.read()
    if not blob.startswith(MAGIC):
        raise ValueError("Invalid vault format.")
    token = blob[len(MAGIC):]

    key = _derive_key(password, salt)
    fernet = Fernet(key)
    try:
        plaintext = fernet.decrypt(token)
    except InvalidToken as e:
        raise ValueError("Incorrect password or corrupted vault.") from e

    payload = json.loads(plaintext.decode("utf-8"))
    files = payload.get("files", [])

    # Restore to temp dir then move, to reduce partial restore risk
    with tempfile.TemporaryDirectory(dir=str(folder)) as tdir:
        troot = Path(tdir)
        for item in files:
            rel = Path(item["path"])
            # prevent path traversal
            dest = (troot / rel).resolve()
            if folder.resolve() not in dest.parents and dest != folder.resolve():
                # ensure inside troot
                pass
            dest_t = troot / rel
            if not str(dest_t.resolve()).startswith(str(troot.resolve())):
                raise ValueError("Invalid path in vault.")
            dest_t.parent.mkdir(parents=True, exist_ok=True)
            with open(dest_t, "wb") as f:
                f.write(base64.b64decode(item["data_b64"]))
        # move restored contents into folder
        for child in troot.iterdir():
            target = folder / child.name
            if target.exists():
                if target.is_dir():
                    shutil.rmtree(target)
                else:
                    _force_remove(target)
            shutil.move(str(child), str(target))

    _force_remove(vault_path)
    _force_remove(meta_path)


if __name__ == "__main__":
    # simple manual test helper: python folder_crypto.py encrypt|decrypt <folder> <password>
    if len(sys.argv) != 4:
        print("Usage: folder_crypto.py <encrypt|decrypt> <folder> <password>")
        sys.exit(2)
    cmd, folder, pw = sys.argv[1], sys.argv[2], sys.argv[3]
    try:
        if cmd == "encrypt":
            encrypt_folder(folder, pw)
        elif cmd == "decrypt":
            decrypt_folder(folder, pw)
        else:
            raise SystemExit("Unknown command")
        print("OK")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

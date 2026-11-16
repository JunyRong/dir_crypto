import argparse
import os
import sys
import tkinter as tk
from tkinter import messagebox, simpledialog

# Allow running as script from src or project root
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if THIS_DIR not in sys.path:
    sys.path.insert(0, THIS_DIR)

from folder_crypto import decrypt_folder, encrypt_folder, is_locked, is_on_system_drive


def _ensure_tk_root():
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    return root


def prompt_password(confirm: bool = False) -> str | None:
    root = _ensure_tk_root()
    try:
        pw = simpledialog.askstring("Folder Encryption", "Enter password:", show="*", parent=root)
        if pw is None:
            return None
        if confirm:
            pw2 = simpledialog.askstring("Folder Encryption", "Confirm password:", show="*", parent=root)
            if pw2 is None:
                return None
            if pw != pw2:
                messagebox.showerror("Folder Encryption", "Passwords do not match.", parent=root)
                return None
        return pw
    finally:
        root.destroy()


def show_info(title: str, msg: str):
    root = _ensure_tk_root()
    try:
        messagebox.showinfo(title, msg, parent=root)
    finally:
        root.destroy()


def show_error(title: str, msg: str):
    root = _ensure_tk_root()
    try:
        messagebox.showerror(title, msg, parent=root)
    finally:
        root.destroy()


def do_encrypt(folder: str):
    if is_on_system_drive(folder):
        show_error("Folder Encryption", "Cannot encrypt folders on the system drive.")
        return 2
    if is_locked(folder):
        show_error("Folder Encryption", "This folder is already encrypted.")
        return 1
    pw = prompt_password(confirm=True)
    if pw is None:
        return 1
    if not pw:
        show_error("Folder Encryption", "Password cannot be empty.")
        return 1
    try:
        encrypt_folder(folder, pw)
        show_info("Folder Encryption", "Folder encrypted successfully.")
        return 0
    except Exception as e:
        show_error("Folder Encryption", f"Encryption failed: {e}")
        return 1


def do_decrypt(folder: str):
    if is_on_system_drive(folder):
        show_error("Folder Encryption", "Cannot decrypt folders on the system drive using this tool.")
        return 2
    if not is_locked(folder):
        show_error("Folder Encryption", "This folder is not encrypted.")
        return 1
    pw = prompt_password(confirm=False)
    if pw is None:
        return 1
    try:
        decrypt_folder(folder, pw)
        show_info("Folder Encryption", "Folder decrypted successfully.")
        return 0
    except Exception as e:
        show_error("Folder Encryption", f"Decryption failed: {e}")
        return 1


def main(argv=None):
    parser = argparse.ArgumentParser(description="Folder encryption GUI entrypoint")
    parser.add_argument("action", choices=["encrypt", "decrypt"], help="Action to perform")
    parser.add_argument("folder", help="Target folder path")
    args = parser.parse_args(argv)

    folder = os.path.abspath(args.folder)
    if not os.path.isdir(folder):
        show_error("Folder Encryption", f"Folder not found: {folder}")
        return 1

    if args.action == "encrypt":
        return do_encrypt(folder)
    else:
        return do_decrypt(folder)


if __name__ == "__main__":
    sys.exit(main())

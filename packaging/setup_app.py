import argparse
import ctypes
import os
import shutil
import sys
import winreg

APP_NAME = "FolderCrypto"
MENU_KEY_ENCRYPT = r"Software\Classes\Directory\shell\EncryptFolder"
MENU_KEY_DECRYPT = r"Software\Classes\Directory\shell\DecryptFolder"


def is_admin() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def relaunch_as_admin():
    params = " ".join(f'"{a}"' for a in sys.argv[1:])
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)


def default_install_dir() -> str:
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    return os.path.join(base, APP_NAME)


def source_app_dir() -> str:
    # When packaged as release, payload sits in ./app next to setup exe/script
    here = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, "frozen", False) else __file__))
    cand = os.path.join(here, "app")
    if os.path.isdir(cand):
        return cand
    # dev fallback
    cand = os.path.join(here, "..", "dist", "FolderCrypto")
    return os.path.abspath(cand)


def gui_exe_path(install_dir: str) -> str:
    return os.path.join(install_dir, "FolderCrypto.exe")


def _delete_tree(root, subkey):
    try:
        with winreg.OpenKey(root, subkey, 0, winreg.KEY_ALL_ACCESS) as k:
            while True:
                try:
                    child = winreg.EnumKey(k, 0)
                except OSError:
                    break
                _delete_tree(root, subkey + "\\" + child)
        winreg.DeleteKey(root, subkey)
    except FileNotFoundError:
        pass


def register_menu(gui_exe: str):
    if not os.path.isfile(gui_exe):
        raise FileNotFoundError(f"GUI executable not found: {gui_exe}")
    enc_cmd = f'"{gui_exe}" encrypt "%1"'
    dec_cmd = f'"{gui_exe}" decrypt "%1"'

    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, MENU_KEY_ENCRYPT) as k:
        winreg.SetValueEx(k, "MUIVerb", 0, winreg.REG_SZ, "Encrypt Folder")
        winreg.SetValueEx(k, "Icon", 0, winreg.REG_SZ, "shell32.dll,47")
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, MENU_KEY_ENCRYPT + r"\command") as k:
        winreg.SetValue(k, "", winreg.REG_SZ, enc_cmd)

    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, MENU_KEY_DECRYPT) as k:
        winreg.SetValueEx(k, "MUIVerb", 0, winreg.REG_SZ, "Decrypt Folder")
        winreg.SetValueEx(k, "Icon", 0, winreg.REG_SZ, "shell32.dll,48")
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, MENU_KEY_DECRYPT + r"\command") as k:
        winreg.SetValue(k, "", winreg.REG_SZ, dec_cmd)


def unregister_menu():
    _delete_tree(winreg.HKEY_CURRENT_USER, MENU_KEY_ENCRYPT)
    _delete_tree(winreg.HKEY_CURRENT_USER, MENU_KEY_DECRYPT)


def do_install(install_dir: str):
    src = source_app_dir()
    if not os.path.isdir(src):
        raise FileNotFoundError(f"Payload app folder not found: {src}")
    if os.path.abspath(src) != os.path.abspath(install_dir):
        if os.path.exists(install_dir):
            shutil.rmtree(install_dir)
        shutil.copytree(src, install_dir)
    gui = gui_exe_path(install_dir)
    register_menu(gui)
    print(f"Installed to: {install_dir}")
    print("Context menu registered for current user.")


def do_uninstall(install_dir: str):
    unregister_menu()
    # try remove installed files if they are in default/user location
    try:
        if os.path.isdir(install_dir):
            shutil.rmtree(install_dir)
            print(f"Removed: {install_dir}")
    except Exception as e:
        print(f"Menu removed, but could not fully remove files: {e}")
    print("Context menu removed.")


def main():
    ap = argparse.ArgumentParser(description="FolderCrypto standalone installer")
    ap.add_argument("action", choices=["install", "uninstall"], nargs="?", default="install")
    ap.add_argument("--dir", dest="install_dir", default=default_install_dir(), help="Install directory")
    ap.add_argument("--no-pause", action="store_true", help="Do not pause before exit")
    args = ap.parse_args()

    try:
        if args.action == "install":
            do_install(args.install_dir)
        else:
            do_uninstall(args.install_dir)
        code = 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        code = 1
    finally:
        if not args.no_pause:
            try:
                input("\nPress Enter to exit...")
            except EOFError:
                pass
    return code


if __name__ == "__main__":
    sys.exit(main())

import argparse
import os
import sys
import winreg

MENU_KEY_ENCRYPT = r"Software\Classes\Directory\shell\EncryptFolder"
MENU_KEY_DECRYPT = r"Software\Classes\Directory\shell\DecryptFolder"


def _pythonw_exe() -> str:
    exe = sys.executable
    # prefer pythonw to avoid console window
    if exe.lower().endswith("python.exe"):
        cand = exe[:-10] + "pythonw.exe"
        if os.path.isfile(cand):
            return cand
    return exe


def install():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    gui = os.path.join(root, "src", "gui.py")
    pyw = _pythonw_exe()
    if not os.path.isfile(gui):
        raise FileNotFoundError(f"gui.py not found: {gui}")

    enc_cmd = f'"{pyw}" "{gui}" encrypt "%1"'
    dec_cmd = f'"{pyw}" "{gui}" decrypt "%1"'

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

    print("Context menu installed for current user.")


def _delete_tree(root, subkey):
    try:
        with winreg.OpenKey(root, subkey, 0, winreg.KEY_ALL_ACCESS) as k:
            # delete children first
            while True:
                try:
                    child = winreg.EnumKey(k, 0)
                except OSError:
                    break
                _delete_tree(root, subkey + "\\" + child)
        winreg.DeleteKey(root, subkey)
    except FileNotFoundError:
        pass


def uninstall():
    _delete_tree(winreg.HKEY_CURRENT_USER, MENU_KEY_ENCRYPT)
    _delete_tree(winreg.HKEY_CURRENT_USER, MENU_KEY_DECRYPT)
    print("Context menu removed for current user.")


def main():
    ap = argparse.ArgumentParser(description="Install/uninstall Explorer context menu entries")
    ap.add_argument("action", choices=["install", "uninstall"])
    args = ap.parse_args()
    if os.name != "nt":
        print("This script only supports Windows.")
        return 1
    if args.action == "install":
        install()
    else:
        uninstall()
    return 0


if __name__ == "__main__":
    sys.exit(main())

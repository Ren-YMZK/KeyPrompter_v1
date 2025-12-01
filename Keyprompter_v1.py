import tkinter as tk
from pynput import keyboard
from itertools import groupby

# 特殊キーのマッピング
special_keys = {
    "enter": "↩︎",
    "esc": "Esc",
    "backspace": "🔙",
    "space": "␣",
    "tab": "➡︎",
    "home": "Home",
    "end": "End",
    "page_up": "[Page Up]",
    "page_down": "[Page Down]",
    "up": "↑",
    "down": "↓",
    "left": "←",
    "right": "→",
    "insert": "Insert",
    "delete": "Delete",
}
special_keys_values = list(special_keys.values())


def compress_sequence(arr):
    """連続する同じキーを圧縮する"""
    result = []
    for key, group in groupby(arr):
        count = len(list(group))
        if (key.isalpha() or key.isdigit()) and key not in special_keys_values:
            for _ in range(count):
                result.append(" " + key)
        else:
            if count > 1:
                result.append(f" {key} ×{count}  ")
            else:
                result.append(" " + key)
    return result


# Tkinter ウィンドウのセットアップ
root = tk.Tk()
root.title("Key Prompter")
root.geometry("800x80")

labelshift = tk.Label(root, text="", font=("Helvetica", 15),
                      anchor="e", justify="right", fg="green")
labelshift.grid(row=0, column=0, columnspan=2, padx=5, pady=0, sticky="ew")

label = tk.Label(root, text="", font=("Helvetica", 30),
                 anchor="e", justify="right", fg="black")
label.grid(row=1, column=0, padx=0, pady=0, sticky="e")

label2 = tk.Label(root, text="", font=("Helvetica", 30),
                  anchor="e", justify="right", fg="blue")
label2.grid(row=1, column=1, padx=0, pady=0, sticky="w")

root.columnconfigure(0, weight=1)
root.columnconfigure(1, weight=0)

# グローバル変数
modifier_keys = set()
current_keys = []
shift_exp = None
shift_exp_ary = []

# Shift+数字記号のマッピング
numshift_src = {
    "!": "1", '"': "2", "#": "3", "$": "4", "%": "5", "&": "6", "'": "7",
    "(": "8", ")": "9", "<": ",", ">": ".", "?": "/", "+": ";", "=": "-",
    "`": "@", "*": ":", "|": "\\", "{": "[", "}": "]",
}


def update_label():
    """現在の修飾キーと直近のキーを表示"""
    buffer = compress_sequence(current_keys)
    display_keys = "".join(buffer[-39:-1])
    label.config(text=display_keys)
    if buffer:
        label2.config(text=buffer[-1] + " ")
    labelshift.config(text=" ".join(shift_exp_ary))


def on_press(key):
    """キーが押されたときの処理"""
    global current_keys, shift_exp, shift_exp_ary

    try:
        # --- ここから修正: Ctrl＋アルファベット の制御文字を変換 ---
        if hasattr(key, 'char') and key.char:
            raw = key.char
            # Ctrl 押下時に返ってくる制御文字 (ord < 32) を A-Z にマッピング
            if 'ctrl' in modifier_keys and len(modifier_keys) == 1 and ord(raw) < 32:
                # '\x01'→'A', '\x02'→'B', ... '\x03'→'C' ...
                letter = chr(ord(raw) + 64)
                combined_key = "ctrl+" + letter
                current_keys.append(combined_key)
                shift_exp_ary.append("  ")
            else:
                # それ以外は従来の処理
                key_name = raw.lower()
                if modifier_keys:
                    if modifier_keys == {"shift"} and key_name.isalpha():
                        key_name = key_name.upper()
                        shift_exp = "  "
                        combined_key = key_name
                    elif modifier_keys == {"shift"} and key_name in numshift_src:
                        tmp = key_name
                        shift_exp = "+".join(modifier_keys) + \
                            "+" + numshift_src[tmp]
                        combined_key = tmp
                    else:
                        combined_key = "+".join(modifier_keys) + f"+{key_name}"
                        shift_exp = "  "
                    current_keys.append(combined_key)
                    shift_exp_ary.append(shift_exp)
                else:
                    current_keys.append(key_name)
                    shift_exp_ary.append("  ")
        # --- ここまで修正 ---

        # 特殊キー or 修飾キー
        elif hasattr(key, 'name'):
            key_name = special_keys.get(key.name)
            if key_name:
                if modifier_keys:
                    combined_key = "+".join(modifier_keys) + f"+{key_name}"
                    current_keys.append(combined_key)
                else:
                    current_keys.append(key_name)
                shift_exp_ary.append("  ")
            elif key.name in [
                "shift", "shift_l", "shift_r",
                "ctrl", "ctrl_l", "ctrl_r",
                "alt", "alt_l", "alt_r",
                "cmd", "cmd_l", "cmd_r"
            ]:
                base = key.name.split('_')[0]
                modifier_keys.add(base)

    except AttributeError:
        pass

    update_label()


def on_release(key):
    """キーが離されたときの処理"""
    try:
        if hasattr(key, 'name'):
            base = key.name.split('_')[0]
            if base in modifier_keys:
                modifier_keys.remove(base)
    except AttributeError:
        pass

    update_label()


# リスナー開始
listener = keyboard.Listener(on_press=on_press, on_release=on_release)
listener.start()

# メインループ
root.mainloop()
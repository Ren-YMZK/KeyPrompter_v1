import tkinter as tk
from pynput import keyboard
from itertools import groupby

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
# special_keys のvalueのみの配列
special_keys_values = list(special_keys.values())

def compress_sequence(arr):
    """連続する同じキーを圧縮する"""
    global special_keys_values
    result = []
    for key, group in groupby(arr):
        count = len(list(group))
        if (key.isalpha() or key.isdigit()) and key not in special_keys_values:  # 'a-z' または '0-9' の場合
            # countの回数だけ、keyを追加
            for _ in range(count):
                result.append(" "+key)
        else:
            if count > 1:
                result.append(f" {key} ×{count}  ")
            else:
                result.append(" "+key)
    return result

    # result = [f"{key}×{len(list(group))}" for key, group in groupby(arr)]
    # return result

root = tk.Tk()
root.title("Key Prompter")
root.geometry("800x80")  # 横幅を広げる

labelshift = tk.Label(root, text="", font=("Helvetica", 15), anchor="e", justify="right", fg="green")
labelshift.grid(row=0, column=0, columnspan=2, padx=5, pady=0, sticky="ew")


label = tk.Label(root, text="", font=("Helvetica", 30), anchor="e", justify="right", fg="black")
label.grid(row=1, column=0, padx=0, pady=0, sticky="e")
# label.pack(expand=True, fill=tk.BOTH)  # ラベルを右寄せにする
label2 = tk.Label(root, text="", font=("Helvetica", 30), anchor="e", justify="right", fg="blue")
label2.grid(row=1, column=1, padx=0, pady=0, sticky="w")
root.columnconfigure(1, weight=0)  # 右ラベルを内容サイズのみにする
root.columnconfigure(0, weight=1)  # 左ラベルを調整
# label2.pack(expand=True, fill=tk.BOTH)  # ラベルを右寄せにする
label2.config(text="")  # 初期化
label.config(text="")  # 初期化


# 修飾キーの状態を追跡するためのセット
modifier_keys = set()
current_keys = []  # 直近のキーを保持するリスト
shift_exp = None
shift_exp_ary = []
numshift_src = {
    "!": "1",
    '"': "2",
    "#": "3",
    "$": "4",
    "%": "5",
    "&": "6",
    "'": "7",
    "(": "8",
    ")": "9",
    "<": ",",
    ">": ".",
    "?": "/",
    "+": ";",
    "=": "-",
    "`": "@",
    "*": ":",
    "|": "\\",
    "{": "[",
    "}": "]",
}

def update_label():
    global current_keys, shift_exp
    """現在の修飾キーと直近のキーを表示"""
    buffer = compress_sequence(current_keys)
    display_keys = "".join(buffer[-39:-1])  # 直近3つのキーを表示
    label.config(text=display_keys)

    if (len(buffer) > 0):
        label2.config(text=buffer[-1]+" ")
    # if (shift_exp != None):
    labelshift.config(text=" ".join(shift_exp_ary))
    # もし、current_keysの長さが100を超えたら、最初の50個を削除する
    # if current_keys and len(current_keys) > 20:
    #     current_keys_2 = current_keys[:20]
    #     current_keys = current_keys[20:]
    #     label2.config(text=" ".join(compress_sequence(current_keys_2)))


def on_press(key):
    """キーが押されたときの処理"""
    global current_keys, special_keys, numshift_src, shift_exp_ary
    # modifier_keysの状態をデバッグ表示
    # print(f"Modifier keys: {modifier_keys}")
    try:
        if hasattr(key, 'char') and key.char:  # 通常のキー
            key_name = key.char.lower()  # 大文字で表示
            if modifier_keys:  # 修飾キーが押されている場合
                # もしmodifier_keys がshiftだけで、かつkey_nameがa-zの範囲にある場合は、key_nameを大文字にする
                if len(modifier_keys) == 1 and "shift" in modifier_keys and key_name.isalpha():
                    key_name = key_name.upper()
                    combined_key = f"{key_name}"
                    shift_exp = "  "
                elif len(modifier_keys) == 1 and "shift" in modifier_keys and key_name in numshift_src.keys() :
                    tmp = key_name
                    shift_exp = "+".join(modifier_keys) + "+"+numshift_src[tmp]
                    combined_key = tmp
                else:
                    combined_key = "+".join(modifier_keys) + f"+{key_name}"
                    shift_exp = "  "
                current_keys.append(combined_key)
                shift_exp_ary.append(shift_exp)
            else:
                current_keys.append(key_name)
                shift_exp_ary.append("  ")
        elif hasattr(key, 'name'):  # 修飾キー
            # print(f"Key name: {key.name}")
            key_name = special_keys.get(key.name)
            if key_name:  # 特殊キーが認識された場合
                if modifier_keys:  # 修飾キーが押されている場合
                    combined_key = "+".join(modifier_keys) + f"+{key_name}"
                    current_keys.append(combined_key)
                else:
                    current_keys.append(key_name)
            elif key.name in ["shift", "ctrl", "alt", "cmd"]:  # 修飾キー
                modifier_keys.add(key.name)  # 修飾キーをセットに追加
                # print(f"Modifier keys: {modifier_keys}")

            # modifier_keys.add(key.name.upper())  # 修飾キーをセットに追加
            # current_keys.append(key.name.upper())  # 修飾キーも履歴に追加
    except AttributeError:
        pass
    update_label()

def on_release(key):
    """キーが離されたときの処理"""
    try:
        if hasattr(key, 'name') and key.name in modifier_keys:
            modifier_keys.remove(key.name)  # 修飾キーをセットから削除
    except AttributeError:
        pass
    update_label()

listener = keyboard.Listener(on_press=on_press, on_release=on_release)
listener.start()

root.mainloop()
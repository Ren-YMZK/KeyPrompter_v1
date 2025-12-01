import tkinter as tk
from tkinter import font as tkFont
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

# 連続する同じキーを圧縮する関数


def compress_sequence(arr):
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
canvas_width = 800
canvas_height = 80
root.geometry(f"{canvas_width}x{canvas_height}")

canvas = tk.Canvas(root, width=canvas_width, height=canvas_height)
canvas.pack()

# フォント設定
font_small = tkFont.Font(family="Helvetica", size=15)
font_large = tkFont.Font(family="Helvetica", size=30)

# グローバル変数
modifier_keys = set()
current_keys = []
shift_exp_ary = []

# Shift+数字記号のマッピング
numshift_src = {
    "!": "1", '"': "2", "#": "3", "$": "4", "%": "5", "&": "6", "'": "7",
    "(": "8", ")": "9", "<": ",", ">": ".", "?": "/", "+": ";", "=": "-",
    "`": "@", "*": ":", "|": "\\", "{": "[", "}": "]",
}

# ラベル更新処理 (Canvas 描画)


def update_canvas():
    canvas.delete("all")
    buffer = compress_sequence(current_keys)
    n = 39  # 表示する直近キー数
    visible_buffer = buffer[-n:]
    visible_shift = shift_exp_ary[-n:]

    # 各キーごとの幅を、Shift補足とキー本体のうち大きい方で確保
    widths = [
        max(
            font_large.measure(key_text + " "),
            font_small.measure(shift_text + " ")
        ) + 10  # 余白を追加
        for shift_text, key_text in zip(visible_shift, visible_buffer)
    ]
    total_width = sum(widths)
    x = canvas_width - 20 - total_width

    for i, (shift_text, key_text) in enumerate(zip(visible_shift, visible_buffer)):
        w = widths[i]
        # 上段: Shift 表示
        canvas.create_text(
            x + w / 2, 20,
            text=shift_text,
            anchor='center',
            font=font_small,
            fill='green'
        )
        # 下段: キー表示
        color = 'blue' if i == len(visible_buffer) - 1 else 'black'
        canvas.create_text(
            x + w / 2, 55,
            text=key_text + " ",
            anchor='center',
            font=font_large,
            fill=color
        )
        x += w

# キー押下時の処理


def on_press(key):
    global current_keys, shift_exp_ary
    try:
        if hasattr(key, 'char') and key.char:
            raw = key.char
            if 'ctrl' in modifier_keys and len(modifier_keys) == 1 and ord(raw) < 32:
                letter = chr(ord(raw) + 64)
                combined = 'ctrl+' + letter
                current_keys.append(combined)
                shift_exp_ary.append('')
            else:
                key_name = raw.lower()
                if modifier_keys:
                    if modifier_keys == {'shift'} and key_name.isalpha():
                        key_name = key_name.upper()
                        combined = key_name
                        shift_exp_ary.append('')
                    elif modifier_keys == {'shift'} and key_name in numshift_src:
                        shift_exp = '+'.join(modifier_keys) + \
                            '+' + numshift_src[key_name]
                        combined = key_name
                        shift_exp_ary.append(shift_exp)
                    else:
                        combined = '+'.join(modifier_keys) + f"+{key_name}"
                        shift_exp_ary.append('')
                    current_keys.append(combined)
                else:
                    current_keys.append(key_name)
                    shift_exp_ary.append('')
        elif hasattr(key, 'name'):
            name = key.name
            mapped = special_keys.get(name)
            if mapped:
                combined = '+'.join(modifier_keys) + \
                    f"+{mapped}" if modifier_keys else mapped
                current_keys.append(combined)
                shift_exp_ary.append('')
            elif name in [
                'shift', 'shift_l', 'shift_r',
                'ctrl', 'ctrl_l', 'ctrl_r',
                'alt', 'alt_l', 'alt_r',
                'cmd', 'cmd_l', 'cmd_r'
            ]:
                base = name.split('_')[0]
                modifier_keys.add(base)
    except AttributeError:
        pass
    update_canvas()

# キー離上時の処理


def on_release(key):
    try:
        if hasattr(key, 'name'):
            base = key.name.split('_')[0]
            if base in modifier_keys:
                modifier_keys.remove(base)
    except AttributeError:
        pass
    update_canvas()


# リスナー開始
listener = keyboard.Listener(on_press=on_press, on_release=on_release)
listener.start()

# メインループ
root.mainloop()
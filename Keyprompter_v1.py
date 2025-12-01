import tkinter as tk
from tkinter import font as tkFont
from pynput import keyboard, mouse
from itertools import groupby
from collections import deque

# 特殊キーの表示マッピング
special_keys = {
    "enter": "Enter", "esc": "Esc", "backspace": "Backspace", "space": "␣",
    "tab": "Tab", "home": "Home", "end": "End",
    "page_up": "[Page Up]", "page_down": "[Page Down]",
    "up": "↑", "down": "↓", "left": "←", "right": "→",
    "insert": "Insert", "delete": "Delete"
}

# Shift+記号のマッピング
shift_symbols = {
    "!": "1", '"': "2", "#": "3", "$": "4", "%": "5", "&": "6", "'": "7",
    "(": "8", ")": "9", "<": ",", ">": ".", "?": "/", "+": ";", "=": "-",
    "`": "@", "*": ":", "|": "\\", "{": "[", "}": "]",
}

# GUI初期設定
root = tk.Tk()
root.title("Key + Mouse Prompter")
canvas_width, canvas_height = 800, 80
canvas = tk.Canvas(root, width=canvas_width, height=canvas_height, bg='white')
canvas.pack()
root.geometry(f"{canvas_width}x{canvas_height}")

font_small = tkFont.Font(family="Helvetica", size=15)
font_large = tkFont.Font(family="Helvetica", size=30)

# 状態変数
modifier_keys = set()

MAX_HISTORY_SIZE = 100
key_history = deque(maxlen=MAX_HISTORY_SIZE)  # 最大100件保持

# キー履歴の圧縮処理


def compress_key_history(history):
    result = []
    for (k, s), group in groupby(history):
        count = len(list(group))
        key_label = f"{k} ×{count}" if count > 1 else k
        shift_label = s if count == 1 else (f"{s} ×{count}" if s else "")
        result.append((key_label, shift_label))
    return result

# Canvas更新処理


def update_canvas():
    canvas.delete("all")
    visible = compress_key_history(key_history)[-30:]

    widths = [
        max(font_large.measure(k), font_small.measure(s or "")) + 10
        for k, s in visible
    ]
    total_width = sum(widths)
    x = canvas_width - total_width - 10

    for i, (key_text, shift_text) in enumerate(visible):
        w = widths[i]
        canvas.create_text(x + w/2, 20, text=shift_text,
                           font=font_small, fill='green')
        color = 'blue' if i == len(visible) - 1 else 'black'
        canvas.create_text(x + w/2, 55, text=key_text,
                           font=font_large, fill=color)
        x += w

# キー押下処理


def on_press(key):
    global key_history
    try:
        if hasattr(key, 'char') and key.char:
            raw = key.char
            shift_text = ''
            key_name = raw

            # Ctrl + A〜Z (制御文字対応)
            if 'ctrl' in modifier_keys and len(modifier_keys) == 1 and ord(raw) <= 26:
                letter = chr(ord(raw.upper()) + 64)
                key_name = letter
                shift_text = f"Ctrl+{letter}"
            else:
                if 'shift' in modifier_keys:
                    if key_name in shift_symbols:
                        shift_text = f"Shift+{shift_symbols[key_name]}"
                    elif key_name.isalpha():
                        key_name = key_name.upper()
                        shift_text = f"Shift+{key_name}"
                    else:
                        shift_text = "Shift"
                if 'ctrl' in modifier_keys:
                    shift_text = f"Ctrl+{key_name}"

            key_history.append((key_name, shift_text))

        elif hasattr(key, 'name'):
            name = key.name
            if name in special_keys:
                label = special_keys[name]
                shift_text = ''
                if 'ctrl' in modifier_keys:
                    shift_text = f"Ctrl+{label}"
                elif 'shift' in modifier_keys:
                    shift_text = f"Shift+{label}"
                elif modifier_keys:
                    shift_text = '+'.join(modifier_keys) + f"+{label}"

                key_history.append((label, shift_text))
            elif name.startswith(('shift', 'ctrl', 'alt', 'cmd')):
                base = name.split('_')[0]
                modifier_keys.add(base)
    except Exception:
        pass
    update_canvas()

# キー離上処理


def on_release(key):
    try:
        if hasattr(key, 'name'):
            base = key.name.split('_')[0]
            modifier_keys.discard(base)
    except Exception:
        pass
    update_canvas()

# マウスクリック処理


def on_click(x, y, button, pressed):
    if not pressed:
        return  # 押したときのみ反応

    button_map = {
        mouse.Button.left: "Left Click",
        mouse.Button.right: "Right Click",
        mouse.Button.middle: "Middle Click"
    }

    label = button_map.get(button, str(button))
    key_history.append((label, ""))
    update_canvas()


# リスナー開始
keyboard_listener = keyboard.Listener(on_press=on_press, on_release=on_release)
keyboard_listener.start()

mouse_listener = mouse.Listener(on_click=on_click)
mouse_listener.start()

root.mainloop()
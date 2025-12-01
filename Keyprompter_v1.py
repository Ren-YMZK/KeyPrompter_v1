import tkinter as tk
from tkinter import font as tkFont
from pynput import keyboard, mouse
from collections import deque
from itertools import groupby

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

# 登録済みコマンド
registered_commands = {
    "ls", "curl", "ping", "cd", "mkdir", "rm", "whoami", "git", "python"
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
key_history = deque(maxlen=100)
command_buffer = []  # コマンド構築用（Backspace対応）
last_command_display = ""  # 中央表示用

# 履歴表示圧縮


def compress_key_history(history):
    result = []
    for (k, s), group in groupby(history):
        count = len(list(group))
        key_label = f"{k} ×{count}" if count > 1 else k
        shift_label = s if count == 1 else (f"{s} ×{count}" if s else "")
        result.append((key_label, shift_label))
    return result

# Canvas描画更新


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

    if last_command_display:
        canvas.create_text(
            canvas_width / 2, canvas_height / 2,
            text=last_command_display,
            font=tkFont.Font(family="Helvetica", size=20, weight="bold"),
            fill="red"
        )

# コマンド検出ロジック（Enter時）


def extract_command():
    global last_command_display
    joined = ''.join(command_buffer)
    # スペース記号を変換
    joined = joined.replace("␣", " ")
    # 最後に登場した登録コマンドを探す（位置付き）
    last_found = -1
    matched_cmd = ""
    for cmd in registered_commands:
        idx = joined.rfind(cmd)
        if idx != -1 and idx >= last_found:
            last_found = idx
            matched_cmd = cmd

    if last_found != -1:
        last_command_display = joined[last_found:].strip()
    else:
        last_command_display = ""

# キー押下処理


def on_press(key):
    global key_history, command_buffer
    try:
        if hasattr(key, 'char') and key.char:
            raw = key.char
            shift_text = ''
            key_name = raw

            if 'ctrl' in modifier_keys and len(modifier_keys) == 1 and ord(raw) <= 26:
                key_name = chr(ord(raw.upper()) + 64)
                shift_text = f"Ctrl+{key_name}"
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
            command_buffer.append(key_name)

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

                if name == "enter":
                    extract_command()
                    command_buffer.clear()
                elif name == "backspace":
                    if command_buffer:
                        command_buffer.pop()

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
        return
    label = {
        button.left: "Left Click",
        button.right: "Right Click",
        button.middle: "Middle Click"
    }.get(button, str(button))
    key_history.append((label, ""))
    update_canvas()


# リスナー起動
keyboard.Listener(on_press=on_press, on_release=on_release).start()
mouse.Listener(on_click=on_click).start()

root.mainloop()
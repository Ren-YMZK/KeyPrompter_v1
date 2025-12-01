import tkinter as tk
from tkinter import font as tkFont
from pynput import keyboard, mouse
from collections import deque
from itertools import groupby

special_keys = {
    "enter": "Enter", "esc": "Esc", "backspace": "Backspace", "space": "␣",
    "tab": "Tab", "home": "Home", "end": "End",
    "page_up": "[Page Up]", "page_down": "[Page Down]",
    "up": "↑", "down": "↓", "left": "←", "right": "→",
    "insert": "Insert", "delete": "Delete"
}

shift_symbols = {
    "!": "1", '"': "2", "#": "3", "$": "4", "%": "5", "&": "6", "'": "7",
    "(": "8", ")": "9", "<": ",", ">": ".", "?": "/", "+": ";", "=": "-",
    "`": "@", "*": ":", "|": "\\", "{": "[", "}": "]",
}

registered_commands = {
    "ls ", "cd ", "pwd ", "cp ", "mv ", "rm ", "mkdir ", "touch ", "find ",
    "stat ", "tree ", "top ", "htop ", "free ", "df ", "du ", "uptime ", "whoami ",
    "uname ", "hostname ", "id ", "ping ", "curl ", "wget ", "nslookup ", "dig ",
    "traceroute ", "ip ", "ifconfig ", "netstat ", "ss ", "chmod ", "chown ",
    "sudo ", "ps ", "kill ", "killall ", "cat ", "less ", "tail ", "head ", "grep ",
    "awk ", "sed ", "cut ", "sort ", "uniq ", "git ", "python ", "node ", "npm ",
    "yarn ", "make ", "gcc ", "g++ ", "java ", "javac ", "apt ", "yum ", "dnf ",
    "pacman ", "brew ", "pip ", "pip3 ", "cargo ", "ssh ", "scp ", "rsync ",
    "sftp ", "alias ", "history ", "clear ", "echo ", "date ", "time ", "man ",
    "which "
}

root = tk.Tk()
root.title("Key Visualizer")
canvas_width, canvas_height = 800, 100
canvas = tk.Canvas(root, width=canvas_width, height=canvas_height, bg='white')
canvas.pack()
root.geometry(f"{canvas_width}x{canvas_height}")

font_mod = tkFont.Font(family="Helvetica", size=12)
font_key = tkFont.Font(family="Helvetica", size=22, weight="bold")
font_cmd = tkFont.Font(family="Helvetica", size=11, slant="italic")

modifier_keys = set()
key_history = deque(maxlen=100)
command_buffer = []
last_command_display = ""


def compress_key_history(history):
    result = []
    for (k, s), group in groupby(history):
        count = len(list(group))
        key_label = f"{k} ×{count}" if count > 1 else k
        shift_label = s if count == 1 else (f"{s} ×{count}" if s else "")
        result.append((key_label, shift_label))
    return result


def copy_command_to_clipboard(event=None):
    if last_command_display:
        root.clipboard_clear()
        root.clipboard_append(last_command_display)


def update_canvas():
    canvas.delete("all")
    visible = compress_key_history(key_history)[-30:]

    widths = [
        max(font_key.measure(k), font_mod.measure(s or "")) + 12
        for k, s in visible
    ]
    total_width = sum(widths)
    x = canvas_width - total_width - 10

    for i, (key_text, shift_text) in enumerate(visible):
        w = widths[i]
        canvas.create_text(x + w/2, 18, text=shift_text,
                           font=font_mod, fill='#666666')
        canvas.create_text(x + w/2, 40, text=key_text,
                           font=font_key, fill='#000000')
        x += w

    canvas.create_line(0, 60, canvas_width, 60, fill="#CCCCCC", width=1)

    if last_command_display:
        canvas.create_text(
            20, 80,
            text=f"直前のコマンド: {last_command_display}",
            font=font_cmd,
            anchor="w",
            fill="#444444",
            tags="command_text"  # タグ追加
        )
        canvas.tag_bind("command_text", "<Button-1>",
                        copy_command_to_clipboard)


def extract_command():
    global last_command_display
    joined = ''.join(command_buffer)
    last_found = -1
    matched_cmd = ""
    for cmd in registered_commands:
        idx = joined.rfind(cmd)
        if idx != -1 and idx >= last_found:
            last_found = idx
            matched_cmd = cmd
    last_command_display = joined[last_found:] if last_found != -1 else ""


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
                elif name == "space":
                    command_buffer.append(" ")
            elif name.startswith(('shift', 'ctrl', 'alt', 'cmd')):
                modifier_keys.add(name.split('_')[0])
    except Exception:
        pass
    update_canvas()


def on_release(key):
    try:
        if hasattr(key, 'name'):
            modifier_keys.discard(key.name.split('_')[0])
    except Exception:
        pass
    update_canvas()


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


keyboard.Listener(on_press=on_press, on_release=on_release).start()
mouse.Listener(on_click=on_click).start()
root.mainloop()
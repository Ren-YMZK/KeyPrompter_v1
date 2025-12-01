# 常に全面に来るバージョン

import tkinter as tk
from tkinter import font as tkFont
from pynput import keyboard, mouse
from collections import deque
from itertools import groupby
from queue import Queue, Empty
import logging

# ------------------------------------------------------------
# 設定／辞書（外見は変更しない）
# ------------------------------------------------------------
logging.basicConfig(level=logging.WARNING)

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

# 外観据え置き
root = tk.Tk()
root.title("Key Visualizer")
root.wm_attributes("-topmost", True)
canvas_width, canvas_height = 800, 100
canvas = tk.Canvas(root, width=canvas_width, height=canvas_height, bg='white')
canvas.pack()
root.geometry(f"{canvas_width}x{canvas_height}")

font_mod = tkFont.Font(family="Helvetica", size=12)
font_key = tkFont.Font(family="Helvetica", size=22, weight="bold")
font_cmd = tkFont.Font(family="Helvetica", size=11, slant="italic")

# ------------------------------------------------------------
# 内部状態（機能改善、外観は不変）
# ------------------------------------------------------------
modifier_keys = set()               # 現在押下中の修飾キー（'ctrl','shift','alt','cmd'）
key_history = deque(maxlen=100)     # 表示用履歴
command_buffer = []                 # Enterまでのバッファ
last_command_display = ""           # 直前のコマンド（表示＆コピー用）
MAX_BUF = 4096                      # コマンドバッファ最大長（機能的改善）

# スレッド安全化：イベントキュー
event_q = Queue()

# 修飾キー表示順（機能改善：順序安定化）
MOD_ORDER = ['ctrl', 'shift', 'alt', 'cmd']

# pynput リスナ（stopのため参照を保持）
kb_listener = None
ms_listener = None

# ------------------------------------------------------------
# 共通ユーティリティ
# ------------------------------------------------------------
def compress_key_history(history):
    """連続同一項目を K ×N / 修飾 ×N で圧縮（外観そのまま）"""
    result = []
    for (k, s), group in groupby(history):
        count = len(list(group))
        key_label = f"{k} ×{count}" if count > 1 else k
        shift_label = s if count == 1 else (f"{s} ×{count}" if s else "")
        result.append((key_label, shift_label))
    return result

def _format_modifiers(label_for_join=None):
    """
    機能改善：修飾は固定順で併記（Ctrl+Shift+...）
    label_for_join があれば「Ctrl+Shift+<label>」のように末尾へ付与。
    """
    mods = [m.title() for m in MOD_ORDER if m in modifier_keys]
    if not mods:
        return ""
    return "+".join(mods) + (f"+{label_for_join}" if label_for_join else "")

def _enforce_buffer_limit():
    """機能改善：バッファ上限で暴走防止"""
    if len(command_buffer) > MAX_BUF:
        del command_buffer[:len(command_buffer) - MAX_BUF]

def copy_command_to_clipboard(event=None):
    """コピー時は末尾空白を整形（外観は変えず、機能のみ改善）"""
    if last_command_display:
        s = last_command_display.rstrip()
        root.clipboard_clear()
        root.clipboard_append(s)

# ------------------------------------------------------------
# 描画（外観・配置は変更なし）
# ------------------------------------------------------------
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
            tags="command_text"
        )
        canvas.tag_bind("command_text", "<Button-1>", copy_command_to_clipboard)

# ------------------------------------------------------------
# コマンド抽出（仕様据え置き、機能改善：末尾整形＋空上書き防止）
# ------------------------------------------------------------
def extract_command():
    global last_command_display
    joined = ''.join(command_buffer)
    last_found = -1
    # setは順序なしだが、ここでは「最後に出現した開始位置」を見るため順序依存なし
    for cmd in registered_commands:
        idx = joined.rfind(cmd)
        if idx != -1 and idx >= last_found:
            last_found = idx
    if last_found != -1:
        candidate = joined[last_found:].rstrip()  # 機能改善：末尾整形
        if candidate:  # 空文字なら上書きしない（ダブルEnter対策）
            last_command_display = candidate

# ------------------------------------------------------------
# イベント処理（pynput→Queue→メインスレッドで処理）
# ------------------------------------------------------------
def _handle_key_press(pkey):
    """
    もとのロジックを踏襲しつつ、修飾表記を併記・固定順に改善。
    """
    try:
        key_name = ''
        shift_text = ''
        # 文字キー
        if hasattr(pkey, 'char') and pkey.char:
            key_name = pkey.char
        # vkのフォールバック（必要最小限、外観変更なし）
        elif hasattr(pkey, 'vk'):
            key_name = {
                191: '/',  # Slash
                220: '\\',  # Backslash
                219: '[',  # [
                221: ']',  # ]
            }.get(pkey.vk, '')

        if key_name:
            # Ctrl単独 + 制御文字の表示（仕様準拠）
            if 'ctrl' in modifier_keys and len(modifier_keys) == 1 and len(key_name) == 1 and ord(key_name) < 32:
                display_char = chr(ord(key_name) + 64)
                key_name = display_char
                shift_text = _format_modifiers(repr(display_char)[1:-1])
            else:
                # Shiftの扱い（大文字化や元キー表示）
                if 'shift' in modifier_keys:
                    if key_name in shift_symbols:
                        # 例：'!'入力 → 上段 "Shift+1" を表示
                        shift_text = _format_modifiers(shift_symbols[key_name])
                    elif key_name.isalpha():
                        key_name = key_name.upper()
                        shift_text = _format_modifiers(key_name)
                    else:
                        shift_text = _format_modifiers(None)  # 単なるShift併記
                # Ctrlが含まれていれば追記（上書きではなく併記）
                if 'ctrl' in modifier_keys and not shift_text.startswith("Ctrl"):
                    label = repr(key_name)[1:-1] if key_name else ''
                    # 既にShiftが付いている場合も _format_modifiers でCtrl+Shift+...の順に揃える
                    shift_text = _format_modifiers(label)

            key_history.append((key_name, shift_text))
            command_buffer.append(key_name)
            _enforce_buffer_limit()

        # 特殊キー
        elif hasattr(pkey, 'name'):
            name = pkey.name
            if name in special_keys:
                label = special_keys[name]
                # 修飾の固定順併記
                shift_text = _format_modifiers(label) if modifier_keys else ""
                key_history.append((label, shift_text))

                # コマンドバッファ操作
                if name == "enter":
                    extract_command()
                    command_buffer.clear()
                elif name == "backspace":
                    if command_buffer:
                        if 'ctrl' in modifier_keys:
                            # 機能改善：Ctrl+Backspace -> 単語削除
                            # 末尾スペースを削り、その後スペースが出るまで削る
                            while command_buffer and command_buffer[-1] == ' ':
                                command_buffer.pop()
                            while command_buffer and command_buffer[-1] != ' ':
                                command_buffer.pop()
                        else:
                            command_buffer.pop()
                elif name == "space":
                    command_buffer.append(" ")
                    _enforce_buffer_limit()
            elif name.startswith(('shift', 'ctrl', 'alt', 'cmd')):
                modifier_keys.add(name.split('_')[0])
    except Exception as e:
        logging.warning("on_press handling error: %s", e)

def _handle_key_release(pkey):
    try:
        if hasattr(pkey, 'name'):
            modifier_keys.discard(pkey.name.split('_')[0])
    except Exception as e:
        logging.warning("on_release handling error: %s", e)

def _handle_mouse_click(x, y, button, pressed):
    if not pressed:
        return
    try:
        label = {
            button.left: "Left Click",
            button.right: "Right Click",
            button.middle: "Middle Click"
        }.get(button, str(button))
        key_history.append((label, ""))
    except Exception as e:
        logging.warning("on_click handling error: %s", e)

# ------------------------------------------------------------
# キュー・ポンプ（メインスレッドで60fps処理）
# ------------------------------------------------------------
def pump():
    try:
        while True:
            kind, payload = event_q.get_nowait()
            if kind == "press":
                _handle_key_press(payload)
            elif kind == "release":
                _handle_key_release(payload)
            elif kind == "click":
                _handle_mouse_click(*payload)
    except Empty:
        pass
    update_canvas()
    root.after(16, pump)  # 約60FPS

# ------------------------------------------------------------
# pynput リスナ（イベントはキューへ）
# ------------------------------------------------------------
def on_press(pkey):
    try:
        event_q.put(("press", pkey))
    except Exception as e:
        logging.warning("queue press error: %s", e)

def on_release(pkey):
    try:
        event_q.put(("release", pkey))
    except Exception as e:
        logging.warning("queue release error: %s", e)

def on_click(x, y, button, pressed):
    try:
        event_q.put(("click", (x, y, button, pressed)))
    except Exception as e:
        logging.warning("queue click error: %s", e)

# ------------------------------------------------------------
# 安全終了
# ------------------------------------------------------------
def on_close():
    try:
        if kb_listener is not None:
            kb_listener.stop()
        if ms_listener is not None:
            ms_listener.stop()
    finally:
        # 少し待ってから閉じる（安全側）
        root.after(50, root.destroy)

# ------------------------------------------------------------
# 起動
# ------------------------------------------------------------
def main():
    global kb_listener, ms_listener
    root.protocol("WM_DELETE_WINDOW", on_close)

    kb_listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    ms_listener = mouse.Listener(on_click=on_click)
    kb_listener.start()
    ms_listener.start()

    root.after(0, pump)
    root.mainloop()

if __name__ == "__main__":
    main()
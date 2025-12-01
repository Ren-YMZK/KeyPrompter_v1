import tkinter as tk
from tkinter import font

root = tk.Tk()
root.geometry("400x300")

canvas = tk.Canvas(root, bg="white")
canvas.pack(fill="both", expand=True)

# フォントの設定
my_font = font.Font(family="Helvetica", size=20)

# 表示するテキスト
text1 = "Hello"
text2 = "World!"


def draw_text(event=None):
    canvas.delete("all")

    # キャンバスサイズ
    width = canvas.winfo_width()
    height = canvas.winfo_height()

    # テキストの幅を取得
    text1_width = my_font.measure(text1)
    text2_width = my_font.measure(text2)

    # 水平方向センターに揃えるため、中央から半分引く
    x1 = (width - text1_width) // 2
    x2 = (width - text2_width) // 2

    # 縦位置
    y1 = height // 2 - 20
    y2 = height // 2 + 20

    # 描画（左上起点なので anchor は "nw"）
    canvas.create_text(x1, y1, text=text1, font=my_font,
                       fill="black", anchor="nw")
    canvas.create_text(x2, y2, text=text2, font=my_font,
                       fill="black", anchor="nw")

    # デバッグ用に幅を表示（オプション）
    canvas.create_text(10, 10, text=f"'{text1}' width: {text1_width}",
                       anchor="nw", fill="gray", font=("Arial", 10))
    canvas.create_text(10, 30, text=f"'{text2}' width: {text2_width}",
                       anchor="nw", fill="gray", font=("Arial", 10))


# 初回表示・リサイズ時に描画
canvas.bind("<Configure>", draw_text)

root.mainloop()
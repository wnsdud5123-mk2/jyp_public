import tkinter as tk
from tkinter import messagebox

def show_info(parent: tk.Misc, title: str, msg: str):
    return messagebox.showinfo(title, msg, parent=parent)

def show_warn(parent: tk.Misc, title: str, msg: str):
    return messagebox.showwarning(title, msg, parent=parent)

def show_error(parent: tk.Misc, title: str, msg: str):
    return messagebox.showerror(title, msg, parent=parent)

def ask_yesno(parent: tk.Misc, title: str, msg: str) -> bool:
    return messagebox.askyesno(title, msg, parent=parent)

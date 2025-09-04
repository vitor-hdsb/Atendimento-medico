import tkinter as tk
from tkinter import ttk

def setup_placeholder(widget, placeholder_text):
    """
    Configura um placeholder para um widget de entrada ou combobox.
    """
    style = ttk.Style()
    style.configure("Placeholder.TEntry", foreground="gray")
    style.configure("Placeholder.TCombobox", foreground="gray")

    is_combobox = isinstance(widget, ttk.Combobox)

    def apply_placeholder():
        """Aplica o placeholder se o widget estiver vazio."""
        if not widget.get():
            if is_combobox:
                widget.set(placeholder_text)
            else:
                widget.insert(0, placeholder_text)
            widget.configure(style=f"Placeholder.{widget.winfo_class()}")

    def on_focus_in(event):
        """Remove o placeholder e restaura o estilo original."""
        if widget.get() == placeholder_text:
            if is_combobox:
                widget.set("")
            else:
                widget.delete(0, 'end')
            widget.configure(style=f"{widget.winfo_class().replace('Placeholder.', '')}")

    def on_focus_out(event):
        """Reaplica o placeholder se o campo ficar vazio."""
        apply_placeholder()

    widget.bind('<FocusIn>', on_focus_in, add='+')
    widget.bind('<FocusOut>', on_focus_out, add='+')
    
    if is_combobox:
        def on_combobox_selected(event):
            widget.configure(style="TCombobox")
        widget.bind('<<ComboboxSelected>>', on_combobox_selected, add='+')
    else: # é um Entry
        def on_key_release(event):
            if widget.get() and widget.get() != placeholder_text:
                 widget.configure(style="TEntry")
        widget.bind('<KeyRelease>', on_key_release, add='+')

    apply_placeholder()

def remove_placeholder_on_fill(widget, placeholder_text):
    """
    Garante que o estilo de placeholder seja removido se o widget
    contiver um valor que não seja o placeholder.
    """
    if widget.get() and widget.get() != placeholder_text:
         widget.configure(style=f"{widget.winfo_class().replace('Placeholder.', '')}")

def clear_placeholder(widget, placeholder_text):
    """Limpa o widget, removendo o texto ou o placeholder e o estilo."""
    if widget.get() == placeholder_text or widget.get():
        style_name = widget.winfo_class().replace('Placeholder.', '')
        widget.configure(style=style_name)
        if isinstance(widget, ttk.Combobox):
            widget.set("")
        else:
            widget.delete(0, 'end')


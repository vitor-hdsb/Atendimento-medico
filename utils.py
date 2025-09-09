import tkinter as tk
from tkinter import ttk

def setup_placeholder(widget, placeholder_text):
    """
    Configura um placeholder para um widget de entrada ou combobox.
    """
    if not placeholder_text: return

    style = ttk.Style()
    style.configure("Placeholder.TEntry", foreground="gray")
    style.configure("Placeholder.TCombobox", foreground="gray")

    is_combobox = isinstance(widget, ttk.Combobox)

    def apply_placeholder():
        if not widget.get():
            widget.configure(style=f"Placeholder.{widget.winfo_class()}")
            if is_combobox:
                widget.set(placeholder_text)
            else:
                widget.insert(0, placeholder_text)

    def on_focus_in(event):
        if widget.get() == placeholder_text:
            widget.configure(style=f"{widget.winfo_class().replace('Placeholder.', '')}")
            if is_combobox:
                widget.set("")
            else:
                widget.delete(0, 'end')

    def on_focus_out(event):
        apply_placeholder()
    
    def on_widget_change(event):
        if widget.get() and widget.get() != placeholder_text:
            widget.configure(style=f"{widget.winfo_class().replace('Placeholder.', '')}")

    widget.bind('<FocusIn>', on_focus_in, add='+')
    widget.bind('<FocusOut>', on_focus_out, add='+')
    
    if is_combobox:
        widget.bind('<<ComboboxSelected>>', on_widget_change, add='+')
    else:
        widget.bind('<KeyRelease>', on_widget_change, add='+')

    # Força a aplicação inicial
    widget.after_idle(apply_placeholder)

def remove_placeholder_on_fill(widget, placeholder_text):
    """Garante que o estilo de placeholder seja removido se houver valor."""
    if widget.get() and widget.get() != placeholder_text:
         widget.configure(style=f"{widget.winfo_class().replace('Placeholder.', '')}")

def clear_placeholder(widget, placeholder_text):
    """Limpa o widget, removendo o texto ou o placeholder e o estilo."""
    if widget.get() == placeholder_text or widget.get():
        widget.configure(style=f"{widget.winfo_class().replace('Placeholder.', '')}")
        if isinstance(widget, ttk.Combobox):
            widget.set("")
        else:
            widget.delete(0, 'end')

def validate_integer_input(value_if_allowed):
    """Permite apenas dígitos."""
    return value_if_allowed.isdigit() or value_if_allowed == ""

def validate_posologia_input(value_if_allowed):
    """Permite dígitos e caracteres especiais comuns em posologia."""
    return all(c in '0123456789/,. ' for c in value_if_allowed) or value_if_allowed == ""


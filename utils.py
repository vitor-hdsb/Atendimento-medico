import tkinter as tk
from tkinter import ttk

def setup_placeholder(widget, placeholder_text):
    """
    Configura um placeholder para um widget de entrada.
    A cor e o texto do placeholder aparecem quando o campo está vazio.
    """
    style = ttk.Style()
    style.configure("Placeholder.TEntry", foreground="gray")
    style.configure("Placeholder.TCombobox", foreground="gray")

    def apply_placeholder():
        """Aplica o placeholder se o widget estiver vazio."""
        current_value = widget.get()
        if not current_value:
            widget.insert(0, placeholder_text)
            widget.configure(style=f"Placeholder.{widget.winfo_class()}")

    def on_focus_in(event):
        """Remove o placeholder e restaura o estilo original."""
        if widget.get() == placeholder_text:
            widget.delete(0, 'end')
            widget.configure(style=f"{widget.winfo_class().replace('Placeholder.', '')}")

    def on_focus_out(event):
        """Reaplica o placeholder se o campo ficar vazio."""
        apply_placeholder()

    widget.bind('<FocusIn>', on_focus_in, add='+')
    widget.bind('<FocusOut>', on_focus_out, add='+')
    
    if widget.winfo_class() == 'TCombobox':
        def on_combobox_selected(event):
            widget.configure(style="TCombobox")
        widget.bind('<<ComboboxSelected>>', on_combobox_selected, add='+')
    
    # Aplica o placeholder inicialmente
    apply_placeholder()

def remove_placeholder_on_fill(widget, placeholder_text):
    """
    Se o widget foi preenchido com dados (não placeholder),
    garante que o estilo de placeholder seja removido.
    """
    if widget.get() and widget.get() != placeholder_text:
         widget.configure(style=f"{widget.winfo_class().replace('Placeholder.', '')}")

def clear_placeholder(widget, placeholder_text):
    """Limpa o widget, removendo o texto ou o placeholder."""
    if widget.get() == placeholder_text:
        widget.configure(style=f"{widget.winfo_class().replace('Placeholder.', '')}")
        widget.delete(0, 'end')
    elif widget.get():
        widget.delete(0, 'end')


"""
utils.py
--------
Funções utilitárias para a interface gráfica e validação.
"""
from tkinter import ttk

def setup_placeholder(widget, placeholder_text):
    """
    Configura um placeholder para um widget de entrada.
    A cor e o texto do placeholder aparecem quando o campo está vazio.
    """
    # Cria e configura um estilo para os placeholders
    style = ttk.Style()
    style.configure("Placeholder.TEntry", foreground="gray")
    style.configure("Placeholder.TCombobox", foreground="gray")

    # Guarda o estilo original do widget para restaurá-lo depois
    original_style = widget.cget("style") if widget.cget("style") else f"{widget.winfo_class()}"
    
    # Adiciona o placeholder inicial e aplica o estilo de placeholder
    widget.insert(0, placeholder_text)
    widget.configure(style=f"Placeholder.{widget.winfo_class()}")

    def on_focus_in(event):
        # Remove o placeholder e restaura o estilo original
        if widget.get() == placeholder_text and widget.cget("style").startswith("Placeholder"):
            widget.delete(0, 'end')
            widget.configure(style=original_style)

    def on_focus_out(event):
        # Se o campo estiver vazio, insere o placeholder e aplica o estilo novamente
        if not widget.get():
            widget.insert(0, placeholder_text)
            widget.configure(style=f"Placeholder.{widget.winfo_class()}")

    widget.bind('<FocusIn>', on_focus_in)
    widget.bind('<FocusOut>', on_focus_out)

    # Permite que o placeholder seja aplicado a Combobox
    if widget.winfo_class() == 'TCombobox':
        def on_combobox_selected(event):
            # Restaura o estilo original quando uma opção é selecionada
            if widget.get() != placeholder_text:
                widget.configure(style=original_style)
        widget.bind('<<ComboboxSelected>>', on_combobox_selected)

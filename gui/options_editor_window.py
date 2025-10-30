import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import gui.constants as constants # Para carregar/salvar opções
import os

class OptionsEditorWindow(tk.Toplevel):
    def __init__(self, parent, update_callback=None):
        super().__init__(parent)
        self.transient(parent) # Mantém a janela na frente da principal
        self.parent = parent
        self.update_callback = update_callback # Função a ser chamada após salvar
        self.title("Editar Opções das Listas")
        self.geometry("600x450")
        self.resizable(False, False)

        # Categorias editáveis (chave interna: texto exibido)
        self.editable_categories = {
            "gestores": "Gestores",
            "setores": "Setores",
            "processos": "Processos",
            "turnos": "Turnos"
        }
        self.current_options = constants.load_options() # Carrega opções atuais

        # --- Layout ---
        main_frame = ttk.Frame(self, padding="15")
        main_frame.pack(fill="both", expand=True)

        # --- Seleção de Categoria ---
        category_frame = ttk.Frame(main_frame)
        category_frame.pack(fill="x", pady=(0, 10))
        ttk.Label(category_frame, text="Selecione a lista para editar:").pack(side="left", padx=(0, 10))
        self.category_var = tk.StringVar()
        self.category_combo = ttk.Combobox(category_frame, textvariable=self.category_var,
                                           values=list(self.editable_categories.values()), state="readonly", width=25)
        self.category_combo.pack(side="left")
        self.category_combo.bind("<<ComboboxSelected>>", self.load_category_options)
        # Seleciona a primeira categoria por padrão
        if self.editable_categories:
             self.category_combo.current(0)


        # --- Listbox e Scrollbar ---
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill="both", expand=True, pady=(0, 10))
        list_frame.rowconfigure(0, weight=1)
        list_frame.columnconfigure(0, weight=1)

        self.listbox = tk.Listbox(list_frame, selectmode=tk.SINGLE, exportselection=False)
        self.listbox.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.listbox.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.listbox.configure(yscrollcommand=scrollbar.set)

        # --- Controles (Adicionar/Remover) ---
        controls_frame = ttk.Frame(main_frame)
        controls_frame.pack(fill="x")
        controls_frame.columnconfigure(1, weight=1) # Entry expande

        ttk.Label(controls_frame, text="Novo Item:").grid(row=0, column=0, padx=(0, 5), pady=5)
        self.new_item_entry = ttk.Entry(controls_frame)
        self.new_item_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.new_item_entry.bind("<Return>", self.add_item) # Permite adicionar com Enter

        add_button = ttk.Button(controls_frame, text="Adicionar", command=self.add_item, width=10)
        add_button.grid(row=0, column=2, padx=(5, 0), pady=5)

        remove_button = ttk.Button(controls_frame, text="Remover Selecionado", command=self.remove_item, width=20)
        remove_button.grid(row=1, column=0, columnspan=3, pady=5) # Centralizado abaixo

        # --- Botões Salvar/Fechar ---
        action_button_frame = ttk.Frame(main_frame)
        action_button_frame.pack(fill="x", pady=(10, 0))
        # Centraliza botões usando um frame intermediário com pesos
        center_frame = ttk.Frame(action_button_frame)
        center_frame.pack()

        save_button = ttk.Button(center_frame, text="Salvar Alterações", command=self.save_changes, width=15)
        save_button.pack(side="left", padx=10)

        close_button = ttk.Button(center_frame, text="Fechar", command=self.destroy, width=15)
        close_button.pack(side="left", padx=10)

        # Carrega as opções da primeira categoria
        self.load_category_options()

        self.grab_set() # Torna a janela modal
        self.wait_window() # Espera até que a janela seja fechada

    def get_selected_category_key(self):
        """Retorna a chave interna (ex: 'gestores') da categoria selecionada."""
        selected_value = self.category_var.get()
        for key, value in self.editable_categories.items():
            if value == selected_value:
                return key
        return None

    def load_category_options(self, event=None):
        """Carrega as opções da categoria selecionada na Listbox."""
        self.listbox.delete(0, tk.END) # Limpa a lista
        category_key = self.get_selected_category_key()
        if category_key and category_key in self.current_options:
            # Ordena antes de exibir (exceto turnos)
            options_list = sorted(self.current_options[category_key]) if category_key != "turnos" else self.current_options[category_key]
            for item in options_list:
                self.listbox.insert(tk.END, item)

    def add_item(self, event=None):
        """Adiciona o item da Entry à Listbox e à lista interna."""
        new_item = self.new_item_entry.get().strip()
        category_key = self.get_selected_category_key()

        if not new_item or not category_key:
            return

        # Verifica se já existe (ignorando maiúsculas/minúsculas)
        current_items_lower = [item.lower() for item in self.listbox.get(0, tk.END)]
        if new_item.lower() in current_items_lower:
            messagebox.showwarning("Item Duplicado", f"O item '{new_item}' já existe nesta lista.", parent=self)
            self.new_item_entry.delete(0, tk.END)
            return

        # Adiciona na lista interna
        if category_key in self.current_options:
            self.current_options[category_key].append(new_item)
            # Recarrega a listbox (para manter ordenado, se aplicável)
            self.load_category_options()
            # Seleciona o item recém-adicionado
            try:
                # Ordena a lista atual para encontrar o índice correto
                options_list = sorted(self.current_options[category_key]) if category_key != "turnos" else self.current_options[category_key]
                new_index = options_list.index(new_item)
                self.listbox.selection_clear(0, tk.END)
                self.listbox.selection_set(new_index)
                self.listbox.activate(new_index)
                self.listbox.see(new_index) # Garante que está visível
            except ValueError:
                pass # Item não encontrado após adicionar (improvável)

            self.new_item_entry.delete(0, tk.END) # Limpa entry
            self.new_item_entry.focus() # Foca na entry novamente
        else:
             messagebox.showerror("Erro", f"Categoria '{category_key}' não encontrada nas opções.", parent=self)


    def remove_item(self):
        """Remove o item selecionado da Listbox e da lista interna."""
        selected_indices = self.listbox.curselection()
        category_key = self.get_selected_category_key()

        if not selected_indices or not category_key:
            messagebox.showwarning("Nenhuma Seleção", "Selecione um item para remover.", parent=self)
            return

        selected_index = selected_indices[0]
        selected_item = self.listbox.get(selected_index)

        if messagebox.askyesno("Confirmar Remoção", f"Tem certeza que deseja remover '{selected_item}'?", parent=self):
            if category_key in self.current_options:
                try:
                    # Remove da lista interna (case-sensitive)
                    self.current_options[category_key].remove(selected_item)
                    # Remove da listbox
                    self.listbox.delete(selected_index)
                except ValueError:
                    messagebox.showerror("Erro", f"Não foi possível encontrar '{selected_item}' na lista interna para remover.", parent=self)
            else:
                messagebox.showerror("Erro", f"Categoria '{category_key}' não encontrada.", parent=self)


    def save_changes(self):
        """Salva todas as alterações no arquivo JSON."""
        if constants.save_options(self.current_options):
            messagebox.showinfo("Sucesso", "Opções salvas com sucesso!", parent=self)
            # Chama o callback na MainWindow para atualizar as comboboxes lá
            if self.update_callback:
                self.update_callback()
            self.destroy() # Fecha a janela de edição
        else:
            messagebox.showerror("Erro ao Salvar", f"Não foi possível salvar as alterações no arquivo '{constants.OPTIONS_FILE}'. Verifique as permissões.", parent=self)

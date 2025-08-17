"""
gui/main_window.py
------------------
Janela principal da aplicação de atendimentos.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
import db
import utils
from models import Atendimento, Conduta
from gui.edit_window import EditWindow, OPTIONS
from gui.export_window import ExportWindow

class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Registro de Atendimentos Médicos")
        self.geometry("1200x800")
        self.atendimento_id_to_edit = None
        self.placeholders = {} # Dicionário para armazenar os placeholders
        
        # Configurações do layout
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        
        # Dicionários para fácil acesso aos widgets
        self.entries = {}
        self.comboboxes = {}
        self.tenure_label = None
        
        self.create_widgets()
        self.clear_form()
        self.refresh_history_tree()
    
    def create_widgets(self):
        """Cria e organiza todos os widgets na janela principal."""
        # Frame da esquerda para o formulário
        form_frame = ttk.Frame(self, padding="10")
        form_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        form_frame.columnconfigure(0, weight=1)
        form_frame.columnconfigure(1, weight=1)
        
        # --- Seção de Identificação do paciente ---
        id_frame = ttk.LabelFrame(form_frame, text="Identificação do paciente", padding="10")
        id_frame.pack(fill="x", pady=5)
        self.create_form_section(id_frame, "id", {
            "Badge Number": {"type": "entry", "placeholder": "Bipe o crachá", "var_name": "badge_number"},
            "Nome": {"type": "entry", "placeholder": "Bipe o crachá", "var_name": "nome"},
            "Login": {"type": "entry", "placeholder": "Bipe o crachá", "var_name": "login"},
            "Gestor": {"type": "combobox", "placeholder": "Selecione", "options": OPTIONS["gestores"], "var_name": "gestor", "width": 40},
            "Turno": {"type": "combobox", "placeholder": "Bipe o crachá ou selecione", "options": OPTIONS["turnos"], "var_name": "turno"},
            "Setor": {"type": "combobox", "placeholder": "Bipe o crachá ou selecione", "options": OPTIONS["setores"], "var_name": "setor"},
            "Processo": {"type": "combobox", "placeholder": "Selecione", "options": OPTIONS["processos"], "var_name": "processo"},
            "Tenure": {"type": "entry", "placeholder": "Digite a data de admissão", "var_name": "tenure"},
        })
        # Adiciona o label de dias ao lado do Tenure
        self.tenure_label = ttk.Label(id_frame, text="")
        self.tenure_label.grid(row=3, column=3, padx=5, pady=2, sticky="w")
        
        # Vincula o evento de digitação para o preenchimento automático
        self.entries['badge_number'].bind("<KeyRelease>", self.on_badge_number_change)
        # Vincula o evento para o cálculo do Tenure
        self.entries['tenure'].bind("<KeyRelease>", self.calculate_tenure)
        
        # --- Seção de Anamnese ---
        anamnese_frame = ttk.LabelFrame(form_frame, text="Anamnese", padding="10")
        anamnese_frame.pack(fill="x", pady=5)
        self.create_form_section(anamnese_frame, "anamnese", {
            "Queixa principal": {"type": "entry", "placeholder": "Ex: Dor de cabeça...", "var_name": "queixa_principal"},
            "HQA (Histórico da queixa atual)": {"type": "entry", "placeholder": "Detalhe a queixa...", "var_name": "hqa"},
            "TAX": {"type": "entry", "placeholder": "Ex: 38º", "var_name": "tax"},
            "PA": {"type": "entry", "placeholder": "Ex: 120/80 mmHg", "var_name": "pa"},
            "FC": {"type": "entry", "placeholder": "Ex: 90 BPM", "var_name": "fc"},
            "SAT": {"type": "entry", "placeholder": "90%", "var_name": "sat"},
            "Doenças pré-existentes": {"type": "entry", "placeholder": "Ex: Diabetes, Hipertensão...", "var_name": "doencas_preexistentes"},
            "Alergias": {"type": "entry", "placeholder": "Ex: Alergias respiratórias...", "var_name": "alergias"},
            "Medicamentos em uso": {"type": "entry", "placeholder": "Ex: Losartana...", "var_name": "medicamentos_em_uso"},
            "Observações": {"type": "entry", "placeholder": "(campo livre)", "var_name": "observacoes"},
        })
        
        # --- Seção de Conduta de Enfermagem ---
        conduta_frame = ttk.LabelFrame(form_frame, text="Conduta de Enfermagem", padding="10")
        conduta_frame.pack(fill="x", pady=5)
        self.create_form_section(conduta_frame, "conduta", {
            "Ocupacional": {"type": "combobox", "placeholder": "Selecione", "options": OPTIONS["ocupacional"], "var_name": "ocupacional"},
            "Hipótese diagnóstica": {"type": "entry", "placeholder": "Ex: Enxaqueca...", "var_name": "hipotese_diagnostica"},
            "Conduta adotada": {"type": "entry", "placeholder": "Descreva a conduta...", "var_name": "conduta_adotada"},
            "Resumo da 1ª conduta": {"type": "combobox", "placeholder": "Selecione", "options": OPTIONS["resumo_conduta"], "var_name": "resumo_conduta"},
            "Medicamento administrado": {"type": "combobox", "placeholder": "Selecione", "options": OPTIONS["medicamento_admin"], "var_name": "medicamento_administrado"},
            "Medicamento": {"type": "entry", "placeholder": "Ex: Paracetamol 1G", "var_name": "medicamento"},
            "Posologia": {"type": "entry", "placeholder": "Ex: 1 comp, 15 gotas", "var_name": "posologia"},
            "Horário da medicação": {"type": "entry", "placeholder": "Insira o horário da medicação", "var_name": "horario_medicao"},
            "Observações": {"type": "entry", "placeholder": "(campo livre)", "var_name": "conduta_obs"},
        })
        
        # Botão Salvar Atendimento
        save_button = ttk.Button(form_frame, text="Salvar Atendimento", command=self.save_atendimento)
        save_button.pack(pady=10)
        
        # --- Seção de Histórico e Exportação ---
        history_frame = ttk.Frame(self)
        history_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        history_frame.columnconfigure(0, weight=1)
        history_frame.rowconfigure(2, weight=1)
        
        ttk.Label(history_frame, text="Histórico de Atendimentos", font=("Arial", 14, "bold")).pack(pady=(0, 10))
        
        # Combobox para filtrar período do histórico
        period_frame = ttk.Frame(history_frame)
        period_frame.pack(fill="x")
        ttk.Label(period_frame, text="Filtrar por:").pack(side="left", padx=5)
        self.history_period_var = tk.StringVar(value="15 dias")
        self.history_period_combo = ttk.Combobox(period_frame, textvariable=self.history_period_var, values=["15 dias", "30 dias", "60 dias", "YTD"], state="readonly")
        self.history_period_combo.pack(side="left", padx=5)
        self.history_period_combo.bind("<<ComboboxSelected>>", self.refresh_history_tree)

        # Treeview para o histórico
        tree_frame = ttk.Frame(history_frame)
        tree_frame.pack(fill="both", expand=True, pady=(5, 10))
        
        self.history_tree = ttk.Treeview(tree_frame, columns=("badge", "nome", "login", "data_hora"), show="headings")
        self.history_tree.heading("badge", text="Badge Number")
        self.history_tree.heading("nome", text="Nome")
        self.history_tree.heading("login", text="Login")
        self.history_tree.heading("data_hora", text="Data e Hora")
        self.history_tree.column("badge", width=100)
        self.history_tree.column("nome", width=200)
        self.history_tree.column("login", width=150)
        self.history_tree.column("data_hora", width=150)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=scrollbar.set)
        
        self.history_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.history_tree.bind("<Double-1>", self.on_double_click_history)
        
        # Botão de Exportar
        export_button = ttk.Button(history_frame, text="Exportar Dados", command=self.open_export_window)
        export_button.pack(pady=10)

    def create_form_section(self, parent_frame, section_name, fields):
        """Função utilitária para criar seções de formulário."""
        for i, (label_text, config) in enumerate(fields.items()):
            row, col = divmod(i, 2)
            ttk.Label(parent_frame, text=label_text).grid(row=row, column=col*2, padx=5, pady=2, sticky="e")
            
            if config["type"] == "entry":
                entry = ttk.Entry(parent_frame)
                entry.grid(row=row, column=col*2+1, padx=5, pady=2, sticky="ew")
                self.placeholders[config["var_name"]] = config["placeholder"]
                utils.setup_placeholder(entry, config["placeholder"])
                self.entries[config["var_name"]] = entry
            elif config["type"] == "combobox":
                combo = ttk.Combobox(parent_frame, values=config["options"], width=config.get("width", 20))
                combo.grid(row=row, column=col*2+1, padx=5, pady=2, sticky="ew")
                self.placeholders[config["var_name"]] = config["placeholder"]
                utils.setup_placeholder(combo, config["placeholder"])
                self.comboboxes[config["var_name"]] = combo

    def calculate_tenure(self, event=None):
        """Calcula e exibe o número de dias desde a data de admissão."""
        tenure_str = self.entries['tenure'].get()
        try:
            # Verifica se o placeholder está presente e o remove antes de tentar converter
            if tenure_str == "Digite a data de admissão":
                self.tenure_label.config(text="")
                return
            
            admissao_date = datetime.strptime(tenure_str, "%d/%m/%Y").date()
            hoje = datetime.now().date()
            diferenca = hoje - admissao_date
            self.tenure_label.config(text=f"{diferenca.days} Dias")
        except (ValueError, TypeError):
            self.tenure_label.config(text="Formato de data inválido")

    def on_badge_number_change(self, event):
        """Preenche automaticamente os campos de identificação ao digitar o Badge Number."""
        badge_number_str = self.entries['badge_number'].get()
        if badge_number_str and badge_number_str.isdigit():
            badge_number = int(badge_number_str)
            last_atendimento = db.get_last_atendimento_by_badge(badge_number)
            if last_atendimento:
                self.entries['nome'].delete(0, 'end')
                self.entries['nome'].insert(0, last_atendimento.nome)
                self.entries['login'].delete(0, 'end')
                self.entries['login'].insert(0, last_atendimento.login)
                self.comboboxes['gestor'].set(last_atendimento.gestor)
                self.comboboxes['turno'].set(last_atendimento.turno)
                self.comboboxes['setor'].set(last_atendimento.setor)
                self.comboboxes['processo'].set(last_atendimento.processo)
                self.entries['tenure'].delete(0, 'end')
                self.entries['tenure'].insert(0, last_atendimento.tenure)
        
        self.refresh_history_tree()
    
    def refresh_history_tree(self, event=None):
        """Atualiza a Treeview do histórico de atendimentos."""
        badge_number_str = self.entries['badge_number'].get()
        
        # Limpa a Treeview antes de inserir os novos dados
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
            
        badge_number = None
        if badge_number_str.isdigit():
            badge_number = int(badge_number_str)
        
        period = self.history_period_var.get()
        days_ago = 15 # Valor padrão
        if period == "30 dias":
            days_ago = 30
        elif period == "60 dias":
            days_ago = 60
        elif period == "YTD":
            start_of_year = datetime.now().replace(month=1, day=1)
            days_ago = (datetime.now() - start_of_year).days + 1
        
        atendimentos = db.get_atendimentos_by_badge(badge_number, days_ago)
        
        if not atendimentos:
            self.history_tree.insert("", "end", values=("Sem atendimentos registrados", "", "", ""))
        else:
            for atendimento in atendimentos:
                data_hora = f"{atendimento[4]} {atendimento[5]}"
                self.history_tree.insert("", "end", iid=atendimento[0], values=(atendimento[1], atendimento[2], atendimento[3], data_hora))
    
    def on_double_click_history(self, event):
        """Abre a janela de edição ao dar um duplo-clique em um item da Treeview."""
        selected_item = self.history_tree.selection()
        if selected_item:
            self.atendimento_id_to_edit = int(selected_item[0])
            EditWindow(self, self.atendimento_id_to_edit, self.refresh_history_tree)
            
    def save_atendimento(self):
        """Valida o formulário e salva um novo atendimento."""
        badge_number_str = self.entries['badge_number'].get()
        if not badge_number_str.isdigit():
            messagebox.showerror("Erro de Validação", "Badge Number deve ser um número válido.")
            return

        try:
            conduta = Conduta(
                hipotese_diagnostica=self.entries['hipotese_diagnostica'].get(),
                conduta_adotada=self.entries['conduta_adotada'].get(),
                resumo_conduta=self.comboboxes['resumo_conduta'].get(),
                medicamento_administrado=self.comboboxes['medicamento_administrado'].get(),
                medicamento=self.entries['medicamento'].get(),
                posologia=self.entries['posologia'].get(),
                horario_medicacao=self.entries['horario_medicao'].get(),
                observacoes=self.entries['conduta_obs'].get()
            )

            atendimento = Atendimento(
                badge_number=int(badge_number_str),
                nome=self.entries['nome'].get(),
                login=self.entries['login'].get(),
                gestor=self.comboboxes['gestor'].get(),
                turno=self.comboboxes['turno'].get(),
                setor=self.comboboxes['setor'].get(),
                processo=self.comboboxes['processo'].get(),
                tenure=self.entries['tenure'].get(),
                queixa_principal=self.entries['queixa_principal'].get(),
                hqa=self.entries['hqa'].get(),
                tax=self.entries['tax'].get(),
                pa=self.entries['pa'].get(),
                fc=self.entries['fc'].get(),
                sat=self.entries['sat'].get(),
                doencas_preexistentes=self.entries['doencas_preexistentes'].get(),
                alergias=self.entries['alergias'].get(),
                medicamentos_em_uso=self.entries['medicamentos_em_uso'].get(),
                observacoes=self.entries['observacoes'].get(),
                condutas=[conduta]
            )

            db.save_atendimento(atendimento)
            messagebox.showinfo("Sucesso", "Atendimento salvo com sucesso!")
            self.clear_form()
            self.refresh_history_tree() # Atualiza o histórico para o novo atendimento
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro ao salvar o atendimento: {e}")

    def clear_form(self):
        """Limpa todos os campos do formulário e restaura os placeholders."""
        for name, entry in self.entries.items():
            entry.delete(0, 'end')
            utils.setup_placeholder(entry, self.placeholders.get(name, ""))

        for name, combo in self.comboboxes.items():
            combo.set("")
            utils.setup_placeholder(combo, self.placeholders.get(name, ""))
            
        # Limpa o label do tenure
        self.tenure_label.config(text="")

    def open_export_window(self):
        """Abre a janela de exportação."""
        ExportWindow(self)

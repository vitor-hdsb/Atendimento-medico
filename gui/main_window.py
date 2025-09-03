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
        self.placeholders = {}
        
        # Configurações do layout
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        
        self.entries = {}
        self.comboboxes = {}
        self.tenure_label = None
        self.queixas_vars = {}
        self.queixa_outros_entry = None
        self.entry_pa_sistolica = None
        self.entry_pa_diastolica = None
        
        self.create_widgets()
        self.clear_form()
        self.refresh_history_tree()
    
    def create_widgets(self):
        """Cria e organiza todos os widgets na janela principal."""
        form_frame = ttk.Frame(self, padding="10")
        form_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        form_frame.columnconfigure(0, weight=1)
        form_frame.columnconfigure(1, weight=1)
        
        # Seção de Identificação do paciente
        id_frame = ttk.LabelFrame(form_frame, text="Identificação do paciente", padding="10")
        id_frame.pack(fill="both", expand=True, pady=5)
        id_frame.columnconfigure(0, weight=1)
        id_frame.columnconfigure(1, weight=1)
        id_frame.columnconfigure(2, weight=1)
        id_frame.columnconfigure(3, weight=1)
        
        self.create_form_section(id_frame, {
            "Badge Number": {"type": "entry", "placeholder": "Bipe o crachá", "var_name": "badge_number"},
            "Nome": {"type": "entry", "placeholder": "Bipe o crachá", "var_name": "nome"},
            "Login": {"type": "entry", "placeholder": "Bipe o crachá", "var_name": "login"},
            "Gestor": {"type": "combobox", "placeholder": "Selecione", "options": OPTIONS["gestores"], "var_name": "gestor", "width": 40},
            "Turno": {"type": "combobox", "placeholder": "Bipe o crachá ou selecione", "options": OPTIONS["turnos"], "var_name": "turno"},
            "Setor": {"type": "combobox", "placeholder": "Bipe o crachá ou selecione", "options": OPTIONS["setores"], "var_name": "setor"},
            "Processo": {"type": "combobox", "placeholder": "Selecione", "options": OPTIONS["processos"], "var_name": "processo"},
            "Tenure": {"type": "entry", "placeholder": "Digite a data de admissão", "var_name": "tenure"},
        })
        self.tenure_label = ttk.Label(id_frame, text="")
        self.tenure_label.grid(row=3, column=3, padx=5, pady=2, sticky="w")
        
        self.entries['badge_number'].bind("<KeyRelease>", self.on_badge_number_change)
        self.entries['tenure'].bind("<KeyRelease>", self.calculate_tenure)
        
        # Seção de Anamnese
        anamnese_frame = ttk.LabelFrame(form_frame, text="Anamnese", padding="10")
        anamnese_frame.pack(fill="both", expand=True, pady=5)
        anamnese_frame.columnconfigure(0, weight=1)
        anamnese_frame.columnconfigure(1, weight=1)
        anamnese_frame.columnconfigure(2, weight=1)
        anamnese_frame.columnconfigure(3, weight=1)
        
        self.create_queixa_section(anamnese_frame)
        self.create_entry_field(anamnese_frame, "HQA (Histórico da queixa atual):", "hqa", row=1, col=2)
        self.create_entry_field(anamnese_frame, "TAX:", "tax", row=2, col=0)
        self.create_pa_section(anamnese_frame)
        self.create_entry_field(anamnese_frame, "FC:", "fc", row=3, col=0)
        self.create_entry_field(anamnese_frame, "SAT:", "sat", row=3, col=2)
        self.create_entry_field(anamnese_frame, "Doenças pré-existentes:", "doencas_preexistentes", row=4, col=0)
        self.create_entry_field(anamnese_frame, "Alergias:", "alergias", row=4, col=2)
        self.create_entry_field(anamnese_frame, "Medicamentos em uso:", "medicamentos_em_uso", row=5, col=0)
        self.create_entry_field(anamnese_frame, "Observações:", "observacoes", row=5, col=2)

        # Seção de Conduta de Enfermagem
        conduta_frame = ttk.LabelFrame(form_frame, text="Conduta de Enfermagem", padding="10")
        conduta_frame.pack(fill="both", expand=True, pady=5)
        conduta_frame.columnconfigure(0, weight=1)
        conduta_frame.columnconfigure(1, weight=1)
        conduta_frame.columnconfigure(2, weight=1)
        conduta_frame.columnconfigure(3, weight=1)
        
        self.create_form_section(conduta_frame, {
            "Ocupacional": {"type": "combobox", "placeholder": "Selecione", "options": OPTIONS["ocupacional"], "var_name": "ocupacional"},
            "Hipótese diagnóstica": {"type": "entry", "placeholder": "Ex: Enxaqueca...", "var_name": "hipotese_diagnostica"},
            "Conduta adotada": {"type": "entry", "placeholder": "Descreva a conduta...", "var_name": "conduta_adotada"},
            "Resumo da 1ª conduta": {"type": "combobox", "placeholder": "Selecione", "options": OPTIONS["resumo_conduta"], "var_name": "resumo_conduta", "width": 40},
            "Medicamento administrado": {"type": "combobox", "placeholder": "Selecione", "options": OPTIONS["medicamento_admin"], "var_name": "medicamento_administrado"},
            "Posologia": {"type": "entry", "placeholder": "Ex: 1 comp, 15 gotas", "var_name": "posologia"},
            "Horário da medicação": {"type": "entry", "placeholder": "Insira o horário da medicação", "var_name": "horario_medicao"},
            "Observações": {"type": "entry", "placeholder": "(campo livre)", "var_name": "conduta_obs"},
        })
        
        save_button = ttk.Button(form_frame, text="Salvar Atendimento", command=self.save_atendimento)
        save_button.pack(pady=10)
        
        # Seção de Histórico e Exportação
        history_frame = ttk.Frame(self)
        history_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        history_frame.columnconfigure(0, weight=1)
        history_frame.rowconfigure(2, weight=1)
        
        ttk.Label(history_frame, text="Histórico de Atendimentos", font=("Arial", 14, "bold")).pack(pady=(0, 10))
        
        period_frame = ttk.Frame(history_frame)
        period_frame.pack(fill="x")
        ttk.Label(period_frame, text="Filtrar por:").pack(side="left", padx=5)
        self.history_period_var = tk.StringVar(value="15 dias")
        self.history_period_combo = ttk.Combobox(period_frame, textvariable=self.history_period_var, values=["15 dias", "30 dias", "60 dias", "YTD"], state="readonly")
        self.history_period_combo.pack(side="left", padx=5)
        self.history_period_combo.bind("<<ComboboxSelected>>", self.refresh_history_tree)

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
        
        export_button = ttk.Button(history_frame, text="Exportar Dados", command=self.open_export_window)
        export_button.pack(pady=10)

    def create_entry_field(self, parent, label_text, attr_name, row, col):
        """Cria e configura um campo de entrada com um label."""
        ttk.Label(parent, text=label_text).grid(row=row, column=col, padx=5, pady=2, sticky="e")
        entry = ttk.Entry(parent)
        entry.grid(row=row, column=col+1, padx=5, pady=2, sticky="ew")
        self.entries[attr_name] = entry
        utils.setup_placeholder(entry, self.placeholders.get(attr_name, ""))

    def create_combobox_field(self, parent, label_text, attr_name, options, row, col, width=20):
        """Cria e configura um campo de combobox com um label."""
        ttk.Label(parent, text=label_text).grid(row=row, column=col, padx=5, pady=2, sticky="e")
        combo = ttk.Combobox(parent, values=options, width=width, state="readonly")
        combo.grid(row=row, column=col+1, padx=5, pady=2, sticky="ew")
        self.comboboxes[attr_name] = combo
        utils.setup_placeholder(combo, self.placeholders.get(attr_name, ""))
                
    def create_form_section(self, parent_frame, fields):
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
                combo = ttk.Combobox(parent_frame, values=config["options"], width=config.get("width", 20), state="readonly")
                combo.grid(row=row, column=col*2+1, padx=5, pady=2, sticky="ew")
                self.placeholders[config["var_name"]] = config["placeholder"]
                utils.setup_placeholder(combo, config["placeholder"])
                self.comboboxes[config["var_name"]] = combo
                
    def create_queixa_section(self, parent):
        """Cria a seção de queixas com caixas de seleção."""
        ttk.Label(parent, text="Queixa principal:").grid(row=0, column=0, padx=5, pady=2, sticky="e")
        
        queixa_frame = ttk.Frame(parent)
        queixa_frame.grid(row=0, column=1, columnspan=3, padx=5, pady=2, sticky="ew")
        queixa_frame.columnconfigure(0, weight=1)
        queixa_frame.columnconfigure(1, weight=1)
        
        self.queixas_vars = {}
        queixas_list = ["Dor de cabeça", "Enjoo", "Tontura", "Fraqueza", "Outros"]
        
        for i, queixa in enumerate(queixas_list):
            var = tk.BooleanVar()
            self.queixas_vars[queixa] = var
            chk = ttk.Checkbutton(queixa_frame, text=queixa, variable=var)
            chk.grid(row=0, column=i, padx=5, sticky="w")
            var.trace("w", lambda *args, q=queixa: self.toggle_other_queixa(q))
            
        self.queixa_outros_entry = ttk.Entry(queixa_frame, state="disabled")
        self.queixa_outros_entry.grid(row=0, column=len(queixas_list), padx=5, sticky="ew")

    def toggle_other_queixa(self, queixa):
        """Habilita/desabilita o campo 'Outros'."""
        if queixa == "Outros":
            state = tk.NORMAL if self.queixas_vars["Outros"].get() else tk.DISABLED
            self.queixa_outros_entry.config(state=state)

    def create_pa_section(self, parent):
        """Cria os campos para pressão arterial."""
        ttk.Label(parent, text="PA:").grid(row=2, column=2, padx=5, pady=2, sticky="e")
        pa_frame = ttk.Frame(parent)
        pa_frame.grid(row=2, column=3, padx=5, pady=2, sticky="ew")
        
        self.entry_pa_sistolica = ttk.Entry(pa_frame, width=5)
        self.entry_pa_sistolica.pack(side="left", fill="x", expand=True)
        ttk.Label(pa_frame, text="x").pack(side="left")
        self.entry_pa_diastolica = ttk.Entry(pa_frame, width=5)
        self.entry_pa_diastolica.pack(side="left", fill="x", expand=True)
        
        self.placeholders["pa_sistolica"] = "Diastólica"
        self.placeholders["pa_diastolica"] = "Sistólica"
        utils.setup_placeholder(self.entry_pa_sistolica, self.placeholders["pa_sistolica"])
        utils.setup_placeholder(self.entry_pa_diastolica, self.placeholders["pa_diastolica"])

    def calculate_tenure(self, event=None):
        """Calcula e exibe o número de dias desde a data de admissão."""
        tenure_str = self.entries['tenure'].get()
        if not tenure_str or tenure_str == self.placeholders.get("tenure"):
            self.tenure_label.config(text="")
            return
            
        try:
            admissao_date = datetime.strptime(tenure_str, "%d/%m/%Y").date()
            hoje = datetime.now().date()
            diferenca = hoje - admissao_date
            self.tenure_label.config(text=f"{diferenca.days} Dias")
        except ValueError:
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
        
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
            
        badge_number = None
        if badge_number_str.isdigit():
            badge_number = int(badge_number_str)
        
        period = self.history_period_var.get()
        days_ago = 15
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
            # Validação de tipos
            tax_val = self.entries['tax'].get()
            if tax_val and not isinstance(float(tax_val), float):
                messagebox.showerror("Erro de Validação", "TAX deve ser um número válido.")
                return

            fc_val = self.entries['fc'].get()
            if fc_val and not fc_val.isdigit():
                messagebox.showerror("Erro de Validação", "FC deve ser um número inteiro.")
                return
            
            sat_val = self.entries['sat'].get()
            if sat_val and not sat_val.isdigit():
                messagebox.showerror("Erro de Validação", "SAT deve ser um número inteiro.")
                return

            pa_sistolica = self.entry_pa_sistolica.get()
            pa_diastolica = self.entry_pa_diastolica.get()
            if pa_sistolica and not pa_sistolica.isdigit():
                messagebox.showerror("Erro de Validação", "Pressão Sistólica (PA) deve ser um número inteiro.")
                return
            if pa_diastolica and not pa_diastolica.isdigit():
                messagebox.showerror("Erro de Validação", "Pressão Diastólica (PA) deve ser um número inteiro.")
                return

            # Coleta das queixas
            queixas_selecionadas = [q for q, var in self.queixas_vars.items() if var.get() and q != "Outros"]
            if self.queixas_vars["Outros"].get() and self.queixa_outros_entry.get():
                queixas_selecionadas.append(self.queixa_outros_entry.get())
            queixas_str = ";".join(queixas_selecionadas)

            conduta = Conduta(
                hipotese_diagnostica=self.entries['hipotese_diagnostica'].get() or "N/A",
                conduta_adotada=self.entries['conduta_adotada'].get() or "N/A",
                resumo_conduta=self.comboboxes['resumo_conduta'].get() or "N/A",
                medicamento_administrado=self.comboboxes['medicamento_administrado'].get() or "N/A",
                posologia=self.entries['posologia'].get() or "N/A",
                horario_medicacao=self.entries['horario_medicao'].get() or "N/A",
                observacoes=self.entries['conduta_obs'].get() or "N/A"
            )

            # Adiciona data, hora e semana ISO ao objeto de atendimento
            data_atendimento = datetime.now().strftime("%Y-%m-%d")
            hora_atendimento = datetime.now().strftime("%H:%M:%S")
            semana_iso = datetime.now().isocalendar()[1]

            atendimento = Atendimento(
                badge_number=int(badge_number_str),
                nome=self.entries['nome'].get() or "N/A",
                login=self.entries['login'].get() or "N/A",
                gestor=self.comboboxes['gestor'].get() or "N/A",
                turno=self.comboboxes['turno'].get() or "N/A",
                setor=self.comboboxes['setor'].get() or "N/A",
                processo=self.comboboxes['processo'].get() or "N/A",
                tenure=self.entries['tenure'].get() or "N/A",
                queixas_principais=queixas_str,
                hqa=self.entries['hqa'].get() or "N/A",
                tax=self.entries['tax'].get() or "N/A",
                pa_sistolica=pa_sistolica or "N/A",
                pa_diastolica=pa_diastolica or "N/A",
                fc=fc_val or "N/A",
                sat=sat_val or "N/A",
                doencas_preexistentes=self.entries['doencas_preexistentes'].get() or "N/A",
                alergias=self.entries['alergias'].get() or "N/A",
                medicamentos_em_uso=self.entries['medicamentos_em_uso'].get() or "N/A",
                observacoes=self.entries['observacoes'].get() or "N/A",
                condutas=[conduta],
                data_atendimento=data_atendimento,
                hora_atendimento=hora_atendimento,
                semana_iso=semana_iso
            )

            db.save_atendimento(atendimento)
            messagebox.showinfo("Sucesso", "Atendimento salvo com sucesso!")
            self.clear_form()
            self.refresh_history_tree()
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
        
        # Limpa os campos da queixa
        for var in self.queixas_vars.values():
            var.set(False)
        if self.queixa_outros_entry:
            self.queixa_outros_entry.delete(0, 'end')
            self.queixa_outros_entry.config(state="disabled")

        # Limpa os campos de PA
        self.entry_pa_sistolica.delete(0, 'end')
        utils.setup_placeholder(self.entry_pa_sistolica, self.placeholders["pa_sistolica"])
        self.entry_pa_diastolica.delete(0, 'end')
        utils.setup_placeholder(self.entry_pa_diastolica, self.placeholders["pa_diastolica"])
        
        self.tenure_label.config(text="")

    def open_export_window(self):
        """Abre a janela de exportação."""
        ExportWindow(self)

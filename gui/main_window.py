import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import db
import utils
from models import Atendimento, Conduta
from gui.edit_window import EditWindow, OPTIONS
from gui.export_window import ExportWindow
import sqlite3

# Constantes para os períodos do filtro
PERIODO_15_DIAS = "15 dias"
PERIODO_30_DIAS = "30 dias"
PERIODO_60_DIAS = "60 dias"
PERIODO_YTD = "YTD"
PERIODOS_FILTRO = [PERIODO_15_DIAS, PERIODO_30_DIAS, PERIODO_60_DIAS, PERIODO_YTD]

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
        self.refresh_history_tree()
    
    def create_widgets(self):
        """Cria e organiza todos os widgets na janela principal."""
        # --- Frame Principal do Formulário ---
        form_frame = ttk.Frame(self, padding="10")
        form_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        form_frame.columnconfigure(0, weight=1)
        form_frame.columnconfigure(1, weight=1)

        # --- Validação para aceitar apenas números ---
        vcmd = (self.register(self.validate_integer_input), '%P')

        # --- Seção de Identificação do paciente ---
        id_frame = ttk.LabelFrame(form_frame, text="Identificação do paciente", padding="10")
        id_frame.pack(fill="x", expand=False, pady=5)
        id_frame.columnconfigure(1, weight=1)
        id_frame.columnconfigure(3, weight=1)
        
        # Placeholders de Identificação
        self.placeholders = {
            "badge_number": "Bipe o crachá", "nome": "Bipe o crachá",
            "login": "Bipe o crachá", "gestor": "Selecione",
            "turno": "Bipe o crachá ou selecione", "setor": "Bipe o crachá ou selecione",
            "processo": "Selecione", "tenure": "Bipe o crachá",
            "queixa_outros": "Ex: Dor de cabeça, dor no braço, tontura, fraqueza...",
            "hqa": "Detalhe a queixa. Ex: Inicio, duração, intensidade, fatores de melhora/piora...",
            "tax": "Ex: 38º", "pa_sistolica": "120", "pa_diastolica": "80",
            "fc": "Ex: 90 BPM", "sat": "90%",
            "doencas_preexistentes": "Ex: Diabetes, Hipertensão, Hipotireoidismo...",
            "alergias": "Ex: Alergias respiratórias, alergias de contato, alergias ingestivas...",
            "medicamentos_em_uso": "Ex: Losartana, Metformina, Sinvastatina, Desvelafaxina...",
            "observacoes": "(Campo livre)",
            "ocupacional": "Selecione",
            "hipotese_diagnostica": "Ex: Enxaqueca, amigdalite, lesão por movimento, ansiedade...",
            "conduta_adotada": "Ex: Descreva a conduta adotada no atendimento",
            "resumo_conduta": "Selecione",
            "medicamento_administrado": "Selecione",
            "posologia": "Ex: 1 comp, 15 gotas",
            "horario_medicao": "Insira o horário da medicação",
            "conduta_obs": "(Campo livre)"
        }
        
        # Campos de Identificação
        self.create_entry_field(id_frame, "Badge Number:", "badge_number", 0, 0, validate_cmd=vcmd)
        self.create_entry_field(id_frame, "Nome:", "nome", 0, 2)
        self.create_entry_field(id_frame, "Login:", "login", 1, 0)
        self.create_combobox_field(id_frame, "Gestor:", "gestor", OPTIONS["gestores"], 1, 2, width=40)
        self.create_combobox_field(id_frame, "Turno:", "turno", OPTIONS["turnos"], 2, 0)
        self.create_combobox_field(id_frame, "Setor:", "setor", OPTIONS["setores"], 2, 2)
        self.create_combobox_field(id_frame, "Processo:", "processo", OPTIONS["processos"], 3, 0)
        self.create_entry_field(id_frame, "Tenure:", "tenure", 3, 2)
        
        self.entries['badge_number'].bind("<KeyRelease>", self.on_badge_number_change)
        
        # --- Seção de Anamnese ---
        anamnese_frame = ttk.LabelFrame(form_frame, text="Anamnese", padding="10")
        anamnese_frame.pack(fill="x", expand=False, pady=5)
        anamnese_frame.columnconfigure(1, weight=1)
        anamnese_frame.columnconfigure(3, weight=1)
        
        self.create_queixa_section(anamnese_frame)
        self.create_entry_field(anamnese_frame, "HQA:", "hqa", 1, 0)
        self.create_entry_field(anamnese_frame, "TAX:", "tax", 2, 0)
        self.create_pa_section(anamnese_frame)
        self.create_entry_field(anamnese_frame, "FC:", "fc", 3, 0)
        self.create_entry_field(anamnese_frame, "SAT:", "sat", 3, 2)
        self.create_entry_field(anamnese_frame, "Doenças pré-existentes:", "doencas_preexistentes", 4, 0)
        self.create_entry_field(anamnese_frame, "Alergias:", "alergias", 4, 2)
        self.create_entry_field(anamnese_frame, "Medicamentos em uso:", "medicamentos_em_uso", 5, 0)
        self.create_entry_field(anamnese_frame, "Observações:", "observacoes", 5, 2)

        # --- Seção de Conduta de Enfermagem ---
        conduta_frame = ttk.LabelFrame(form_frame, text="Conduta de Enfermagem", padding="10")
        conduta_frame.pack(fill="x", expand=False, pady=5)
        conduta_frame.columnconfigure(1, weight=1)
        conduta_frame.columnconfigure(3, weight=1)
        
        self.create_combobox_field(conduta_frame, "Ocupacional:", "ocupacional", OPTIONS["ocupacional"], 0, 0)
        self.create_entry_field(conduta_frame, "Hipótese diagnóstica:", "hipotese_diagnostica", 0, 2)
        self.create_entry_field(conduta_frame, "Conduta adotada:", "conduta_adotada", 1, 0)
        self.create_combobox_field(conduta_frame, "Resumo da 1ª conduta:", "resumo_conduta", OPTIONS["resumo_conduta"], 1, 2, width=40)
        self.create_combobox_field(conduta_frame, "Medicamento administrado:", "medicamento_administrado", OPTIONS["medicamento_admin"], 2, 0)
        self.create_entry_field(conduta_frame, "Posologia:", "posologia", 2, 2)
        self.create_entry_field(conduta_frame, "Horário da medicação:", "horario_medicao", 3, 0)
        self.create_entry_field(conduta_frame, "Observações:", "conduta_obs", 3, 2)
        
        save_button = ttk.Button(form_frame, text="Salvar Atendimento", command=self.save_atendimento)
        save_button.pack(pady=10)
        
        # --- Seção de Histórico e Exportação ---
        history_frame = ttk.Frame(self)
        history_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        history_frame.columnconfigure(0, weight=1)
        history_frame.rowconfigure(2, weight=1)
        
        ttk.Label(history_frame, text="Histórico de Atendimentos", font=("Arial", 14, "bold")).pack(pady=(0, 10))
        
        period_frame = ttk.Frame(history_frame)
        period_frame.pack(fill="x")
        ttk.Label(period_frame, text="Filtrar por:").pack(side="left", padx=5)
        self.history_period_var = tk.StringVar(value=PERIODO_15_DIAS)
        self.history_period_combo = ttk.Combobox(period_frame, textvariable=self.history_period_var, values=PERIODOS_FILTRO, state="readonly")
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

        # Inicia com o formulário limpo
        self.clear_form()

    def validate_integer_input(self, value_if_allowed):
        """Permite apenas dígitos no campo de entrada."""
        if value_if_allowed.isdigit() or value_if_allowed == "":
            return True
        return False

    def create_entry_field(self, parent, label_text, attr_name, row, col, validate_cmd=None):
        """Cria e configura um campo de entrada com um label."""
        ttk.Label(parent, text=label_text).grid(row=row, column=col*2, padx=5, pady=2, sticky="w")
        entry = ttk.Entry(parent, validate="key", validatecommand=validate_cmd)
        entry.grid(row=row, column=col*2+1, padx=5, pady=2, sticky="ew")
        self.entries[attr_name] = entry
        utils.setup_placeholder(entry, self.placeholders.get(attr_name, ""))

    def create_combobox_field(self, parent, label_text, attr_name, options, row, col, width=20):
        """Cria e configura um campo de combobox com um label."""
        ttk.Label(parent, text=label_text).grid(row=row, column=col*2, padx=5, pady=2, sticky="w")
        combo = ttk.Combobox(parent, values=options, width=width, state="readonly")
        combo.grid(row=row, column=col*2+1, padx=5, pady=2, sticky="ew")
        self.comboboxes[attr_name] = combo
        utils.setup_placeholder(combo, self.placeholders.get(attr_name, ""))
                
    def create_queixa_section(self, parent):
        """Cria a seção de queixas com caixas de seleção."""
        ttk.Label(parent, text="Queixa principal:").grid(row=0, column=0, columnspan=4, padx=5, pady=2, sticky="w")
        
        queixa_frame = ttk.Frame(parent)
        queixa_frame.grid(row=0, column=1, columnspan=3, padx=5, pady=2, sticky="ew")
        
        self.queixas_vars = {}
        queixas_list = ["Dor de cabeça", "Enjoo", "Tontura", "Fraqueza", "Outros"]
        
        for i, queixa in enumerate(queixas_list):
            var = tk.BooleanVar()
            self.queixas_vars[queixa] = var
            chk = ttk.Checkbutton(queixa_frame, text=queixa, variable=var, command=lambda q=queixa: self.toggle_other_queixa(q))
            chk.pack(side="left", padx=5)

        self.queixa_outros_entry = ttk.Entry(queixa_frame, state="disabled")
        self.queixa_outros_entry.pack(side="left", fill="x", expand=True, padx=5)
        utils.setup_placeholder(self.queixa_outros_entry, self.placeholders.get("queixa_outros"))

    def toggle_other_queixa(self, queixa):
        """Habilita/desabilita o campo 'Outros'."""
        if queixa == "Outros":
            is_checked = self.queixas_vars["Outros"].get()
            new_state = tk.NORMAL if is_checked else tk.DISABLED
            self.queixa_outros_entry.config(state=new_state)
            if not is_checked:
                self.queixa_outros_entry.delete(0, 'end')
                utils.setup_placeholder(self.queixa_outros_entry, self.placeholders.get("queixa_outros", ""))

    def create_pa_section(self, parent):
        """Cria os campos para pressão arterial."""
        ttk.Label(parent, text="PA:").grid(row=2, column=2, padx=5, pady=2, sticky="w")
        pa_frame = ttk.Frame(parent)
        pa_frame.grid(row=2, column=3, padx=5, pady=2, sticky="ew")
        
        self.entry_pa_sistolica = ttk.Entry(pa_frame, width=5)
        self.entry_pa_sistolica.pack(side="left")
        ttk.Label(pa_frame, text="/").pack(side="left")
        self.entry_pa_diastolica = ttk.Entry(pa_frame, width=5)
        self.entry_pa_diastolica.pack(side="left")
        ttk.Label(pa_frame, text="mmHg").pack(side="left", padx=5)
        
        self.entries['pa_sistolica'] = self.entry_pa_sistolica
        self.entries['pa_diastolica'] = self.entry_pa_diastolica
        utils.setup_placeholder(self.entry_pa_sistolica, self.placeholders["pa_sistolica"])
        utils.setup_placeholder(self.entry_pa_diastolica, self.placeholders["pa_diastolica"])

    def on_badge_number_change(self, event):
        """Preenche ou limpa os campos com base no Badge Number."""
        badge_number_str = self.entries['badge_number'].get()
        
        if not badge_number_str:
            self.clear_form(clear_badge=False)
        else:
            last_atendimento = db.get_last_atendimento_by_badge(badge_number_str)
            if last_atendimento:
                # Limpa placeholders antes de inserir
                for name, widget in {**self.entries, **self.comboboxes}.items():
                    if name != 'badge_number':
                        utils.clear_placeholder(widget, self.placeholders.get(name))
                
                self.entries['nome'].insert(0, last_atendimento.nome)
                self.entries['login'].insert(0, last_atendimento.login)
                self.comboboxes['gestor'].set(last_atendimento.gestor)
                self.comboboxes['turno'].set(last_atendimento.turno)
                self.comboboxes['setor'].set(last_atendimento.setor)
                self.comboboxes['processo'].set(last_atendimento.processo)
                self.entries['tenure'].insert(0, last_atendimento.tenure)
                
                # Garante que placeholders sejam removidos se o campo foi preenchido
                for name, widget in {**self.entries, **self.comboboxes}.items():
                    utils.remove_placeholder_on_fill(widget, self.placeholders.get(name, ""))
        
        self.refresh_history_tree()
    
    def refresh_history_tree(self, event=None):
        """Atualiza a Treeview do histórico de atendimentos."""
        badge_widget = self.entries.get('badge_number')
        badge_number_str = badge_widget.get() if badge_widget else ""
        
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)

        is_placeholder = (badge_number_str == self.placeholders.get("badge_number"))
        badge_number = None if not badge_number_str or is_placeholder else badge_number_str

        period = self.history_period_var.get()
        days_ago = {
            PERIODO_15_DIAS: 15,
            PERIODO_30_DIAS: 30,
            PERIODO_60_DIAS: 60,
        }.get(period, 15)

        if period == PERIODO_YTD:
            start_of_year = datetime.now().replace(month=1, day=1)
            days_ago = (datetime.now() - start_of_year).days + 1
        
        atendimentos = db.get_atendimentos_by_badge(badge_number, days_ago)
        
        if not atendimentos:
            self.history_tree.insert("", "end", values=("Sem atendimentos no período", "", "", ""))
        else:
            for atendimento in atendimentos:
                data_hora = f"{atendimento[4]} {atendimento[5]}"
                self.history_tree.insert("", "end", iid=atendimento[0], values=(atendimento[1], atendimento[2], atendimento[3], data_hora))
    
    def on_double_click_history(self, event):
        """Abre a janela de edição ao dar um duplo-clique em um item da Treeview."""
        selected_item = self.history_tree.selection()
        if selected_item:
            try:
                self.atendimento_id_to_edit = int(selected_item[0])
                EditWindow(self, self.atendimento_id_to_edit, self.refresh_history_tree)
            except (ValueError, IndexError):
                pass
            
    def save_atendimento(self):
        """Valida o formulário e salva um novo atendimento."""
        try:
            badge_number = self.entries['badge_number'].get()
            if not badge_number or badge_number == self.placeholders.get('badge_number'):
                messagebox.showerror("Erro de Validação", "O campo Badge Number é obrigatório.")
                return

            # Validações numéricas
            for field in ['tax', 'fc', 'sat', 'pa_sistolica', 'pa_diastolica']:
                value = self.entries[field].get()
                if value and value != self.placeholders.get(field):
                    float(value)

            queixas_selecionadas = [q for q, var in self.queixas_vars.items() if var.get() and q != "Outros"]
            if self.queixas_vars.get("Outros", tk.BooleanVar(value=False)).get() and self.queixa_outros_entry.get():
                queixas_selecionadas.append(self.queixa_outros_entry.get())
            queixas_str = ";".join(queixas_selecionadas) if queixas_selecionadas else "N/A"

            conduta_data = {}
            for key in self.entries:
                if key.startswith('conduta_'):
                    conduta_data[key.replace('conduta_', '')] = self.entries[key].get() or "N/A"
            for key in self.comboboxes:
                 if key.startswith('conduta_'):
                    conduta_data[key.replace('conduta_', '')] = self.comboboxes[key].get() or "N/A"
            conduta = Conduta(**conduta_data)
            
            now = datetime.now()
            atendimento_data = {key: (widget.get() if widget.get() != self.placeholders.get(key) else "N/A") for key, widget in {**self.entries, **self.comboboxes}.items()}
            atendimento = Atendimento(
                **atendimento_data,
                queixas_principais=queixas_str,
                condutas=[conduta],
                data_atendimento=now.strftime("%Y-%m-%d"),
                hora_atendimento=now.strftime("%H:%M:%S"),
                semana_iso=now.isocalendar()[1]
            )

            db.save_atendimento(atendimento)
            messagebox.showinfo("Sucesso", "Atendimento salvo com sucesso!")
            self.clear_form()
            self.refresh_history_tree()
        except ValueError:
            messagebox.showerror("Erro de Validação", "Verifique se os campos numéricos (TAX, FC, SAT, PA) estão corretos.")
        except sqlite3.Error as e:
            messagebox.showerror("Erro de Banco de Dados", f"Ocorreu um erro ao salvar: {e}")
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro inesperado: {e}")

    def clear_form(self, clear_badge=True):
        """Limpa todos os campos do formulário e restaura os placeholders."""
        widgets_to_clear = self.entries.copy()
        if not clear_badge:
            widgets_to_clear.pop('badge_number', None)

        for name, entry in widgets_to_clear.items():
            entry.delete(0, 'end')
            utils.setup_placeholder(entry, self.placeholders.get(name, ""))

        for name, combo in self.comboboxes.items():
            combo.set("")
            utils.setup_placeholder(combo, self.placeholders.get(name, ""))
        
        for var in self.queixas_vars.values():
            var.set(False)

        if self.queixa_outros_entry:
            self.toggle_other_queixa("Outros") # Reseta o estado e o placeholder

    def open_export_window(self):
        """Abre a janela de exportação."""
        ExportWindow(self)


import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
import db
import utils
from models import Atendimento, Conduta
from gui.edit_window import EditWindow, OPTIONS
from gui.export_window import ExportWindow
import sqlite3

# Constantes para os períodos do filtro
PERIODO_ESCALA_ATUAL = "Escala Atual"
PERIODO_15_DIAS = "15 dias"
PERIODO_30_DIAS = "30 dias"
PERIODO_60_DIAS = "60 dias"
PERIODO_YTD = "YTD"
PERIODOS_FILTRO = [PERIODO_ESCALA_ATUAL, PERIODO_15_DIAS, PERIODO_30_DIAS, PERIODO_60_DIAS, PERIODO_YTD]

class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Registro de Atendimentos Médicos")
        self.geometry("1200x800")
        
        self.entries = {}
        self.comboboxes = {}
        self.queixas_vars = {}
        
        self.create_widgets()
        self.refresh_history_tree()
    
    def create_widgets(self):
        self.columnconfigure(0, weight=1); self.columnconfigure(1, weight=1); self.rowconfigure(0, weight=1)

        form_frame = ttk.Frame(self, padding="10")
        form_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        form_frame.columnconfigure(1, weight=1)

        vcmd_int = (self.register(utils.validate_integer_input), '%P')
        vcmd_posologia = (self.register(utils.validate_posologia_input), '%P')

        self.placeholders = {
            "badge_number": "Bipe o crachá", "nome": "Bipe o crachá", "login": "Bipe o crachá",
            "gestor": "Selecione", "turno": "Bipe o crachá ou selecione", "setor": "Bipe o crachá ou selecione",
            "processo": "Selecione", "tenure": "Bipe o crachá",
            "hqa": "Detalhe a queixa...", "tax": "Ex: 38", "pa_sistolica": "120", "pa_diastolica": "80",
            "fc": "Ex: 90", "sat": "Ex: 95",
            "doencas_preexistentes": "Ex: Diabetes, Hipertensão...", "alergias": "Ex: Dipirona, AAS...",
            "medicamentos_em_uso": "Ex: Losartana, Metformina...", "observacoes": "(Campo livre)",
            "hipotese_diagnostica": "Ex: Enxaqueca, ansiedade...", "conduta_adotada": "Descreva a conduta...",
            "resumo_conduta": "Selecione", "medicamento_administrado": "Selecione",
            "posologia": "Ex: 1 comp, 15 gotas", "horario_medicao": "HH:MM", "conduta_obs": "(Campo livre)"
        }

        # --- Seções do Formulário ---
        id_frame = self.create_section_frame(form_frame, "Identificação do paciente")
        anamnese_frame = self.create_section_frame(form_frame, "Anamnese")
        conduta_frame = self.create_section_frame(form_frame, "Conduta de Enfermagem")

        # --- Campos de Identificação ---
        self.create_entry_field(id_frame, "Badge Number:", "badge_number", 0, 0, vcmd_int)
        self.create_entry_field(id_frame, "Nome:", "nome", 0, 1)
        self.create_entry_field(id_frame, "Login:", "login", 1, 0)
        self.create_combobox_field(id_frame, "Gestor:", "gestor", OPTIONS["gestores"], 1, 1)
        self.create_combobox_field(id_frame, "Turno:", "turno", OPTIONS["turnos"], 2, 0)
        self.create_combobox_field(id_frame, "Setor:", "setor", OPTIONS["setores"], 2, 1)
        self.create_combobox_field(id_frame, "Processo:", "processo", OPTIONS["processos"], 3, 0)
        self.create_entry_field(id_frame, "Tenure:", "tenure", 3, 1)
        self.entries['badge_number'].bind("<KeyRelease>", self.on_badge_number_change)

        # --- Campos de Anamnese ---
        self.create_queixa_section(anamnese_frame)
        self.create_entry_field(anamnese_frame, "HQA:", "hqa", 1, 0, columnspan=3)
        self.create_entry_field(anamnese_frame, "TAX:", "tax", 2, 0)
        self.create_pa_section(anamnese_frame, 2, 1)
        self.create_entry_field(anamnese_frame, "FC:", "fc", 3, 0)
        self.create_entry_field(anamnese_frame, "SAT:", "sat", 3, 1)
        self.create_entry_field(anamnese_frame, "Doenças pré-existentes:", "doencas_preexistentes", 4, 0, columnspan=3)
        self.create_entry_field(anamnese_frame, "Alergias:", "alergias", 5, 0, columnspan=3)
        self.create_entry_field(anamnese_frame, "Medicamentos em uso:", "medicamentos_em_uso", 6, 0, columnspan=3)
        self.create_entry_field(anamnese_frame, "Observações:", "observacoes", 7, 0, columnspan=3)

        # --- Campos de Conduta ---
        self.create_combobox_field(conduta_frame, "Ocupacional:", "ocupacional", OPTIONS["ocupacional"], 0, 0)
        self.create_entry_field(conduta_frame, "Hipótese:", "hipotese_diagnostica", 0, 1)
        self.create_entry_field(conduta_frame, "Conduta:", "conduta_adotada", 1, 0, columnspan=3)
        self.create_combobox_field(conduta_frame, "Resumo:", "resumo_conduta", OPTIONS["resumo_conduta"], 2, 0)
        self.create_combobox_field(conduta_frame, "Medicação:", "medicamento_administrado", OPTIONS["medicamento_admin"], 2, 1)
        self.create_entry_field(conduta_frame, "Posologia:", "posologia", 3, 0, vcmd=vcmd_posologia)
        self.create_horario_field(conduta_frame, "Horário:", "horario_medicao", 3, 1)
        self.create_entry_field(conduta_frame, "Obs:", "conduta_obs", 4, 0, columnspan=3)
        
        ttk.Button(form_frame, text="Salvar Atendimento", command=self.save_atendimento).pack(pady=10)
        
        self.create_history_section()
        self.clear_form()

    def create_section_frame(self, parent, text):
        frame = ttk.LabelFrame(parent, text=text, padding="10")
        frame.pack(fill="x", pady=5)
        frame.columnconfigure(1, weight=1); frame.columnconfigure(3, weight=1)
        return frame

    def create_entry_field(self, parent, label, name, r, c, vcmd=None, columnspan=1):
        ttk.Label(parent, text=label).grid(row=r, column=c*2, padx=5, pady=2, sticky="w")
        entry = ttk.Entry(parent, validate="key", validatecommand=vcmd)
        entry.grid(row=r, column=c*2+1, padx=5, pady=2, sticky="ew", columnspan=columnspan)
        self.entries[name] = entry
        utils.setup_placeholder(entry, self.placeholders.get(name, ""))

    def create_combobox_field(self, parent, label, name, opts, r, c):
        ttk.Label(parent, text=label).grid(row=r, column=c*2, padx=5, pady=2, sticky="w")
        combo = ttk.Combobox(parent, values=opts)
        combo.grid(row=r, column=c*2+1, padx=5, pady=2, sticky="ew")
        self.comboboxes[name] = combo
        utils.setup_placeholder(combo, self.placeholders.get(name, ""))

    def create_horario_field(self, parent, label, name, r, c):
        ttk.Label(parent, text=label).grid(row=r, column=c*2, padx=5, pady=2, sticky="w")
        frame = ttk.Frame(parent)
        frame.grid(row=r, column=c*2+1, padx=5, pady=2, sticky="ew")
        entry = ttk.Entry(frame); entry.pack(side="left", fill="x", expand=True)
        self.entries[name] = entry
        utils.setup_placeholder(entry, self.placeholders.get(name, ""))
        ttk.Button(frame, text="Agora", command=self.set_current_time).pack(side="left", padx=5)

    def create_queixa_section(self, parent):
        ttk.Label(parent, text="Queixa principal:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        frame = ttk.Frame(parent)
        frame.grid(row=0, column=1, columnspan=3, padx=5, pady=2, sticky="ew")
        
        for queixa in ["Dor de cabeça", "Enjoo", "Tontura", "Fraqueza", "Outros"]:
            var = tk.BooleanVar(); self.queixas_vars[queixa] = var
            chk = ttk.Checkbutton(frame, text=queixa, variable=var, command=lambda q=queixa: self.toggle_other_queixa(q))
            chk.pack(side="left", padx=2)

        self.queixa_outros_entry = ttk.Entry(frame, state="disabled")
        self.queixa_outros_entry.pack(side="left", fill="x", expand=True, padx=2)
        utils.setup_placeholder(self.queixa_outros_entry, "Outra queixa...")

    def create_pa_section(self, parent, r, c):
        ttk.Label(parent, text="PA:").grid(row=r, column=c*2, padx=5, pady=2, sticky="w")
        frame = ttk.Frame(parent)
        frame.grid(row=r, column=c*2+1, padx=5, pady=2, sticky="ew")
        self.entries['pa_sistolica'] = ttk.Entry(frame, width=5); self.entries['pa_sistolica'].pack(side="left")
        ttk.Label(frame, text="/").pack(side="left")
        self.entries['pa_diastolica'] = ttk.Entry(frame, width=5); self.entries['pa_diastolica'].pack(side="left")

    def create_history_section(self):
        history_frame = ttk.Frame(self); history_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        history_frame.columnconfigure(0, weight=1); history_frame.rowconfigure(1, weight=1)
        
        controls = ttk.Frame(history_frame); controls.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        ttk.Label(controls, text="Histórico:", font=("Arial", 14, "bold")).pack(side="left")
        self.history_period_var = tk.StringVar(value=PERIODO_15_DIAS)
        combo = ttk.Combobox(controls, textvariable=self.history_period_var, values=PERIODOS_FILTRO, state="readonly", width=12)
        combo.pack(side="right"); combo.bind("<<ComboboxSelected>>", self.refresh_history_tree)

        tree_frame = ttk.Frame(history_frame); tree_frame.grid(row=1, column=0, sticky="nsew")
        self.history_tree = ttk.Treeview(tree_frame, columns=("badge", "nome", "data_hora"), show="headings")
        self.history_tree.heading("badge", text="Badge"); self.history_tree.heading("nome", text="Nome"); self.history_tree.heading("data_hora", text="Data/Hora")
        self.history_tree.column("badge", width=80, anchor="center"); self.history_tree.column("nome", width=200); self.history_tree.column("data_hora", width=120)
        
        scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=scroll.set)
        self.history_tree.pack(side="left", fill="both", expand=True); scroll.pack(side="right", fill="y")
        self.history_tree.bind("<Double-1>", self.on_double_click_history)
        
        ttk.Button(history_frame, text="Exportar Dados", command=self.open_export_window).grid(row=2, column=0, pady=10)

    def set_current_time(self):
        if entry := self.entries.get("horario_medicao"):
            utils.clear_placeholder(entry, self.placeholders.get("horario_medicao", ""))
            entry.delete(0, tk.END)
            entry.insert(0, datetime.now().strftime("%H:%M"))

    def toggle_other_queixa(self, q):
        if q == "Outros":
            is_checked = self.queixas_vars["Outros"].get()
            self.queixa_outros_entry.config(state=tk.NORMAL if is_checked else tk.DISABLED)
            if not is_checked:
                utils.clear_placeholder(self.queixa_outros_entry, "Outra queixa...")
                utils.setup_placeholder(self.queixa_outros_entry, "Outra queixa...")
            else:
                utils.remove_placeholder_on_fill(self.queixa_outros_entry, "Outra queixa...")
    
    def on_badge_number_change(self, event):
        badge = self.entries['badge_number'].get()
        if not badge:
            self.clear_form(clear_badge=False)
        elif last := db.get_last_atendimento_by_badge(badge):
            self.clear_form(clear_badge=False)
            fields = {'nome': last.nome, 'login': last.login, 'gestor': last.gestor, 'turno': last.turno,
                      'setor': last.setor, 'processo': last.processo, 'tenure': last.tenure}
            for name, value in fields.items():
                widget = self.entries.get(name) or self.comboboxes.get(name)
                utils.clear_placeholder(widget, self.placeholders.get(name));
                if isinstance(widget, ttk.Combobox): widget.set(value)
                else: widget.delete(0, tk.END); widget.insert(0, value)
                utils.remove_placeholder_on_fill(widget, self.placeholders.get(name))
        self.refresh_history_tree()
    
    def refresh_history_tree(self, event=None):
        for item in self.history_tree.get_children(): self.history_tree.delete(item)
        
        badge = self.entries.get('badge_number', tk.Entry()).get()
        badge = None if not badge or badge == self.placeholders.get("badge_number") else badge

        period = self.history_period_var.get()
        
        if period == PERIODO_ESCALA_ATUAL:
            now = datetime.now()
            if 7 <= now.hour < 19: # Turno do dia
                start_dt = now.replace(hour=7, minute=0, second=0, microsecond=0)
                end_dt = now.replace(hour=18, minute=59, second=59, microsecond=999999)
            else: # Turno da noite
                if now.hour >= 19: # Começou hoje
                    start_dt = now.replace(hour=19, minute=0, second=0, microsecond=0)
                    end_dt = (now + timedelta(days=1)).replace(hour=6, minute=59, second=59, microsecond=999999)
                else: # Termina hoje (começou ontem)
                    start_dt = (now - timedelta(days=1)).replace(hour=19, minute=0, second=0, microsecond=0)
                    end_dt = now.replace(hour=6, minute=59, second=59, microsecond=999999)
            atendimentos = db.get_atendimentos_by_datetime_range(
                start_dt.strftime("%Y-%m-%d %H:%M:%S"), end_dt.strftime("%Y-%m-%d %H:%M:%S"), badge)
        else:
            days = {PERIODO_15_DIAS: 15, PERIODO_30_DIAS: 30, PERIODO_60_DIAS: 60}.get(period, 15)
            if period == PERIODO_YTD: days = (datetime.now() - datetime.now().replace(month=1, day=1)).days + 1
            atendimentos = db.get_atendimentos_by_badge(badge, days)

        if not atendimentos:
            self.history_tree.insert("", "end", values=("Sem registros", "", ""))
        else:
            for at in atendimentos:
                self.history_tree.insert("", "end", iid=at[0], values=(at[1], at[2], f"{at[4]} {at[5]}"))
    
    def on_double_click_history(self, event):
        if item := self.history_tree.selection():
            try: EditWindow(self, int(item[0]), self.refresh_history_tree)
            except (ValueError, IndexError): pass
            
    def save_atendimento(self):
        try:
            if not (badge := self.entries['badge_number'].get()) or badge == self.placeholders.get('badge_number'):
                return messagebox.showerror("Erro", "Badge Number é obrigatório.")

            data = {k: (w.get() if w.get() != self.placeholders.get(k, '') else "N/A") for k, w in {**self.entries, **self.comboboxes}.items()}
            
            queixas = [q for q, v in self.queixas_vars.items() if v.get() and q != "Outros"]
            if self.queixas_vars.get("Outros").get() and (o := self.queixa_outros_entry.get()) and o != "Outra queixa...": 
                queixas.append(o)
            
            now = datetime.now()
            
            conduta_data = {
                'ocupacional': data.get('ocupacional', 'N/A'),
                'hipotese_diagnostica': data.get('hipotese_diagnostica', 'N/A'),
                'conduta_adotada': data.get('conduta_adotada', 'N/A'),
                'resumo_conduta': data.get('resumo_conduta', 'N/A'),
                'medicamento_administrado': data.get('medicamento_administrado', 'N/A'),
                'posologia': data.get('posologia', 'N/A'),
                'horario_medicacao': data.get('horario_medicao', 'N/A'),
                'observacoes': data.get('conduta_obs', 'N/A')
            }

            atendimento_data = {k:v for k,v in data.items() if k not in conduta_data and k != 'conduta_obs'}

            atendimento = Atendimento(
                **atendimento_data,
                queixas_principais="; ".join(queixas) if queixas else "N/A",
                condutas=[Conduta(**conduta_data)],
                data_atendimento=now.strftime("%Y-%m-%d"),
                hora_atendimento=now.strftime("%H:%M:%S"),
                semana_iso=now.isocalendar()[1]
            )
            db.save_atendimento(atendimento)
            messagebox.showinfo("Sucesso", "Atendimento salvo!")
            self.clear_form(); self.refresh_history_tree()
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro: {e}")

    def clear_form(self, clear_badge=True):
        for name, w in self.entries.items():
            if clear_badge or name != 'badge_number':
                utils.clear_placeholder(w, self.placeholders.get(name, "")); utils.setup_placeholder(w, self.placeholders.get(name, ""))
        for name, w in self.comboboxes.items():
            utils.clear_placeholder(w, self.placeholders.get(name, "")); utils.setup_placeholder(w, self.placeholders.get(name, ""))
        for var in self.queixas_vars.values(): var.set(False)
        if hasattr(self, 'queixa_outros_entry'): self.toggle_other_queixa("Outros")

    def open_export_window(self): ExportWindow(self)


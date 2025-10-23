import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
import db
import utils
from models import Atendimento, Conduta
from gui.edit_window import EditWindow
from gui.export_window import ExportWindow
from gui.constants import OPTIONS, SINTOMAS, REGIOES # Importa constantes
import sqlite3
import json # Para salvar listas de queixas
import main # Importa o main para acessar select_database_path

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
        # Novos dicts para checkbuttons de queixa secundária
        self.qs_sintomas_vars = {}
        self.qs_regioes_vars = {}
        
        # Lista para guardar todos os widgets do formulário para habilitar/desabilitar
        self.form_widgets = [] 
        
        self.create_widgets()
        self.refresh_history_tree()
    
    def create_widgets(self):
        self.columnconfigure(0, weight=1); self.columnconfigure(1, weight=1); self.rowconfigure(0, weight=1)

        form_frame = ttk.Frame(self, padding="10")
        form_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        form_frame.columnconfigure(1, weight=1)
        
        # Frame para os botões Salvar e Limpar
        button_frame = ttk.Frame(form_frame)
        button_frame.pack(pady=10)


        vcmd_int = (self.register(utils.validate_integer_input), '%P')
        vcmd_posologia = (self.register(utils.validate_posologia_input), '%P')

        self.placeholders = {
            "badge_number": "Bipe o crachá", "nome": "Bipe o crachá", "login": "Bipe o crachá",
            "gestor": "Selecione", "turno": "Bipe o crachá ou selecione", "setor": "Bipe o crachá ou selecione",
            "processo": "Selecione", "tenure": "Bipe o crachá",
            "qp_sintoma": "Selecione", "qp_regiao": "Selecione",
            "hqa": "Detalhe a queixa...", "tax": "Ex: 38", "pa_sistolica": "120", "pa_diastolica": "80",
            "fc": "Ex: 90", "sat": "Ex: 95",
            "doencas_preexistentes": "Ex: Diabetes, Hipertensão...", "alergias": "Ex: Dipirona, AAS...",
            "medicamentos_em_uso": "Ex: Losartana, Metformina...", "observacoes": "(Campo livre)",
            "hipotese_diagnostica": "Ex: Enxaqueca, ansiedade...", 
            "resumo_conduta": "Selecione", "medicamento_administrado": "Selecione",
            "posologia": "Ex: 1 comp, 15 gotas", "horario_medicao": "HH:MM", "conduta_obs": "(Campo livre)"
        }

        # --- Seções do Formulário ---
        id_frame = self.create_section_frame(form_frame, "Identificação do paciente")
        anamnese_frame = self.create_section_frame(form_frame, "Anamnese")
        conduta_frame = self.create_section_frame(form_frame, "Conduta de Enfermagem")

        # --- Campos de Identificação ---
        # Note: Esses widgets NÃO são adicionados a self.form_widgets aqui,
        # pois não precisam ser desabilitados pelas regras "Absorvente"/"Trabalho em altura"
        self.create_entry_field(id_frame, "Badge Number:", "badge_number", 0, 0, vcmd_int)
        self.create_entry_field(id_frame, "Nome:", "nome", 0, 1)
        self.create_entry_field(id_frame, "Login:", "login", 1, 0)
        self.create_combobox_field(id_frame, "Gestor:", "gestor", OPTIONS["gestores"], 1, 1)
        self.create_combobox_field(id_frame, "Turno:", "turno", OPTIONS["turnos"], 2, 0)
        self.create_combobox_field(id_frame, "Setor:", "setor", OPTIONS["setores"], 2, 1)
        self.create_combobox_field(id_frame, "Processo:", "processo", OPTIONS["processos"], 3, 0)
        self.create_entry_field(id_frame, "Tenure:", "tenure", 3, 1)
        self.entries['badge_number'].bind("<KeyRelease>", self.on_badge_number_change)

        # --- Campos de Anamnese (MODIFICADO) ---
        self.create_queixa_section(anamnese_frame) # Nova seção de queixas
        self.create_entry_field(anamnese_frame, "HQA:", "hqa", 2, 0, columnspan=3, add_to_form_widgets=True) # Mudou row
        self.create_entry_field(anamnese_frame, "TAX:", "tax", 3, 0, add_to_form_widgets=True) # Mudou row
        self.create_pa_section(anamnese_frame, 3, 1) # Mudou row
        self.create_entry_field(anamnese_frame, "FC:", "fc", 4, 0, add_to_form_widgets=True) # Mudou row
        self.create_entry_field(anamnese_frame, "SAT:", "sat", 4, 1, add_to_form_widgets=True) # Mudou row
        self.create_entry_field(anamnese_frame, "Doenças pré-existentes:", "doencas_preexistentes", 5, 0, columnspan=3, add_to_form_widgets=True) # Mudou row
        self.create_entry_field(anamnese_frame, "Alergias:", "alergias", 6, 0, columnspan=3, add_to_form_widgets=True) # Mudou row
        self.create_entry_field(anamnese_frame, "Medicamentos em uso:", "medicamentos_em_uso", 7, 0, columnspan=3, add_to_form_widgets=True) # Mudou row
        self.create_entry_field(anamnese_frame, "Observações:", "observacoes", 8, 0, columnspan=3, add_to_form_widgets=True) # Mudou row

        # --- Campos de Conduta (MODIFICADO) ---
        self.create_entry_field(conduta_frame, "Hipótese:", "hipotese_diagnostica", 0, 1, add_to_form_widgets=True)
        self.create_combobox_field(conduta_frame, "Resumo:", "resumo_conduta", OPTIONS["resumo_conduta"], 2, 0, add_to_form_widgets=True) # Atualizado
        self.create_combobox_field(conduta_frame, "Medicação:", "medicamento_administrado", OPTIONS["medicamento_admin"], 2, 1, add_to_form_widgets=True)
        self.create_entry_field(conduta_frame, "Posologia:", "posologia", 3, 0, vcmd=vcmd_posologia, add_to_form_widgets=True)
        self.create_horario_field(conduta_frame, "Horário:", "horario_medicao", 3, 1) # Adiciona à lista dentro da função
        self.create_entry_field(conduta_frame, "Obs:", "conduta_obs", 4, 0, columnspan=3, add_to_form_widgets=True)
        
        # --- Lógica de Habilitar/Desabilitar ---
        # Widgets que permanecem ativos para "Trabalho em altura"
        self.trabalho_altura_exceptions = {
            self.entries["pa_sistolica"],
            self.entries["pa_diastolica"],
            self.comboboxes["resumo_conduta"]
        }
        
        # --- CORREÇÃO: Excluir qp_sintoma da lista self.form_widgets ---
        # A lista é populada nas funções create_*, então removemos qp_sintoma após a criação
        if self.comboboxes.get("qp_sintoma") in self.form_widgets:
            self.form_widgets.remove(self.comboboxes.get("qp_sintoma"))
            
        # Vincula a função de mudança
        self.comboboxes["qp_sintoma"].bind("<<ComboboxSelected>>", self.on_qp_sintoma_change)

        # Adiciona botões ao button_frame
        ttk.Button(button_frame, text="Salvar Atendimento", command=self.save_atendimento).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Limpar Campos", command=lambda: self.clear_form(clear_all=True)).pack(side=tk.LEFT, padx=5) # Botão Limpar
        
        self.create_history_section()
        self.clear_form() # Chama clear_form sem argumentos inicialmente

    def create_section_frame(self, parent, text):
        frame = ttk.LabelFrame(parent, text=text, padding="10")
        frame.pack(fill="x", pady=5)
        frame.columnconfigure(1, weight=1); frame.columnconfigure(3, weight=1)
        return frame

    # Modificado para adicionar widget à lista se add_to_form_widgets=True
    def create_entry_field(self, parent, label, name, r, c, vcmd=None, columnspan=1, add_to_form_widgets=False):
        ttk.Label(parent, text=label).grid(row=r, column=c*2, padx=5, pady=2, sticky="w")
        entry = ttk.Entry(parent, validate="key", validatecommand=vcmd)
        entry.grid(row=r, column=c*2+1, padx=5, pady=2, sticky="ew", columnspan=columnspan)
        self.entries[name] = entry
        utils.setup_placeholder(entry, self.placeholders.get(name, ""))
        if add_to_form_widgets:
            self.form_widgets.append(entry)
        return entry

    # Modificado para adicionar widget à lista se add_to_form_widgets=True
    def create_combobox_field(self, parent, label, name, opts, r, c, add_to_form_widgets=False):
        ttk.Label(parent, text=label).grid(row=r, column=c*2, padx=5, pady=2, sticky="w")
        combo = ttk.Combobox(parent, values=opts, state="readonly")
        combo.grid(row=r, column=c*2+1, padx=5, pady=2, sticky="ew")
        self.comboboxes[name] = combo
        utils.setup_placeholder(combo, self.placeholders.get(name, ""))
        if add_to_form_widgets:
            self.form_widgets.append(combo)
        return combo

    def create_horario_field(self, parent, label, name, r, c):
        ttk.Label(parent, text=label).grid(row=r, column=c*2, padx=5, pady=2, sticky="w")
        frame = ttk.Frame(parent)
        frame.grid(row=r, column=c*2+1, padx=5, pady=2, sticky="ew")
        entry = ttk.Entry(frame); entry.pack(side="left", fill="x", expand=True)
        self.entries[name] = entry
        self.form_widgets.append(entry) # Adiciona à lista
        utils.setup_placeholder(entry, self.placeholders.get(name, ""))
        btn_agora = ttk.Button(frame, text="Agora", command=self.set_current_time)
        btn_agora.pack(side="left", padx=5)
        self.form_widgets.append(btn_agora) # Adiciona o botão também

    def create_queixa_section(self, parent):
        # Frame principal para todas as queixas
        queixa_frame = ttk.Frame(parent)
        queixa_frame.grid(row=0, column=0, columnspan=4, sticky="ew", pady=5)
        queixa_frame.columnconfigure(1, weight=1)
        queixa_frame.columnconfigure(3, weight=1)

        # --- Queixa Principal (Seleção Única) ---
        ttk.Label(queixa_frame, text="QP Sintoma:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        # Adiciona qp_sintoma à lista form_widgets (será removido depois)
        combo_qp_sintoma = self.create_combobox_field(queixa_frame, "", "qp_sintoma", SINTOMAS, 0, 0, add_to_form_widgets=True)
        combo_qp_sintoma.grid(row=0, column=1, sticky="ew")
        
        ttk.Label(queixa_frame, text="QP Região:").grid(row=0, column=2, padx=5, pady=2, sticky="w")
        # Adiciona qp_regiao à lista form_widgets
        combo_qp_regiao = self.create_combobox_field(queixa_frame, "", "qp_regiao", REGIOES, 0, 1, add_to_form_widgets=True)
        combo_qp_regiao.grid(row=0, column=3, sticky="ew")


        # --- Queixa Secundária (Múltipla Seleção) ---
        ttk.Label(queixa_frame, text="QS Sintomas:", font=("Arial", 10, "bold")).grid(row=1, column=0, padx=5, pady=(10, 2), sticky="nw")
        self.qs_sintomas_vars = self._create_checkable_frame(queixa_frame, SINTOMAS, 1, 1)
        
        ttk.Label(queixa_frame, text="QS Regiões:", font=("Arial", 10, "bold")).grid(row=1, column=2, padx=5, pady=(10, 2), sticky="nw")
        self.qs_regioes_vars = self._create_checkable_frame(queixa_frame, REGIOES, 1, 3)

    def _create_checkable_frame(self, parent, options, r, c):
        """Cria um frame com scroll e checkbuttons para uma lista de opções."""
        frame = ttk.Frame(parent, borderwidth=1, relief="sunken", height=100)
        frame.grid(row=r, column=c, sticky="nsew", padx=5, pady=2)
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        canvas = tk.Canvas(frame, height=100)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        vars_dict = {}
        options_filtered = [opt for opt in options if opt != "N/A"]
        
        for i, option in enumerate(options_filtered):
            var = tk.BooleanVar(value=False)
            chk = ttk.Checkbutton(scrollable_frame, text=option, variable=var)
            chk.pack(anchor="w", fill="x", padx=5)
            vars_dict[option] = var
            self.form_widgets.append(chk) # Adiciona O WIDGET (Checkbutton) à lista

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        return vars_dict


    def create_pa_section(self, parent, r, c):
        ttk.Label(parent, text="PA:").grid(row=r, column=c*2, padx=5, pady=2, sticky="w")
        frame = ttk.Frame(parent)
        frame.grid(row=r, column=c*2+1, padx=5, pady=2, sticky="ew")
        entry_sis = ttk.Entry(frame, width=5); entry_sis.pack(side="left")
        self.entries['pa_sistolica'] = entry_sis
        ttk.Label(frame, text="/").pack(side="left")
        entry_dia = ttk.Entry(frame, width=5); entry_dia.pack(side="left")
        self.entries['pa_diastolica'] = entry_dia
        
        # Adiciona PA à lista form_widgets
        self.form_widgets.extend([entry_sis, entry_dia])


    def create_history_section(self):
        history_frame = ttk.Frame(self); history_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        history_frame.columnconfigure(0, weight=1); history_frame.rowconfigure(1, weight=1)
        
        controls = ttk.Frame(history_frame); controls.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        ttk.Label(controls, text="Histórico:", font=("Arial", 14, "bold")).pack(side="left", padx=(0, 10))
        
        # Botão Atualizar Histórico
        ttk.Button(controls, text="Atualizar", command=self.refresh_history_tree).pack(side="left", padx=(0, 10))

        # Dropdown de Período
        self.history_period_var = tk.StringVar(value=PERIODO_15_DIAS)
        combo = ttk.Combobox(controls, textvariable=self.history_period_var, values=PERIODOS_FILTRO, state="readonly", width=12)
        combo.pack(side="right"); combo.bind("<<ComboboxSelected>>", self.refresh_history_tree)
        ttk.Label(controls, text="Período:").pack(side="right", padx=(0, 5))


        tree_frame = ttk.Frame(history_frame); tree_frame.grid(row=1, column=0, sticky="nsew")
        self.history_tree = ttk.Treeview(tree_frame, columns=("badge", "nome", "data_hora"), show="headings")
        self.history_tree.heading("badge", text="Badge"); self.history_tree.heading("nome", text="Nome"); self.history_tree.heading("data_hora", text="Data/Hora")
        self.history_tree.column("badge", width=80, anchor="center"); self.history_tree.column("nome", width=200); self.history_tree.column("data_hora", width=120)
        
        scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=scroll.set)
        self.history_tree.pack(side="left", fill="both", expand=True); scroll.pack(side="right", fill="y")
        self.history_tree.bind("<Double-1>", self.on_double_click_history)
        
        # Frame para botões abaixo do histórico
        history_button_frame = ttk.Frame(history_frame)
        history_button_frame.grid(row=2, column=0, pady=10, sticky='ew')
        
        ttk.Button(history_button_frame, text="Selecionar Banco de Dados", command=self.change_database).pack(side=tk.LEFT, padx=5)
        ttk.Button(history_button_frame, text="Exportar Dados", command=self.open_export_window).pack(side=tk.LEFT, padx=5)

    def set_current_time(self):
        if entry := self.entries.get("horario_medicao"):
            utils.clear_placeholder(entry, self.placeholders.get("horario_medicao", ""))
            entry.delete(0, tk.END)
            entry.insert(0, datetime.now().strftime("%H:%M"))
    
    def on_qp_sintoma_change(self, event=None):
        """Habilita/desabilita campos com base na QP selecionada."""
        sintoma = self.comboboxes["qp_sintoma"].get()
        
        # --- CORREÇÃO: Garante que qp_sintoma nunca seja desabilitado ---
        qp_sintoma_combo = self.comboboxes.get("qp_sintoma")

        if sintoma == "Absorvente":
            # Desabilita TUDO e preenche N/A
            for widget in self.form_widgets:
                 # Pula o próprio combobox qp_sintoma
                if widget != qp_sintoma_combo:
                    self.set_widget_state(widget, "disabled", "N/A")
        
        elif sintoma == "Trabalho em altura":
            # Desabilita tudo EXCETO PA e Resumo
            for widget in self.form_widgets:
                # Pula o próprio combobox qp_sintoma
                if widget == qp_sintoma_combo:
                    continue
                if widget in self.trabalho_altura_exceptions:
                    self.set_widget_state(widget, "normal", "") # Habilita exceções
                else:
                    self.set_widget_state(widget, "disabled", "N/A") # Desabilita o resto
        
        else:
            # Habilita TUDO
            for widget in self.form_widgets:
                # Pula o próprio combobox qp_sintoma
                if widget != qp_sintoma_combo:
                    self.set_widget_state(widget, "normal", "")

    def set_widget_state(self, widget, state, fill_value=""):
        """Define o estado (normal/disabled) e o valor de um widget."""
        try:
            # --- CORREÇÃO: Verifica se o widget existe antes de chamar winfo_class ---
            if not widget or not hasattr(widget, 'winfo_exists') or not widget.winfo_exists():
                return # Ignora se o widget foi destruído ou não é um widget válido

            widget_type = widget.winfo_class()
            
            if state == "disabled":
                if widget_type == "TEntry":
                    widget.config(state="normal") # Habilita temporariamente para limpar/inserir
                    widget.delete(0, tk.END)
                    widget.insert(0, fill_value)
                    widget.config(state="disabled")
                elif widget_type == "TCombobox":
                    # --- CORREÇÃO: Não desabilita se for qp_sintoma ---
                    if widget == self.comboboxes.get("qp_sintoma"):
                         widget.set(fill_value) # Apenas define o valor
                         widget.config(state="readonly") # Garante que permaneça readonly
                    else:
                        current_state = widget.cget("state")
                        widget.config(state="normal") # Permite alterar valor
                        widget.set(fill_value)
                        widget.config(state="disabled")

                elif widget_type == "TCheckbutton":
                    # Checkbuttons podem não ter getvar diretamente, acessamos a variável associada
                    var_name = str(widget.cget("variable")) # str() para garantir string
                    if var_name:
                         try:
                             # Tenta obter a variável Booleana do Tkinter associada
                             var = widget.getvar(var_name) # Pega o NOME da variável
                             # Assume que o nome é o mesmo que a chave em qs_sintomas_vars ou qs_regioes_vars
                             # Isso é frágil. Seria melhor armazenar a var diretamente com o widget.
                             
                             # Abordagem alternativa: Procurar a var nos dicionários
                             found_var = None
                             for d in [self.qs_sintomas_vars, self.qs_regioes_vars]:
                                 for key, v in d.items():
                                     if str(v) == var_name: # Compara representação string da variável
                                         found_var = v
                                         break
                                 if found_var: break
                             
                             if found_var and isinstance(found_var, tk.BooleanVar):
                                 found_var.set(False) # Desmarca a variável
                             else:
                                 # Fallback se não encontrar a variável (pode acontecer se a lógica mudar)
                                 # Tenta definir o estado visual diretamente (pode não funcionar perfeitamente)
                                 widget.state(['!selected'])

                         except (tk.TclError, AttributeError):
                             pass # Ignora erros ao obter/definir variável
                    widget.config(state="disabled") # Desabilita o widget Checkbutton
                elif widget_type == "TButton": # Trata o botão "Agora"
                    widget.config(state="disabled")
            
            else: # state == "normal"
                if widget_type == "TEntry":
                    # Limpa N/A se estava desabilitado, antes de habilitar
                    if widget.cget("state") == "disabled" and widget.get() == "N/A":
                        widget.config(state="normal")
                        widget.delete(0, tk.END)
                        # Reaplicar placeholder se necessário (utils.setup_placeholder)
                        for name, entry_widget in self.entries.items():
                            if entry_widget == widget:
                                utils.setup_placeholder(widget, self.placeholders.get(name, ""))
                                break
                    else:
                         widget.config(state="normal")

                elif widget_type == "TCombobox":
                     # Limpa N/A se estava desabilitado, antes de habilitar
                    if widget.cget("state") == "disabled" and widget.get() == "N/A":
                        widget.config(state="normal") # Permite alterar valor
                        widget.set("")
                        widget.config(state="readonly")
                        # Reaplicar placeholder
                        for name, combo_widget in self.comboboxes.items():
                            if combo_widget == widget:
                                utils.setup_placeholder(widget, self.placeholders.get(name, ""))
                                break
                    else:
                        # Garante que sempre seja readonly quando habilitado
                        widget.config(state="readonly")

                elif widget_type == "TCheckbutton":
                    widget.config(state="normal")
                elif widget_type == "TButton":
                    widget.config(state="normal")
        except tk.TclError as e:
            print(f"TclError in set_widget_state for {widget}: {e}") # Log erro
            pass # Ignora o erro silenciosamente

    def on_badge_number_change(self, event):
        badge_entry = self.entries.get('badge_number')
        if not badge_entry: return # Sai se o widget não existe
        
        badge = badge_entry.get()

        if not badge or badge == self.placeholders.get("badge_number"):
            # Limpa campos de ID (exceto badge) e restaura placeholders
            self.clear_form(clear_badge=False, clear_id_fields=True, clear_anamnese_conduta=False, restore_placeholders=True)
            return

        last_data = db.get_last_atendimento_by_badge(badge)
        if last_data:
            # NÃO limpa o formulário aqui. Apenas preenche os campos de ID.
            fields_to_fill = {'nome': 'nome', 'login': 'login', 'gestor': 'gestor', 'turno': 'turno',
                              'setor': 'setor', 'processo': 'processo', 'tenure': 'tenure'}

            for name, db_key in fields_to_fill.items():
                value = last_data.get(db_key, '') # Pega valor do dict retornado pelo DB
                widget = self.entries.get(name) or self.comboboxes.get(name)
                if widget:
                    current_placeholder = self.placeholders.get(name)
                    utils.clear_placeholder(widget, current_placeholder) # Limpa placeholder antes de inserir
                    if isinstance(widget, ttk.Combobox):
                        # Define valor se existir nas opções, senão limpa
                        if value in widget['values']:
                            widget.set(value)
                        else:
                            widget.set('')
                            if current_placeholder: utils.setup_placeholder(widget, current_placeholder) # Restaura placeholder se limpou
                    else: # É Entry
                        widget.delete(0, tk.END)
                        widget.insert(0, value if value else '') # Insere valor ou string vazia
                        if not value and current_placeholder: # Restaura placeholder se valor vazio
                            utils.setup_placeholder(widget, current_placeholder)

        else:
             # Se não encontrou 'last', limpa campos de ID (exceto badge)
             self.clear_form(clear_badge=False, clear_id_fields=True, clear_anamnese_conduta=False, restore_placeholders=True)

        self.refresh_history_tree() # Atualiza histórico independentemente de encontrar ou não
    
    def refresh_history_tree(self, event=None):
        # Adiciona um try-except para capturar erros durante a atualização
        try:
            for item in self.history_tree.get_children(): self.history_tree.delete(item)
            
            badge_entry = self.entries.get('badge_number')
            badge = badge_entry.get() if badge_entry else None
            badge = None if not badge or badge == self.placeholders.get("badge_number") else badge

            period = self.history_period_var.get()
            
            atendimentos = [] # Inicializa
            
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
                    # Verifica o número de elementos na tupla 'at' antes de acessar índices
                    at_id = at[0] if len(at) > 0 else "N/A"
                    badge_val = at[1] if len(at) > 1 else "N/A"
                    nome_val = at[2] if len(at) > 2 else "N/A"
                    data_val = at[4] if len(at) > 4 else "N/A"
                    hora_val = at[5] if len(at) > 5 else "N/A"
                    self.history_tree.insert("", "end", iid=at_id, values=(badge_val, nome_val, f"{data_val} {hora_val}"))
        except Exception as e:
            print(f"Erro ao atualizar histórico: {e}") # Loga o erro
            messagebox.showerror("Erro de Banco de Dados", f"Não foi possível carregar o histórico: {e}", parent=self)
            # Insere uma linha indicando o erro
            try: # Evita erro se a treeview já foi destruída
                if not self.history_tree.get_children(): # Só insere se estiver vazia
                    self.history_tree.insert("", "end", values=("Erro ao carregar", "", ""))
            except tk.TclError:
                 pass # Ignora se a treeview não existe mais
    
    def on_double_click_history(self, event):
        if item := self.history_tree.selection():
            try: EditWindow(self, int(item[0]), self.refresh_history_tree)
            except (ValueError, IndexError): pass
            
    def save_atendimento(self):
        try:
            badge_entry = self.entries.get('badge_number')
            badge = badge_entry.get() if badge_entry else None
            if not badge or badge == self.placeholders.get('badge_number'):
                return messagebox.showerror("Erro", "Badge Number é obrigatório.")

            data = {}
            for k, w in {**self.entries, **self.comboboxes}.items():
                val = w.get() if w.get() != self.placeholders.get(k, '') else "" 
                # Se o campo estiver desabilitado E for N/A, mantém N/A, senão usa o valor (ou N/A se vazio)
                try:
                     state = w.cget('state')
                     if state == 'disabled' and val == "N/A":
                         data[k] = "N/A"
                     else:
                         data[k] = val if val else "N/A"
                except tk.TclError: # Caso get Cget falhe (ex: widget destruído)
                     data[k] = val if val else "N/A"

            
            # --- Coleta de Queixas (MODIFICADO) ---
            qp_sintoma = data.get("qp_sintoma", "N/A")
            qp_regiao = data.get("qp_regiao", "N/A")
            
            qs_sintomas_list = [q for q, v in self.qs_sintomas_vars.items() if v.get()]
            qs_regioes_list = [r for r, v in self.qs_regioes_vars.items() if v.get()]
            
            qs_sintomas_json = json.dumps(qs_sintomas_list)
            qs_regioes_json = json.dumps(qs_regioes_list)
            # --- Fim da Coleta de Queixas ---

            now = datetime.now()
            
            conduta_data = {
                'hipotese_diagnostica': data.get('hipotese_diagnostica', 'N/A'),
                'resumo_conduta': data.get('resumo_conduta', 'N/A'),
                'medicamento_administrado': data.get('medicamento_administrado', 'N/A'),
                'posologia': data.get('posologia', 'N/A'),
                'horario_medicacao': data.get('horario_medicao', 'N/A'),
                'observacoes': data.get('conduta_obs', 'N/A')
            }

            atendimento_data = {k:v for k,v in data.items() if k not in conduta_data and k not in ["conduta_obs", "qp_sintoma", "qp_regiao"]}

            atendimento = Atendimento(
                **atendimento_data,
                qp_sintoma=qp_sintoma,
                qp_regiao=qp_regiao,
                qs_sintomas=qs_sintomas_json,
                qs_regioes=qs_regioes_json,
                condutas=[Conduta(**conduta_data)],
                data_atendimento=now.strftime("%Y-%m-%d"),
                hora_atendimento=now.strftime("%H:%M:%S"),
                semana_iso=now.isocalendar()[1]
            )
            db.save_atendimento(atendimento)
            messagebox.showinfo("Sucesso", "Atendimento salvo!")
            self.clear_form(clear_all=True); self.refresh_history_tree() # Limpa tudo após salvar
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro ao salvar o atendimento: {e}")
            print(f"Erro detalhado ao salvar: {e}") # Log para depuração
            import traceback
            traceback.print_exc() # Imprime traceback detalhado

    # --- CORREÇÃO: Lógica clear_form revisada ---
    def clear_form(self, clear_all=False, clear_badge=False, clear_id_fields=False, clear_anamnese_conduta=True, restore_placeholders=True):
        """Limpa os campos do formulário com mais controle."""

        # Campos de identificação (exceto badge)
        id_fields_no_badge = ["nome", "login", "gestor", "turno", "setor", "processo", "tenure"]
        
        # Se clear_all ou clear_id_fields, limpa campos de ID
        if clear_all or clear_id_fields:
            for name in id_fields_no_badge:
                if widget := self.entries.get(name):
                    utils.clear_placeholder(widget, self.placeholders.get(name, ""))
                    if restore_placeholders: utils.setup_placeholder(widget, self.placeholders.get(name, ""))
                if widget := self.comboboxes.get(name):
                    utils.clear_placeholder(widget, self.placeholders.get(name, ""))
                    if restore_placeholders: utils.setup_placeholder(widget, self.placeholders.get(name, ""))

        # Se clear_all ou clear_badge, limpa o badge
        if clear_all or clear_badge:
             if widget := self.entries.get("badge_number"):
                utils.clear_placeholder(widget, self.placeholders.get("badge_number", ""))
                if restore_placeholders: utils.setup_placeholder(widget, self.placeholders.get("badge_number", ""))

        # Se clear_all ou clear_anamnese_conduta, limpa o resto
        if clear_all or clear_anamnese_conduta:
            # Todos os campos exceto os de identificação
            fields_to_clear = [
                k for k in self.entries if k not in id_fields_no_badge and k != "badge_number"
            ] + [
                k for k in self.comboboxes if k not in id_fields_no_badge
            ]

            for name in fields_to_clear:
                if widget := self.entries.get(name):
                    utils.clear_placeholder(widget, self.placeholders.get(name, ""))
                    if restore_placeholders: utils.setup_placeholder(widget, self.placeholders.get(name, ""))
                if widget := self.comboboxes.get(name):
                    # Garante que qp_sintoma não seja limpo aqui se a intenção for apenas limpar anamnese/conduta
                    if name != "qp_sintoma" or clear_all:
                        utils.clear_placeholder(widget, self.placeholders.get(name, ""))
                        if restore_placeholders: utils.setup_placeholder(widget, self.placeholders.get(name, ""))


            # Limpa checkbuttons
            for var in self.qs_sintomas_vars.values(): var.set(False)
            for var in self.qs_regioes_vars.values(): var.set(False)
        
        # Garante que os campos sejam reabilitados (exceto se chamado com clear_all=True após salvar)
        if hasattr(self, 'form_widgets') and self.form_widgets:
             # Sempre reabilita tudo, a função on_qp_sintoma_change cuidará de desabilitar se necessário
             for widget in self.form_widgets:
                 # Reabilita apenas se o widget ainda existir
                 if widget and hasattr(widget, 'winfo_exists') and widget.winfo_exists():
                     self.set_widget_state(widget, "normal", "")
             # Chama on_qp_sintoma_change para aplicar o estado correto baseado na seleção atual
             self.on_qp_sintoma_change()

    # Função para ser chamada pelo botão/menu "Selecionar Banco de Dados"
    def change_database(self):
        new_path = main.select_database_path(initial=False) # Chama a função do main.py
        if new_path:
            try:
                # Re-define o path e re-inicializa
                if db.init_db(): # Verifica/cria tabelas no novo DB
                     self.refresh_history_tree() # Atualiza o histórico
                     self.clear_form(clear_all=True) # Limpa o formulário
                     messagebox.showinfo("Banco de Dados Alterado", f"Aplicação agora usando:\n{new_path}", parent=self)
                else:
                     messagebox.showerror("Erro", "Não foi possível inicializar o novo banco de dados.", parent=self)
            except Exception as e:
                 messagebox.showerror("Erro ao Recarregar", f"Erro ao tentar usar o novo banco de dados: {e}", parent=self)


    def open_export_window(self): ExportWindow(self)


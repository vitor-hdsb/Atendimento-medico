import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
import db
import utils
from models import Atendimento, Conduta
from gui.edit_window import EditWindow
from gui.export_window import ExportWindow
from gui.constants import OPTIONS, SINTOMAS, REGIOES, load_options # Importa load_options
from gui.options_editor_window import OptionsEditorWindow # Importa a nova janela
import sqlite3
import json
import main

# Constantes para os períodos do filtro (mantido)
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
        self.qs_sintomas_vars = {}
        self.qs_regioes_vars = {}
        self.form_widgets = []

        self.create_widgets()
        self.refresh_history_tree()
        self.setup_menu() # Chama a função para criar o menu

    def setup_menu(self):
        """Cria a barra de menu da aplicação."""
        menu_bar = tk.Menu(self)

        # Menu Arquivo
        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Selecionar Banco de Dados...", command=self.change_database)
        file_menu.add_separator()
        file_menu.add_command(label="Sair", command=self.quit)
        menu_bar.add_cascade(label="Arquivo", menu=file_menu)

        # --- NOVO: Menu Configurações ---
        config_menu = tk.Menu(menu_bar, tearoff=0)
        config_menu.add_command(label="Editar Opções das Listas...", command=self.open_options_editor)
        menu_bar.add_cascade(label="Configurações", menu=config_menu)

        self.config(menu=menu_bar)

    def open_options_editor(self):
        """Abre a janela para editar as opções das comboboxes."""
        # Passa self.update_combobox_options como callback
        OptionsEditorWindow(self, update_callback=self.update_combobox_options)

    def update_combobox_options(self):
        """Recarrega as opções do arquivo e atualiza as comboboxes."""
        global OPTIONS # Precisa modificar a global OPTIONS
        OPTIONS = load_options() # Recarrega as opções do arquivo constants.py (que agora lê o JSON)

        # Atualiza os valores das comboboxes relevantes
        combos_to_update = {
            "gestor": "gestores",
            "turno": "turnos",
            "setor": "setores",
            "processo": "processos"
            # Adicione outras comboboxes se necessário (resumo, medicamento?)
            # Elas já são fixas em constants.py, então não precisam ser atualizadas
        }

        for combo_name, options_key in combos_to_update.items():
            if combo_widget := self.comboboxes.get(combo_name):
                current_value = combo_widget.get() # Salva o valor atual
                # Atualiza a lista de valores
                new_values = OPTIONS.get(options_key, [])
                combo_widget['values'] = new_values
                # Tenta restaurar o valor selecionado se ainda existir na nova lista
                if current_value in new_values:
                    combo_widget.set(current_value)
                else:
                    # Se o valor antigo não existe mais, limpa e aplica placeholder
                    placeholder = self.placeholders.get(combo_name, "Selecione")
                    utils.clear_placeholder(combo_widget, placeholder)
                    utils.setup_placeholder(combo_widget, placeholder)

        print("Opções das comboboxes atualizadas.")


    def create_widgets(self):
        # ... (restante do código create_widgets permanece o mesmo da versão anterior) ...
        # ... (Certifique-se que create_combobox_field usa OPTIONS[key] para pegar os valores) ...

        self.columnconfigure(0, weight=1); self.columnconfigure(1, weight=1); self.rowconfigure(0, weight=1)

        form_frame = ttk.Frame(self, padding="10")
        form_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        form_frame.columnconfigure(1, weight=1)

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

        id_frame = self.create_section_frame(form_frame, "Identificação do paciente")
        anamnese_frame = self.create_section_frame(form_frame, "Anamnese")
        conduta_frame = self.create_section_frame(form_frame, "Conduta de Enfermagem")

        self.create_entry_field(id_frame, "Badge Number:", "badge_number", 0, 0, vcmd_int)
        self.create_entry_field(id_frame, "Nome:", "nome", 0, 1)
        self.create_entry_field(id_frame, "Login:", "login", 1, 0)
        # --- Modificação: Usa OPTIONS carregado ---
        self.create_combobox_field(id_frame, "Gestor:", "gestor", OPTIONS.get("gestores", []), 1, 1)
        self.create_combobox_field(id_frame, "Turno:", "turno", OPTIONS.get("turnos", []), 2, 0)
        self.create_combobox_field(id_frame, "Setor:", "setor", OPTIONS.get("setores", []), 2, 1)
        self.create_combobox_field(id_frame, "Processo:", "processo", OPTIONS.get("processos", []), 3, 0)
        # --- Fim Modificação ---
        self.create_entry_field(id_frame, "Tenure:", "tenure", 3, 1)
        self.entries['badge_number'].bind("<KeyRelease>", self.on_badge_number_change)

        self.create_queixa_section(anamnese_frame)
        self.create_entry_field(anamnese_frame, "HQA:", "hqa", 2, 0, columnspan=3, add_to_form_widgets=True)
        self.create_entry_field(anamnese_frame, "TAX:", "tax", 3, 0, add_to_form_widgets=True)
        self.create_pa_section(anamnese_frame, 3, 1)
        self.create_entry_field(anamnese_frame, "FC:", "fc", 4, 0, add_to_form_widgets=True)
        self.create_entry_field(anamnese_frame, "SAT:", "sat", 4, 1, add_to_form_widgets=True)
        self.create_entry_field(anamnese_frame, "Doenças pré-existentes:", "doencas_preexistentes", 5, 0, columnspan=3, add_to_form_widgets=True)
        self.create_entry_field(anamnese_frame, "Alergias:", "alergias", 6, 0, columnspan=3, add_to_form_widgets=True)
        self.create_entry_field(anamnese_frame, "Medicamentos em uso:", "medicamentos_em_uso", 7, 0, columnspan=3, add_to_form_widgets=True)
        self.create_entry_field(anamnese_frame, "Observações:", "observacoes", 8, 0, columnspan=3, add_to_form_widgets=True)

        self.create_entry_field(conduta_frame, "Hipótese:", "hipotese_diagnostica", 0, 1, add_to_form_widgets=True)
        # --- Modificação: Usa OPTIONS carregado ---
        self.create_combobox_field(conduta_frame, "Resumo:", "resumo_conduta", OPTIONS.get("resumo_conduta", []), 2, 0, add_to_form_widgets=True)
        self.create_combobox_field(conduta_frame, "Medicação:", "medicamento_administrado", OPTIONS.get("medicamento_admin", []), 2, 1, add_to_form_widgets=True)
        # --- Fim Modificação ---
        self.create_entry_field(conduta_frame, "Posologia:", "posologia", 3, 0, vcmd=vcmd_posologia, add_to_form_widgets=True)
        self.create_horario_field(conduta_frame, "Horário:", "horario_medicao", 3, 1)
        self.create_entry_field(conduta_frame, "Obs:", "conduta_obs", 4, 0, columnspan=3, add_to_form_widgets=True)

        self.trabalho_altura_exceptions = {
            self.entries["pa_sistolica"],
            self.entries["pa_diastolica"],
            self.comboboxes["resumo_conduta"]
        }

        if self.comboboxes.get("qp_sintoma") in self.form_widgets:
            self.form_widgets.remove(self.comboboxes.get("qp_sintoma"))

        self.comboboxes["qp_sintoma"].bind("<<ComboboxSelected>>", self.on_qp_sintoma_change)

        ttk.Button(button_frame, text="Salvar Atendimento", command=self.save_atendimento).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Limpar Campos", command=lambda: self.clear_form(clear_all=True)).pack(side=tk.LEFT, padx=5)

        self.create_history_section()
        self.clear_form()

    # ... (O resto das funções de MainWindow permanecem as mesmas da versão anterior) ...
    # create_section_frame, create_entry_field, create_combobox_field, etc.
    # on_badge_number_change, save_atendimento, clear_form, etc.
    # A única mudança necessária foi em create_widgets para usar OPTIONS.get()

    def create_section_frame(self, parent, text):
        # Versão original do padding e colunas
        frame = ttk.LabelFrame(parent, text=text, padding="10")
        frame.pack(fill="x", pady=5)
        frame.columnconfigure(1, weight=1); frame.columnconfigure(3, weight=1)
        return frame

    # Modificado para adicionar widget à lista se add_to_form_widgets=True
    def create_entry_field(self, parent, label, name, r, c, vcmd=None, columnspan=1, add_to_form_widgets=False):
        # Versão original do grid
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
        # Versão original do grid
        ttk.Label(parent, text=label).grid(row=r, column=c*2, padx=5, pady=2, sticky="w")
        # --- Usa opts passados como argumento ---
        combo = ttk.Combobox(parent, values=opts, state="readonly")
        combo.grid(row=r, column=c*2+1, padx=5, pady=2, sticky="ew")
        self.comboboxes[name] = combo
        utils.setup_placeholder(combo, self.placeholders.get(name, ""))
        if add_to_form_widgets:
            self.form_widgets.append(combo)
        return combo

    def create_horario_field(self, parent, label, name, r, c):
        # Versão original do grid
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
        queixa_frame.grid(row=0, column=0, columnspan=4, sticky="ew", pady=5) # columnspan=4 original
        queixa_frame.columnconfigure(1, weight=1)
        queixa_frame.columnconfigure(3, weight=1)


        # --- Queixa Principal (Seleção Única) ---
        ttk.Label(queixa_frame, text="QP Sintoma:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        # Passa False explicitamente
        combo_qp_sintoma = self.create_combobox_field(queixa_frame, "", "qp_sintoma", SINTOMAS, 0, 0, add_to_form_widgets=False)
        combo_qp_sintoma.grid(row=0, column=1, sticky="ew", padx=5) # padx adicionado

        ttk.Label(queixa_frame, text="QP Região:").grid(row=0, column=2, padx=5, pady=2, sticky="w") # padx adicionado
        # Adiciona qp_regiao à lista form_widgets
        combo_qp_regiao = self.create_combobox_field(queixa_frame, "", "qp_regiao", REGIOES, 0, 1, add_to_form_widgets=True)
        combo_qp_regiao.grid(row=0, column=3, sticky="ew", padx=5) # padx adicionado


        # --- Queixa Secundária (Múltipla Seleção) ---
        ttk.Label(queixa_frame, text="QS Sintomas:", font=("Arial", 10, "bold")).grid(row=1, column=0, padx=5, pady=(10, 2), sticky="nw")
        # Layout original com grid/pack
        qs_sintoma_frame, self.qs_sintomas_vars = self._create_checkable_frame(queixa_frame, SINTOMAS)
        qs_sintoma_frame.grid(row=1, column=1, sticky="nsew", padx=5, pady=(10, 2))

        ttk.Label(queixa_frame, text="QS Regiões:", font=("Arial", 10, "bold")).grid(row=1, column=2, padx=5, pady=(10, 2), sticky="nw")
        qs_regiao_frame, self.qs_regioes_vars = self._create_checkable_frame(queixa_frame, REGIOES)
        qs_regiao_frame.grid(row=1, column=3, sticky="nsew", padx=5, pady=(10, 2))


    def _create_checkable_frame(self, parent, options):
        """Cria um frame com scroll e checkbuttons para uma lista de opções."""
        # Frame original sem tamanho fixo
        frame = ttk.Frame(parent, borderwidth=1, relief="sunken")
        # frame.grid(row=r, column=c, sticky="nsew", padx=5, pady=2) # Grid era feito fora
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        canvas = tk.Canvas(frame, height=100) # Altura original
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
            chk.pack(anchor="w", fill="x", padx=5) # Pack original
            vars_dict[option] = var
            self.form_widgets.append(chk) # Adiciona O WIDGET (Checkbutton) à lista

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        return frame, vars_dict # Retorna o frame principal e o dict


    def create_pa_section(self, parent, r, c):
        # Grid original
        ttk.Label(parent, text="PA:").grid(row=r, column=c*2, padx=5, pady=2, sticky="w")
        frame = ttk.Frame(parent)
        frame.grid(row=r, column=c*2+1, padx=5, pady=2, sticky="ew")
        # Validação original ausente
        entry_sis = ttk.Entry(frame, width=5); entry_sis.pack(side="left")
        self.entries['pa_sistolica'] = entry_sis
        ttk.Label(frame, text="/").pack(side="left") # Sem padx original
        entry_dia = ttk.Entry(frame, width=5); entry_dia.pack(side="left")
        self.entries['pa_diastolica'] = entry_dia

        # Adiciona PA à lista form_widgets
        self.form_widgets.extend([entry_sis, entry_dia])


    def create_history_section(self, parent_frame=None): # Volta a não precisar do parent_frame
        # Grid original direto em self
        history_frame = ttk.Frame(self); history_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        history_frame.columnconfigure(0, weight=1); history_frame.rowconfigure(1, weight=1)

        controls = ttk.Frame(history_frame); controls.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        ttk.Label(controls, text="Histórico:", font=("Arial", 14, "bold")).pack(side="left") # Sem padx original

        # Botão Atualizar Histórico
        ttk.Button(controls, text="Atualizar", command=self.refresh_history_tree).pack(side="left", padx=(10, 0)) # Padding ajustado

        # Dropdown de Período
        self.history_period_var = tk.StringVar(value=PERIODO_15_DIAS)
        combo = ttk.Combobox(controls, textvariable=self.history_period_var, values=PERIODOS_FILTRO, state="readonly", width=12)
        combo.pack(side="right"); combo.bind("<<ComboboxSelected>>", self.refresh_history_tree)
        # Label Período volta a ficar implícito ou antes do combo
        ttk.Label(controls, text="Período:").pack(side="right", padx=(0, 5)) # Adiciona label de volta


        tree_frame = ttk.Frame(history_frame); tree_frame.grid(row=1, column=0, sticky="nsew")
        # Expansão original
        # tree_frame.rowconfigure(0, weight=1); tree_frame.columnconfigure(0, weight=1)

        self.history_tree = ttk.Treeview(tree_frame, columns=("badge", "nome", "data_hora"), show="headings")
        self.history_tree.heading("badge", text="Badge"); self.history_tree.heading("nome", text="Nome"); self.history_tree.heading("data_hora", text="Data/Hora")
        # Larguras originais
        self.history_tree.column("badge", width=80, anchor="center")
        self.history_tree.column("nome", width=200)
        self.history_tree.column("data_hora", width=120)

        scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=scroll.set)
        # Pack original
        self.history_tree.pack(side="left", fill="both", expand=True); scroll.pack(side="right", fill="y")

        self.history_tree.bind("<Double-1>", self.on_double_click_history)

        # Frame original para botões abaixo do histórico
        history_button_frame = ttk.Frame(history_frame)
        history_button_frame.grid(row=2, column=0, pady=10) # Sem sticky='ew'

        ttk.Button(history_button_frame, text="Selecionar Banco de Dados", command=self.change_database).pack(side=tk.LEFT, padx=5)
        ttk.Button(history_button_frame, text="Exportar Dados", command=self.open_export_window).pack(side=tk.LEFT, padx=5)

    def set_current_time(self):
        if entry := self.entries.get("horario_medicao"):
            utils.clear_placeholder(entry, self.placeholders.get("horario_medicao", ""))
            entry.delete(0, tk.END)
            entry.insert(0, datetime.now().strftime("%H:%M"))

    def on_qp_sintoma_change(self, event=None):
        """Habilita/desabilita campos com base na QP selecionada."""
        qp_sintoma_combo = self.comboboxes.get("qp_sintoma")
        sintoma = qp_sintoma_combo.get() if qp_sintoma_combo else None

        # --- CORREÇÃO: Garante que qp_sintoma NUNCA seja desabilitado ---
        if qp_sintoma_combo:
            qp_sintoma_combo.config(state="readonly") # Garante que está sempre ativo

        if sintoma == "Absorvente":
            for widget in self.form_widgets:
                 # Pula o próprio combobox qp_sintoma
                if widget != qp_sintoma_combo:
                    self.set_widget_state(widget, "disabled", "N/A")

        elif sintoma == "Trabalho em altura":
            for widget in self.form_widgets:
                # Pula o próprio combobox qp_sintoma
                if widget == qp_sintoma_combo:
                    continue
                if widget in self.trabalho_altura_exceptions:
                    self.set_widget_state(widget, "normal", "") # Habilita exceções
                else:
                    self.set_widget_state(widget, "disabled", "N/A") # Desabilita o resto

        else:
            # Habilita TUDO (exceto qp_sintoma que já está readonly)
            for widget in self.form_widgets:
                if widget != qp_sintoma_combo:
                    self.set_widget_state(widget, "normal", "")

    def set_widget_state(self, widget, state, fill_value=""):
        """Define o estado (normal/disabled/readonly) e o valor de um widget."""
        try:
            if not widget or not hasattr(widget, 'winfo_exists') or not widget.winfo_exists():
                return

            widget_type = widget.winfo_class()
            current_state = widget.cget("state")

            if state == "disabled":
                if widget_type == "TEntry":
                    widget.config(state="normal")
                    widget.delete(0, tk.END)
                    widget.insert(0, fill_value)
                    widget.config(state="disabled")
                elif widget_type == "TCombobox":
                    # --- CORREÇÃO IMPORTANTE: Não desabilita qp_sintoma ---
                    if widget == self.comboboxes.get("qp_sintoma"):
                         if fill_value == "N/A": widget.set(self.placeholders.get("qp_sintoma", "Selecione"))
                         widget.config(state="readonly") # Garante
                    else:
                        widget.config(state="normal")
                        widget.set(fill_value)
                        widget.config(state="disabled")

                elif widget_type == "TCheckbutton":
                    # Desmarca a variável associada
                    var_name = str(widget.cget("variable"))
                    found_var = None
                    for d in [self.qs_sintomas_vars, self.qs_regioes_vars]:
                        for key, v in d.items():
                            if str(v) == var_name:
                                found_var = v
                                break
                        if found_var: break
                    if found_var and isinstance(found_var, tk.BooleanVar):
                        found_var.set(False)
                    widget.config(state="disabled")
                elif widget_type == "TButton":
                    widget.config(state="disabled")

            else: # state == "normal" (ou "readonly" para comboboxes)
                target_state = "readonly" if widget_type == "TCombobox" else "normal"

                # Só altera se o estado atual for diferente do desejado
                if current_state != target_state:
                    widget.config(state=target_state)

                # Limpa "N/A" apenas se estava previamente desabilitado
                if current_state == "disabled":
                     placeholder = ""
                     widget_name_part = ""
                     # Mapeamento simplificado para placeholder
                     placeholder_map = self.placeholders

                     entry_match = next((name for name, w in self.entries.items() if w == widget), None)
                     combo_match = next((name for name, w in self.comboboxes.items() if w == widget), None)

                     if entry_match:
                         widget_name_part = entry_match
                         placeholder = placeholder_map.get(widget_name_part, "")
                     elif combo_match:
                          widget_name_part = combo_match
                          placeholder = placeholder_map.get(widget_name_part, "Selecione") # Default combo placeholder


                     if widget_type == "TEntry" and widget.get() == "N/A":
                        widget.config(state="normal"); widget.delete(0, tk.END)
                        widget.config(state=target_state)
                        if placeholder: utils.setup_placeholder(widget, placeholder)

                     elif widget_type == "TCombobox" and widget.get() == "N/A":
                        if widget != self.comboboxes.get("qp_sintoma"):
                            widget.config(state="normal"); widget.set("")
                            widget.config(state=target_state)
                            if placeholder: utils.setup_placeholder(widget, placeholder)
        except tk.TclError as e:
            print(f"TclError in set_widget_state for {widget}: {e}")
            pass

    def on_badge_number_change(self, event):
        badge_entry = self.entries.get('badge_number')
        if not badge_entry: return

        badge = badge_entry.get()

        # --- CORREÇÃO: Não limpar o campo badge ao preencher os outros ---
        if not badge or badge == self.placeholders.get("badge_number"):
            self.clear_form(clear_badge=False, clear_id_fields=True, clear_anamnese_conduta=False, restore_placeholders=True)
            self.refresh_history_tree() # Atualiza mesmo se limpar
            return # Sai se o badge estiver vazio ou for placeholder

        last_data = db.get_last_atendimento_by_badge(badge)
        if last_data:
            fields_to_fill = {'nome': 'nome', 'login': 'login', 'gestor': 'gestor', 'turno': 'turno',
                              'setor': 'setor', 'processo': 'processo', 'tenure': 'tenure'}

            for name, db_key in fields_to_fill.items():
                value = last_data.get(db_key, '')
                widget = self.entries.get(name) or self.comboboxes.get(name)
                if widget:
                    current_placeholder = self.placeholders.get(name)
                    utils.clear_placeholder(widget, current_placeholder)
                    if isinstance(widget, ttk.Combobox):
                        if value in widget['values']:
                            widget.set(value)
                        else:
                            widget.set('')
                            if current_placeholder: utils.setup_placeholder(widget, current_placeholder)
                    else: # É Entry
                        widget.delete(0, tk.END)
                        widget.insert(0, value if value else '')
                        # Restaura placeholder APENAS se o valor for realmente vazio
                        if not value and current_placeholder:
                             utils.setup_placeholder(widget, current_placeholder)
                         # Garante que o placeholder seja removido se houver valor
                        elif value:
                             utils.remove_placeholder_on_fill(widget, current_placeholder)


        else:
             self.clear_form(clear_badge=False, clear_id_fields=True, clear_anamnese_conduta=False, restore_placeholders=True)

        self.refresh_history_tree()

    def refresh_history_tree(self, event=None):
        try:
            for item in self.history_tree.get_children(): self.history_tree.delete(item)

            badge_entry = self.entries.get('badge_number')
            badge = badge_entry.get() if badge_entry else None
            badge = None if not badge or badge == self.placeholders.get("badge_number") else badge

            period = self.history_period_var.get()

            atendimentos = []

            if period == PERIODO_ESCALA_ATUAL:
                now = datetime.now()
                if 7 <= now.hour < 19:
                    start_dt = now.replace(hour=7, minute=0, second=0, microsecond=0)
                    end_dt = now.replace(hour=18, minute=59, second=59, microsecond=999999)
                else:
                    if now.hour >= 19:
                        start_dt = now.replace(hour=19, minute=0, second=0, microsecond=0)
                        end_dt = (now + timedelta(days=1)).replace(hour=6, minute=59, second=59, microsecond=999999)
                    else:
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
                    at_id = at[0] if len(at) > 0 else "N/A"
                    badge_val = at[1] if len(at) > 1 else "N/A"
                    nome_val = at[2] if len(at) > 2 else "N/A"
                    data_val = at[4] if len(at) > 4 else "N/A"
                    hora_val = at[5] if len(at) > 5 else "N/A"
                    self.history_tree.insert("", "end", iid=at_id, values=(badge_val, nome_val, f"{data_val} {hora_val}"))
        except Exception as e:
            print(f"Erro ao atualizar histórico: {e}")
            messagebox.showerror("Erro de Banco de Dados", f"Não foi possível carregar o histórico: {e}", parent=self)
            try:
                if not self.history_tree.get_children():
                    self.history_tree.insert("", "end", values=("Erro ao carregar", "", ""))
            except tk.TclError:
                 pass

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
                 if not w or not hasattr(w, 'winfo_exists') or not w.winfo_exists(): continue

                 val = w.get() if hasattr(w, 'get') else ""
                 placeholder = self.placeholders.get(k, '')
                 val = "" if val == placeholder else val

                 try:
                     state = w.cget('state')
                     if state == 'disabled' and val == "N/A":
                         data[k] = "N/A"
                     else:
                         data[k] = val if val else "N/A"
                 except tk.TclError:
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
            self.clear_form(clear_all=True); self.refresh_history_tree()
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro ao salvar o atendimento: {e}")
            print(f"Erro detalhado ao salvar: {e}")
            import traceback
            traceback.print_exc()

    def clear_form(self, clear_all=False, clear_badge=False, clear_id_fields=False, clear_anamnese_conduta=True, restore_placeholders=True):
        """Limpa os campos do formulário com mais controle."""

        id_fields_no_badge = ["nome", "login", "gestor", "turno", "setor", "processo", "tenure"]

        if clear_all or clear_id_fields:
            for name in id_fields_no_badge:
                widget = self.entries.get(name) or self.comboboxes.get(name)
                if widget:
                    utils.clear_placeholder(widget, self.placeholders.get(name, ""))
                    if restore_placeholders: utils.setup_placeholder(widget, self.placeholders.get(name, ""))

        if clear_all or clear_badge:
             widget = self.entries.get("badge_number")
             if widget:
                utils.clear_placeholder(widget, self.placeholders.get("badge_number", ""))
                if restore_placeholders: utils.setup_placeholder(widget, self.placeholders.get("badge_number", ""))

        if clear_all or clear_anamnese_conduta:
            fields_to_clear = [
                k for k in self.entries if k not in id_fields_no_badge and k != "badge_number"
            ] + [
                k for k in self.comboboxes if k not in id_fields_no_badge
            ]

            for name in fields_to_clear:
                 widget = self.entries.get(name) or self.comboboxes.get(name)
                 if widget:
                    # Não limpa qp_sintoma se a intenção for apenas limpar anamnese/conduta
                    if name != "qp_sintoma" or clear_all:
                         utils.clear_placeholder(widget, self.placeholders.get(name, ""))
                         if restore_placeholders: utils.setup_placeholder(widget, self.placeholders.get(name, ""))


            for var in self.qs_sintomas_vars.values(): var.set(False)
            for var in self.qs_regioes_vars.values(): var.set(False)

        # Garante que os campos sejam reabilitados (exceto se controlado por qp_sintoma)
        if hasattr(self, 'form_widgets') and self.form_widgets:
            # Chama on_qp_sintoma_change para aplicar o estado correto baseado na seleção atual (ou falta dela)
             self.on_qp_sintoma_change()


    def change_database(self):
        new_path = main.select_database_path(initial=False, parent_window=self) # Passa self como parent
        if new_path:
            try:
                if db.init_db():
                     self.refresh_history_tree()
                     self.clear_form(clear_all=True)
                     messagebox.showinfo("Banco de Dados Alterado", f"Aplicação agora usando:\n{new_path}", parent=self)
                else:
                     messagebox.showerror("Erro", "Não foi possível inicializar o novo banco de dados.", parent=self)
            except Exception as e:
                 messagebox.showerror("Erro ao Recarregar", f"Erro ao tentar usar o novo banco de dados: {e}", parent=self)


    def open_export_window(self): ExportWindow(self)


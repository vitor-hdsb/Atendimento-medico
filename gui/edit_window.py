import tkinter as tk
from tkinter import ttk, messagebox
from models import Atendimento, Conduta
import db
import utils
from typing import List, Optional
from datetime import datetime
from gui.constants import OPTIONS, SINTOMAS, REGIOES # Importa constantes
import json # Para carregar/salvar listas JSON

class EditWindow(tk.Toplevel):
    def __init__(self, parent, atendimento_id, callback):
        super().__init__(parent)
        self.parent = parent
        self.atendimento_id = atendimento_id
        self.callback = callback
        self.title("Editar Atendimento")
        self.geometry("1050x750") # Tamanho original
        self.resizable(False, False) # Original
        self.changed = False
        self.condutas_frames = []

        self.entries = {}
        self.comboboxes = {}
        # Para queixas na edit window
        self.qs_sintomas_vars = {}
        self.qs_regioes_vars = {}
        self.form_widgets = [] # Widgets a serem desabilitados

        # Layout principal com barra de botões fixa
        self.button_frame = ttk.Frame(self, padding=(10, 5, 10, 10)) # Padding original
        self.button_frame.pack(side="bottom", fill="x") # Sem pady/padx extra

        container = ttk.Frame(self)
        container.pack(side="top", fill="both", expand=True) # Sem pady/padx extra

        self.canvas = tk.Canvas(container, borderwidth=0)
        v_scrollbar = ttk.Scrollbar(container, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=v_scrollbar.set)

        self.scrollable_frame = ttk.Frame(self.canvas) # Padding original ausente
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        self.scrollable_frame.bind("<Configure>", self._on_frame_configure)
        v_scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.bind_mousewheel(self.canvas)
        self.bind_mousewheel_recursive(self.scrollable_frame) # Mantém bind recursivo


        self.setup_ui()
        self.load_data()

        # Configura peso da coluna principal do scrollable_frame (mantido)
        # self.scrollable_frame.columnconfigure(0, weight=1) # Pode não ser necessário


    def _on_frame_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        # Ajuste original da largura
        self.canvas.itemconfig(self.canvas_window, width=self.canvas.winfo_width()) # Volta ao ajuste original

    # --- Funções de bind do mousewheel mantidas ---
    def bind_mousewheel_recursive(self, widget):
        self.bind_mousewheel(widget)
        for child in widget.winfo_children():
            # Evita erro se child for None
            if child: self.bind_mousewheel_recursive(child)


    def bind_mousewheel(self, widget):
        if isinstance(widget, (tk.Widget, tk.Tk, tk.Toplevel)):
            widget.bind("<MouseWheel>", self._on_mousewheel, add="+")
            widget.bind("<Button-4>", self._on_scroll_linux, add="+") # Linux scroll up
            widget.bind("<Button-5>", self._on_scroll_linux, add="+") # Linux scroll down

    def unbind_mousewheel(self):
        try: self.unbind_all("<MouseWheel>")
        except tk.TclError: pass
        try: self.unbind_all("<Button-4>")
        except tk.TclError: pass
        try: self.unbind_all("<Button-5>")
        except tk.TclError: pass

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def _on_scroll_linux(self, event):
        if event.num == 4: self.canvas.yview_scroll(-1, "units")
        elif event.num == 5: self.canvas.yview_scroll(1, "units")

    def destroy(self):
        self.unbind_mousewheel()
        super().destroy()

    def setup_ui(self):
        """Cria a interface gráfica da janela de edição."""

        self.placeholders = {
             "hqa": "Detalhe a queixa...", "tax": "Ex: 38", "pa_sistolica": "120", "pa_diastolica": "80",
             "fc": "Ex: 90", "sat": "Ex: 95",
             "doencas_preexistentes": "Ex: Diabetes, Hipertensão...", "alergias": "Ex: Dipirona, AAS...",
             "medicamentos_em_uso": "Ex: Losartana, Metformina...", "observacoes": "(Campo livre)",
             "hipotese_diagnostica": "Ex: Enxaqueca, ansiedade...",
             "resumo_conduta": "Selecione", "medicamento_administrado": "Selecione",
             "posologia": "Ex: 1 comp, 15 gotas", "horario_medicacao": "HH:MM", "conduta_obs": "(Campo livre)"
         }

        # --- Seção de Identificação ---
        id_frame = self.create_section_frame("Identificação do paciente")
        self.create_entry_field(id_frame, "Badge Number:", "badge_number", 0, 0, read_only=True) # Não adiciona a form_widgets
        self.create_entry_field(id_frame, "Nome:", "nome", 0, 1, add_to_form_widgets=True)
        self.create_entry_field(id_frame, "Login:", "login", 1, 0, add_to_form_widgets=True)
        self.create_combobox_field(id_frame, "Gestor:", "gestor", OPTIONS["gestores"], 1, 1, add_to_form_widgets=True)
        self.create_combobox_field(id_frame, "Turno:", "turno", OPTIONS["turnos"], 2, 0, add_to_form_widgets=True)
        self.create_combobox_field(id_frame, "Setor:", "setor", OPTIONS["setores"], 2, 1, add_to_form_widgets=True)
        self.create_combobox_field(id_frame, "Processo:", "processo", OPTIONS["processos"], 3, 0, add_to_form_widgets=True)
        self.create_entry_field(id_frame, "Tenure:", "tenure", 3, 1, add_to_form_widgets=True)

        # --- Seção de Anamnese ---
        anamnese_frame = self.create_section_frame("Anamnese")
        self.create_queixa_section(anamnese_frame) # Cria QP e QS
        self.create_entry_field(anamnese_frame, "HQA:", "hqa", 2, 0, columnspan=3, add_to_form_widgets=True)
        self.create_entry_field(anamnese_frame, "TAX:", "tax", 3, 0, add_to_form_widgets=True)
        self.create_pa_section(anamnese_frame, 3, 1) # Adiciona widgets PA à lista dentro da função
        self.create_entry_field(anamnese_frame, "FC:", "fc", 4, 0, add_to_form_widgets=True)
        self.create_entry_field(anamnese_frame, "SAT:", "sat", 4, 1, add_to_form_widgets=True)
        self.create_entry_field(anamnese_frame, "Doenças Pré-existentes:", "doencas_preexistentes", 5, 0, columnspan=3, add_to_form_widgets=True)
        self.create_entry_field(anamnese_frame, "Alergias:", "alergias", 6, 0, columnspan=3, add_to_form_widgets=True)
        self.create_entry_field(anamnese_frame, "Medicamentos em uso:", "medicamentos_em_uso", 7, 0, columnspan=3, add_to_form_widgets=True)
        self.create_entry_field(anamnese_frame, "Observações:", "observacoes", 8, 0, columnspan=3, add_to_form_widgets=True)

        # --- Seção de Condutas ---
        self.condutas_container = ttk.Frame(self.scrollable_frame)
        self.condutas_container.pack(fill="x", padx=10, pady=5) # Padding original

        # --- Lógica de Habilitar/Desabilitar ---
        self.trabalho_altura_exceptions = {
             self.entries.get("pa_sistolica"),
             self.entries.get("pa_diastolica"),
             # Resumo será adicionado dinamicamente em create_conduta_section
        }
        # Garante que None não esteja no set inicial
        self.trabalho_altura_exceptions.discard(None)


        # Remove qp_sintoma da lista self.form_widgets APÓS TUDO SER CRIADO
        if hasattr(self, 'comboboxes') and self.comboboxes.get("qp_sintoma") in self.form_widgets:
             self.form_widgets.remove(self.comboboxes.get("qp_sintoma"))

        # Vincula a função de mudança APÓS qp_sintoma ser criado
        if combo_qp := self.comboboxes.get("qp_sintoma"):
            combo_qp.bind("<<ComboboxSelected>>", self.on_qp_sintoma_change)


        # --- Botões ---
        # Organização original dos botões
        ttk.Button(self.button_frame, text="Acrescentar Conduta", command=self.add_conduta_section).pack(side="left", padx=5)
        ttk.Button(self.button_frame, text="Apagar Atendimento", command=self.delete_atendimento).pack(side="left", padx=5) # Sem anchor
        ttk.Button(self.button_frame, text="Salvar Alterações", command=self.save_and_close).pack(side="right", padx=5)
        ttk.Button(self.button_frame, text="Fechar", command=self.confirm_close).pack(side="right", padx=5)

        self.protocol("WM_DELETE_WINDOW", self.confirm_close)

    def create_section_frame(self, text):
        # Padding e configuração de coluna originais
        frame = ttk.LabelFrame(self.scrollable_frame, text=text, padding=10)
        frame.pack(fill="x", padx=10, pady=5) # Padding original
        frame.columnconfigure(1, weight=1); frame.columnconfigure(3, weight=1) # Config original
        return frame

    def create_entry_field(self, parent, label, name, r, c, read_only=False, is_conduta=False, index=0, columnspan=1, vcmd=None, add_to_form_widgets=False):
        # Padding e sticky originais
        ttk.Label(parent, text=label).grid(row=r, column=c*2, padx=5, pady=2, sticky="w")
        entry = ttk.Entry(parent, validate="key", validatecommand=vcmd)
        entry.grid(row=r, column=c*2+1, padx=5, pady=2, sticky="ew", columnspan=columnspan)
        key = f"conduta_{index}_{name}" if is_conduta else name
        self.entries[key] = entry
        if read_only: entry.configure(state="readonly")
        else: entry.bind("<KeyRelease>", self.mark_as_changed)
        if add_to_form_widgets and not read_only:
             self.form_widgets.append(entry)
        utils.setup_placeholder(entry, self.placeholders.get(name, ""))
        return entry


    def create_combobox_field(self, parent, label, name, opts, r, c, is_conduta=False, index=0, add_to_form_widgets=False):
        # Padding e sticky originais
        ttk.Label(parent, text=label).grid(row=r, column=c*2, padx=5, pady=2, sticky="w")
        # --- Modificação: Carrega opções do OPTIONS global ---
        options_list = OPTIONS.get(name if not is_conduta else name.split('_')[-1], []) # Pega lista atualizada
        combo = ttk.Combobox(parent, values=options_list, state="readonly")
        # --- Fim Modificação ---
        combo.grid(row=r, column=c*2+1, padx=5, pady=2, sticky="ew")
        key = f"conduta_{index}_{name}" if is_conduta else name
        self.comboboxes[key] = combo
        combo.bind("<<ComboboxSelected>>", self.mark_as_changed)
        if add_to_form_widgets:
             self.form_widgets.append(combo)
        utils.setup_placeholder(combo, self.placeholders.get(name.split('_')[-1] if is_conduta else name, "Selecione")) # Ajuste placeholder
        return combo

    def create_queixa_section(self, parent):
        # Frame principal original
        queixa_frame = ttk.Frame(parent)
        queixa_frame.grid(row=0, column=0, columnspan=4, sticky="ew", pady=5) # columnspan=4 original
        queixa_frame.columnconfigure(1, weight=1)
        queixa_frame.columnconfigure(3, weight=1)
        # Sem config extra de colunas 4-7

        # --- Queixa Principal ---
        ttk.Label(queixa_frame, text="QP Sintoma:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        combo_qp_sintoma = self.create_combobox_field(queixa_frame, "", "qp_sintoma", SINTOMAS, 0, 0, add_to_form_widgets=False)
        combo_qp_sintoma.grid(row=0, column=1, sticky="ew", padx=5)

        ttk.Label(queixa_frame, text="QP Região:").grid(row=0, column=2, padx=5, pady=2, sticky="w")
        combo_qp_regiao = self.create_combobox_field(queixa_frame, "", "qp_regiao", REGIOES, 0, 1, add_to_form_widgets=True)
        combo_qp_regiao.grid(row=0, column=3, sticky="ew", padx=5)

        # --- Queixa Secundária ---
        # Grid original
        qs_sintoma_label = ttk.Label(queixa_frame, text="QS Sintomas:", font=("Arial", 10, "bold"))
        qs_sintoma_label.grid(row=1, column=0, padx=5, pady=(10, 2), sticky="nw")
        qs_sintoma_frame, self.qs_sintomas_vars = self._create_checkable_frame(queixa_frame, SINTOMAS)
        qs_sintoma_frame.grid(row=1, column=1, sticky="nsew", padx=5, pady=(10, 2))

        qs_regiao_label = ttk.Label(queixa_frame, text="QS Regiões:", font=("Arial", 10, "bold"))
        qs_regiao_label.grid(row=1, column=2, padx=5, pady=(10, 2), sticky="nw")
        qs_regiao_frame, self.qs_regioes_vars = self._create_checkable_frame(queixa_frame, REGIOES)
        qs_regiao_frame.grid(row=1, column=3, sticky="nsew", padx=5, pady=(10, 2))


    def _create_checkable_frame(self, parent, options):
        """Cria um frame com scroll e checkbuttons."""
        # Frame original
        frame = ttk.Frame(parent, borderwidth=1, relief="sunken", height=100) # Altura 100 original
        # Sem grid_propagate(False)
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        canvas = tk.Canvas(frame, height=100) # Altura 100 original
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas) # Frame interno

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")) # Sem ajuste de width
        )
        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        vars_dict = {}
        options_filtered = [opt for opt in options if opt != "N/A"]

        for i, option in enumerate(options_filtered):
            var = tk.BooleanVar(value=False)
            chk = ttk.Checkbutton(scrollable_frame, text=option, variable=var, command=self.mark_as_changed)
            chk.pack(anchor="w", fill="x", padx=5) # Padding original
            vars_dict[option] = var
            self.form_widgets.append(chk) # Adiciona o WIDGET à lista

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Sem bind extra no canvas
        # self.bind_mousewheel(canvas) # Bind é feito recursivamente
        # self.bind_mousewheel(scrollable_frame)
        # for child in scrollable_frame.winfo_children():
        #      self.bind_mousewheel(child)

        return frame, vars_dict


    def create_pa_section(self, parent, r, c):
        # Padding e sticky originais
        ttk.Label(parent, text="PA:").grid(row=r, column=c*2, padx=5, pady=2, sticky="w")
        frame = ttk.Frame(parent)
        frame.grid(row=r, column=c*2+1, padx=5, pady=2, sticky="ew")
        # Sem validação original
        entry_sis = ttk.Entry(frame, width=5); entry_sis.pack(side="left")
        entry_sis.bind("<KeyRelease>", self.mark_as_changed)
        self.entries['pa_sistolica'] = entry_sis

        ttk.Label(frame, text="/").pack(side="left") # Sem padx
        entry_dia = ttk.Entry(frame, width=5); entry_dia.pack(side="left")
        entry_dia.bind("<KeyRelease>", self.mark_as_changed)
        self.entries['pa_diastolica'] = entry_dia

        # Adiciona PA à lista form_widgets
        if entry_sis not in self.form_widgets: self.form_widgets.append(entry_sis)
        if entry_dia not in self.form_widgets: self.form_widgets.append(entry_dia)


    def create_conduta_section(self, index=0, is_new=False, conduta_data=None):
        # Padding e configuração de coluna originais
        frame = ttk.LabelFrame(self.condutas_container, text=f"Conduta - {index+1}ª", padding="10") # Padding original
        frame.pack(fill="x", expand=True, padx=0, pady=5) # Padding original
        frame.columnconfigure(1, weight=1); frame.columnconfigure(3, weight=1) # Original


        timestamp_label = ttk.Label(frame, text="")
        # Grid original do timestamp
        timestamp_label.grid(row=0, column=4, columnspan=2, sticky="e", padx=5)
        if is_new:
            timestamp_label.config(text=f"Adicionada: {datetime.now().strftime('%H:%M:%S')}")
        # --- CORREÇÃO: Pega hora do atendimento principal se não houver timestamp na conduta ---
        elif conduta_data and hasattr(conduta_data, 'horario_medicacao') and conduta_data.horario_medicacao != "N/A":
             # Tenta usar horario_medicacao como referência, ou uma hora padrão
             try:
                 # Se horario_medicacao tiver data e hora, usar. Senão, só hora.
                 ts_hora = conduta_data.horario_medicacao
                 timestamp_label.config(text=f"Medicação: {ts_hora}")
             except: # Se falhar em formatar, mostra N/A
                  timestamp_label.config(text=f"Registrada: N/A")
        elif self.atendimento_id: # Pega hora do atendimento geral
            atendimento_geral = db.get_atendimento_by_id(self.atendimento_id) # Busca de novo (ineficiente, mas seguro)
            if atendimento_geral:
                 timestamp_label.config(text=f"Atend: {atendimento_geral.hora_atendimento}")


        # Grid original do botão Remover
        if index >= 0: # Lógica mantida, ajustar se necessário
            remove_button = ttk.Button(frame, text="Remover", command=lambda i=index: self.remove_conduta_section(i)) # Largura original
            remove_button.grid(row=1, column=4, padx=5, pady=2, sticky="ne")


        # Cria os campos para esta conduta (mantém add_to_form_widgets=True onde aplicável)
        self.create_entry_field(frame, "Hipótese:", "hipotese_diagnostica", 0, 1, is_conduta=True, index=index, add_to_form_widgets=True)
        # Campo Conduta removido
        self.create_combobox_field(frame, "Resumo:", "resumo_conduta", OPTIONS["resumo_conduta"], 2, 0, is_conduta=True, index=index, add_to_form_widgets=True)
        self.create_combobox_field(frame, "Medicação:", "medicamento_administrado", OPTIONS["medicamento_admin"], 2, 1, is_conduta=True, index=index, add_to_form_widgets=True)

        vcmd = (self.register(utils.validate_posologia_input), '%P')
        self.create_entry_field(frame, "Posologia:", "posologia", 3, 0, is_conduta=True, index=index, vcmd=vcmd, add_to_form_widgets=True)

        # Campo Horário (grid original)
        ttk.Label(frame, text="Horário:").grid(row=3, column=2, padx=5, pady=2, sticky="w") # Padding original
        h_frame = ttk.Frame(frame); h_frame.grid(row=3, column=3, sticky="ew", padx=5) # Padding original
        entry = ttk.Entry(h_frame, width=10); entry.pack(side="left", fill="x", expand=True) # Sem fill/expand originais?
        entry.bind("<KeyRelease>", self.mark_as_changed)
        self.entries[f"conduta_{index}_horario_medicacao"] = entry
        self.form_widgets.append(entry)

        btn_agora = ttk.Button(h_frame, text="Agora", command=lambda i=index: self.set_current_time(i)) # Largura original
        btn_agora.pack(side="left", padx=5) # Padding original
        self.form_widgets.append(btn_agora)

        self.create_entry_field(frame, "Obs:", "observacoes", 4, 0, is_conduta=True, index=index, columnspan=3, add_to_form_widgets=True)

        # Adiciona o frame à lista e preenche dados se houver
        if index >= len(self.condutas_frames): self.condutas_frames.append(frame)
        if conduta_data: self._fill_conduta_fields(index, conduta_data)

        # Atualiza a lista de exceções para "Trabalho em altura"
        if combo_resumo := self.comboboxes.get(f"conduta_{index}_resumo_conduta"):
             self.trabalho_altura_exceptions.add(combo_resumo)

        # Reaplica o estado dos widgets baseado no sintoma QP atual
        self.on_qp_sintoma_change()


    def _fill_conduta_fields(self, index, conduta):
        """Preenche os campos de uma seção de conduta específica."""
        fields_map = {
            "hipotese_diagnostica": "entry",
            "resumo_conduta": "combo",
            "medicamento_administrado": "combo",
            "posologia": "entry",
            "horario_medicacao": "entry",
            "observacoes": "entry",
        }
        for name, field_type in fields_map.items():
            key = f"conduta_{index}_{name}"
            value = getattr(conduta, name, '') # Pega valor do objeto Conduta
            if field_type == "entry":
                widget = self.entries.get(key)
                if widget:
                     # Usa nome base para placeholder
                     placeholder = self.placeholders.get(name, "")
                     utils.clear_placeholder(widget, placeholder)
                     widget.delete(0, 'end'); widget.insert(0, value if value != "N/A" else "")
                     if not (value and value != "N/A"): utils.setup_placeholder(widget, placeholder)
                     else: utils.remove_placeholder_on_fill(widget, placeholder)
            elif field_type == "combo":
                 widget = self.comboboxes.get(key)
                 if widget:
                     # Usa nome base para placeholder
                     placeholder = self.placeholders.get(name, "Selecione")
                     utils.clear_placeholder(widget, placeholder)
                     if value and value != "N/A" and value in widget['values']:
                         widget.set(value)
                     else:
                         widget.set("")
                         utils.setup_placeholder(widget, placeholder)

    def set_current_time(self, index):
        key = f"conduta_{index}_horario_medicacao"
        if entry := self.entries.get(key):
            placeholder = self.placeholders.get("horario_medicacao", "HH:MM")
            utils.clear_placeholder(entry, placeholder)
            entry.delete(0, tk.END)
            entry.insert(0, datetime.now().strftime("%H:%M"))
            utils.remove_placeholder_on_fill(entry, placeholder)
            self.mark_as_changed()

    def remove_conduta_section(self, index_to_remove):
        if len(self.condutas_frames) <= 0: return

        frame_to_remove = self.condutas_frames.pop(index_to_remove)

        widgets_to_remove = []
        keys_to_remove_entries = [k for k in self.entries if k.startswith(f"conduta_{index_to_remove}_")]
        keys_to_remove_combos = [k for k in self.comboboxes if k.startswith(f"conduta_{index_to_remove}_")]

        for key in keys_to_remove_entries:
             widget = self.entries.pop(key)
             widgets_to_remove.append(widget)
             if key.endswith("_horario_medicacao"):
                 try:
                     # Tenta encontrar o botão "Agora" pelo objeto, não índice
                     agora_button = next(w for w in self.form_widgets if isinstance(w, ttk.Button) and w.master == widget.master and w.cget('text') == "Agora")
                     widgets_to_remove.append(agora_button)
                 except (StopIteration, tk.TclError): pass # Ignora se não encontrar

        for key in keys_to_remove_combos:
             widget = self.comboboxes.pop(key)
             widgets_to_remove.append(widget)
             if key.endswith("_resumo_conduta") and widget in self.trabalho_altura_exceptions:
                 try: self.trabalho_altura_exceptions.remove(widget)
                 except KeyError: pass


        self.form_widgets = [w for w in self.form_widgets if w not in widgets_to_remove]

        frame_to_remove.destroy()
        self.changed = True

        # Reindexa os frames restantes e seus widgets
        for i, frame in enumerate(self.condutas_frames):
            frame.config(text=f"Conduta - {i+1}ª")
            new_prefix = f"conduta_{i}_"
            # Reindexa keys de forma mais segura iterando nos widgets do frame
            for child in frame.winfo_children():
                # Encontra a chave antiga baseada no widget
                old_key = None
                for d in [self.entries, self.comboboxes]:
                     for k, v in d.items():
                         if v == child and k.startswith("conduta_"):
                             old_key = k
                             break
                     if old_key: break

                if old_key:
                     old_index_str = old_key.split('_')[1]
                     if old_index_str.isdigit() and int(old_index_str) != i:
                         # Atualiza o dicionário
                         widget_instance = None
                         if old_key in self.entries: widget_instance = self.entries.pop(old_key)
                         elif old_key in self.comboboxes: widget_instance = self.comboboxes.pop(old_key)

                         if widget_instance:
                             new_key = new_prefix + "_".join(old_key.split("_")[2:])
                             if isinstance(widget_instance, ttk.Entry): self.entries[new_key] = widget_instance
                             elif isinstance(widget_instance, ttk.Combobox): self.comboboxes[new_key] = widget_instance


            # Reconfigura comando do botão remover
            for child in frame.winfo_children():
                if isinstance(child, ttk.Button) and child.cget('text') == "Remover":
                    child.config(command=lambda current_i=i: self.remove_conduta_section(current_i))
                    break

        self.scrollable_frame.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))


    def add_conduta_section(self):
         index = len(self.condutas_frames)
         self.create_conduta_section(index=index, is_new=True)
         self.scrollable_frame.update_idletasks()
         self.canvas.yview_moveto(1) # Rola para o final


    def load_data(self):
        atendimento = db.get_atendimento_by_id(self.atendimento_id)
        if not atendimento:
            messagebox.showerror("Erro", "Atendimento não encontrado.", parent=self); self.destroy(); return

        # --- Preenche campos de identificação ---
        id_fields = ["nome","login","tenure", "gestor", "turno", "setor", "processo"]
        for name in id_fields:
            value = getattr(atendimento, name, '')
            widget = self.entries.get(name) or self.comboboxes.get(name)
            if widget:
                 placeholder = self.placeholders.get(name, "") if name in self.entries else self.placeholders.get(name, "Selecione")
                 utils.clear_placeholder(widget, placeholder)
                 if isinstance(widget, ttk.Combobox):
                     # --- CORREÇÃO: Atualiza values antes de setar ---
                     options_key = name + "s" # 'gestor' -> 'gestores'
                     if options_key in OPTIONS: widget['values'] = OPTIONS[options_key]
                     # --- Fim Correção ---
                     if value in widget['values']: widget.set(value)
                     else: widget.set("")
                 else:
                     widget.delete(0, 'end'); widget.insert(0, value if value != "N/A" else "")
                 if not value or value=="N/A": utils.setup_placeholder(widget, placeholder)
                 else: utils.remove_placeholder_on_fill(widget, placeholder)


        if badge_entry := self.entries.get("badge_number"):
            badge_entry.configure(state="normal")
            badge_entry.delete(0, 'end'); badge_entry.insert(0, atendimento.badge_number)
            badge_entry.configure(state="readonly")


        # --- CORREÇÃO: Mapeamento Anamnese ---
        anamnese_fields_map = {
             "hqa": "hqa", "tax": "tax", "pa_sistolica": "pa_sistolica",
             "pa_diastolica": "pa_diastolica", "fc": "fc", "sat": "sat",
             "doencas_preexistentes": "doencas_preexistentes", "alergias": "alergias",
             "medicamentos_em_uso": "medicamentos_em_uso", "observacoes": "observacoes"
        }
        for widget_name, db_attr in anamnese_fields_map.items():
             value = getattr(atendimento, db_attr, '')
             widget = self.entries.get(widget_name)
             if widget:
                 placeholder = self.placeholders.get(widget_name, "")
                 utils.clear_placeholder(widget, placeholder)
                 widget.delete(0, 'end'); widget.insert(0, value if value != "N/A" else "")
                 if not value or value=="N/A": utils.setup_placeholder(widget, placeholder)
                 else: utils.remove_placeholder_on_fill(widget, placeholder)

        # --- Preenche Queixas ---
        if combo_qp_s := self.comboboxes.get("qp_sintoma"):
             qp_s_val = getattr(atendimento, 'qp_sintoma', '')
             placeholder_qp_s = self.placeholders.get("qp_sintoma", "Selecione")
             utils.clear_placeholder(combo_qp_s, placeholder_qp_s)
             if qp_s_val and qp_s_val != "N/A" and qp_s_val in combo_qp_s['values']: combo_qp_s.set(qp_s_val)
             else: combo_qp_s.set(""); utils.setup_placeholder(combo_qp_s, placeholder_qp_s)

        if combo_qp_r := self.comboboxes.get("qp_regiao"):
             qp_r_val = getattr(atendimento, 'qp_regiao', '')
             placeholder_qp_r = self.placeholders.get("qp_regiao", "Selecione")
             utils.clear_placeholder(combo_qp_r, placeholder_qp_r)
             if qp_r_val and qp_r_val != "N/A" and qp_r_val in combo_qp_r['values']: combo_qp_r.set(qp_r_val)
             else: combo_qp_r.set(""); utils.setup_placeholder(combo_qp_r, placeholder_qp_r)

        # QS
        try: qs_sintomas_list = json.loads(getattr(atendimento, 'qs_sintomas', '[]'))
        except json.JSONDecodeError: qs_sintomas_list = []
        try: qs_regioes_list = json.loads(getattr(atendimento, 'qs_regioes', '[]'))
        except json.JSONDecodeError: qs_regioes_list = []

        if hasattr(self, 'qs_sintomas_vars'):
            for sintoma, var in self.qs_sintomas_vars.items(): var.set(sintoma in qs_sintomas_list)
        if hasattr(self, 'qs_regioes_vars'):
            for regiao, var in self.qs_regioes_vars.items(): var.set(regiao in qs_regioes_list)

        # --- Recria Condutas ---
        for frame in self.condutas_frames: frame.destroy()
        self.condutas_frames = []
        self.entries = {k:v for k,v in self.entries.items() if not k.startswith("conduta_")}
        self.comboboxes = {k:v for k,v in self.comboboxes.items() if not k.startswith("conduta_")}
        # Recria form_widgets com base nos widgets atuais não-conduta
        self.form_widgets = []
        non_conduta_widgets = list(self.entries.values()) + list(self.comboboxes.values())
        non_conduta_widgets += [chk for chk_dict in [self.qs_sintomas_vars, self.qs_regioes_vars] for var in chk_dict.values() if hasattr(var, '_widget')] # Adiciona Checkbuttons
        # Adiciona PA
        if pa_sis := self.entries.get('pa_sistolica'): non_conduta_widgets.append(pa_sis)
        if pa_dia := self.entries.get('pa_diastolica'): non_conduta_widgets.append(pa_dia)

        # Filtra apenas widgets válidos e não readonly (exceto qp_regiao)
        for w in non_conduta_widgets:
             if w and hasattr(w, 'cget'):
                 try:
                     state = w.cget('state')
                     if state != 'readonly' or w == self.comboboxes.get('qp_regiao'): # Inclui qp_regiao na lógica
                          self.form_widgets.append(w)
                 except tk.TclError: pass # Ignora erro ao pegar estado
        # Remove qp_sintoma explicitamente
        if combo_qp_s in self.form_widgets: self.form_widgets.remove(combo_qp_s)


        self.trabalho_altura_exceptions = {
             self.entries.get("pa_sistolica"),
             self.entries.get("pa_diastolica")
         }
        self.trabalho_altura_exceptions.discard(None)


        if not atendimento.condutas:
             self.create_conduta_section(index=0, is_new=True)
        else:
            for i, conduta_db in enumerate(atendimento.condutas):
                 self.create_conduta_section(index=i, is_new=False, conduta_data=conduta_db)

        self.on_qp_sintoma_change()

        self.changed = False
        if self.title().endswith("*"):
             self.title(self.title()[:-1])


    def get_form_data(self):
        """Coleta dados do formulário e retorna um objeto Atendimento."""
        data = {}
        # --- CORREÇÃO: Usa um mapeamento explícito para evitar problemas ---
        form_to_db_map = {
            "badge_number": "badge_number", "nome": "nome", "login": "login",
            "gestor": "gestor", "turno": "turno", "setor": "setor", "processo": "processo",
            "tenure": "tenure", "hqa": "hqa", "tax": "tax",
            "pa_sistolica": "pa_sistolica", "pa_diastolica": "pa_diastolica",
            "fc": "fc", "sat": "sat",
            "doencas_preexistentes": "doencas_preexistentes", "alergias": "alergias",
            "medicamentos_em_uso": "medicamentos_em_uso", "observacoes": "observacoes",
            "qp_sintoma": "qp_sintoma", "qp_regiao": "qp_regiao"
        }

        all_widgets = {**self.entries, **self.comboboxes}

        for form_key, db_key in form_to_db_map.items():
            widget = all_widgets.get(form_key)
            if widget:
                val = widget.get()
                placeholder = self.placeholders.get(form_key, "") if form_key in self.entries else self.placeholders.get(form_key, "Selecione")

                if form_key == "badge_number": data[db_key] = val
                else: data[db_key] = "N/A" if not val or val == placeholder else val
            elif db_key not in data: # Garante N/A se widget não encontrado
                 data[db_key] = "N/A"


        # Coleta Queixas QS
        qs_sintomas_list = [q for q, v in self.qs_sintomas_vars.items() if v.get()]
        qs_regioes_list = [r for r, v in self.qs_regioes_vars.items() if v.get()]
        qs_sintomas_json = json.dumps(qs_sintomas_list)
        qs_regioes_json = json.dumps(qs_regioes_list)

        data['qs_sintomas'] = qs_sintomas_json
        data['qs_regioes'] = qs_regioes_json


        atendimento = Atendimento(
             id=self.atendimento_id,
             **data
        )

        # Coleta Condutas
        atendimento.condutas = []
        for i in range(len(self.condutas_frames)):
            conduta_data = {}
            conduta_fields_map = { # Mapeamento explícito para conduta
                 "hipotese_diagnostica": "hipotese_diagnostica",
                 "resumo_conduta": "resumo_conduta",
                 "medicamento_administrado": "medicamento_administrado",
                 "posologia": "posologia",
                 "horario_medicacao": "horario_medicacao",
                 "observacoes": "observacoes" # Mapeia 'obs' do form para 'observacoes' do DB
            }
            for form_key_base, db_key in conduta_fields_map.items():
                 widget_key = f"conduta_{i}_{form_key_base}" # Usa form_key_base para achar widget
                 widget = self.entries.get(widget_key) or self.comboboxes.get(widget_key)
                 if widget:
                      placeholder_key = form_key_base # Usa nome base para placeholder
                      placeholder = self.placeholders.get(placeholder_key,"")
                      val = widget.get()
                      conduta_data[db_key] = "N/A" if not val or val == placeholder else val
                 else:
                      conduta_data[db_key] = "N/A"

            conduta_data['conduta_adotada'] = 'N/A'

            is_empty = all(v == "N/A" for k, v in conduta_data.items() if k != 'conduta_adotada')
            if not is_empty:
                 atendimento.condutas.append(Conduta(**conduta_data))

        return atendimento

    # ... (Restante das funções: mark_as_changed, save_and_close, delete_atendimento, confirm_close,
    #      on_qp_sintoma_change, set_widget_state permanecem as mesmas da versão anterior) ...

    def mark_as_changed(self, event=None):
        self.changed = True
        if not self.title().endswith("*"):
            self.title(self.title() + "*")

    def save_and_close(self):
        try:
            atendimento_atualizado = self.get_form_data()
            db.update_atendimento(atendimento_atualizado)
            messagebox.showinfo("Sucesso", "Atendimento atualizado!", parent=self)
            self.callback()
            self.changed = False
            self.destroy()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar: {e}", parent=self)
            print(f"Erro detalhado ao salvar (edit): {e}")
            import traceback
            traceback.print_exc()

    def delete_atendimento(self):
        if messagebox.askyesno("Confirmar", "Apagar este atendimento? A ação é irreversível.", parent=self):
            try:
                db.delete_atendimento(self.atendimento_id)
                messagebox.showinfo("Sucesso", "Atendimento apagado.", parent=self)
                self.callback(); self.destroy()
            except Exception as e: messagebox.showerror("Erro", f"Erro ao apagar: {e}", parent=self)

    def confirm_close(self):
        if self.changed:
             response = messagebox.askyesnocancel("Sair?", "Há alterações não salvas. Deseja salvar antes de fechar?", parent=self)
             if response is True:
                 self.save_and_close()
             elif response is False:
                 self.destroy()
             # else: Cancelar
        else:
            self.destroy()

    def on_qp_sintoma_change(self, event=None):
        """Habilita/desabilita campos com base na QP selecionada."""
        qp_sintoma_combo = self.comboboxes.get("qp_sintoma")
        sintoma = qp_sintoma_combo.get() if qp_sintoma_combo else None

        if qp_sintoma_combo:
            qp_sintoma_combo.config(state="readonly")

        if sintoma == "Absorvente":
            for widget in self.form_widgets:
                if widget != qp_sintoma_combo:
                    self.set_widget_state(widget, "disabled", "N/A")

        elif sintoma == "Trabalho em altura":
             current_resumo_combos = {self.comboboxes.get(f"conduta_{i}_resumo_conduta") for i in range(len(self.condutas_frames))}
             current_resumo_combos.discard(None)
             self.trabalho_altura_exceptions = {
                 self.entries.get("pa_sistolica"),
                 self.entries.get("pa_diastolica")
             }.union(current_resumo_combos)
             self.trabalho_altura_exceptions.discard(None)

             for widget in self.form_widgets:
                if widget == qp_sintoma_combo:
                    continue
                if widget in self.trabalho_altura_exceptions:
                    self.set_widget_state(widget, "normal", "")
                else:
                    self.set_widget_state(widget, "disabled", "N/A")

        else:
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
                    if widget == self.comboboxes.get("qp_sintoma"):
                         if fill_value == "N/A": widget.set(self.placeholders.get("qp_sintoma", "Selecione"))
                         widget.config(state="readonly")
                    else:
                        widget.config(state="normal")
                        widget.set(fill_value)
                        widget.config(state="disabled")

                elif widget_type == "TCheckbutton":
                    var_name = str(widget.cget("variable"))
                    found_var = None
                    for d in [self.qs_sintomas_vars, self.qs_regioes_vars]:
                        for key, v in d.items():
                            if str(v) == var_name: found_var = v; break
                        if found_var: break
                    if found_var and isinstance(found_var, tk.BooleanVar): found_var.set(False)
                    widget.config(state="disabled")
                elif widget_type == "TButton":
                    widget.config(state="disabled")

            else: # state == "normal" (ou "readonly" para comboboxes)
                target_state = "readonly" if widget_type == "TCombobox" else "normal"

                if current_state != target_state: widget.config(state=target_state)

                if current_state == "disabled":
                     placeholder = ""
                     widget_name_part = ""
                     placeholder_map = self.placeholders

                     entry_match = next((name for name, w in self.entries.items() if w == widget), None)
                     combo_match = next((name for name, w in self.comboboxes.items() if w == widget), None)

                     if entry_match:
                         if entry_match.startswith("conduta_"): widget_name_part = "_".join(entry_match.split("_")[2:])
                         else: widget_name_part = entry_match
                         placeholder = placeholder_map.get(widget_name_part, "")
                     elif combo_match:
                          if combo_match.startswith("conduta_"): widget_name_part = "_".join(combo_match.split("_")[2:])
                          else: widget_name_part = combo_match
                          placeholder = placeholder_map.get(widget_name_part, "Selecione")


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
            print(f"TclError in set_widget_state (EditWindow) for {widget}: {e}")
            pass


import tkinter as tk
from tkinter import ttk, messagebox
from models import Atendimento, Conduta
import db
import utils
from typing import List, Optional
from datetime import datetime
from gui.constants import OPTIONS, SINTOMAS, REGIOES # Importa constantes
import json # Para carregar listas de queixas

class EditWindow(tk.Toplevel):
    def __init__(self, parent, atendimento_id, callback):
        super().__init__(parent)
        self.parent = parent
        self.atendimento_id = atendimento_id
        self.callback = callback
        self.title("Editar Atendimento")
        self.geometry("1050x750")
        self.resizable(False, False)
        self.changed = False
        self.condutas_frames = []

        self.entries = {}
        self.comboboxes = {}
        # Novos dicts para checkbuttons de queixa secundária
        self.qs_sintomas_vars = {}
        self.qs_regioes_vars = {}
        
        # Lista para guardar todos os widgets do formulário para habilitar/desabilitar
        self.form_widgets = []

        # Layout principal com barra de botões fixa
        self.button_frame = ttk.Frame(self, padding=(10, 5, 10, 10))
        self.button_frame.pack(side="bottom", fill="x")
        
        container = ttk.Frame(self)
        container.pack(side="top", fill="both", expand=True)

        self.canvas = tk.Canvas(container, borderwidth=0)
        v_scrollbar = ttk.Scrollbar(container, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=v_scrollbar.set)
        
        self.scrollable_frame = ttk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        self.scrollable_frame.bind("<Configure>", self._on_frame_configure)
        v_scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.bind_mousewheel(self.canvas)
        self.bind_mousewheel(self.scrollable_frame)

        self.setup_ui()
        self.load_data()

    def _on_frame_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        # --- CORREÇÃO: Garante que winfo_width() seja chamado em um widget existente ---
        if self.canvas.winfo_exists():
            self.canvas.itemconfig(self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw"), width=self.canvas.winfo_width())


    def bind_mousewheel(self, widget):
        widget.bind_all("<MouseWheel>", self._on_mousewheel, add="+")
        widget.bind_all("<Button-4>", self._on_scroll_linux, add="+")
        widget.bind_all("<Button-5>", self._on_scroll_linux, add="+")

    def unbind_mousewheel(self):
        try:
            # --- CORREÇÃO: Desvincula da janela principal (self.parent) ---
            if self.parent and self.parent.winfo_exists():
                self.parent.unbind_all("<MouseWheel>")
                self.parent.unbind_all("<Button-4>")
                self.parent.unbind_all("<Button-5>")
        except tk.TclError:
            pass # Janela pai pode já estar destruída

    def _on_mousewheel(self, event):
        # --- CORREÇÃO: Verifica se canvas existe ---
        if self.canvas.winfo_exists():
             self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")


    def _on_scroll_linux(self, event):
         # --- CORREÇÃO: Verifica se canvas existe ---
        if self.canvas.winfo_exists():
            if event.num == 4: self.canvas.yview_scroll(-1, "units")
            elif event.num == 5: self.canvas.yview_scroll(1, "units")
    
    def destroy(self):
        self.unbind_mousewheel()
        super().destroy()

    def setup_ui(self):
        """Cria a interface gráfica da janela de edição."""
        # --- Seção de Identificação ---
        id_frame = self.create_section_frame("Identificação do paciente")
        self.create_entry_field(id_frame, "Badge Number:", "badge_number", 0, 0, read_only=True)
        self.create_entry_field(id_frame, "Nome:", "nome", 0, 1)
        self.create_entry_field(id_frame, "Login:", "login", 1, 0)
        self.create_combobox_field(id_frame, "Gestor:", "gestor", OPTIONS["gestores"], 1, 1)
        self.create_combobox_field(id_frame, "Turno:", "turno", OPTIONS["turnos"], 2, 0)
        self.create_combobox_field(id_frame, "Setor:", "setor", OPTIONS["setores"], 2, 1)
        self.create_combobox_field(id_frame, "Processo:", "processo", OPTIONS["processos"], 3, 0)
        self.create_entry_field(id_frame, "Tenure:", "tenure", 3, 1)
        
        self.label_data_hora = ttk.Label(id_frame, text="Data/Hora: Carregando...", font=("Arial", 9, "italic"))
        self.label_data_hora.grid(row=4, column=0, columnspan=4, sticky="w", padx=5, pady=5)

        # --- Seção de Anamnese (MODIFICADO) ---
        anamnese_frame = self.create_section_frame("Anamnese")
        self.create_queixa_section(anamnese_frame) # Nova seção de queixas
        self.create_entry_field(anamnese_frame, "HQA:", "hqa", 2, 0, columnspan=3, add_to_form_widgets=True)
        self.create_entry_field(anamnese_frame, "TAX:", "tax", 3, 0, add_to_form_widgets=True)
        self.create_pa_section(anamnese_frame, 3, 1)
        self.create_entry_field(anamnese_frame, "FC:", "fc", 4, 0, add_to_form_widgets=True)
        self.create_entry_field(anamnese_frame, "SAT:", "sat", 4, 1, add_to_form_widgets=True)
        self.create_entry_field(anamnese_frame, "Doenças Pré-existentes:", "doencas_preexistentes", 5, 0, columnspan=3, add_to_form_widgets=True)
        self.create_entry_field(anamnese_frame, "Alergias:", "alergias", 6, 0, columnspan=3, add_to_form_widgets=True)
        self.create_entry_field(anamnese_frame, "Medicamentos em uso:", "medicamentos_em_uso", 7, 0, columnspan=3, add_to_form_widgets=True)
        self.create_entry_field(anamnese_frame, "Observações:", "observacoes", 8, 0, columnspan=3, add_to_form_widgets=True)

        # --- Seção de Condutas ---
        self.condutas_container = ttk.Frame(self.scrollable_frame)
        self.condutas_container.pack(fill="x", padx=10, pady=5)
        
        # --- Botões ---
        ttk.Button(self.button_frame, text="Acrescentar Conduta", command=self.add_conduta_section).pack(side="left", padx=5)
        ttk.Button(self.button_frame, text="Apagar Atendimento", command=self.delete_atendimento).pack(side="left", padx=5)
        ttk.Button(self.button_frame, text="Salvar Alterações", command=self.save_and_close).pack(side="right", padx=5)
        ttk.Button(self.button_frame, text="Fechar", command=self.confirm_close).pack(side="right", padx=5)

        self.protocol("WM_DELETE_WINDOW", self.confirm_close)
        
        # --- Lógica de Habilitar/Desabilitar ---
        # Widgets que permanecem ativos para "Trabalho em altura"
        self.trabalho_altura_exceptions = {
            self.entries.get("pa_sistolica"), # Usa .get() para segurança
            self.entries.get("pa_diastolica")
            # Resumo será adicionado dinamicamente em create_conduta_section
        }
        # Remove None caso .get() falhe
        self.trabalho_altura_exceptions = {w for w in self.trabalho_altura_exceptions if w is not None}

        # --- CORREÇÃO: Excluir qp_sintoma da lista self.form_widgets ---
        if self.comboboxes.get("qp_sintoma") in self.form_widgets:
            self.form_widgets.remove(self.comboboxes.get("qp_sintoma"))

        # Vincula a função de mudança
        # --- CORREÇÃO: Garante que qp_sintoma existe antes de bind ---
        qp_sintoma_combo = self.comboboxes.get("qp_sintoma")
        if qp_sintoma_combo:
            qp_sintoma_combo.bind("<<ComboboxSelected>>", self.on_qp_sintoma_change)


    def create_section_frame(self, text):
        frame = ttk.LabelFrame(self.scrollable_frame, text=text, padding=10)
        frame.pack(fill="x", padx=10, pady=5)
        frame.columnconfigure(1, weight=1); frame.columnconfigure(3, weight=1)
        return frame

    def create_entry_field(self, parent, label, name, r, c, read_only=False, is_conduta=False, index=0, columnspan=1, vcmd=None, add_to_form_widgets=False):
        ttk.Label(parent, text=label).grid(row=r, column=c*2, padx=5, pady=2, sticky="w")
        entry = ttk.Entry(parent, validate="key", validatecommand=vcmd)
        entry.grid(row=r, column=c*2+1, padx=5, pady=2, sticky="ew", columnspan=columnspan)
        key = f"conduta_{index}_{name}" if is_conduta else name
        self.entries[key] = entry
        if read_only: entry.configure(state="readonly")
        entry.bind("<KeyRelease>", self.mark_as_changed)
        
        # Adiciona à lista geral se aplicável
        if add_to_form_widgets and not is_conduta and name not in ["badge_number", "nome", "login", "tenure"]:
             self.form_widgets.append(entry)
        return entry

    def create_combobox_field(self, parent, label, name, opts, r, c, is_conduta=False, index=0, add_to_form_widgets=False):
        ttk.Label(parent, text=label).grid(row=r, column=c*2, padx=5, pady=2, sticky="w")
        combo = ttk.Combobox(parent, values=opts, state="readonly")
        combo.grid(row=r, column=c*2+1, padx=5, pady=2, sticky="ew")
        key = f"conduta_{index}_{name}" if is_conduta else name
        self.comboboxes[key] = combo
        combo.bind("<<ComboboxSelected>>", self.mark_as_changed)

        # Adiciona à lista geral se aplicável
        if add_to_form_widgets and not is_conduta and name not in ["gestor", "turno", "setor", "processo"]:
            self.form_widgets.append(combo)
        return combo
        
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
            chk.bind("<ButtonRelease-1>", self.mark_as_changed) # Marca como alterado ao clicar
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
        
        # Adiciona PA à lista form_widgets e bind de alteração
        entry_sis.bind("<KeyRelease>", self.mark_as_changed)
        entry_dia.bind("<KeyRelease>", self.mark_as_changed)
        self.form_widgets.extend([entry_sis, entry_dia])


    def create_conduta_section(self, index=0, is_new=False, horario_medicacao=""):
        frame = ttk.LabelFrame(self.condutas_container, text=f"Conduta - {index+1}ª")
        frame.pack(fill="x", expand=True, padx=0, pady=5)
        frame.columnconfigure(1, weight=1); frame.columnconfigure(3, weight=1)
        
        timestamp_label = ttk.Label(frame, text="")
        timestamp_label.grid(row=0, column=4, columnspan=2, sticky="e")
        if is_new:
            timestamp_label.config(text=f"Adicionada às {datetime.now().strftime('%H:%M')}")
        elif horario_medicacao and horario_medicacao != "N/A":
             timestamp_label.config(text=f"Medicação às {horario_medicacao}")
            
        if index > 0:
            ttk.Button(frame, text="Remover", command=lambda i=index: self.remove_conduta_section(i)).grid(row=1, column=4, padx=5, pady=2, sticky="ne")
            
        entry_hip = self.create_entry_field(frame, "Hipótese:", "hipotese_diagnostica", 0, 1, is_conduta=True, index=index)
        
        combo_resumo = self.create_combobox_field(frame, "Resumo:", "resumo_conduta", OPTIONS["resumo_conduta"], 2, 0, is_conduta=True, index=index)
        combo_med = self.create_combobox_field(frame, "Medicação:", "medicamento_administrado", OPTIONS["medicamento_admin"], 2, 1, is_conduta=True, index=index)
        
        vcmd = (self.register(utils.validate_posologia_input), '%P')
        entry_pos = self.create_entry_field(frame, "Posologia:", "posologia", 3, 0, is_conduta=True, index=index, vcmd=vcmd)
        
        ttk.Label(frame, text="Horário:").grid(row=3, column=2, padx=5, pady=2, sticky="w")
        h_frame = ttk.Frame(frame); h_frame.grid(row=3, column=3, sticky="ew")
        entry_hor = ttk.Entry(h_frame, width=10); entry_hor.pack(side="left")
        self.entries[f"conduta_{index}_horario_medicacao"] = entry_hor
        btn_agora = ttk.Button(h_frame, text="Agora", command=lambda i=index: self.set_current_time(i))
        btn_agora.pack(side="left", padx=5)
        # Bind de alteração para entry_hor
        entry_hor.bind("<KeyRelease>", self.mark_as_changed)


        entry_obs = self.create_entry_field(frame, "Obs:", "observacoes", 4, 0, is_conduta=True, index=index, columnspan=3)
        
        # Adiciona widgets de conduta à lista principal
        conduta_widgets = [entry_hip, combo_resumo, combo_med, entry_pos, entry_hor, btn_agora, entry_obs]
        self.form_widgets.extend(conduta_widgets)
        
        # Adiciona combo_resumo às exceções
        self.trabalho_altura_exceptions.add(combo_resumo)
        
        if index >= len(self.condutas_frames): self.condutas_frames.append(frame)

    def on_qp_sintoma_change(self, event=None):
        """Habilita/desabilita campos com base na QP selecionada."""
        sintoma = self.comboboxes.get("qp_sintoma", ttk.Combobox()).get() # Usa .get() para segurança
        qp_sintoma_combo = self.comboboxes.get("qp_sintoma")

        if sintoma == "Absorvente":
            for widget in self.form_widgets:
                if widget != qp_sintoma_combo:
                    self.set_widget_state(widget, "disabled", "N/A")
        
        elif sintoma == "Trabalho em altura":
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
        """Define o estado (normal/disabled) e o valor de um widget."""
        try:
            if not widget or not widget.winfo_exists():
                return 

            widget_type = widget.winfo_class()
            
            if state == "disabled":
                if widget_type == "TEntry":
                    widget.config(state="normal") 
                    widget.delete(0, tk.END)
                    widget.insert(0, fill_value)
                    widget.config(state="disabled")
                elif widget_type == "TCombobox":
                    # --- CORREÇÃO: Não desabilita qp_sintoma ---
                    current_value = widget.get() # Guarda valor atual
                    widget.config(state="normal") # Permite alterar valor
                    widget.set(fill_value)
                    # Só desabilita se NÃO for qp_sintoma
                    if widget != self.comboboxes.get("qp_sintoma"):
                         widget.config(state="disabled")
                    else:
                         # Se for qp_sintoma e o valor for N/A, restaura valor anterior (opcional)
                         # Ou apenas deixa como N/A mas habilitado
                         # widget.set(current_value) # Descomente para restaurar
                         widget.config(state="readonly") # Mantém readonly

                elif widget_type == "TCheckbutton":
                    var_name = widget.cget("variable")
                    try:
                        var = widget.getvar(var_name) 
                        if isinstance(var, tk.BooleanVar): 
                           var.set(False) 
                    except tk.TclError:
                        pass 
                    widget.config(state="disabled") 
                elif widget_type == "TButton": 
                    widget.config(state="disabled")
            
            else: # state == "normal"
                if widget_type == "TEntry":
                    # Limpa N/A se estava desabilitado, antes de habilitar
                    if widget.cget("state") == "disabled" and widget.get() == "N/A":
                        widget.config(state="normal")
                        widget.delete(0, tk.END)
                    else:
                         widget.config(state="normal")

                elif widget_type == "TCombobox":
                     # Limpa N/A se estava desabilitado, antes de habilitar
                    if widget.cget("state") == "disabled" and widget.get() == "N/A":
                        widget.config(state="normal") # Permite alterar valor
                        widget.set("")
                        widget.config(state="readonly")
                    else:
                        widget.config(state="readonly")

                elif widget_type == "TCheckbutton":
                    widget.config(state="normal")
                elif widget_type == "TButton":
                    widget.config(state="normal")
        except tk.TclError:
            pass 

    def set_current_time(self, index):
        key = f"conduta_{index}_horario_medicacao"
        if entry := self.entries.get(key):
            # Não precisa de clear_placeholder aqui
            entry.delete(0, tk.END)
            entry.insert(0, datetime.now().strftime("%H:%M"))
            self.mark_as_changed()
            
    def remove_conduta_section(self, index):
        if not self.condutas_frames or index >= len(self.condutas_frames):
            return 
            
        frame_to_remove = self.condutas_frames.pop(index)
        
        # Identifica widgets a serem removidos
        widget_keys = [
            f"conduta_{index}_hipotese_diagnostica", 
            f"conduta_{index}_resumo_conduta", 
            f"conduta_{index}_medicamento_administrado",
            f"conduta_{index}_posologia", 
            f"conduta_{index}_horario_medicacao",
            # O botão 'Agora' associado a horario_medicacao
            f"conduta_{index}_observacoes"
        ]
        
        widgets_to_remove = []
        # Localiza o botão 'Agora' específico desta conduta
        horario_entry = self.entries.get(f"conduta_{index}_horario_medicacao")
        agora_button = None
        if horario_entry:
            parent_frame = horario_entry.master
            for child in parent_frame.winfo_children():
                if isinstance(child, ttk.Button) and child.cget("text") == "Agora":
                    agora_button = child
                    break
        
        for key in widget_keys:
            widget = self.entries.pop(key, None) or self.comboboxes.pop(key, None)
            if widget:
                widgets_to_remove.append(widget)
        if agora_button:
             widgets_to_remove.append(agora_button)

        # Remove da lista principal e das exceções
        self.form_widgets = [w for w in self.form_widgets if w not in widgets_to_remove]
        self.trabalho_altura_exceptions = {w for w in self.trabalho_altura_exceptions if w not in widgets_to_remove}

        frame_to_remove.destroy()
        self.mark_as_changed()
        
        # Renumera os frames restantes e atualiza as chaves nos dicionários
        new_entries = {}
        new_comboboxes = {}
        
        # Copia não-conduta
        for k, v in self.entries.items():
            if not k.startswith("conduta_"): new_entries[k] = v
        for k, v in self.comboboxes.items():
            if not k.startswith("conduta_"): new_comboboxes[k] = v

        for new_idx, frame in enumerate(self.condutas_frames):
            frame.config(text=f"Conduta - {new_idx+1}")
            # Atualiza command do botão Remover
            remove_button = None
            for child in frame.winfo_children():
                if isinstance(child, ttk.Button) and child.cget("text") == "Remover":
                     remove_button = child
                     break
            if remove_button:
                remove_button.config(command=lambda i=new_idx: self.remove_conduta_section(i))

            # Atualiza command do botão Agora
            agora_button = None
            for child in frame.winfo_children(): # Procura dentro do frame da conduta
                 if isinstance(child, ttk.Frame): # Procura o h_frame
                     for sub_child in child.winfo_children():
                         if isinstance(sub_child, ttk.Button) and sub_child.cget("text") == "Agora":
                              agora_button = sub_child
                              break
                     if agora_button: break
            if agora_button:
                 agora_button.config(command=lambda i=new_idx: self.set_current_time(i))


            # Atualiza chaves nos dicionários entries/comboboxes
            old_prefix = f"conduta_{index if new_idx >= index else new_idx}_" # A lógica aqui é complexa, simplificando
            new_prefix = f"conduta_{new_idx}_"

            # Reatribui widgets aos novos índices (exemplo simplificado)
            for suffix in ["hipotese_diagnostica", "posologia", "horario_medicacao", "observacoes"]:
                 widget = frame.nametowidget(self.entries[f"conduta_{new_idx+1}_{suffix}"].winfo_name()) # Nome antigo pode variar
                 new_key = new_prefix + suffix
                 new_entries[new_key] = widget
            for suffix in ["resumo_conduta", "medicamento_administrado"]:
                 widget = frame.nametowidget(self.comboboxes[f"conduta_{new_idx+1}_{suffix}"].winfo_name()) # Nome antigo pode variar
                 new_key = new_prefix + suffix
                 new_comboboxes[new_key] = widget


        # self.entries = new_entries # Reatribuir pode ser problemático, melhor apenas ajustar chaves se necessário
        # self.comboboxes = new_comboboxes

        # Força reajuste do scroll
        self.update_idletasks()
        self._on_frame_configure(None)

    def add_conduta_section(self): 
        self.create_conduta_section(index=len(self.condutas_frames), is_new=True)
        self.on_qp_sintoma_change() # Aplica o estado N/A se necessário
        # Força reajuste do scroll
        self.update_idletasks() 
        self._on_frame_configure(None)
        # Rola para o final
        if self.canvas.winfo_exists():
            self.canvas.yview_moveto(1.0)

    def load_data(self):
        atendimento = db.get_atendimento_by_id(self.atendimento_id)
        if not atendimento:
            messagebox.showerror("Erro", "Atendimento não encontrado."); self.destroy(); return
        
        data_hora_str = f"{getattr(atendimento, 'data_atendimento', 'N/A')} {getattr(atendimento, 'hora_atendimento', 'N/A')}"
        self.label_data_hora.config(text=f"Data/Hora do Registro: {data_hora_str}")
            
        # --- CORREÇÃO: Mapeamento de Campos ---
        # Garante que os atributos corretos do objeto 'atendimento' sejam usados
        entry_map = {
            "badge_number": "badge_number", "nome": "nome", "login": "login", "tenure": "tenure",
            "hqa": "hqa", "tax": "tax", "pa_sistolica": "pa_sistolica", "pa_diastolica": "pa_diastolica",
            "fc": "fc", "sat": "sat", "doencas_preexistentes": "doencas_preexistentes",
            "alergias": "alergias", "medicamentos_em_uso": "medicamentos_em_uso",
            "observacoes": "observacoes"
        }
        combo_map = {
            "gestor": "gestor", "turno": "turno", "setor": "setor", "processo": "processo",
            "qp_sintoma": "qp_sintoma", "qp_regiao": "qp_regiao"
        }

        self.entries["badge_number"].configure(state="normal")
        self.entries["badge_number"].delete(0, 'end'); self.entries["badge_number"].insert(0, getattr(atendimento, "badge_number", ''))
        self.entries["badge_number"].configure(state="readonly")
        
        for name, attr in entry_map.items():
            if name != "badge_number" and name in self.entries: # Pula badge, já preenchido
                self.entries[name].delete(0, 'end'); self.entries[name].insert(0, getattr(atendimento, attr, ''))
        
        for name, attr in combo_map.items():
            if name in self.comboboxes:
                 self.comboboxes[name].set(getattr(atendimento, attr, ''))

        # --- Carregar Queixas Secundárias ---
        try:
            sintomas_salvos = json.loads(getattr(atendimento, "qs_sintomas", "[]"))
            for sintoma, var in self.qs_sintomas_vars.items():
                var.set(sintoma in sintomas_salvos)
        except json.JSONDecodeError: pass

        try:
            regioes_salvas = json.loads(getattr(atendimento, "qs_regioes", "[]"))
            for regiao, var in self.qs_regioes_vars.items():
                 var.set(regiao in regioes_salvas)
        except json.JSONDecodeError: pass
        
        # --- Limpa condutas pré-existentes antes de criar novas ---
        for frame in self.condutas_frames:
            frame.destroy()
        self.condutas_frames = []
        # Remove widgets de condutas antigas das listas (importante)
        self.form_widgets = [w for w in self.form_widgets if not isinstance(w, (ttk.Checkbutton)) and not (hasattr(w,'master') and hasattr(w.master,'master') and w.master.master == self.condutas_container)] # Remove checkbuttons temporariamente
        # A linha acima é complexa, uma abordagem mais segura seria reconstruir a lista form_widgets do zero aqui,
        # adicionando apenas os widgets que NÃO são de conduta, e depois adicionar os de conduta em create_conduta_section.
        
        # Recria as seções de conduta com os dados carregados
        if not atendimento.condutas: 
            self.create_conduta_section(index=0, is_new=True) # Cria uma nova se vazia
        else:
            for i, conduta in enumerate(atendimento.condutas):
                self.create_conduta_section(index=i, is_new=False, horario_medicacao=getattr(conduta, "horario_medicacao", ""))
        
        # Preenche os dados das condutas recriadas
        for i, conduta in enumerate(atendimento.condutas):
            conduta_entry_map = {
                f"conduta_{i}_hipotese_diagnostica": "hipotese_diagnostica",
                f"conduta_{i}_posologia": "posologia",
                f"conduta_{i}_horario_medicacao": "horario_medicacao",
                f"conduta_{i}_observacoes": "observacoes"
            }
            conduta_combo_map = {
                 f"conduta_{i}_resumo_conduta": "resumo_conduta",
                 f"conduta_{i}_medicamento_administrado": "medicamento_administrado"
            }
            for key, attr in conduta_entry_map.items():
                if key in self.entries:
                    self.entries[key].delete(0,'end'); self.entries[key].insert(0, getattr(conduta, attr, ''))
            for key, attr in conduta_combo_map.items():
                if key in self.comboboxes:
                    self.comboboxes[key].set(getattr(conduta, attr, ''))

        # Aplica estado N/A (Absorvente/Trabalho em altura) após carregar dados
        self.on_qp_sintoma_change()
        self.changed = False # Reseta 'changed' após carregar


    def get_form_data(self):
        data = {}
        # Coleta dados de identificação e anamnese (não conduta)
        for k, w in self.entries.items():
            if not k.startswith("conduta_"): data[k] = w.get()
        for k, w in self.comboboxes.items():
             if not k.startswith("conduta_") and k not in ["qp_sintoma", "qp_regiao"]: data[k] = w.get()
        
        # Cria objeto Atendimento (sem condutas ainda)
        atendimento = Atendimento(id=self.atendimento_id, **data)
        
        # Coleta Queixas
        atendimento.qp_sintoma = self.comboboxes.get("qp_sintoma", ttk.Combobox()).get() or "N/A"
        atendimento.qp_regiao = self.comboboxes.get("qp_regiao", ttk.Combobox()).get() or "N/A"
        
        qs_sintomas_list = [q for q, v in self.qs_sintomas_vars.items() if v.get()]
        qs_regioes_list = [r for r, v in self.qs_regioes_vars.items() if v.get()]
        
        atendimento.qs_sintomas = json.dumps(qs_sintomas_list)
        atendimento.qs_regioes = json.dumps(qs_regioes_list)
        
        # Coleta Condutas
        atendimento.condutas = []
        for i in range(len(self.condutas_frames)):
            conduta_data = {
                "hipotese_diagnostica": self.entries.get(f"conduta_{i}_hipotese_diagnostica", tk.Entry()).get() or "N/A",
                "resumo_conduta": self.comboboxes.get(f"conduta_{i}_resumo_conduta", ttk.Combobox()).get() or "N/A",
                "medicamento_administrado": self.comboboxes.get(f"conduta_{i}_medicamento_administrado", ttk.Combobox()).get() or "N/A",
                "posologia": self.entries.get(f"conduta_{i}_posologia", tk.Entry()).get() or "N/A",
                "horario_medicacao": self.entries.get(f"conduta_{i}_horario_medicacao", tk.Entry()).get() or "N/A",
                "observacoes": self.entries.get(f"conduta_{i}_observacoes", tk.Entry()).get() or "N/A"
            }
            atendimento.condutas.append(Conduta(**conduta_data))
        return atendimento

    def mark_as_changed(self, event=None): self.changed = True

    def save_and_close(self):
        try:
            atendimento_data = self.get_form_data()
            db.update_atendimento(atendimento_data)
            messagebox.showinfo("Sucesso", "Atendimento atualizado!"); self.callback(); self.destroy()
        except Exception as e: 
            messagebox.showerror("Erro", f"Erro ao salvar: {e}")
            print(f"Erro detalhado ao salvar: {e}") # Log
            import traceback
            traceback.print_exc()


    def delete_atendimento(self):
        if messagebox.askyesno("Confirmar", "Apagar este atendimento? A ação é irreversível."):
            try:
                db.delete_atendimento(self.atendimento_id)
                messagebox.showinfo("Sucesso", "Atendimento apagado."); self.callback(); self.destroy()
            except Exception as e: messagebox.showerror("Erro", f"Erro ao apagar: {e}")

    def confirm_close(self):
        if self.changed and messagebox.askyesno("Sair?", "Há alterações não salvas. Deseja salvar antes de fechar?"):
            self.save_and_close()
        else:
            self.destroy()


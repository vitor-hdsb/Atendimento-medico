import tkinter as tk
from tkinter import ttk, messagebox
from models import Atendimento, Conduta
import db
import utils
from typing import List, Optional
from datetime import datetime

# --- Opções dos ComboBoxes (usadas em várias janelas) ---
OPTIONS = {
    "gestores": sorted([
        "ARTHUR MANZELA DIAS DE SOUZA (MANZELAR)", "RAIANY INGRID DA SILVA (RAIANY)", 
        "DIEGO CARLOS DA SILVA (CADIEGOV)", "BARBARA SAYURI IKI CORREA MENDES (SAYURIBA)",
        "GUILHERME DE OLIVEIRA MORAES (DEOLIVGU)", "ANA CAROLINE RODRIGUES RATES (ANCAROC)",
        "LUCAS GANDOLFI (LUCASGAN)", "LUCIANA VARGAS VILAR (LLUCIAVA)", "VIRGÍNIA RASTE (VRRASTE)",
        "RUAN RODRIGO FERREIRA DE ANDRADE (RUANRODR)", "ANDERSON COSTA SOUZA (ZCOSTASO)",
        "DOUGLAS SANTOS SILVA (SILVDOU)", "POLYANA GONCALVES DUMBA (GONCPOLY)",
        "LORENA MOREIRA DA SILVA (SILORE)", "PEDRO HENRIQUE DE JESUS (JESPEDR)",
        "KARINE FARIA (FAKARINE)", "VANIA LUCIA APOLINARIO PEREIRA (VANIAPER)",
        "SILVIO MARTINS SOUZA (SILVISOU)", "MILLANE AZEVEDO MEIRA (AZMILLAN)",
        "RAFAEL PEREIRA (PERAFAEU)", "JOAO VITOR BARBOSA CARNEIRO (JOACARNE)",
        "KAMILLY APARECIDA SOUZA DA SILVA (APARKAMI)", "MATEUS FLORES (MATTMF)",
        "INGRID DA COSTA ZANETI (IZZANETI)", "VITOR HUGO DE SOUZA BRAGA (VITODESO)",
        "LETICIA GOMES PEREIRA (LVGOMESP)", "LUDMILA MARIA DE JESUS (JLUDMILA)",
        "MARESSA LUIZA PAIXAO PEGA (MPAIXAO)", "ANA PAULA DOS SANTOS PINHEIRO (PAULADOS)",
        "TAÍS CORREIA (TAISREIS)", "LUANA REBECCA DE SOUZA (LUANAREB)",
        "HUMBERTO LEANDRO REGIS SILVA (LEAHUMBE)", "MAICON VALERIO DE SOUZA (MAICVALE)",
        "LEILANY PRISCILA BARROS CIRINO DE SOUZA (LEILASOU)", "ANIELLE CRISTINA DE LIMA RODRIGUES (CANIELLE)",
        "ANA CAROLINE FERREIRA DUARTE (ANRCAROL)", "CAROLINE GEORGia VICENTINI MAIA (CAROMAIA)",
        "GABRIEL ITALO CHAVES (CHVESG)", "ALICE DIAS SILVA (DIASALI)",
        "PAULO HENRIQUE G KERN BELLO (HENRPAUI)", "FABRÍCIO ORTIZ (FWOO)",
        "FRANK DIAS DA SILVA (FRNKSIL)", "DIEGO ROCHA RIBEIRO DE SOUZA (ROCHARIB)",
        "WAGNER GUIMARAES DOS SANTOS (WAGNSANT)", "ANA CAROLINA SANTOS F CALDEIRA (CARANAH)",
        "LUANA PAIVA DA SILVA (LUAPAIVU)", "WILLIAN RODRIGUES DA SILVA (WILLSIL)",
        "RAUL ESPINOSA (RAULESPB)", "BEATRIZ MOREIRA SOUZA (MOBEATRJ)",
        "LUCIANA PEREIRA RODRIGUES (LCIANR)", "MAYCON DOUGLAS FERREIRA DE PAULA (DOUGMAYC)",
        "MARCILENE APARECIDA DE ALMEIDA (APAMARCF)", "ALANIS VIANA CASTRO (ALANISCV)",
        "DEBORA ACASSIO LOPES (LODEBOR)", "MERLEN CÂNDIDO (MKRC)", "AQUILA COSTA DO CARMO (AQUCARMO)",
        "KAROLINE MOURA (KAROLMT)", "RONIERY MAGALHAES PAES (PAESRONI)",
        "JOSE OSWALDO BRASILEiro ROSSI LIMA LIMA (JOSELIMW)", "THIAGO HAMACHER (THIHAM)",
        "BRUNO CEZAR VARELA (VARBRUNO)", "FELICIO FRANCISCO JARDIM MATOS (FELIJFRA)",
        "MARIO MONTEIRO (AMMANTE)"
    ]),
    "turnos": ["Blue Day", "Blue Night", "Red Day", "Red Night", "MID", "ADM", "12X36 - Ímpar", "12X36 - Par"],
    "setores": sorted([
        "C-RET", "Enviroment", "IB", "ICQA", "Insumos", "Learning", "LP", 
        "Melhoria Contínua (ICQA)", "N/A", "OB", "RME - Sodexo", "RME - Terceiros", 
        "RME - Toledo", "Sodexo - Cozinha", "TI", "TOM", "Transfer-in", 
        "Transfer-out", "Sodexo - Limpeza", "WHS", "PXT"
    ]),
    "processos": sorted([
        "Administrativo", "Contagem", "Cozinha", "Damaged", "Decante", "Doca", 
        "Drop test", "Geral", "Inbound", "ISS", "Líder TDR", "Manutenção", 
        "Melhora Continua", "NED", "Observador", "Pack", "Pick", "Pick - PIT", 
        "PIT", "PREP", "Problem Solve", "Rebin", "Recebimento", "Slam", 
        "Spider", "Stow", "Stow - PIT", "Stow Pallet", "Suporte", 
        "Transfer In", "Transfer Out", "Yard Marshal"
    ]),
    "ocupacional": ["Sim", "Não", "N/A"],
    "resumo_conduta": ["Em observação", "Liberado para operação", "Liberado para atendimento externo c/ brigadista", "Liberado para atendimento externo s/ brigadista"],
    "medicamento_admin": ["Paracetamol", "Dipirona", "Ibuprofeno", "Outros", "N/A"]
}

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
        self.canvas.itemconfig(self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw"), width=self.canvas.winfo_width())

    def bind_mousewheel(self, widget):
        widget.bind_all("<MouseWheel>", self._on_mousewheel, add="+")
        widget.bind_all("<Button-4>", self._on_scroll_linux, add="+")
        widget.bind_all("<Button-5>", self._on_scroll_linux, add="+")

    def unbind_mousewheel(self):
        self.parent.unbind_all("<MouseWheel>")
        self.parent.unbind_all("<Button-4>")
        self.parent.unbind_all("<Button-5>")

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

        # --- Seção de Anamnese ---
        anamnese_frame = self.create_section_frame("Anamnese")
        self.create_queixa_section(anamnese_frame)
        self.create_entry_field(anamnese_frame, "HQA:", "hqa", 1, 0, columnspan=3)
        self.create_entry_field(anamnese_frame, "TAX:", "tax", 2, 0)
        self.create_pa_section(anamnese_frame, 2, 1)
        self.create_entry_field(anamnese_frame, "FC:", "fc", 3, 0)
        self.create_entry_field(anamnese_frame, "SAT:", "sat", 3, 1)
        self.create_entry_field(anamnese_frame, "Doenças Pré-existentes:", "doencas_preexistentes", 4, 0, columnspan=3)
        self.create_entry_field(anamnese_frame, "Alergias:", "alergias", 5, 0, columnspan=3)
        self.create_entry_field(anamnese_frame, "Medicamentos em uso:", "medicamentos_em_uso", 6, 0, columnspan=3)
        self.create_entry_field(anamnese_frame, "Observações:", "observacoes", 7, 0, columnspan=3)

        # --- Seção de Condutas ---
        self.condutas_container = ttk.Frame(self.scrollable_frame)
        self.condutas_container.pack(fill="x", padx=10, pady=5)
        
        # --- Botões ---
        ttk.Button(self.button_frame, text="Acrescentar Conduta", command=self.add_conduta_section).pack(side="left", padx=5)
        ttk.Button(self.button_frame, text="Apagar Atendimento", command=self.delete_atendimento).pack(side="left", padx=5)
        ttk.Button(self.button_frame, text="Salvar Alterações", command=self.save_and_close).pack(side="right", padx=5)
        ttk.Button(self.button_frame, text="Fechar", command=self.confirm_close).pack(side="right", padx=5)

        self.protocol("WM_DELETE_WINDOW", self.confirm_close)

    def create_section_frame(self, text):
        frame = ttk.LabelFrame(self.scrollable_frame, text=text, padding=10)
        frame.pack(fill="x", padx=10, pady=5)
        frame.columnconfigure(1, weight=1); frame.columnconfigure(3, weight=1)
        return frame

    def create_entry_field(self, parent, label, name, r, c, read_only=False, is_conduta=False, index=0, columnspan=1, vcmd=None):
        ttk.Label(parent, text=label).grid(row=r, column=c*2, padx=5, pady=2, sticky="w")
        entry = ttk.Entry(parent, validate="key", validatecommand=vcmd)
        entry.grid(row=r, column=c*2+1, padx=5, pady=2, sticky="ew", columnspan=columnspan)
        key = f"conduta_{index}_{name}" if is_conduta else name
        self.entries[key] = entry
        if read_only: entry.configure(state="readonly")
        entry.bind("<KeyRelease>", self.mark_as_changed)

    def create_combobox_field(self, parent, label, name, opts, r, c, is_conduta=False, index=0):
        ttk.Label(parent, text=label).grid(row=r, column=c*2, padx=5, pady=2, sticky="w")
        combo = ttk.Combobox(parent, values=opts)
        combo.grid(row=r, column=c*2+1, padx=5, pady=2, sticky="ew")
        key = f"conduta_{index}_{name}" if is_conduta else name
        self.comboboxes[key] = combo
        combo.bind("<<ComboboxSelected>>", self.mark_as_changed)
        
    def create_queixa_section(self, parent):
        ttk.Label(parent, text="Queixa principal:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        frame = ttk.Frame(parent)
        frame.grid(row=0, column=1, columnspan=3, padx=5, pady=2, sticky="ew")
        
        self.queixas_vars = {}
        for queixa in ["Dor de cabeça", "Enjoo", "Tontura", "Fraqueza", "Outros"]:
            var = tk.BooleanVar()
            self.queixas_vars[queixa] = var
            chk = ttk.Checkbutton(frame, text=queixa, variable=var, command=lambda q=queixa: self.toggle_other_queixa(q))
            chk.pack(side="left", padx=2)

        self.queixa_outros_entry = ttk.Entry(frame, state="disabled")
        self.queixa_outros_entry.pack(side="left", fill="x", expand=True, padx=2)
        self.queixa_outros_entry.bind("<KeyRelease>", self.mark_as_changed)

    def create_pa_section(self, parent, r, c):
        ttk.Label(parent, text="PA:").grid(row=r, column=c*2, padx=5, pady=2, sticky="w")
        frame = ttk.Frame(parent)
        frame.grid(row=r, column=c*2+1, padx=5, pady=2, sticky="ew")
        self.entries['pa_sistolica'] = ttk.Entry(frame, width=5); self.entries['pa_sistolica'].pack(side="left")
        ttk.Label(frame, text="/").pack(side="left")
        self.entries['pa_diastolica'] = ttk.Entry(frame, width=5); self.entries['pa_diastolica'].pack(side="left")

    def create_conduta_section(self, index=0, is_new=False):
        frame = ttk.LabelFrame(self.condutas_container, text=f"Conduta - {index+1}ª")
        frame.pack(fill="x", expand=True, padx=0, pady=5)
        frame.columnconfigure(1, weight=1); frame.columnconfigure(3, weight=1)
        
        timestamp_label = ttk.Label(frame, text="")
        timestamp_label.grid(row=0, column=4, columnspan=2, sticky="e")
        if is_new:
            timestamp_label.config(text=f"Adicionada às {datetime.now().strftime('%H:%M:%S')}")
        
        if index > 0:
            ttk.Button(frame, text="Remover", command=lambda i=index: self.remove_conduta_section(i)).grid(row=1, column=4, padx=5, pady=2, sticky="ne")
            
        self.create_combobox_field(frame, "Ocupacional:", "ocupacional", OPTIONS["ocupacional"], 0, 0, is_conduta=True, index=index)
        self.create_entry_field(frame, "Hipótese:", "hipotese_diagnostica", 0, 1, is_conduta=True, index=index)
        self.create_entry_field(frame, "Conduta:", "conduta_adotada", 1, 0, is_conduta=True, index=index, columnspan=3)
        self.create_combobox_field(frame, "Resumo:", "resumo_conduta", OPTIONS["resumo_conduta"], 2, 0, is_conduta=True, index=index)
        self.create_combobox_field(frame, "Medicação:", "medicamento_administrado", OPTIONS["medicamento_admin"], 2, 1, is_conduta=True, index=index)
        
        vcmd = (self.register(utils.validate_posologia_input), '%P')
        self.create_entry_field(frame, "Posologia:", "posologia", 3, 0, is_conduta=True, index=index, vcmd=vcmd)
        
        ttk.Label(frame, text="Horário:").grid(row=3, column=2, padx=5, pady=2, sticky="w")
        h_frame = ttk.Frame(frame); h_frame.grid(row=3, column=3, sticky="ew")
        entry = ttk.Entry(h_frame, width=10); entry.pack(side="left")
        self.entries[f"conduta_{index}_horario_medicacao"] = entry
        ttk.Button(h_frame, text="Agora", command=lambda i=index: self.set_current_time(i)).pack(side="left", padx=5)

        self.create_entry_field(frame, "Obs:", "observacoes", 4, 0, is_conduta=True, index=index, columnspan=3)
        
        if index >= len(self.condutas_frames): self.condutas_frames.append(frame)

    def toggle_other_queixa(self, q):
        if q == "Outros":
            is_checked = self.queixas_vars["Outros"].get()
            self.queixa_outros_entry.config(state=tk.NORMAL if is_checked else tk.DISABLED)
            if is_checked: utils.remove_placeholder_on_fill(self.queixa_outros_entry, "")
        self.mark_as_changed()

    def set_current_time(self, index):
        if entry := self.entries.get(f"conduta_{index}_horario_medicacao"):
            entry.delete(0, tk.END)
            utils.clear_placeholder(entry, ""); entry.insert(0, datetime.now().strftime("%H:%M")); self.mark_as_changed()
            
    def remove_conduta_section(self, index):
        self.condutas_frames.pop(index).destroy()
        self.changed = True
        for i, frame in enumerate(self.condutas_frames):
            frame.config(text=f"Conduta - {i+1}ª")

    def add_conduta_section(self): self.create_conduta_section(index=len(self.condutas_frames), is_new=True)

    def load_data(self):
        atendimento = db.get_atendimento_by_id(self.atendimento_id)
        if not atendimento:
            messagebox.showerror("Erro", "Atendimento não encontrado."); self.destroy(); return
            
        self.entries["badge_number"].configure(state="normal")
        self.entries["badge_number"].delete(0, 'end'); self.entries["badge_number"].insert(0, atendimento.badge_number)
        self.entries["badge_number"].configure(state="readonly")
        
        for name in ["nome","login","tenure","hqa","tax","pa_sistolica","pa_diastolica","fc","sat","doencas_preexistentes","alergias","medicamentos_em_uso","observacoes"]:
            self.entries[name].delete(0, 'end'); self.entries[name].insert(0, getattr(atendimento, name, ''))
        for name in ["gestor", "turno", "setor", "processo"]:
            self.comboboxes[name].set(getattr(atendimento, name, ''))

        if queixas := getattr(atendimento, 'queixas_principais', ''):
            queixas_salvas = queixas.split(';')
            for q, v in self.queixas_vars.items(): v.set(q in queixas_salvas)
            if outros := [q for q in queixas_salvas if q not in self.queixas_vars.keys()]:
                self.queixas_vars["Outros"].set(True); self.toggle_other_queixa("Outros")
                self.queixa_outros_entry.delete(0, 'end'); self.queixa_outros_entry.insert(0, ", ".join(outros))
        
        if not atendimento.condutas: self.add_conduta_section()
        else:
            while len(self.condutas_frames) < len(atendimento.condutas): self.add_conduta_section()
        
        for i, conduta in enumerate(atendimento.condutas):
            for name in ["hipotese_diagnostica", "conduta_adotada", "posologia", "horario_medicacao", "observacoes"]:
                key = f"conduta_{i}_{name}"
                self.entries[key].delete(0,'end'); self.entries[key].insert(0, getattr(conduta, name, ''))
            for name in ["resumo_conduta", "medicamento_administrado", "ocupacional"]:
                key = f"conduta_{i}_{name}"
                self.comboboxes[key].set(getattr(conduta, name, ''))


    def get_form_data(self):
        data = {k: w.get() for k, w in {**self.entries, **self.comboboxes}.items() if not k.startswith("conduta_")}
        atendimento = Atendimento(id=self.atendimento_id, **data)
        
        queixas = [q for q, v in self.queixas_vars.items() if v.get() and q != "Outros"]
        if self.queixas_vars["Outros"].get() and (o := self.queixa_outros_entry.get()): queixas.append(o)
        atendimento.queixas_principais = ";".join(queixas) if queixas else "N/A"
        
        atendimento.condutas = []
        for i in range(len(self.condutas_frames)):
            conduta_data = {k.replace(f"conduta_{i}_", ""): w.get() for k, w in {**self.entries, **self.comboboxes}.items() if k.startswith(f"conduta_{i}_")}
            atendimento.condutas.append(Conduta(**conduta_data))
        return atendimento

    def mark_as_changed(self, event=None): self.changed = True

    def save_and_close(self):
        try:
            db.update_atendimento(self.get_form_data())
            messagebox.showinfo("Sucesso", "Atendimento atualizado!"); self.callback(); self.destroy()
        except Exception as e: messagebox.showerror("Erro", f"Erro ao salvar: {e}")

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


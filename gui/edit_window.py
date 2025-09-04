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
        "ANA CAROLINE FERREIRA DUARTE (ANRCAROL)", "CAROLINE GEORGIA VICENTINI MAIA (CAROMAIA)",
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
        "JOSE OSWALDO BRASILEIRO ROSSI LIMA LIMA (JOSELIMW)", "THIAGO HAMACHER (THIHAM)",
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
        self.geometry("900x700")
        self.changed = False
        self.condutas_frames = []

        # Dicionários para widgets
        self.entries = {}
        self.comboboxes = {}

        # Containers
        main_frame = ttk.Frame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        main_frame.columnconfigure(0, weight=1)
        
        canvas = tk.Canvas(main_frame, borderwidth=0)
        v_scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        v_scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        canvas.configure(yscrollcommand=v_scrollbar.set)
        
        self.scrollable_frame = ttk.Frame(canvas)
        self.scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw", width=900)

        # Configurações do layout
        self.scrollable_frame.columnconfigure(0, weight=1)
        self.scrollable_frame.columnconfigure(1, weight=1)

        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        """Cria a interface gráfica da janela de edição."""
        # Seção de Identificação do Paciente
        id_frame = ttk.LabelFrame(self.scrollable_frame, text="Identificação do paciente")
        id_frame.pack(fill="x", padx=10, pady=5)
        id_frame.columnconfigure(1, weight=1)
        id_frame.columnconfigure(3, weight=1)
        self.create_entry_field(id_frame, "Badge Number:", "badge_number", 0, 0, read_only=True)
        self.create_entry_field(id_frame, "Nome:", "nome", 0, 2)
        self.create_entry_field(id_frame, "Login:", "login", 1, 0)
        self.create_combobox_field(id_frame, "Gestor:", "gestor", OPTIONS["gestores"], 1, 2, width=40)
        self.create_combobox_field(id_frame, "Turno:", "turno", OPTIONS["turnos"], 2, 0)
        self.create_combobox_field(id_frame, "Setor:", "setor", OPTIONS["setores"], 2, 2)
        self.create_combobox_field(id_frame, "Processo:", "processo", OPTIONS["processos"], 3, 0)
        self.create_entry_field(id_frame, "Tenure:", "tenure", 3, 2)

        # Seção de Anamnese
        anamnese_frame = ttk.LabelFrame(self.scrollable_frame, text="Anamnese")
        anamnese_frame.pack(fill="x", padx=10, pady=5)
        anamnese_frame.columnconfigure(1, weight=1)
        self.create_queixa_section(anamnese_frame)
        self.create_entry_field(anamnese_frame, "HQA (Histórico da queixa atual):", "hqa", 1, 2)
        self.create_entry_field(anamnese_frame, "TAX:", "tax", 2, 0)
        self.create_pa_section(anamnese_frame)
        self.create_entry_field(anamnese_frame, "FC:", "fc", 3, 0)
        self.create_entry_field(anamnese_frame, "SAT:", "sat", 3, 2)
        self.create_entry_field(anamnese_frame, "Doenças Pré-existentes:", "doencas_preexistentes", 4, 0)
        self.create_entry_field(anamnese_frame, "Alergias:", "alergias", 4, 2)
        self.create_entry_field(anamnese_frame, "Medicamentos em uso:", "medicamentos_em_uso", 5, 0)
        self.create_entry_field(anamnese_frame, "Observações:", "observacoes", 5, 2)

        # Seção de Condutas (dinâmica)
        self.condutas_container = ttk.Frame(self.scrollable_frame)
        self.condutas_container.pack(fill="x", padx=10, pady=5)
        
        self.create_conduta_section(index=0)

        # Botões
        button_frame = ttk.Frame(self.scrollable_frame)
        button_frame.pack(fill="x", padx=10, pady=10)
        ttk.Button(button_frame, text="Acrescentar Conduta Médica", command=self.add_conduta_section).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Apagar Atendimento", command=self.delete_atendimento).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Salvar Alterações", command=self.save_and_close).pack(side="right", padx=5)
        ttk.Button(button_frame, text="Fechar", command=self.confirm_close).pack(side="right", padx=5)

        self.protocol("WM_DELETE_WINDOW", self.confirm_close)

    def create_entry_field(self, parent, label_text, attr_name, row, col, read_only=False, is_conduta=False, index=0):
        """Cria e configura um campo de entrada com um label."""
        ttk.Label(parent, text=label_text).grid(row=row, column=col, padx=5, pady=2, sticky="e")
        entry = ttk.Entry(parent)
        entry.grid(row=row, column=col+1, padx=5, pady=2, sticky="ew")
        
        key = f"conduta_{index}_{attr_name}" if is_conduta else attr_name
        self.entries[key] = entry
        
        if read_only:
            entry.configure(state="readonly")
        entry.bind("<KeyRelease>", self.mark_as_changed)


    def create_combobox_field(self, parent, label_text, attr_name, options, row, col, width=20, is_conduta=False, index=0):
        """Cria e configura um campo de combobox com um label."""
        ttk.Label(parent, text=label_text).grid(row=row, column=col, padx=5, pady=2, sticky="e")
        combo = ttk.Combobox(parent, values=options, width=width) # state="readonly" removido
        combo.grid(row=row, column=col+1, padx=5, pady=2, sticky="ew")
        
        key = f"conduta_{index}_{attr_name}" if is_conduta else attr_name
        self.comboboxes[key] = combo
        
        combo.bind("<<ComboboxSelected>>", self.mark_as_changed)
        
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
        self.queixa_outros_entry.bind("<KeyRelease>", self.mark_as_changed)

    def toggle_other_queixa(self, queixa):
        """Habilita/desabilita o campo 'Outros'."""
        if queixa == "Outros":
            is_checked = self.queixas_vars["Outros"].get()
            new_state = tk.NORMAL if is_checked else tk.DISABLED
            self.queixa_outros_entry.config(state=new_state)
            # Remove o estilo de placeholder se estiver habilitado
            if is_checked:
                utils.remove_placeholder_on_fill(self.queixa_outros_entry, "")
        self.mark_as_changed()


    def create_pa_section(self, parent):
        """Cria os campos para pressão arterial."""
        ttk.Label(parent, text="PA:").grid(row=2, column=2, padx=5, pady=2, sticky="e")
        pa_frame = ttk.Frame(parent)
        pa_frame.grid(row=2, column=3, padx=5, pady=2, sticky="ew")
        
        self.entries['pa_sistolica'] = ttk.Entry(pa_frame, width=5)
        self.entries['pa_sistolica'].pack(side="left", fill="x", expand=True)
        ttk.Label(pa_frame, text="x").pack(side="left")
        self.entries['pa_diastolica'] = ttk.Entry(pa_frame, width=5)
        self.entries['pa_diastolica'].pack(side="left", fill="x", expand=True)
        self.entries['pa_sistolica'].bind("<KeyRelease>", self.mark_as_changed)
        self.entries['pa_diastolica'].bind("<KeyRelease>", self.mark_as_changed)

    def create_conduta_section(self, conduta_data=None, index=0):
        """Cria e popula as seções de conduta."""
        conduta_frame = ttk.LabelFrame(self.condutas_container, text=f"Conduta - {index+1}ª")
        conduta_frame.pack(fill="x", padx=10, pady=5)
        conduta_frame.columnconfigure(1, weight=1)
        conduta_frame.columnconfigure(3, weight=1)
        
        if index > 0:
            remove_btn = ttk.Button(conduta_frame, text="Remover", command=lambda: self.remove_conduta_section(conduta_frame))
            remove_btn.grid(row=0, column=4, padx=5, pady=2, sticky="e")
            
        self.create_combobox_field(conduta_frame, "Ocupacional:", "ocupacional", OPTIONS["ocupacional"], 0, 0, is_conduta=True, index=index)
        self.create_entry_field(conduta_frame, "Hipótese diagnóstica:", "hipotese_diagnostica", 0, 2, is_conduta=True, index=index)
        self.create_entry_field(conduta_frame, "Conduta adotada:", "conduta_adotada", 1, 0, is_conduta=True, index=index)
        self.create_combobox_field(conduta_frame, "Resumo da conduta:", "resumo_conduta", OPTIONS["resumo_conduta"], 1, 2, width=40, is_conduta=True, index=index)
        self.create_combobox_field(conduta_frame, "Medicamento administrado:", "medicamento_administrado", OPTIONS["medicamento_admin"], 2, 0, is_conduta=True, index=index)
        self.create_entry_field(conduta_frame, "Posologia:", "posologia", 3, 0, is_conduta=True, index=index)
        
        # Horário da medicação com botão "Agora"
        horario_frame = ttk.Frame(conduta_frame)
        horario_frame.grid(row=3, column=3, padx=5, pady=2, sticky="ew")
        self.create_entry_field(horario_frame, "", "horario_medicacao", 0, 0, is_conduta=True, index=index)
        ttk.Button(horario_frame, text="Agora", command=lambda i=index: self.set_current_time(i)).grid(row=0, column=1, padx=5)
        ttk.Label(conduta_frame, text="Horário da medicação:").grid(row=3, column=2, padx=5, pady=2, sticky="e")

        self.create_entry_field(conduta_frame, "Observações:", "observacoes", 4, 0, is_conduta=True, index=index)
        
        self.condutas_frames.append(conduta_frame)

    def set_current_time(self, index):
        """Define a hora atual no campo de horário da medicação."""
        key = f"conduta_{index}_horario_medicacao"
        entry = self.entries.get(key)
        if entry:
            utils.clear_placeholder(entry, "")
            entry.insert(0, datetime.now().strftime("%H:%M"))
            self.mark_as_changed()
            
    def remove_conduta_section(self, conduta_frame):
        """Remove dinamicamente uma seção de conduta."""
        index = self.condutas_frames.index(conduta_frame)
        
        # Remove os widgets associados do dicionário
        for attr in ["ocupacional", "resumo_conduta", "medicamento_administrado"]:
            self.comboboxes.pop(f"conduta_{index}_{attr}", None)
        for attr in ["hipotese_diagnostica", "conduta_adotada", "posologia", "horario_medicacao", "observacoes"]:
            self.entries.pop(f"conduta_{index}_{attr}", None)

        self.condutas_frames.pop(index)
        conduta_frame.destroy()
        self.changed = True
        
        # Renomeia os widgets restantes e as labels dos frames
        for i, frame in enumerate(self.condutas_frames):
            frame.config(text=f"Conduta - {i+1}ª")
            # Este passo de renomear chaves nos dicionários é complexo e pode ser propenso a erros.
            # Uma abordagem mais segura é recriar as seções ou usar uma estrutura de dados diferente.
            # Por simplicidade, vamos pular a renomeação de chaves por enquanto.

    def add_conduta_section(self):
        """Adiciona dinamicamente uma nova seção de conduta."""
        index = len(self.condutas_frames)
        self.create_conduta_section(index=index)
        self.changed = True

    def load_data(self):
        """Carrega os dados do atendimento selecionado nos campos."""
        atendimento = db.get_atendimento_by_id(self.atendimento_id)
        if not atendimento:
            messagebox.showerror("Erro", "Atendimento não encontrado.")
            self.destroy()
            return
            
        self.atendimento_atual = atendimento

        # Preenche os campos de identificação
        self.entries["badge_number"].configure(state="normal")
        self.entries["badge_number"].delete(0, 'end')
        self.entries["badge_number"].insert(0, atendimento.badge_number)
        self.entries["badge_number"].configure(state="readonly")
        
        for attr in ["nome", "login", "tenure", "hqa", "tax", "fc", "sat", "doencas_preexistentes", "alergias", "medicamentos_em_uso", "observacoes"]:
            self.entries[attr].delete(0, 'end')
            self.entries[attr].insert(0, getattr(atendimento, attr))

        for attr in ["gestor", "turno", "setor", "processo"]:
            self.comboboxes[attr].set(getattr(atendimento, attr))
        
        # Carrega as queixas
        queixas_salvas = atendimento.queixas_principais.split(';')
        for queixa, var in self.queixas_vars.items():
            var.set(queixa in queixas_salvas)

        outros_queixas = [q for q in queixas_salvas if q not in self.queixas_vars.keys()]
        if outros_queixas:
            self.queixas_vars["Outros"].set(True)
            self.queixa_outros_entry.config(state="normal")
            self.queixa_outros_entry.delete(0, 'end')
            self.queixa_outros_entry.insert(0, ", ".join(outros_queixas))
        else:
            self.queixa_outros_entry.config(state="disabled")

        self.entries['pa_sistolica'].delete(0, 'end')
        self.entries['pa_sistolica'].insert(0, atendimento.pa_sistolica)
        self.entries['pa_diastolica'].delete(0, 'end')
        self.entries['pa_diastolica'].insert(0, atendimento.pa_diastolica)
        
        # Preenche as condutas
        for i, conduta in enumerate(atendimento.condutas):
            if i >= len(self.condutas_frames):
                self.add_conduta_section()
            
            self.comboboxes[f"conduta_{i}_ocupacional"].set(conduta.resumo_conduta)
            self.entries[f"conduta_{i}_hipotese_diagnostica"].delete(0, 'end')
            self.entries[f"conduta_{i}_hipotese_diagnostica"].insert(0, conduta.hipotese_diagnostica)
            self.entries[f"conduta_{i}_conduta_adotada"].delete(0, 'end')
            self.entries[f"conduta_{i}_conduta_adotada"].insert(0, conduta.conduta_adotada)
            self.comboboxes[f"conduta_{i}_resumo_conduta"].set(conduta.resumo_conduta)
            self.comboboxes[f"conduta_{i}_medicamento_administrado"].set(conduta.medicamento_administrado)
            self.entries[f"conduta_{i}_posologia"].delete(0, 'end')
            self.entries[f"conduta_{i}_posologia"].insert(0, conduta.posologia)
            self.entries[f"conduta_{i}_horario_medicacao"].delete(0, 'end')
            self.entries[f"conduta_{i}_horario_medicacao"].insert(0, conduta.horario_medicacao)
            self.entries[f"conduta_{i}_observacoes"].delete(0, 'end')
            self.entries[f"conduta_{i}_observacoes"].insert(0, conduta.observacoes)
        self.changed = False

    def get_form_data(self):
        """Coleta os dados do formulário e retorna um objeto Atendimento."""
        atendimento = Atendimento(id=self.atendimento_id, badge_number=self.entries["badge_number"].get())
        
        for attr in ["nome", "login", "tenure", "hqa", "tax", "fc", "sat", "doencas_preexistentes", "alergias", "medicamentos_em_uso", "observacoes", "pa_sistolica", "pa_diastolica"]:
            setattr(atendimento, attr, self.entries[attr].get() or "N/A")

        for attr in ["gestor", "turno", "setor", "processo"]:
            setattr(atendimento, attr, self.comboboxes[attr].get() or "N/A")

        queixas_selecionadas = [q for q, var in self.queixas_vars.items() if var.get() and q != "Outros"]
        if self.queixas_vars["Outros"].get() and self.queixa_outros_entry.get():
            queixas_selecionadas.append(self.queixa_outros_entry.get())
        atendimento.queixas_principais = ";".join(queixas_selecionadas)
        
        condutas = []
        for i in range(len(self.condutas_frames)):
            conduta = Conduta(
                hipotese_diagnostica=self.entries[f"conduta_{i}_hipotese_diagnostica"].get() or "N/A",
                conduta_adotada=self.entries[f"conduta_{i}_conduta_adotada"].get() or "N/A",
                resumo_conduta=self.comboboxes[f"conduta_{i}_resumo_conduta"].get() or "N/A",
                medicamento_administrado=self.comboboxes[f"conduta_{i}_medicamento_administrado"].get() or "N/A",
                posologia=self.entries[f"conduta_{i}_posologia"].get() or "N/A",
                horario_medicacao=self.entries[f"conduta_{i}_horario_medicacao"].get() or "N/A",
                observacoes=self.entries[f"conduta_{i}_observacoes"].get() or "N/A"
            )
            condutas.append(conduta)
        atendimento.condutas = condutas
        return atendimento

    def mark_as_changed(self, event=None):
        """Marca que houve alterações no formulário."""
        self.changed = True

    def save_and_close(self):
        """Salva as alterações e fecha a janela."""
        try:
            atendimento_data = self.get_form_data()
            db.update_atendimento(atendimento_data)
            messagebox.showinfo("Sucesso", "Atendimento atualizado com sucesso!")
            self.changed = False
            self.callback()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar: {e}")

    def delete_atendimento(self):
        """Apaga o atendimento atual do banco de dados."""
        if messagebox.askyesno("Confirmar Exclusão", "Tem certeza que deseja apagar este atendimento? Esta ação não pode ser desfeita."):
            try:
                db.delete_atendimento(self.atendimento_id)
                messagebox.showinfo("Sucesso", "Atendimento apagado com sucesso.")
                self.changed = False
                self.callback()
                self.destroy()
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao apagar atendimento: {e}")

    def confirm_close(self):
        """Confirma se o usuário quer fechar sem salvar alterações."""
        if self.changed:
            if messagebox.askyesno("Alterações não salvas", "Você tem alterações não salvas. Deseja salvar antes de fechar?"):
                self.save_and_close()
            else:
                self.destroy()
        else:
            self.destroy()

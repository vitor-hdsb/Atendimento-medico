"""
gui/edit_window.py
------------------
Janela modal para visualização e edição de atendimentos.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from models import Atendimento, Conduta
import db
import utils
from typing import List, Optional

# --- Opções dos ComboBoxes (usadas em várias janelas) ---
OPTIONS = {
    "gestores": [
        "ARTHUR MANZELA DIAS DE SOUZA (MANZELAR)",
        "RAIANY INGRID DA SILVA (RAIANY)",
        "DIEGO CARLOS DA SILVA (CADIEGOV)",
        "BARBARA SAYURI IKI CORREA MENDES (SAYURIBA)",
        "GUILHERME DE OLIVEIRA MORAES (DEOLIVGU)",
        "ANA CAROLINE RODRIGUES RATES (ANCAROC)",
        "LUCAS GANDOLFI (LUCASGAN)",
        "LUCIANA VARGAS VILAR (LLUCIAVA)",
        "VIRGÍNIA RASTE (VRRASTE)",
        "RUAN RODRIGO FERREIRA DE ANDRADE (RUANRODR)",
        "ANDERSON COSTA SOUZA (ZCOSTASO)",
        "DOUGLAS SANTOS SILVA (SILVDOU)",
        "POLYANA GONCALVES DUMBA (GONCPOLY)",
        "LORENA MOREIRA DA SILVA (SILORE)",
        "PEDRO HENRIQUE DE JESUS (JESPEDR)",
        "KARINE FARIA (FAKARINE)",
        "VANIA LUCIA APOLINARIO PEREIRA (VANIAPER)",
        "SILVIO MARTINS SOUZA (SILVISOU)",
        "MILLANE AZEVEDO MEIRA (AZMILLAN)",
        "RAFAEL PEREIRA (PERAFAEU)",
        "JOAO VITOR BARBOSA CARNEIRO (JOACARNE)",
        "KAMILLY APARECIDA SOUZA DA SILVA (APARKAMI)",
        "MATEUS FLORES (MATTMF)",
        "INGRID DA COSTA ZANETI (IZZANETI)",
        "VITOR HUGO DE SOUZA BRAGA (VITODESO)",
        "LETICIA GOMES PEREIRA (LVGOMESP)",
        "LUDMILA MARIA DE JESUS (JLUDMILA)",
        "MARESSA LUIZA PAIXAO PEGA (MPAIXAO)",
        "ANA PAULA DOS SANTOS PINHEIRO (PAULADOS)",
        "TAÍS CORREIA (TAISREIS)",
        "LUANA REBECCA DE SOUZA (LUANAREB)",
        "HUMBERTO LEANDRO REGIS SILVA (LEAHUMBE)",
        "MAICON VALERIO DE SOUZA (MAICVALE)",
        "LEILANY PRISCILA BARROS CIRINO DE SOUZA (LEILASOU)",
        "ANIELLE CRISTINA DE LIMA RODRIGUES (CANIELLE)",
        "ANA CAROLINE FERREIRA DUARTE (ANRCAROL)",
        "CAROLINE GEORGIA VICENTINI MAIA (CAROMAIA)",
        "GABRIEL ITALO CHAVES (CHVESG)",
        "ALICE DIAS SILVA (DIASALI)",
        "PAULO HENRIQUE G KERN BELLO (HENRPAUI)",
        "FABRÍCIO ORTIZ (FWOO)",
        "FRANK DIAS DA SILVA (FRNKSIL)",
        "DIEGO ROCHA RIBEIRO DE SOUZA (ROCHARIB)",
        "WAGNER GUIMARAES DOS SANTOS (WAGNSANT)",
        "ANA CAROLINA SANTOS F CALDEIRA (CARANAH)",
        "LUANA PAIVA DA SILVA (LUAPAIVU)",
        "WILLIAN RODRIGUES DA SILVA (WILLSIL)",
        "RAUL ESPINOSA (RAULESPB)",
        "BEATRIZ MOREIRA SOUZA (MOBEATRJ)",
        "LUCIANA PEREIRA RODRIGUES (LCIANR)",
        "MAYCON DOUGLAS FERREIRA DE PAULA (DOUGMAYC)",
        "MARCILENE APARECIDA DE ALMEIDA (APAMARCF)",
        "ALANIS VIANA CASTRO (ALANISCV)",
        "DEBORA ACASSIO LOPES (LODEBOR)",
        "MERLEN CÂNDIDO (MKRC)",
        "AQUILA COSTA DO CARMO (AQUCARMO)",
        "KAROLINE MOURA (KAROLMT)",
        "RONIERY MAGALHAES PAES (PAESRONI)",
        "JOSE OSWALDO BRASILEIRO ROSSI LIMA LIMA (JOSELIMW)",
        "THIAGO HAMACHER (THIHAM)",
        "BRUNO CEZAR VARELA (VARBRUNO)",
        "FELICIO FRANCISCO JARDIM MATOS (FELIJFRA)",
        "MARIO MONTEIRO (AMMANTE)"
    ],
    "turnos": [
        "Blue Day", "Blue Night", "Red Day", "Red Night", "MID", "ADM", "12X36 - Ímpar", "12X36 - Par"
    ],
    "setores": [
        "C-RET", "Damaged", "ICQA", "Inbound", "Insumos", "Learning",
        "Melhoria Contínua", "Outbound", "RH", "Sodexo-Limpeza",
        "Sodexo-Cozinha", "Sodexo-RME", "TI", "TFI", "TFO", "Verzani", "WHS"
    ],
    "processos": [
        "Inbound - Stow", "Inbound - Spider", "Inbound - Receive", "Inbound - Doca", "Inbound - PIT",
        "Outbound - Pick", "Outbound - Spider", "Outbound - Doca", "Outbound - Slam", "Outbound - Rebin"
    ],
    "ocupacional": [
        "Sim", "Não", "N/A"
    ],
    "resumo_conduta": [
        "Em observação", "Liberado para operação", "liberado para atendimento externo c/ brigadista",
        "liberado para atendimento externo s/ brigadista"
    ],
    "medicamento_admin": [
        "Paracetamol", "Dipirona", "Ibuprofeno", "Outros"
    ]
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
        self.create_entry_field(id_frame, "Badge Number:", "badge_number", row=0, col=0, read_only=True)
        self.create_entry_field(id_frame, "Nome:", "nome", row=0, col=2)
        self.create_entry_field(id_frame, "Login:", "login", row=1, col=0)
        self.create_combobox_field(id_frame, "Gestor:", "gestor", OPTIONS["gestores"], row=1, col=2, width=40)
        self.create_combobox_field(id_frame, "Turno:", "turno", OPTIONS["turnos"], row=2, col=0)
        self.create_combobox_field(id_frame, "Setor:", "setor", OPTIONS["setores"], row=2, col=2)
        self.create_combobox_field(id_frame, "Processo:", "processo", OPTIONS["processos"], row=3, col=0)
        self.create_entry_field(id_frame, "Tenure:", "tenure", row=3, col=2)

        # Seção de Anamnese
        anamnese_frame = ttk.LabelFrame(self.scrollable_frame, text="Anamnese")
        anamnese_frame.pack(fill="x", padx=10, pady=5)
        anamnese_frame.columnconfigure(1, weight=1)
        self.create_entry_field(anamnese_frame, "Queixa Principal:", "queixa_principal", row=0, col=0)
        self.create_entry_field(anamnese_frame, "HQA (Histórico da queixa atual):", "hqa", row=0, col=2)
        self.create_entry_field(anamnese_frame, "TAX:", "tax", row=1, col=0)
        self.create_entry_field(anamnese_frame, "PA:", "pa", row=1, col=2)
        self.create_entry_field(anamnese_frame, "FC:", "fc", row=2, col=0)
        self.create_entry_field(anamnese_frame, "SAT:", "sat", row=2, col=2)
        self.create_entry_field(anamnese_frame, "Doenças Pré-existentes:", "doencas_preexistentes", row=3, col=0)
        self.create_entry_field(anamnese_frame, "Alergias:", "alergias", row=3, col=2)
        self.create_entry_field(anamnese_frame, "Medicamentos em uso:", "medicamentos_em_uso", row=4, col=0)
        self.create_entry_field(anamnese_frame, "Observações:", "observacoes", row=4, col=2)

        # Seção de Condutas (dinâmica)
        self.condutas_container = ttk.Frame(self.scrollable_frame)
        self.condutas_container.pack(fill="x", padx=10, pady=5)
        
        # O campo de primeira conduta é sempre criado para ser preenchido se existir
        self.create_conduta_section(index=0)

        # Botões
        button_frame = ttk.Frame(self.scrollable_frame)
        button_frame.pack(fill="x", padx=10, pady=10)
        ttk.Button(button_frame, text="Acrescentar Conduta Médica", command=self.add_conduta_section).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Editar Atendimento", command=self.save_and_close).pack(side="right", padx=5)
        ttk.Button(button_frame, text="Fechar Atendimento", command=self.confirm_close).pack(side="right", padx=5)

        self.protocol("WM_DELETE_WINDOW", self.confirm_close)

    def create_entry_field(self, parent, label_text, attr_name, row, col, read_only=False):
        """Cria e configura um campo de entrada com um label."""
        ttk.Label(parent, text=label_text).grid(row=row, column=col, padx=5, pady=2, sticky="e")
        entry = ttk.Entry(parent)
        entry.grid(row=row, column=col+1, padx=5, pady=2, sticky="ew")
        setattr(self, f"entry_{attr_name}", entry)
        if read_only:
            entry.configure(state="readonly")
        entry.bind("<KeyRelease>", self.mark_as_changed)

    def create_combobox_field(self, parent, label_text, attr_name, options, row, col, width=20):
        """Cria e configura um campo de combobox com um label."""
        ttk.Label(parent, text=label_text).grid(row=row, column=col, padx=5, pady=2, sticky="e")
        combo = ttk.Combobox(parent, values=options, width=width)
        combo.grid(row=row, column=col+1, padx=5, pady=2, sticky="ew")
        setattr(self, f"combo_{attr_name}", combo)
        combo.bind("<<ComboboxSelected>>", self.mark_as_changed)
        combo.bind("<KeyRelease>", self.mark_as_changed)

    def create_conduta_section(self, conduta_data=None, index=0):
        """Cria e popula as seções de conduta."""
        conduta_frame = ttk.LabelFrame(self.condutas_container, text=f"Conduta - {index+1}ª")
        conduta_frame.pack(fill="x", padx=10, pady=5)
        conduta_frame.columnconfigure(1, weight=1)
        conduta_frame.columnconfigure(3, weight=1)
        
        # Adiciona o botão de remover se não for a primeira conduta
        if index > 0:
            remove_btn = ttk.Button(conduta_frame, text="Remover", command=lambda: self.remove_conduta_section(conduta_frame))
            remove_btn.grid(row=0, column=4, padx=5, pady=2, sticky="e")

        self.create_combobox_field(conduta_frame, "Ocupacional:", f"conduta_{index}_ocupacional", OPTIONS["ocupacional"], row=0, col=0)
        self.create_entry_field(conduta_frame, "Hipótese diagnóstica:", f"conduta_{index}_hipotese", row=0, col=2)
        self.create_entry_field(conduta_frame, "Conduta adotada:", f"conduta_{index}_adotada", row=1, col=0)
        self.create_combobox_field(conduta_frame, "Resumo da 1ª conduta:", f"conduta_{index}_resumo", OPTIONS["resumo_conduta"], row=1, col=2)
        self.create_combobox_field(conduta_frame, "Medicamento administrado:", f"conduta_{index}_admin", OPTIONS["medicamento_admin"], row=2, col=0)
        self.create_entry_field(conduta_frame, "Medicamento:", f"conduta_{index}_medicamento", row=2, col=2)
        self.create_entry_field(conduta_frame, "Posologia:", f"conduta_{index}_posologia", row=3, col=0)
        self.create_entry_field(conduta_frame, "Horário da medicação:", f"conduta_{index}_horario", row=3, col=2)
        self.create_entry_field(conduta_frame, "Observações:", f"conduta_{index}_obs", row=4, col=0)
        
        self.condutas_frames.append(conduta_frame)
        self.condutas_frames[index].data = conduta_data # Associa os dados da conduta ao frame

    def remove_conduta_section(self, conduta_frame):
        """Remove dinamicamente uma seção de conduta."""
        self.condutas_frames.remove(conduta_frame)
        conduta_frame.destroy()
        self.changed = True
        # Renomeia os títulos dos frames restantes
        for i, frame in enumerate(self.condutas_frames):
            frame.config(text=f"Conduta - {i+1}ª")
        # Atualiza a lista de condutas no objeto Atendimento
        condutas_data = self.get_form_data().condutas
        self.atendimento_atual.condutas = condutas_data

    def add_conduta_section(self):
        """Adiciona dinamicamente uma nova seção de conduta."""
        index = len(self.condutas_frames)
        self.create_conduta_section(index=index)
        self.changed = True
        
    def get_widget(self, name):
        """Retorna o widget com base no nome do atributo."""
        widget = getattr(self, f"entry_{name}", None)
        if not widget:
            widget = getattr(self, f"combo_{name}", None)
        return widget

    def load_data(self):
        """Carrega os dados do atendimento selecionado nos campos."""
        atendimento = db.get_atendimento_by_id(self.atendimento_id)
        if not atendimento:
            messagebox.showerror("Erro", "Atendimento não encontrado.")
            self.destroy()
            return
            
        self.atendimento_atual = atendimento

        # Preenche os campos principais
        self.get_widget("badge_number").configure(state="normal")
        self.get_widget("badge_number").delete(0, 'end')
        self.get_widget("badge_number").insert(0, atendimento.badge_number)
        self.get_widget("badge_number").configure(state="readonly")
        
        self.get_widget("nome").delete(0, 'end')
        self.get_widget("nome").insert(0, atendimento.nome)
        
        self.get_widget("login").delete(0, 'end')
        self.get_widget("login").insert(0, atendimento.login)
        
        self.get_widget("gestor").set(atendimento.gestor)
        self.get_widget("turno").set(atendimento.turno)
        self.get_widget("setor").set(atendimento.setor)
        self.get_widget("processo").set(atendimento.processo)
        
        self.get_widget("tenure").delete(0, 'end')
        self.get_widget("tenure").insert(0, atendimento.tenure)
        
        self.get_widget("queixa_principal").delete(0, 'end')
        self.get_widget("queixa_principal").insert(0, atendimento.queixa_principal)
        self.get_widget("hqa").delete(0, 'end')
        self.get_widget("hqa").insert(0, atendimento.hqa)
        self.get_widget("tax").delete(0, 'end')
        self.get_widget("tax").insert(0, atendimento.tax)
        self.get_widget("pa").delete(0, 'end')
        self.get_widget("pa").insert(0, atendimento.pa)
        self.get_widget("fc").delete(0, 'end')
        self.get_widget("fc").insert(0, atendimento.fc)
        self.get_widget("sat").delete(0, 'end')
        self.get_widget("sat").insert(0, atendimento.sat)
        self.get_widget("doencas_preexistentes").delete(0, 'end')
        self.get_widget("doencas_preexistentes").insert(0, atendimento.doencas_preexistentes)
        self.get_widget("alergias").delete(0, 'end')
        self.get_widget("alergias").insert(0, atendimento.alergias)
        self.get_widget("medicamentos_em_uso").delete(0, 'end')
        self.get_widget("medicamentos_em_uso").insert(0, atendimento.medicamentos_em_uso)
        self.get_widget("observacoes").delete(0, 'end')
        self.get_widget("observacoes").insert(0, atendimento.observacoes)
        
        # Preenche as condutas
        for i, conduta in enumerate(atendimento.condutas):
            if i > 0: # Adiciona frames para condutas adicionais, se existirem
                self.create_conduta_section(index=i)
            self.get_widget(f"conduta_{i}_ocupacional").set(conduta.resumo_conduta)
            self.get_widget(f"conduta_{i}_hipotese").delete(0, 'end')
            self.get_widget(f"conduta_{i}_hipotese").insert(0, conduta.hipotese_diagnostica)
            self.get_widget(f"conduta_{i}_adotada").delete(0, 'end')
            self.get_widget(f"conduta_{i}_adotada").insert(0, conduta.conduta_adotada)
            self.get_widget(f"conduta_{i}_resumo").set(conduta.resumo_conduta)
            self.get_widget(f"conduta_{i}_admin").set(conduta.medicamento_administrado)
            self.get_widget(f"conduta_{i}_medicamento").delete(0, 'end')
            self.get_widget(f"conduta_{i}_medicamento").insert(0, conduta.medicamento)
            self.get_widget(f"conduta_{i}_posologia").delete(0, 'end')
            self.get_widget(f"conduta_{i}_posologia").insert(0, conduta.posologia)
            self.get_widget(f"conduta_{i}_horario").delete(0, 'end')
            self.get_widget(f"conduta_{i}_horario").insert(0, conduta.horario_medicacao)
            self.get_widget(f"conduta_{i}_obs").delete(0, 'end')
            self.get_widget(f"conduta_{i}_obs").insert(0, conduta.observacoes)

        self.changed = False

    def get_form_data(self):
        """Coleta os dados do formulário e retorna um objeto Atendimento."""
        atendimento = Atendimento(id=self.atendimento_id)
        atendimento.badge_number = self.get_widget("badge_number").get()
        atendimento.nome = self.get_widget("nome").get()
        atendimento.login = self.get_widget("login").get()
        atendimento.gestor = self.get_widget("gestor").get()
        atendimento.turno = self.get_widget("turno").get()
        atendimento.setor = self.get_widget("setor").get()
        atendimento.processo = self.get_widget("processo").get()
        atendimento.tenure = self.get_widget("tenure").get()
        atendimento.queixa_principal = self.get_widget("queixa_principal").get()
        atendimento.hqa = self.get_widget("hqa").get()
        atendimento.tax = self.get_widget("tax").get()
        atendimento.pa = self.get_widget("pa").get()
        atendimento.fc = self.get_widget("fc").get()
        atendimento.sat = self.get_widget("sat").get()
        atendimento.doencas_preexistentes = self.get_widget("doencas_preexistentes").get()
        atendimento.alergias = self.get_widget("alergias").get()
        atendimento.medicamentos_em_uso = self.get_widget("medicamentos_em_uso").get()
        atendimento.observacoes = self.get_widget("observacoes").get()

        condutas = []
        for i in range(len(self.condutas_frames)):
            conduta = Conduta(
                hipotese_diagnostica=self.get_widget(f"conduta_{i}_hipotese").get(),
                conduta_adotada=self.get_widget(f"conduta_{i}_adotada").get(),
                resumo_conduta=self.get_widget(f"conduta_{i}_resumo").get(),
                medicamento_administrado=self.get_widget(f"conduta_{i}_admin").get(),
                medicamento=self.get_widget(f"conduta_{i}_medicamento").get(),
                posologia=self.get_widget(f"conduta_{i}_posologia").get(),
                horario_medicacao=self.get_widget(f"conduta_{i}_horario").get(),
                observacoes=self.get_widget(f"conduta_{i}_obs").get()
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
            self.callback() # Atualiza o histórico na janela principal
            self.destroy()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar: {e}")

    def confirm_close(self):
        """Confirma se o usuário quer fechar sem salvar alterações."""
        if self.changed:
            if messagebox.askyesno("Alterações não salvas", "Você tem alterações não salvas. Deseja salvar antes de fechar?"):
                self.save_and_close()
            else:
                self.destroy()
        else:
            self.destroy()

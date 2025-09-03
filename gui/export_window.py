"""
gui/export_window.py
--------------------
Janela modal para exportação de dados para CSV.
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, timedelta
import db
import utils

class ExportWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Exportar Dados")
        self.geometry("400x300")
        self.parent = parent
        
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill="both", expand=True)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

        self.placeholders = {}

        self.periodo_var = tk.StringVar(value="hoje")
        
        ttk.Label(main_frame, text="Selecione o período para exportar:", font=("Arial", 12)).pack(pady=10)
        
        ttk.Radiobutton(main_frame, text="Dia Atual", variable=self.periodo_var, value="hoje").pack(anchor="w", padx=20)
        ttk.Radiobutton(main_frame, text="Semana ISO", variable=self.periodo_var, value="semana").pack(anchor="w", padx=20)
        
        semana_frame = ttk.Frame(main_frame)
        semana_frame.pack(fill="x", padx=30)
        semana_frame.columnconfigure(0, weight=1)
        self.semana_entry = ttk.Entry(semana_frame)
        self.semana_entry.pack(side="left", padx=5)
        self.semana_entry.bind("<FocusIn>", lambda e: self.periodo_var.set("semana"))
        self.placeholders["semana_entry"] = "Ex: 25"
        utils.setup_placeholder(self.semana_entry, self.placeholders["semana_entry"])

        ttk.Radiobutton(main_frame, text="Últimos 30 dias", variable=self.periodo_var, value="30dias").pack(anchor="w", padx=20)
        ttk.Radiobutton(main_frame, text="Período personalizado", variable=self.periodo_var, value="personalizado").pack(anchor="w", padx=20)
        
        self.custom_frame = ttk.Frame(main_frame)
        self.custom_frame.pack(anchor="w", padx=30, pady=5)
        
        ttk.Label(self.custom_frame, text="Início (YYYY-MM-DD):").pack(side="left", padx=5)
        self.start_date_entry = ttk.Entry(self.custom_frame, width=15)
        self.start_date_entry.pack(side="left", padx=5)
        self.start_date_entry.bind("<FocusIn>", lambda e: self.periodo_var.set("personalizado"))
        self.placeholders["start_date_entry"] = "YYYY-MM-DD"
        utils.setup_placeholder(self.start_date_entry, self.placeholders["start_date_entry"])
        
        ttk.Label(self.custom_frame, text="Fim (YYYY-MM-DD):").pack(side="left", padx=5)
        self.end_date_entry = ttk.Entry(self.custom_frame, width=15)
        self.end_date_entry.pack(side="left", padx=5)
        self.end_date_entry.bind("<FocusIn>", lambda e: self.periodo_var.set("personalizado"))
        self.placeholders["end_date_entry"] = "YYYY-MM-DD"
        utils.setup_placeholder(self.end_date_entry, self.placeholders["end_date_entry"])
        
        ttk.Button(main_frame, text="Gerar CSV", command=self.generate_csv).pack(pady=20)

    def generate_csv(self):
        """Executa a exportação com base no período selecionado."""
        periodo = self.periodo_var.get()
        start_date, end_date, week_iso = None, None, None
        
        if periodo == "hoje":
            start_date = datetime.now().strftime("%Y-%m-%d")
            end_date = start_date
        elif periodo == "semana":
            try:
                week_iso_str = self.semana_entry.get()
                if week_iso_str == self.placeholders["semana_entry"]:
                    messagebox.showerror("Erro de Formato", "Por favor, insira um número de semana ISO válido.")
                    return
                week_iso = int(week_iso_str)
            except ValueError:
                messagebox.showerror("Erro de Formato", "Por favor, insira um número de semana ISO válido.")
                return
        elif periodo == "30dias":
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        elif periodo == "personalizado":
            start_date = self.start_date_entry.get()
            end_date = self.end_date_entry.get()
            if start_date == self.placeholders["start_date_entry"] or end_date == self.placeholders["end_date_entry"]:
                messagebox.showerror("Erro de Formato", "Por favor, insira as datas no formato YYYY-MM-DD.")
                return
            try:
                datetime.strptime(start_date, "%Y-%m-%d")
                datetime.strptime(end_date, "%Y-%m-%d")
            except ValueError:
                messagebox.showerror("Erro de Formato", "Por favor, insira as datas no formato YYYY-MM-DD.")
                return

        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("Arquivos CSV", "*.csv")],
            initialfile=f"atendimentos_export_{datetime.now().strftime('%Y-%m-%d')}.csv"
        )
        
        if filepath:
            try:
                db.export_to_csv(filepath, start_date, end_date, week_iso)
                messagebox.showinfo("Sucesso", f"Dados exportados com sucesso para:\n{filepath}")
                self.destroy()
            except Exception as e:
                messagebox.showerror("Erro de Exportação", f"Ocorreu um erro ao exportar os dados: {e}")

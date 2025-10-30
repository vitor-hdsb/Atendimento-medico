"""
main.py
-------
Ponto de entrada da aplicação de atendimentos médicos.
"""
import db
import gui.main_window as main_window
import config_manager
import tkinter as tk
from tkinter import filedialog, messagebox
import os

def select_database_path(initial=False, parent_window=None):
    """Pede ao usuário para selecionar o arquivo de banco de dados."""
    if initial:
        message = "Arquivo de configuração não encontrado ou inválido.\nPor favor, selecione o arquivo do banco de dados (atendimentos.db)."
        title = "Selecionar Banco de Dados (Primeira Execução)"
    else:
        message = "Selecione o novo arquivo do banco de dados (atendimentos.db)."
        title = "Selecionar Banco de Dados"
        
    # Usa parent_window se fornecido para o filedialog
    filepath = filedialog.askopenfilename(
        parent=parent_window, # Adiciona parent
        title=title,
        filetypes=[("SQLite Database", "*.db"), ("Todos os arquivos", "*.*")],
        initialdir=os.getcwd() # Começa no diretório atual
    )
    if filepath:
        # Garante que o db.py importado tenha a função set_db_path
        if db.set_db_path(filepath): 
            config_manager.save_db_path(filepath) # Salva o caminho válido
            return filepath
        else:
            messagebox.showerror("Erro", f"O caminho selecionado não é válido ou o diretório não existe:\n{filepath}", parent=parent_window)
            return select_database_path(initial, parent_window) # Pede novamente
    else:
        # O usuário cancelou
        if initial:
            # Não mostra erro fatal aqui, a lógica de loop em initialize_app tratará isso
            return None
        else:
            return None # Retorna None se o usuário cancelar a mudança

def initialize_app():
    """Carrega config, pede DB se necessário e inicia a GUI."""
    
    # --- LÓGICA DE INICIALIZAÇÃO REVISADA ---
    
    # 1. Crie a janela principal primeiro, mas mantenha-a oculta
    #    Isso nos dá uma 'root' estável para todos os diálogos.
    try:
        app = main_window.MainWindow()
        app.withdraw() # Esconde a janela principal
    except Exception as e:
        messagebox.showerror("Erro Crítico na GUI", f"Falha ao inicializar a interface gráfica:\n{e}")
        return

    db_path = config_manager.load_db_path()
    db_initialized = False

    while not db_initialized:
        # 2. Se não há caminho, ou o caminho falhou, pede um novo
        if not db_path:
            db_path = select_database_path(initial=True, parent_window=app)
            if not db_path:
                # Usuário cancelou a seleção inicial. Fechar o app.
                messagebox.showerror("Erro Fatal", "Nenhum banco de dados selecionado. A aplicação será fechada.", parent=app)
                app.destroy()
                return # Sai da aplicação

        # 3. Tenta definir o caminho e inicializar o DB
        if not db.set_db_path(db_path):
            messagebox.showerror("Erro de Caminho", f"O caminho do banco de dados não pôde ser definido:\n{db_path}", parent=app)
            db_path = None # Força pedir novamente
            continue # Volta ao início do loop

        if not db.init_db():
            messagebox.showerror("Erro de Banco de Dados", f"Não foi possível inicializar ou ler o banco de dados em:\n{db_path}\n\nO arquivo pode estar corrompido ou você não tem permissão.\nPor favor, selecione um arquivo válido.", parent=app)
            db_path = None # Força pedir novamente
            continue # Volta ao início do loop

        # 4. Se chegou aqui, o DB está OK
        db_initialized = True

    # 5. DB está pronto, agora mostre a janela principal
    app.deiconify() # Mostra a janela
    
    # O setup_menu() já é chamado dentro do __init__ da MainWindow
    # A atualização do histórico também
    
    app.mainloop()


if __name__ == "__main__":
    initialize_app()


"""
main.py
-------
Ponto de entrada da aplicação de atendimentos médicos.
"""
import db
import gui.main_window as main_window
import config_manager # Importa o gerenciador de config
import tkinter as tk
from tkinter import filedialog, messagebox
import os

def select_database_path(initial=False):
    """Pede ao usuário para selecionar o arquivo de banco de dados."""
    if initial:
        message = "Arquivo de configuração não encontrado ou inválido.\nPor favor, selecione o arquivo do banco de dados (atendimentos.db)."
        title = "Selecionar Banco de Dados (Primeira Execução)"
    else:
        message = "Selecione o novo arquivo do banco de dados (atendimentos.db)."
        title = "Selecionar Banco de Dados"
        
    # Mostra mensagem antes do filedialog (opcional)
    # root = tk.Tk() # Cria uma janela raiz temporária se não houver outra
    # root.withdraw() # Esconde a janela raiz
    # messagebox.showinfo(title, message, parent=None) # parent=None para não depender da main_window ainda
    # root.destroy()

    filepath = filedialog.askopenfilename(
        title=title,
        filetypes=[("SQLite Database", "*.db"), ("Todos os arquivos", "*.*")],
        initialdir=os.getcwd() # Começa no diretório atual
    )
    if filepath:
        if db.set_db_path(filepath):
            config_manager.save_db_path(filepath) # Salva o caminho válido
            return filepath
        else:
            messagebox.showerror("Erro", f"O caminho selecionado não é válido ou o diretório não existe:\n{filepath}", parent=None)
            return select_database_path(initial) # Pede novamente
    else:
        # O usuário cancelou
        if initial:
            messagebox.showerror("Erro Fatal", "Nenhum banco de dados selecionado. A aplicação será fechada.", parent=None)
            return None
        else:
            return None # Retorna None se o usuário cancelar a mudança

def initialize_app():
    """Carrega config, pede DB se necessário e inicia a GUI."""
    db_path = config_manager.load_db_path()

    if not db_path:
        # Pede ao usuário para selecionar na primeira vez ou se o caminho salvo for inválido
        db_path = select_database_path(initial=True)
        if not db_path:
            return # Fecha a aplicação se o usuário cancelar na inicialização

    # Define o caminho no db.py (redundante se select_database_path já fez, mas garante)
    if not db.set_db_path(db_path):
         # Se set_db_path falhar aqui (improvável se select_database_path funcionou), trata
         messagebox.showerror("Erro Fatal", "Falha ao definir o caminho do banco de dados. Verifique as permissões.")
         return

    # Tenta inicializar (criar tabelas se necessário)
    if not db.init_db():
         messagebox.showerror("Erro Fatal", f"Não foi possível inicializar o banco de dados em:\n{db_path}\nVerifique o arquivo ou permissões.")
         # Poderia tentar selecionar outro DB aqui? Ou apenas sair?
         # Tenta pedir outro DB:
         new_path = select_database_path(initial=True) # Força a seleção novamente
         if not new_path or not db.init_db(): # Tenta inicializar com o novo caminho
              return # Sai se falhar novamente

    # Cria a janela principal da aplicação
    app = main_window.MainWindow()
    
    # Adiciona a opção de menu para mudar o DB
    def change_db():
        new_path = select_database_path(initial=False)
        if new_path:
            # TODO: Idealmente, recarregar a conexão e atualizar a GUI
            # Por enquanto, apenas informa e pede reinício
            messagebox.showinfo("Banco de Dados Alterado", "O caminho do banco de dados foi alterado.\nPor favor, reinicie a aplicação para usar o novo banco de dados.", parent=app)
            # app.destroy() # Força o fechamento
            # Alternativa: tentar recarregar dados
            try:
                if db.init_db(): # Verifica/cria tabelas no novo DB
                     app.refresh_history_tree() # Atualiza o histórico
                     app.clear_form(clear_all=True) # Limpa o formulário
                     messagebox.showinfo("Banco de Dados Alterado", f"Aplicação agora usando:\n{new_path}", parent=app)
                else:
                     messagebox.showerror("Erro", "Não foi possível inicializar o novo banco de dados.", parent=app)
            except Exception as e:
                 messagebox.showerror("Erro ao Recarregar", f"Erro ao tentar usar o novo banco de dados: {e}", parent=app)


    menu_bar = tk.Menu(app)
    file_menu = tk.Menu(menu_bar, tearoff=0)
    file_menu.add_command(label="Selecionar Banco de Dados...", command=change_db)
    file_menu.add_separator()
    file_menu.add_command(label="Sair", command=app.quit)
    menu_bar.add_cascade(label="Arquivo", menu=file_menu)
    app.config(menu=menu_bar)

    # Executa o loop principal da interface gráfica
    app.mainloop()

if __name__ == "__main__":
    initialize_app()

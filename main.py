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

# Move a função para fora para ser acessível por outros módulos
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
        # Garanta que o db.py importado tenha a função set_db_path
        if db.set_db_path(filepath): 
            config_manager.save_db_path(filepath) # Salva o caminho válido
            return filepath
        else:
            messagebox.showerror("Erro", f"O caminho selecionado não é válido ou o diretório não existe:\n{filepath}", parent=parent_window)
            return select_database_path(initial, parent_window) # Pede novamente
    else:
        # O usuário cancelou
        if initial:
            messagebox.showerror("Erro Fatal", "Nenhum banco de dados selecionado. A aplicação será fechada.", parent=parent_window)
            return None
        else:
            return None # Retorna None se o usuário cancelar a mudança

def initialize_app():
    """Carrega config, pede DB se necessário e inicia a GUI."""
    db_path = config_manager.load_db_path()

    root_temp = None # Janela temporária para diálogos iniciais
    if not db_path:
        # Cria janela temporária se não houver caminho salvo
        root_temp = tk.Tk()
        root_temp.withdraw()
        # Pede ao usuário para selecionar na primeira vez ou se o caminho salvo for inválido
        db_path = select_database_path(initial=True, parent_window=root_temp)
        if not db_path:
            if root_temp: root_temp.destroy()
            return # Fecha a aplicação se o usuário cancelar na inicialização
        # Destroi janela temporária após seleção
        if root_temp: root_temp.destroy()
        root_temp = None


    # Define o caminho no db.py (redundante se select_database_path já fez, mas garante)
    if not db.set_db_path(db_path):
         # Se set_db_path falhar aqui (improvável se select_database_path funcionou), trata
         if not root_temp: # Cria janela temporária se ainda não existir
             root_temp = tk.Tk()
             root_temp.withdraw()
         messagebox.showerror("Erro Fatal", "Falha ao definir o caminho do banco de dados. Verifique as permissões.", parent=root_temp)
         if root_temp: root_temp.destroy()
         return

    # Tenta inicializar (criar tabelas se necessário)
    if not db.init_db():
         if not root_temp: # Cria janela temporária se ainda não existir
             root_temp = tk.Tk()
             root_temp.withdraw()
         messagebox.showerror("Erro Fatal", f"Não foi possível inicializar o banco de dados em:\n{db_path}\nVerifique o arquivo ou permissões.", parent=root_temp)

         # Tenta pedir outro DB:
         new_path = select_database_path(initial=True, parent_window=root_temp) # Força a seleção novamente
         if not new_path or not db.init_db(): # Tenta inicializar com o novo caminho
              if root_temp: root_temp.destroy()
              return # Sai se falhar novamente
         # Destroi janela temporária se foi usada
         if root_temp: root_temp.destroy()
         root_temp = None

    # Cria a janela principal da aplicação
    app = main_window.MainWindow()
    
    # Adiciona a opção de menu para mudar o DB (chama o método da MainWindow)
    menu_bar = tk.Menu(app)
    file_menu = tk.Menu(menu_bar, tearoff=0)
    # A função agora está em MainWindow, chamada pelo botão e pelo menu
    file_menu.add_command(label="Selecionar Banco de Dados...", command=app.change_database) 
    file_menu.add_separator()
    file_menu.add_command(label="Sair", command=app.quit)
    menu_bar.add_cascade(label="Arquivo", menu=file_menu)
    app.config(menu=menu_bar)

    # Executa o loop principal da interface gráfica
    app.mainloop()

if __name__ == "__main__":
    initialize_app()


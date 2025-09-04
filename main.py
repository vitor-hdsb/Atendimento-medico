"""
main.py
-------
Ponto de entrada da aplicação de atendimentos médicos.
"""
import db
import gui.main_window as main_window

def main():
    """Função principal para iniciar a aplicação."""
    # 1. Inicializa o banc  o de dados
    db.init_db()
    
    # 2. Cria a janela principal da aplicação
    app = main_window.MainWindow()
    
    # 3. Executa o loop principal da interface gráfica
    app.mainloop()

if __name__ == "__main__":
    main()
"""
gui/constants.py
----------------
Armazena constantes, como listas de opções para comboboxes e queixas,
para serem usadas em diferentes partes da GUI.
"""

# --- Listas para Anamnese ---

SINTOMAS = [
    "Dor", "Ardência/Queimação", "Coçeira/Irritaçao", "Corte", 
    "Torção/Distensão", "Vertigem", "Vômito", "Náuseas", "Fraqueza", 
    "Confusão mental", "Abrasão/Escoriação", "Ansiedade", 
    "Absorvente", "Trabalho em altura", "N/A"
]

REGIOES = [
    "Cabeça", "Rosto", "Olhos", "Braços", "Mãos/Dedos", "Peitoral/Seios", 
    "Barriga/Estômago", "Pernas", "Pé", "Tornozelo", "Menstrual", "N/A"
]


# --- Opções dos ComboBoxes ---
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
    "ocupacional": ["Sim", "Não", "N/A"], # Mantido caso seja usado em outro local
    "resumo_conduta": [
        "Em observação", "Liberado para operação", 
        "Liberado para atendimento externo c/ brigadista", 
        "Liberado para atendimento externo s/ brigadista",
        "Apto para trabalho em altura", # Adicionado
        "Inapto para trabalho em altura", # Adicionado
        "N/A"
    ],
    "medicamento_admin": ["Paracetamol", "Dipirona", "Ibuprofeno", "Outros", "N/A"]
}

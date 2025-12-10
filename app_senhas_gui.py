
import os
import csv
import string
import secrets
from datetime import datetime

# === Configuração ===
CHARSET = string.digits + string.ascii_uppercase + string.ascii_lowercase  # 0-9 A-Z a-z (62 chars)
sysrand = secrets.SystemRandom()
MIN_LENGTH = 1
MAX_LENGTH = 64  # limite prático para evitar exageros e manter performance
DEFAULT_LENGTH = 5

# === Funções de senha ===
def gerar_senha(length=DEFAULT_LENGTH, require_all=False):
    """
    Gera uma senha de 'length' caracteres.
    Se require_all=True, garante ao menos: 1 dígito, 1 maiúscula e 1 minúscula.
    """
    if length < MIN_LENGTH or length > MAX_LENGTH:
        raise ValueError(f"Comprimento inválido. Use entre {MIN_LENGTH} e {MAX_LENGTH}.")
    if require_all and length < 3:
        raise ValueError("Para exigir composição mínima, use comprimento ≥ 3.")

    if not require_all:
        return ''.join(secrets.choice(CHARSET) for _ in range(length))

    # Garante ao menos 1 de cada tipo
    partes = [
        secrets.choice(string.digits),
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.ascii_lowercase),
    ]
    # Completa até 'length' com qualquer char do charset
    while len(partes) < length:
        partes.append(secrets.choice(CHARSET))
    # Embaralha de forma criptográfica
    sysrand.shuffle(partes)
    return ''.join(partes)

def gerar_lista(qtd, length=DEFAULT_LENGTH, unique=False, require_all=False):
    """
    Gera 'qtd' senhas com 'length' caracteres.
    Se unique=True, evita repetições.
    """
    if qtd < 1 or qtd > 10000:
        raise ValueError("Informe uma quantidade entre 1 e 10.000.")
    if length < MIN_LENGTH or length > MAX_LENGTH:
        raise ValueError(f"Comprimento inválido. Use entre {MIN_LENGTH} e {MAX_LENGTH}.")
    if require_all and length < 3:
        raise ValueError("Para exigir composição mínima, use comprimento ≥ 3.")

    # Se pediu únicas, verifica se é possível
    if unique:
        total_combinacoes = len(CHARSET) ** length  # 62^length
        if qtd > total_combinacoes:
            raise ValueError(
                f"Você solicitou {qtd} senhas únicas, mas só existem {total_combinacoes} combinações possíveis "
                f"para comprimento {length}. Reduza a quantidade ou aumente o comprimento."
            )

    if not unique:
        return [gerar_senha(length=length, require_all=require_all) for _ in range(qtd)]

    # Únicas
    senhas = set()
    while len(senhas) < qtd:
        senhas.add(gerar_senha(length=length, require_all=require_all))
    return list(senhas)

def salvar_csv(caminho, senhas):
    """Salva CSV com cabeçalho 'senha'."""
    with open(caminho, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['senha'])
        for s in senhas:
            w.writerow([s])

def abrir_pasta_do_arquivo(caminho):
    """Tenta abrir a pasta do arquivo no sistema operacional."""
    try:
        pasta = os.path.dirname(os.path.abspath(caminho))
        if os.name == 'nt':  # Windows
            os.startfile(pasta)
        elif os.name == 'posix':  # Linux/Mac
            import subprocess, sys
            if sys.platform == 'darwin':
                subprocess.run(['open', pasta])
            else:
                subprocess.run(['xdg-open', pasta])
    except Exception:
        pass

# === GUI ===
import FreeSimpleGUI as sg

def set_theme_safe(name="SystemDefault"):
    """Aplica tema se a API existir; caso contrário, segue sem tema global."""
    try:
        if hasattr(sg, "theme") and callable(getattr(sg, "theme")):
            sg.theme(name); return
        if hasattr(sg, "ChangeLookAndFeel") and callable(getattr(sg, "ChangeLookAndFeel")):
            sg.ChangeLookAndFeel(name); return
    except Exception:
        pass

set_theme_safe("SystemDefault")

layout = [
    [sg.Text("Gerador de Senhas", font=("Segoe UI", 12, "bold"))],
    [
        sg.Text("Quantidade (1–10.000):"),
        sg.Input(default_text="100", size=(7,1), key="-QTD-"),
        sg.Text("Comprimento (1–64):"),
        sg.Input(default_text=str(DEFAULT_LENGTH), size=(6,1), key="-LEN-"),
    ],
    [sg.Checkbox("Evitar repetições (senhas únicas)", default=True, key="-UNQ-")],
    [sg.Checkbox("Exigir ao menos 1 maiúscula, 1 minúscula e 1 número", default=False, key="-REQ-")],
    [
        sg.Button("Gerar", key="-GERAR-", bind_return_key=True),
        sg.Button("Salvar CSV...", key="-SALVAR-"),
        sg.Button("Abrir pasta", key="-ABRIR-"),
        sg.Button("Limpar", key="-LIMPAR-"),
        sg.Button("Copiar última", key="-COPIA-ULT-", tooltip="Copia a última senha gerada"),
        sg.Button("Copiar todas", key="-COPIA-TOD-", tooltip="Copia todas as senhas geradas"),
        sg.Button("Sair")
    ],
    [sg.Text("Resultado:")],
    [sg.Multiline("", size=(60,15), key="-OUT-", disabled=True, autoscroll=True, font=("Consolas", 10))]
]

window = sg.Window("Gerador de Senhas", layout)
senhas_atuais = []
ultimo_arquivo = None
ultimo_length = DEFAULT_LENGTH  # para referência no texto

while True:
    event, values = window.read()
    if event in (sg.WIN_CLOSED, "Sair"):
        break

    if event == "-GERAR-":
        # Valida quantidade e comprimento
        try:
            qtd = int(str(values["-QTD-"]).strip())
        except (ValueError, TypeError):
            sg.popup_error("A quantidade precisa ser um número inteiro entre 1 e 10.000.")
            continue
        
        # Valida comprimento
        raw_length = str(values["-LEN-"]).strip()
        if not raw_length:
            length = 12  # valor padrão mais seguro
        else:
            try:
                length = int(raw_length)
            except ValueError:
                sg.popup_error(f"O comprimento precisa ser um número inteiro entre {MIN_LENGTH} e {MAX_LENGTH}.")
                continue
        
        if length < MIN_LENGTH or length > MAX_LENGTH:
            sg.popup_error(f"Comprimento inválido. Use entre {MIN_LENGTH} e {MAX_LENGTH}.")
            continue


        try:
            senhas_atuais = gerar_lista(
                qtd,
                length=length,
                unique=values["-UNQ-"],
                require_all=values["-REQ-"]
            )
            ultimo_length = length
        except Exception as e:
            sg.popup_error(f"Erro ao gerar: {e}")
            continue

        # Exibe
        window["-OUT-"].update("")
        window["-OUT-"].print(f"Gerado: {len(senhas_atuais)} senhas (comprimento = {ultimo_length}).\n")
        for s in senhas_atuais:
            window["-OUT-"].print(s)
        ultimo_arquivo = None

    if event == "-SALVAR-":
        if not senhas_atuais:
            sg.popup("Nada para salvar. Gere as senhas primeiro.")
            continue
        nome_sugerido = f"senhas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        caminho = sg.popup_get_file(
            "Escolha onde salvar",
            save_as=True,
            default_extension=".csv",
            file_types=(("CSV", "*.csv"),),
            default_path=nome_sugerido,
            no_window=True
        )
        if not caminho:
            continue
        try:
            salvar_csv(caminho, senhas_atuais)
            ultimo_arquivo = caminho
            sg.popup(f"Arquivo salvo:\n{os.path.basename(caminho)}")
        except Exception as e:
            sg.popup_error(f"Erro ao salvar: {e}")

    if event == "-ABRIR-":
        if ultimo_arquivo:
            abrir_pasta_do_arquivo(ultimo_arquivo)
        else:
            sg.popup("Nenhum arquivo salvo ainda.")

    if event == "-LIMPAR-":
        window["-OUT-"].update("")
        senhas_atuais = []
        ultimo_arquivo = None

    if event == "-COPIA-ULT-":
        # Copia a última senha gerada (ignora a linha de resumo)
        linhas = window["-OUT-"].get().strip().splitlines()
        if linhas:
            ultima = linhas[-1]
            if ultima.startswith("Gerado:") and len(linhas) > 1:
                ultima = linhas[-2]
            sg.clipboard_set(ultima)
            sg.popup("Última senha copiada!")
        else:
            sg.popup("Nada para copiar.")

    if event == "-COPIA-TOD-":
        if senhas_atuais:
            sg.clipboard_set("\n".join(senhas_atuais))
            sg.popup("Todas as senhas copiadas!")
        else:
            sg.popup("Nada para copiar. Gere as senhas primeiro.")

window.close()

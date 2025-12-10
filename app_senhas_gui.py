
import os
import csv
import string
import secrets
from datetime import datetime

# === Configuração de limites ===
MIN_LENGTH = 1
MAX_LENGTH = 64
DEFAULT_LENGTH = 12  # troque para 5 se quiser manter seu padrão anterior

# === Funções de senha (comprimento variável) ===
CHARSET = string.digits + string.ascii_uppercase + string.ascii_lowercase
sysrand = secrets.SystemRandom()

def gerar_senha(length=DEFAULT_LENGTH, require_all=False):
    """Gera uma senha de 'length' caracteres. Se require_all=True, garante A/a/0-9."""
    if length < MIN_LENGTH or length > MAX_LENGTH:
        raise ValueError(f"Comprimento inválido. Use entre {MIN_LENGTH} e {MAX_LENGTH}.")
    if require_all and length < 3:
        raise ValueError("Para exigir composição mínima, use comprimento ≥ 3.")

    if not require_all:
        return ''.join(secrets.choice(CHARSET) for _ in range(length))

    # Garante ao menos 1 dígito, 1 maiúscula e 1 minúscula
    partes = [
        secrets.choice(string.digits),
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.ascii_lowercase),
    ]
    while len(partes) < length:
        partes.append(secrets.choice(CHARSET))
    sysrand.shuffle(partes)
    return ''.join(partes)

def gerar_lista(qtd, length=DEFAULT_LENGTH, unique=False, require_all=False):
    """Gera 'qtd' senhas. Se unique=True, evita repetições. Respeita 'length'."""
    if qtd < 1 or qtd > 10000:
        raise ValueError("Informe um número entre 1 e 10.000.")
    if length < MIN_LENGTH or length > MAX_LENGTH:
        raise ValueError(f"Comprimento inválido. Use entre {MIN_LENGTH} e {MAX_LENGTH}.")
    if require_all and length < 3:
        raise ValueError("Para exigir composição mínima, use comprimento ≥ 3.")

    if not unique:
        return [gerar_senha(length=length, require_all=require_all) for _ in range(qtd)]

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
        elif os.name == 'posix':
            import subprocess, sys
            if sys.platform == 'darwin':
                subprocess.run(['open', pasta])
            else:
                subprocess.run(['xdg-open', pasta])
    except Exception:
        # Não interrompe a aplicação se não conseguir abrir a pasta
        pass

# === GUI ===
import FreeSimpleGUI as sg  # usar FreeSimpleGUI

def set_theme_safe(name="SystemDefault"):
    """Aplica tema se a API existir; caso contrário, segue sem tema global."""
    try:
        if hasattr(sg, "theme") and callable(getattr(sg, "theme")):
            sg.theme(name)
            return
        if hasattr(sg, "ChangeLookAndFeel") and callable(getattr(sg, "ChangeLookAndFeel")):
            sg.ChangeLookAndFeel(name)
            return
    except Exception:
        # Qualquer erro aqui não deve travar a GUI
        pass

set_theme_safe("SystemDefault")

layout = [
    [sg.Text("Gerador de Senhas", font=("Segoe UI", 12, "bold"))],
    [
        sg.Text("Quantidade (1–10.000):"),
        sg.Input(default_text="100", size=(8,1), key="-QTD-"),
        sg.Text("Comprimento (1–64):"),
        sg.Input(default_text=str(DEFAULT_LENGTH), size=(6,1), key="-LEN-"),
    ],
    [sg.Checkbox("Evitar repetições (senhas únicas)", default=True, key="-UNQ-")],
    [sg.Checkbox("Exigir ao menos 1 maiúscula, 1 minúscula e 1 número", default=False, key="-REQ-")],
    [sg.Button("Gerar", key="-GERAR-", bind_return_key=True),
     sg.Button("Salvar CSV...", key="-SALVAR-"),
     sg.Button("Abrir pasta", key="-ABRIR-"),
     sg.Button("Limpar", key="-LIMPAR-"),
     sg.Button("Sair")],
    [sg.Text("Resultado:")],
    [sg.Multiline("", size=(60,15), key="-OUT-", disabled=True, autoscroll=True, font=("Consolas", 10))]
]

window = sg.Window("Gerador de Senhas", layout)
senhas_atuais = []
ultimo_arquivo = None
ultimo_length = DEFAULT_LENGTH

while True:
    event, values = window.read()
    if event in (sg.WINDOW_CLOSED, "Sair"):
        break

    if event == "-GERAR-":
        # Valida quantidade
        try:
            qtd = int(str(values["-QTD-"]).strip())
        except (ValueError, TypeError):
            sg.popup_error("A quantidade precisa ser um número inteiro entre 1 e 10.000.")
            continue

        # Valida comprimento
        raw_length = str(values["-LEN-"]).strip()
        if not raw_length:
            length = DEFAULT_LENGTH
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
                qtd, length=length, unique=values["-UNQ-"], require_all=values["-REQ-"]
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
            try:
                abrir_pasta_do_arquivo(ultimo_arquivo)
            except Exception:
                # Não interrompe a GUI se falhar ao abrir
                pass
        else:
            sg.popup("Nenhum arquivo salvo ainda.")

    if event == "-LIMPAR-":
        window["-OUT-"].update("")
        senhas_atuais = []
        ultimo_arquivo = None

window.close()

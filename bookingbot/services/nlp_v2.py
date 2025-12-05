import re
import numpy as np
from datetime import datetime, timedelta
from dateutil.parser import parse as date_parse


# ----------------------------------------
# MAPAS DE APOIO
# ----------------------------------------
RECURSOS_MAP = {
    "sala a": "Sala A",
    "sala b": "Sala B",
    "estudio grande": "Estúdio Grande",
    "estudio pequeno": "Estúdio Pequeno",
    "sala de gravação": "Estúdio Grande",
    "sala de ensaio": "Sala B",
}

DIAS_SEMANA = {
    "segunda": 0,
    "terça": 1, "terca": 1,
    "quarta": 2,
    "quinta": 3,
    "sexta": 4,
    "sábado": 5, "sabado": 5,
    "domingo": 6,
}

PERIODOS_NATURAIS = {
    "manhã": ("08:00", "12:00"),
    "manha": ("08:00", "12:00"),
    "tarde": ("13:00", "18:00"),
    "noite": ("18:00", "22:00"),
    "madrugada": ("00:00", "05:00"),
    "horário comercial": ("08:00", "18:00"),
    "horario comercial": ("08:00", "18:00"),
}

HORAS_ESPECIAIS = {
    "meio-dia": "12:00",
    "meio dia": "12:00",
    "meia-noite": "00:00",
    "meia noite": "00:00",
}


# ----------------------------------------
# FUNÇÕES DE EXTRAÇÃO
# ----------------------------------------

def extrair_duracao(texto):
    # "por 2 horas", "por 1h", "por 90 minutos"
    padrao = re.search(r"por (\d+)\s*(hora|horas|h|minuto|minutos)", texto)

    if not padrao:
        return None

    valor = int(padrao.group(1))
    unidade = padrao.group(2)

    if unidade.startswith("min"):
        return valor  # minutos
    else:
        return valor * 60  # horas -> minutos


def extrair_horarios_simples(texto):
    # inclui: 14:00, 14h, 2 da tarde, 7 da noite
    horarios = []

    # 14:00 / 07:30
    horarios += re.findall(r"\d{1,2}:\d{2}", texto)

    # 14h / 7h
    h_simples = re.findall(r"\b(\d{1,2})h\b", texto)
    for h in h_simples:
        horarios.append(f"{h}:00")

    # expressões como “2 da tarde”
    exp = re.search(r"(\d{1,2}) (da tarde|da noite|da manhã|de manhã|de tarde)", texto)
    if exp:
        h = int(exp.group(1))
        periodo = exp.group(2)

        if "tarde" in periodo and h < 12:
            h += 12
        if "noite" in periodo and h < 12:
            h += 12

        horarios.append(f"{h:02d}:00")

    # horas especiais
    for termo, hora in HORAS_ESPECIAIS.items():
        if termo in texto:
            horarios.append(hora)

    return horarios


def extrair_intervalo(texto):
    padrao = re.search(
        r"(entre|das|do)\s+(\d{1,2}[:h]?\d{0,2}|\w+)\s*(às|as|a)\s*(\d{1,2}[:h]?\d{0,2}|\w+)",
        texto
    )

    if not padrao:
        return None, None

    ini = padrao.group(2)
    fim = padrao.group(4)

    def normalizar(h):
        # meio-dia / meia-noite
        if h in HORAS_ESPECIAIS:
            return HORAS_ESPECIAIS[h]

        h = h.replace("h", ":")
        if ":" not in h:
            return f"{h}:00"
        return h

    return normalizar(ini), normalizar(fim)


def extrair_periodo(texto):
    for termo, (ini, fim) in PERIODOS_NATURAIS.items():
        if termo in texto:
            return ini, fim
    return None, None


def extrair_recurso(texto):
    t = texto.lower()
    for termo, nome_recurso in RECURSOS_MAP.items():
        if termo in t:
            return nome_recurso
    return None


def interpretar_datas(texto):
    hoje = datetime.now().date()
    datas = []

    # hoje / amanhã
    if "hoje" in texto:
        datas.append(hoje)

    if "amanhã" in texto or "amanha" in texto:
        datas.append(hoje + timedelta(days=1))

    if "depois de amanhã" in texto or "depois de amanha" in texto:
        datas.append(hoje + timedelta(days=2))

    # daqui X dias
    m = re.search(r"daqui (\d+) dias", texto)
    if m:
        dias = int(m.group(1))
        datas.append(hoje + timedelta(days=dias))

    # próxima/este/essa segunda
    sem = re.search(r"(próxima|proxima|este|essa) (\w+)", texto)
    if sem:
        nome = sem.group(2)
        if nome in DIAS_SEMANA:
            alvo = DIAS_SEMANA[nome]
            atual = hoje.weekday()
            add = (alvo - atual + 7) % 7
            add = 7 if add == 0 else add
            datas.append(hoje + timedelta(days=add))

    # múltiplos dias: segunda e quarta
    multi = re.findall(r"(segunda|terça|terca|quarta|quinta|sexta|sábado|sabado|domingo)", texto)
    for m in multi:
        alvo = DIAS_SEMANA[m]
        atual = hoje.weekday()
        add = (alvo - atual + 7) % 7
        datas.append(hoje + timedelta(days=add))

    # datas completas 10/02/2025
    for d in re.findall(r"\d{1,2}/\d{1,2}/\d{2,4}", texto):
        try:
            datas.append(date_parse(d, dayfirst=True).date())
        except:
            pass

    return list(dict.fromkeys(datas))  # remove duplicatas


# ----------------------------------------
# INTENT FINAL
# ----------------------------------------

def interpretar_intent(texto):
    if any(w in texto for w in ["reservar", "agendar", "marcar", "quero um horário"]):
        return "criar_reserva"
    if any(w in texto for w in ["cancelar"]):
        return "cancelar_reserva"
    if any(w in texto for w in ["ver", "consultar", "horários disponíveis"]):
        return "listar_disponibilidade"
    if any(w in texto for w in ["mudar", "remarcar"]):
        return "remarcar_reserva"
    return "desconhecido"


# ----------------------------------------
# FUNÇÃO PRINCIPAL
# ----------------------------------------

def interpretar_mensagem(texto):
    t = texto.lower().strip()

    intent = interpretar_intent(t)

    datas = interpretar_datas(t)
    horarios_simples = extrair_horarios_simples(t)
    intervalo_ini, intervalo_fim = extrair_intervalo(t)

    periodo_ini, periodo_fim = extrair_periodo(t)
    duracao = extrair_duracao(t)
    recurso_nome = extrair_recurso(t)

    # horário único se houver apenas um simples
    horario_unico = horarios_simples[0] if len(horarios_simples) == 1 else None

    return {
        "intent": np.str_(intent),

        "dates": [str(d) for d in datas],
        "date": str(datas[0]) if datas else None,

        "times": horarios_simples,
        "time": horario_unico,

        "interval_start": intervalo_ini or periodo_ini,
        "interval_end": intervalo_fim or periodo_fim,

        "duration_minutes": duracao,

        "texto_original": texto,

        "resource_name": recurso_nome,
    }

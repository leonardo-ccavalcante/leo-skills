#!/usr/bin/env python3
"""pcm — capacidades determinísticas da skill prompt-claude-models.

Quatro frentes, todas sem dependências (Python 3.9+, só stdlib):

1. Autoatualização das fontes (`fontes-check`, `fontes-aplicar`): as páginas
   oficiais mudam sem aviso; o sha256 registrado em fontes.json diz qual versão
   as references refletem, e o diff local mostra o que ler de novo.
2. Snippets verbatim (`snippets-verificar`): todo bloco marcado como citação
   literal tem de existir na página-fonte, senão a skill estaria inventando.
3. Lint de prompts por modelo (`lint`): regras de cruft.json (texto) e
   restricoes-api.json (corpo de request) + heurísticas embutidas.
4. Memória com reforço (`episodio`, `recompensa`, `politica`, `candidatos`,
   `pendentes`, `stats`): bandit contextual Beta por (modelo, tarefa, decisão).

Contrato: JSON no stdout, diagnóstico no stderr.
Exit: 0 ok/parcial · 1 bug · 2 dado insuficiente · 3 falha de validação.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import contextlib
import datetime as _dt
import difflib
import hashlib
import io
import json
import os
import re
import secrets
import shutil
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

VERSION = "1.0.0"

EXIT_OK = 0
EXIT_BUG = 1
EXIT_INSUFICIENTE = 2
EXIT_VALIDACAO = 3

USER_AGENT = "pcm/1.0"
URL_NOVA_TMPL = "https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/{id}.md"

# Modelos conhecidos e grupos: a expansão é a mesma para cruft.json e
# restricoes-api.json, para que uma regra "all-4-6-plus" signifique o mesmo nos dois.
MODELOS_CONHECIDOS = (
    "fable-5-1", "mythos-5-1", "fable-5", "mythos-5", "opus-5-5", "opus-5",
    "opus-4-8", "opus-4-7", "opus-4-6", "opus-4-5", "sonnet-5", "sonnet-4-6",
    "sonnet-4-5", "haiku-4-5",
)
_G_4_5_PLUS = (
    "opus-4-5", "opus-4-6", "opus-4-7", "opus-4-8", "opus-5", "opus-5-5",
    "sonnet-4-5", "sonnet-4-6", "sonnet-5", "haiku-4-5", "fable-5", "fable-5-1",
    "mythos-5", "mythos-5-1",
)
GRUPOS = {
    "all-current": MODELOS_CONHECIDOS,
    "all-4-5-plus": _G_4_5_PLUS,
    "all-4-6-plus": tuple(m for m in _G_4_5_PLUS if m not in ("opus-4-5", "sonnet-4-5", "haiku-4-5")),
}

TIPOS_CHECAGEM = ("campo_presente", "valor_igual", "combinacao", "ultimo_role")
SEVERIDADES = ("hard", "soft")

# Pesos da recompensa: eval é o sinal mais objetivo, a rubrica o mais fraco.
PESOS = {"eval": 0.30, "nota": 0.25, "iteracoes": 0.20, "edicao": 0.15, "rubrica": 0.10}
CAMPOS_EPISODIO = ("modo", "modelo", "effort", "superficie", "tarefa", "patamar",
                   "origem_skill", "decisoes", "lint", "rubrica")
OBRIGATORIOS_EPISODIO = ("modo", "modelo", "tarefa", "decisoes")
MAX_TEXTO = 300

# Regex compiladas uma vez (heurísticas do lint e blocos verbatim).
RE_CAPS = re.compile(r"\b(CRITICAL|MUST|NEVER|ALWAYS|IMPORTANT)\b")
RE_EXEMPLO = re.compile(r"<example(?:\s[^<>]*)?>")
RE_TAG_ABRE = re.compile(r"<([a-z_]+)(\s[^<>]*)?>")
RE_TAG_FECHA = re.compile(r"</([a-z_]+)\s*>")
RE_FENCE_CODIGO = re.compile(r"^[ \t]*(`{3,}|~{3,})[^\n]*\n.*?^[ \t]*\1[ \t]*$", re.S | re.M)
RE_CRASE = re.compile(r"`[^`\n]*`")
RE_DOC_ABRE = re.compile(r"<documents?\b")
RE_DOC_FECHA = re.compile(r"</documents?\s*>")
RE_VERBATIM_ABRE = re.compile(r"^\s*(`{3,})text\s+verbatim\b(.*)$")
RE_ATRIB = re.compile(r"(\w+)=(\S+)")
RE_WS = re.compile(r"\s+")
RE_SHA = re.compile(r"^[0-9a-f]{64}$")

FONTE_GUIA = "claude-prompting-best-practices"


class ErroUso(Exception):
    """Erro com exit code definido (dado insuficiente ou validação)."""

    def __init__(self, msg: str, code: int = EXIT_VALIDACAO, payload: dict | None = None):
        super().__init__(msg)
        self.code = code
        self.payload = payload


class ErroRede(Exception):
    """Falha de busca (rede, HTTP, domínio): vira status, nunca exit 1."""


# ---------------------------------------------------------------------------
# Utilidades de caminho, tempo e E/S
# ---------------------------------------------------------------------------

def skill_dir() -> Path:
    """SKILL_DIR lido a cada chamada: o selftest troca a variável em tempo de execução."""
    env = os.environ.get("PCM_SKILL_DIR")
    return Path(env) if env else Path(__file__).resolve().parent.parent


def state_dir(criar: bool = True) -> Path:
    """Estado fora do repo, para a memória não virar diff no git."""
    env = os.environ.get("PCM_STATE_DIR")
    p = Path(env) if env else Path.home() / ".claude" / "state" / "prompt-claude-models"
    if criar:
        p.mkdir(parents=True, exist_ok=True)
    return p


def cache_dir() -> Path:
    p = state_dir() / "cache"
    p.mkdir(parents=True, exist_ok=True)
    return p


def agora_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def hoje_utc() -> str:
    return _dt.datetime.now(_dt.timezone.utc).date().isoformat()


def parse_iso(s: str) -> _dt.datetime | None:
    try:
        return _dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def diag(msg: str) -> None:
    print(f"pcm: {msg}", file=sys.stderr)


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def escrever_atomico(path: Path, data: bytes) -> None:
    """Temporário + os.replace: um crash no meio nunca deixa arquivo pela metade."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        os.replace(tmp, path)
    except BaseException:
        with contextlib.suppress(OSError):
            os.unlink(tmp)
        raise


def escrever_json(path: Path, obj, final_nl: bool = True) -> None:
    txt = json.dumps(obj, indent=2, ensure_ascii=False)
    escrever_atomico(path, (txt + ("\n" if final_nl else "")).encode("utf-8"))


def ler_json(path: Path, padrao=None):
    """Arquivo de estado ausente ou vazio vale o padrão (primeiro uso)."""
    try:
        txt = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return padrao
    if not txt.strip():
        return padrao
    return json.loads(txt)


def ler_entrada(arg: str | None) -> str:
    if arg in (None, "-"):
        return sys.stdin.read()
    try:
        return Path(arg).read_text(encoding="utf-8")
    except FileNotFoundError:
        raise ErroUso(f"arquivo não encontrado: {arg}", EXIT_INSUFICIENTE)


def lista_csv(s: str | None) -> list[str]:
    return [x.strip() for x in (s or "").split(",") if x.strip()]


# ---------------------------------------------------------------------------
# Modelos
# ---------------------------------------------------------------------------

def expandir_modelos(modelos) -> set[str]:
    """Troca grupos (all-current, all-4-5-plus...) pelos modelos concretos."""
    out: set[str] = set()
    for m in modelos or []:
        out.update(GRUPOS.get(m, (m,)))
    return out


def modelo_conhecido(m: str) -> bool:
    return m in MODELOS_CONHECIDOS


# ---------------------------------------------------------------------------
# Rede
# ---------------------------------------------------------------------------

def id_da_url(url: str) -> str:
    ultimo = urllib.parse.urlparse(url).path.rstrip("/").rsplit("/", 1)[-1]
    return ultimo[:-3] if ultimo.endswith(".md") else ultimo


def validar_url(url: str, dominio: str) -> None:
    """Só https no domínio oficial: evita que um fontes.json adulterado puxe outra coisa."""
    p = urllib.parse.urlparse(url or "")
    if p.scheme != "https" or (p.hostname or "").lower() != (dominio or "").lower():
        raise ErroRede(f"URL fora de https://{dominio}: {url}")


def fetch(url: str, timeout: float = 15.0) -> bytes:
    """Busca a página; com PCM_FETCH_DIR lê fixture local (testes sem rede)."""
    fdir = os.environ.get("PCM_FETCH_DIR")
    if fdir:
        p = Path(fdir) / f"{id_da_url(url)}.md"
        try:
            return p.read_bytes()
        except OSError as e:
            raise ErroRede(f"rede simulada: {p.name} ausente ({e.__class__.__name__})")
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read()
    except urllib.error.HTTPError as e:
        raise ErroRede(f"HTTP {e.code} em {url}")
    except (urllib.error.URLError, OSError, ValueError) as e:
        raise ErroRede(f"falha de rede em {url}: {getattr(e, 'reason', e)}")


# ---------------------------------------------------------------------------
# fontes.json
# ---------------------------------------------------------------------------

def caminho_fontes() -> Path:
    return skill_dir() / "fontes.json"


def carregar_fontes() -> tuple[dict, bool]:
    """Devolve (dados, terminava_com_newline) para reescrever sem ruído no diff."""
    p = caminho_fontes()
    try:
        raw = p.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise ErroUso(f"fontes.json ausente em {p}", EXIT_INSUFICIENTE)
    try:
        dados = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ErroUso(f"fontes.json inválido: {e}", EXIT_VALIDACAO)
    # URL fora do domínio não invalida o arquivo aqui: vira status "erro" da página.
    erros = validar_fontes(dados, checar_urls=False)
    if erros:
        raise ErroUso("fontes.json inválido: " + "; ".join(erros), EXIT_VALIDACAO)
    return dados, raw.endswith("\n")


def validar_fontes(d, checar_urls: bool = True) -> list[str]:
    """Checagem estrutural: outros agentes editam o arquivo, então conferimos a forma."""
    erros: list[str] = []
    if not isinstance(d, dict):
        return ["raiz não é objeto"]
    dom = d.get("dominio_permitido")
    if not isinstance(dom, str) or not dom:
        erros.append("dominio_permitido ausente")
    desc = d.get("descoberta")
    if desc is not None:
        if not isinstance(desc, dict) or not isinstance(desc.get("pagina"), str) or not isinstance(desc.get("padrao"), str):
            erros.append("descoberta precisa de pagina e padrao")
        else:
            try:
                re.compile(desc["padrao"])
            except re.error as e:
                erros.append(f"descoberta.padrao não compila: {e}")
    pags = d.get("paginas")
    if not isinstance(pags, list):
        return erros + ["paginas não é lista"]
    vistos: set[str] = set()
    for i, p in enumerate(pags):
        if not isinstance(p, dict):
            erros.append(f"paginas[{i}] não é objeto")
            continue
        pid = p.get("id")
        if not isinstance(pid, str) or not pid:
            erros.append(f"paginas[{i}] sem id")
            continue
        if pid in vistos:
            erros.append(f"id duplicado: {pid}")
        vistos.add(pid)
        if not isinstance(p.get("url"), str):
            erros.append(f"{pid}: url ausente")
        elif checar_urls:
            try:
                validar_url(p["url"], dom or "")
            except ErroRede as e:
                erros.append(f"{pid}: {e}")
        if not isinstance(p.get("sha256"), str) or not RE_SHA.match(p["sha256"]):
            erros.append(f"{pid}: sha256 inválido")
        if not isinstance(p.get("bytes"), int):
            erros.append(f"{pid}: bytes não é inteiro")
        for campo in ("modelos", "alimenta"):
            if not isinstance(p.get(campo, []), list):
                erros.append(f"{pid}: {campo} não é lista")
    return erros


def ler_cache(pid: str, sufixo: str = ".md") -> bytes | None:
    p = cache_dir() / f"{pid}{sufixo}"
    try:
        return p.read_bytes()
    except FileNotFoundError:
        return None


def _checar_pagina(pag: dict, dominio: str, timeout: float) -> tuple[dict, bytes | None]:
    """Busca uma página, atualiza cache e diz se mudou em relação ao sha registrado."""
    pid = pag["id"]
    sha_reg = pag.get("sha256")
    item = {"id": pid, "status": "erro", "sha_registrado": sha_reg, "sha_atual": None, "diff": None, "nota": None}
    try:
        validar_url(pag.get("url", ""), dominio)
        conteudo = fetch(pag["url"], timeout)
    except ErroRede as e:
        item["nota"] = str(e)
        return item, None
    sha = sha256_bytes(conteudo)
    item["sha_atual"] = sha
    cdir = cache_dir()
    atual, anterior = cdir / f"{pid}.md", cdir / f"{pid}.anterior.md"
    velho = ler_cache(pid)
    # Procura a baseline (conteúdo com o sha registrado) antes de mexer no cache.
    baseline = None
    for cand in (velho, ler_cache(pid, ".anterior.md")):
        if cand is not None and sha256_bytes(cand) == sha_reg:
            baseline = cand
            break
    if velho is not None and sha256_bytes(velho) != sha:
        escrever_atomico(anterior, velho)
    if velho is None or sha256_bytes(velho) != sha:
        escrever_atomico(atual, conteudo)
    if sha == sha_reg:
        item["status"] = "inalterado"
        return item, conteudo
    item["status"] = "mudou"
    if baseline is None:
        item["nota"] = "sem baseline local: ler a página inteira"
        return item, conteudo
    linhas = difflib.unified_diff(
        baseline.decode("utf-8", "replace").splitlines(keepends=True),
        conteudo.decode("utf-8", "replace").splitlines(keepends=True),
        fromfile=f"{pid}@{(sha_reg or '')[:12]}", tofile=f"{pid}@{sha[:12]}",
    )
    dpath = cdir / f"{pid}.diff"
    escrever_atomico(dpath, "".join(linhas).encode("utf-8"))
    item["diff"] = str(dpath)
    return item, conteudo


def _descobrir(fontes: dict, conteudos: dict, timeout: float) -> tuple[list[dict], str | None]:
    """Links prompting-claude-* na página-índice revelam modelos novos."""
    desc = fontes.get("descoberta")
    if not desc:
        return [], None
    pid = desc["pagina"]
    conteudo = conteudos.get(pid)
    if conteudo is None:
        url = next((p["url"] for p in fontes["paginas"] if p["id"] == pid), URL_NOVA_TMPL.format(id=pid))
        try:
            validar_url(url, fontes["dominio_permitido"])
            conteudo = fetch(url, timeout)
        except ErroRede as e:
            return [], f"descoberta indisponível: {e}"
    conhecidos = {p["id"] for p in fontes["paginas"]}
    novas, vistos = [], set()
    for m in re.finditer(desc["padrao"], conteudo.decode("utf-8", "replace")):
        nid = m.group(1) if m.groups() else m.group(0)
        if nid in conhecidos or nid in vistos:
            continue
        vistos.add(nid)
        novas.append({"id": nid, "url": URL_NOVA_TMPL.format(id=nid)})
    return novas, None


def cmd_fontes_check(args) -> tuple[dict, int]:
    fontes, _ = carregar_fontes()
    so = lista_csv(args.so)
    paginas = fontes["paginas"]
    if so:
        ids = {p["id"] for p in paginas}
        faltam = [x for x in so if x not in ids]
        if faltam:
            raise ErroUso(f"ids desconhecidos em --so: {', '.join(faltam)}", EXIT_INSUFICIENTE)
        paginas = [p for p in paginas if p["id"] in so]
    dominio = fontes["dominio_permitido"]
    resultados: dict[str, dict] = {}
    conteudos: dict[str, bytes] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, min(8, len(paginas)))) as ex:
        futs = {ex.submit(_checar_pagina, p, dominio, args.timeout): p["id"] for p in paginas}
        for f in concurrent.futures.as_completed(futs):
            item, conteudo = f.result()
            resultados[item["id"]] = item
            if conteudo is not None:
                conteudos[item["id"]] = conteudo
    itens = [resultados[p["id"]] for p in paginas]  # ordem de fontes.json, não de chegada
    novas, nota_desc = _descobrir(fontes, conteudos, args.timeout)
    resumo = {s: sum(1 for i in itens if i["status"] == s) for s in ("inalterado", "mudou", "erro")}
    resumo["novas"] = len(novas)
    out = {
        "checado_em": agora_iso(),
        "offline": bool(itens) and resumo["erro"] == len(itens),
        "paginas": itens,
        "novas": novas,
        "resumo": resumo,
    }
    if nota_desc:
        out["nota_descoberta"] = nota_desc
    escrever_json(state_dir() / "fontes-estado.json", {"ultima_checagem": out["checado_em"], "resumo": resumo})
    for i in itens:
        if i["status"] == "erro":
            diag(f"{i['id']}: {i['nota']}")
    return out, EXIT_OK


def cmd_fontes_aplicar(args) -> tuple[dict, int]:
    fontes, nl = carregar_fontes()
    dominio = fontes["dominio_permitido"]
    por_id = {p["id"]: p for p in fontes["paginas"]}
    ids = lista_csv(args.ids)
    if args.todas_mudadas:
        for p in fontes["paginas"]:
            c = ler_cache(p["id"])
            if c is not None and sha256_bytes(c) != p["sha256"] and p["id"] not in ids:
                ids.append(p["id"])
    adicionar: list[tuple[str, str]] = []
    for spec in args.adicionar or []:
        if "=" not in spec:
            raise ErroUso(f"--adicionar espera id=url: {spec}", EXIT_VALIDACAO)
        nid, url = spec.split("=", 1)
        nid, url = nid.strip(), url.strip()
        if nid in por_id:
            raise ErroUso(f"id já existe em fontes.json: {nid}", EXIT_VALIDACAO)
        try:
            validar_url(url, dominio)
        except ErroRede as e:
            raise ErroUso(str(e), EXIT_VALIDACAO)
        adicionar.append((nid, url))
    if not ids and not adicionar:
        raise ErroUso("nada a aplicar: use --ids, --todas-mudadas ou --adicionar", EXIT_INSUFICIENTE)
    desconhecidos = [i for i in ids if i not in por_id]
    if desconhecidos:
        raise ErroUso(f"ids fora de fontes.json: {', '.join(desconhecidos)}", EXIT_INSUFICIENTE)
    # Valida tudo antes de escrever: aplicar metade deixaria fontes.json incoerente.
    sem_cache = [i for i in ids if ler_cache(i) is None]
    novos_conteudos: dict[str, bytes] = {}
    for nid, url in adicionar:
        c = ler_cache(nid)
        if c is None:
            try:
                c = fetch(url, args.timeout)
            except ErroRede as e:
                diag(f"{nid}: {e}")
                sem_cache.append(nid)
                continue
            escrever_atomico(cache_dir() / f"{nid}.md", c)
        novos_conteudos[nid] = c
    if sem_cache:
        raise ErroUso(f"sem cache (rode fontes-check antes): {', '.join(sem_cache)}", EXIT_INSUFICIENTE,
                      {"sem_cache": sem_cache, "alteradas": [], "adicionadas": []})
    hoje = hoje_utc()
    alteradas = []
    for i in ids:
        c = ler_cache(i)
        p = por_id[i]
        antes = p["sha256"]
        p["sha256"], p["bytes"], p["verificado_em"] = sha256_bytes(c), len(c), hoje
        alteradas.append({"id": i, "sha_anterior": antes, "sha_novo": p["sha256"], "bytes": p["bytes"]})
    adicionadas = []
    for nid, url in adicionar:
        c = novos_conteudos[nid]
        entrada = {"id": nid, "url": url, "sha256": sha256_bytes(c), "bytes": len(c), "verificado_em": hoje,
                   "tipo": "prompting", "modelos": [], "alimenta": []}
        fontes["paginas"].append(entrada)
        adicionadas.append({"id": nid, "sha_novo": entrada["sha256"], "bytes": len(c)})
    escrever_json(caminho_fontes(), fontes, final_nl=nl)
    return {"arquivo": str(caminho_fontes()), "alteradas": alteradas, "adicionadas": adicionadas}, EXIT_OK


# ---------------------------------------------------------------------------
# Snippets verbatim
# ---------------------------------------------------------------------------

def normalizar(txt: str) -> str:
    """Mesma normalização do checador de fatos: ignora recuo, NBSP e linhas vazias."""
    linhas = (ln.replace(" ", " ").strip() for ln in txt.replace("\r\n", "\n").split("\n"))
    return "\n".join(ln for ln in linhas if ln)


def colapsar(txt: str) -> str:
    return RE_WS.sub(" ", txt.replace(" ", " ")).strip()


def contem_verbatim(bloco: str, pagina: str) -> bool:
    nb = normalizar(bloco)
    if nb and nb in normalizar(pagina):
        return True
    cb = colapsar(bloco)
    return bool(cb) and cb in colapsar(pagina)


def extrair_blocos(texto: str) -> list[dict]:
    """Blocos ```text verbatim fonte=... id=...```; bloco sem fechamento vira erro."""
    linhas = texto.split("\n")
    blocos, i = [], 0
    while i < len(linhas):
        m = RE_VERBATIM_ABRE.match(linhas[i])
        if not m:
            i += 1
            continue
        cerca, attrs = m.group(1), dict(RE_ATRIB.findall(m.group(2)))
        j = i + 1
        while j < len(linhas) and linhas[j].strip() != cerca:
            j += 1
        blocos.append({"linha": i + 1, "fonte": attrs.get("fonte"), "id": attrs.get("id"),
                       "conteudo": "\n".join(linhas[i + 1:j]), "fechado": j < len(linhas)})
        i = j + 1
    return blocos


def hash8(txt: str) -> str:
    return hashlib.sha256(normalizar(txt).encode("utf-8")).hexdigest()[:8]


def cmd_snippets(args) -> tuple[dict, int]:
    raiz = skill_dir()
    refs = raiz / "references"
    arquivos = sorted(refs.rglob("*.md")) if refs.is_dir() else []
    cache_pag: dict[str, str | None] = {}
    total = ok = 0
    falhas, sem_cache, ids = [], [], {}
    for arq in arquivos:
        rel = str(arq.relative_to(raiz))
        for b in extrair_blocos(arq.read_text(encoding="utf-8")):
            total += 1
            falha = {"arquivo": rel, "linha": b["linha"], "fonte": b["fonte"], "id": b["id"],
                     "inicio": normalizar(b["conteudo"])[:80]}
            if not b["fonte"] or not b["id"]:
                falhas.append({**falha, "motivo": "atributos fonte= e id= obrigatórios"})
                continue
            if b["id"] in ids:
                falhas.append({**falha, "motivo": "id de snippet duplicado"})
                continue
            ids[b["id"]] = hash8(b["conteudo"])
            if not b["fechado"]:
                falhas.append({**falha, "motivo": "bloco sem fechamento"})
                continue
            if b["fonte"] not in cache_pag:
                c = ler_cache(b["fonte"])
                cache_pag[b["fonte"]] = None if c is None else c.decode("utf-8", "replace")
            pagina = cache_pag[b["fonte"]]
            if pagina is None:
                if b["fonte"] not in sem_cache:
                    sem_cache.append(b["fonte"])
                continue
            if contem_verbatim(b["conteudo"], pagina):
                ok += 1
            else:
                falhas.append({**falha, "motivo": "conteúdo não encontrado na página-fonte"})
    out = {"total": total, "ok": ok, "falhas": falhas, "sem_cache": sem_cache, "ids": ids}
    if falhas:
        return out, EXIT_VALIDACAO
    if sem_cache:
        diag("páginas sem cache local; rode `pcm.py fontes-check` e repita")
        return out, EXIT_INSUFICIENTE
    return out, EXIT_OK


# ---------------------------------------------------------------------------
# Regras de lint (cruft.json / restricoes-api.json)
# ---------------------------------------------------------------------------

def validar_cruft(d) -> list[str]:
    erros: list[str] = []
    if not isinstance(d, dict) or not isinstance(d.get("regras"), list):
        return ["cruft.json: esperado {\"regras\": [...]}"]
    vistos: set[str] = set()
    for i, r in enumerate(d["regras"]):
        rid = r.get("id") if isinstance(r, dict) else None
        tag = rid or f"regras[{i}]"
        if not isinstance(r, dict) or not isinstance(rid, str):
            erros.append(f"{tag}: sem id")
            continue
        if rid in vistos:
            erros.append(f"{tag}: id duplicado")
        vistos.add(rid)
        erros.extend(_validar_comum(r, tag))
        try:
            rx = re.compile(r.get("padrao", ""), re.I | re.M)
        except (re.error, TypeError) as e:
            erros.append(f"{tag}: padrao não compila: {e}")
            continue
        if not r.get("padrao"):
            erros.append(f"{tag}: padrao vazio")
        ex = r.get("exemplo")
        if not isinstance(ex, str) or not ex:
            erros.append(f"{tag}: exemplo obrigatório")
        elif not rx.search(ex):
            erros.append(f"{tag}: exemplo não casa com padrao")
        ce = r.get("contra_exemplo")
        if isinstance(ce, str) and ce and rx.search(ce):
            erros.append(f"{tag}: contra_exemplo casa com padrao")
    return erros


def validar_restricoes(d) -> list[str]:
    erros: list[str] = []
    if not isinstance(d, dict) or not isinstance(d.get("regras"), list):
        return ["restricoes-api.json: esperado {\"regras\": [...]}"]
    vistos: set[str] = set()
    for i, r in enumerate(d["regras"]):
        rid = r.get("id") if isinstance(r, dict) else None
        tag = rid or f"regras[{i}]"
        if not isinstance(r, dict) or not isinstance(rid, str):
            erros.append(f"{tag}: sem id")
            continue
        if rid in vistos:
            erros.append(f"{tag}: id duplicado")
        vistos.add(rid)
        erros.extend(_validar_comum(r, tag))
        erros.extend(_validar_checagem(r.get("checagem"), tag))
    return erros


def _validar_comum(r: dict, tag: str) -> list[str]:
    erros = []
    mods = r.get("modelos")
    if not isinstance(mods, list) or not mods:
        erros.append(f"{tag}: modelos vazio")
    else:
        desconhecidos = [m for m in mods if m not in GRUPOS and m not in MODELOS_CONHECIDOS]
        if desconhecidos:
            erros.append(f"{tag}: modelos desconhecidos {desconhecidos}")
    if r.get("severidade") not in SEVERIDADES:
        erros.append(f"{tag}: severidade deve ser hard|soft")
    for campo in ("motivo_pt", "sugestao_pt"):
        if not isinstance(r.get(campo), str) or not r.get(campo):
            erros.append(f"{tag}: {campo} obrigatório")
    f = r.get("fonte")
    if not isinstance(f, dict) or not f.get("page_id"):
        erros.append(f"{tag}: fonte.page_id obrigatório")
    return erros


def _validar_checagem(c, tag: str) -> list[str]:
    if not isinstance(c, dict) or c.get("tipo") not in TIPOS_CHECAGEM:
        return [f"{tag}: checagem.tipo deve ser um de {TIPOS_CHECAGEM}"]
    t = c["tipo"]
    if t == "campo_presente" and not (isinstance(c.get("campos"), list) and c["campos"]):
        return [f"{tag}: campo_presente exige campos"]
    if t == "valor_igual" and not (isinstance(c.get("caminho"), str) and isinstance(c.get("valores"), list)):
        return [f"{tag}: valor_igual exige caminho e valores"]
    if t == "ultimo_role" and not isinstance(c.get("valores"), list):
        return [f"{tag}: ultimo_role exige valores"]
    if t == "combinacao":
        todas = c.get("todas")
        if not isinstance(todas, list) or not todas:
            return [f"{tag}: combinacao exige todas"]
        for s in todas:
            if not (isinstance(s, dict) and isinstance(s.get("caminho"), str) and isinstance(s.get("valores"), list)):
                return [f"{tag}: subcondição de combinacao exige caminho e valores"]
    return []


def carregar_regras(nome: str, validador) -> list[dict]:
    """Arquivo ausente = sem regras (a skill ainda está sendo montada)."""
    p = skill_dir() / "references" / nome
    try:
        d = ler_json(p)
    except json.JSONDecodeError as e:
        raise ErroUso(f"{nome} inválido: {e}", EXIT_VALIDACAO)
    if d is None:
        diag(f"{nome} ausente: regras dele não aplicadas")
        return []
    erros = validador(d)
    if erros:
        raise ErroUso(f"{nome} inválido: " + "; ".join(erros), EXIT_VALIDACAO)
    return d["regras"]


# ---------------------------------------------------------------------------
# Lint
# ---------------------------------------------------------------------------

def _linha_de(texto: str, pos: int) -> int:
    return texto.count("\n", 0, pos) + 1


def _trecho(texto: str, pos: int) -> str:
    ini = texto.rfind("\n", 0, pos) + 1
    fim = texto.find("\n", pos)
    return texto[ini: fim if fim >= 0 else len(texto)].strip()[:160]


def _mascarar_codigo(texto: str) -> str:
    """Troca código (cercas e crases) por espaços, preservando posições e linhas."""
    def branco(m):
        return re.sub(r"[^\n]", " ", m.group(0))
    return RE_CRASE.sub(branco, RE_FENCE_CODIGO.sub(branco, texto))


def _achado(regra, sev, linha, trecho, motivo, sugestao, fonte, origem=None) -> dict:
    a = {"regra": regra, "severidade": sev, "linha": linha, "trecho": trecho,
         "motivo_pt": motivo, "sugestao_pt": sugestao, "fonte": fonte}
    if origem:
        a["origem"] = origem
    return a


def lint_texto(texto: str, modelo: str, regras: list[dict], compiladas: dict, origem=None) -> list[dict]:
    achados = []
    for r in regras:
        if modelo not in expandir_modelos(r["modelos"]):
            continue
        rx = compiladas[r["id"]]
        linhas_vistas: set[int] = set()
        for m in rx.finditer(texto):
            ln = _linha_de(texto, m.start())
            if ln in linhas_vistas:
                continue
            linhas_vistas.add(ln)
            achados.append(_achado(r["id"], r["severidade"], ln, _trecho(texto, m.start()),
                                   r["motivo_pt"], r["sugestao_pt"], r["fonte"], origem))
    achados.extend(heuristicas(texto, modelo, origem))
    return achados


def heuristicas(texto: str, modelo: str, origem=None) -> list[dict]:
    """Heurísticas soft embutidas; independem dos arquivos de regras."""
    out = []
    semcod = _mascarar_codigo(texto)
    # (a) Ênfase em caixa alta: modelos 4.5+ seguem o system prompt à risca e overtriggeram.
    caps = list(RE_CAPS.finditer(semcod))
    if len(caps) >= 2 and modelo in GRUPOS["all-4-5-plus"]:
        out.append(_achado("heur.enfase_caixa_alta", "soft", _linha_de(texto, caps[0].start()),
                           f"{len(caps)} ocorrências: " + ", ".join(sorted({m.group(1) for m in caps})),
                           "ênfase agressiva em caixa alta (CRITICAL/MUST/NEVER...) faz modelos atuais exagerarem",
                           "trocar por linguagem normal e explicar o porquê da instrução",
                           {"page_id": FONTE_GUIA, "section": "Tool usage"}, origem))
    # (b) Quantidade de exemplos: o guia recomenda 3–5.
    exs = list(RE_EXEMPLO.finditer(semcod))
    if exs and not 3 <= len(exs) <= 5:
        out.append(_achado("heur.qtd_exemplos", "soft", _linha_de(texto, exs[0].start()),
                           f"{len(exs)} bloco(s) <example>",
                           "o guia recomenda 3–5 exemplos diversos",
                           "ajustar para 3–5 exemplos variados e relevantes",
                           {"page_id": FONTE_GUIA, "section": "Use examples effectively"}, origem))
    # (c) Tags XML abertas e nunca fechadas: estrutura quebrada confunde o parsing do modelo.
    abertas: dict[str, list[int]] = {}
    for m in RE_TAG_ABRE.finditer(semcod):
        if m.group(0).endswith("/>"):
            continue
        abertas.setdefault(m.group(1), []).append(m.start())
    fechadas: dict[str, int] = {}
    for m in RE_TAG_FECHA.finditer(semcod):
        fechadas[m.group(1)] = fechadas.get(m.group(1), 0) + 1
    for nome, posicoes in abertas.items():
        if len(posicoes) > fechadas.get(nome, 0):
            pos = posicoes[fechadas.get(nome, 0)]
            out.append(_achado("heur.tag_sem_fechamento", "soft", _linha_de(texto, pos), f"<{nome}>",
                               f"tag <{nome}> aberta sem </{nome}> correspondente",
                               f"fechar com </{nome}> ou remover a tag",
                               {"page_id": FONTE_GUIA, "section": "Structure prompts with XML tags"}, origem))
    # (d) Documentos longos depois da instrução: o guia manda documentos no topo, pergunta no fim.
    ab = RE_DOC_ABRE.search(semcod)
    fechs = list(RE_DOC_FECHA.finditer(semcod))
    if ab and fechs:
        antes, depois = semcod[:ab.start()].strip(), semcod[fechs[-1].end():].strip()
        if len(depois) < 60 and len(antes) > 400:
            out.append(_achado("heur.documentos_no_fim", "soft", _linha_de(texto, ab.start()),
                               _trecho(texto, ab.start()),
                               "pergunta/instrução antes dos documentos; o guia recomenda documentos no topo e pergunta no fim",
                               "mover os documentos para o início e a pergunta para depois deles",
                               {"page_id": FONTE_GUIA, "section": "Long context prompting"}, origem))
    return out


def obter_caminho(obj, caminho: str):
    """Caminho pontuado a.b.c; devolve (existe, valor)."""
    atual = obj
    for parte in caminho.split("."):
        if not isinstance(atual, dict) or parte not in atual:
            return False, None
        atual = atual[parte]
    return True, atual


def checar_request(req: dict, c: dict) -> str | None:
    """Devolve o trecho que violou a regra, ou None se passou."""
    t = c["tipo"]
    if t == "campo_presente":
        for campo in c["campos"]:
            existe, v = obter_caminho(req, campo)
            if existe:
                return f"{campo}={json.dumps(v, ensure_ascii=False)}"
        return None
    if t == "valor_igual":
        existe, v = obter_caminho(req, c["caminho"])
        return f"{c['caminho']}={json.dumps(v, ensure_ascii=False)}" if existe and v in c["valores"] else None
    if t == "combinacao":
        partes = []
        for s in c["todas"]:
            existe, v = obter_caminho(req, s["caminho"])
            if not (existe and v in s["valores"]):
                return None
            partes.append(f"{s['caminho']}={json.dumps(v, ensure_ascii=False)}")
        return " + ".join(partes)
    if t == "ultimo_role":
        msgs = req.get("messages")
        if isinstance(msgs, list) and msgs and isinstance(msgs[-1], dict) and msgs[-1].get("role") in c["valores"]:
            return f"messages[-1].role={msgs[-1]['role']}"
        return None
    return None


def _textos_request(req: dict) -> list[tuple[str, str]]:
    """Extrai o texto de system e das mensagens para o lint de texto."""
    out = []

    def blocos(conteudo, origem):
        if isinstance(conteudo, str):
            out.append((origem, conteudo))
        elif isinstance(conteudo, list):
            for k, b in enumerate(conteudo):
                if isinstance(b, dict) and isinstance(b.get("text"), str):
                    out.append((f"{origem}[{k}]", b["text"]))
                elif isinstance(b, str):
                    out.append((f"{origem}[{k}]", b))

    blocos(req.get("system"), "system")
    for i, m in enumerate(req.get("messages") or []):
        if isinstance(m, dict):
            blocos(m.get("content"), f"messages[{i}]")
    return out


def executar_lint(texto: str, modelo: str) -> dict:
    cruft = carregar_regras("cruft.json", validar_cruft)
    restr = carregar_regras("restricoes-api.json", validar_restricoes)
    compiladas = {r["id"]: re.compile(r["padrao"], re.I | re.M) for r in cruft}
    req = None
    with contextlib.suppress(ValueError):
        cand = json.loads(texto)
        if isinstance(cand, dict) and "messages" in cand:
            req = cand
    achados: list[dict] = []
    if req is None:
        achados = lint_texto(texto, modelo, cruft, compiladas)
    else:
        for r in restr:
            if modelo not in expandir_modelos(r["modelos"]):
                continue
            trecho = checar_request(req, r["checagem"])
            if trecho is not None:
                achados.append(_achado(r["id"], r["severidade"], None, trecho, r["motivo_pt"],
                                       r["sugestao_pt"], r["fonte"], "request"))
        for origem, t in _textos_request(req):
            achados.extend(lint_texto(t, modelo, cruft, compiladas, origem))
    cont = {"hard": sum(1 for a in achados if a["severidade"] == "hard"),
            "soft": sum(1 for a in achados if a["severidade"] == "soft")}
    return {"modelo": modelo, "entrada": "request" if req is not None else "texto",
            "achados": achados, "contagem": cont}


def cmd_lint(args) -> tuple[dict, int]:
    if not modelo_conhecido(args.modelo):
        raise ErroUso(f"modelo desconhecido: {args.modelo} (conhecidos: {', '.join(MODELOS_CONHECIDOS)})",
                      EXIT_INSUFICIENTE)
    out = executar_lint(ler_entrada(args.arquivo), args.modelo)
    return out, EXIT_VALIDACAO if out["contagem"]["hard"] else EXIT_OK


# ---------------------------------------------------------------------------
# Memória: episódios, placar, política
# ---------------------------------------------------------------------------
# episodios.jsonl é só-append: cada linha é um retrato completo do episódio e o
# último retrato de um id vence. Assim nenhuma escrita reescreve o histórico.

def caminho_episodios() -> Path:
    return state_dir() / "episodios.jsonl"


def carregar_episodios() -> dict[str, dict]:
    eps: dict[str, dict] = {}
    try:
        with caminho_episodios().open(encoding="utf-8") as f:
            for n, linha in enumerate(f, 1):
                if not linha.strip():
                    continue
                try:
                    ep = json.loads(linha)
                except json.JSONDecodeError:
                    diag(f"episodios.jsonl linha {n} ilegível; ignorada")
                    continue
                if isinstance(ep, dict) and ep.get("id"):
                    eps[ep["id"]] = ep
    except FileNotFoundError:
        pass
    return eps


def anexar_episodio(ep: dict) -> None:
    with caminho_episodios().open("a", encoding="utf-8") as f:
        f.write(json.dumps(ep, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())


def _strings_longas(obj, caminho="") -> list[str]:
    if isinstance(obj, str):
        return [caminho] if len(obj) > MAX_TEXTO else []
    if isinstance(obj, dict):
        return [c for k, v in obj.items() for c in _strings_longas(v, f"{caminho}.{k}" if caminho else k)]
    if isinstance(obj, list):
        return [c for i, v in enumerate(obj) for c in _strings_longas(v, f"{caminho}[{i}]")]
    return []


def _num01(v, nome: str) -> float:
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not 0 <= v <= 1:
        raise ErroUso(f"{nome} deve estar entre 0 e 1", EXIT_VALIDACAO)
    return float(v)


def validar_episodio(d) -> dict:
    if not isinstance(d, dict):
        raise ErroUso("episódio deve ser objeto JSON", EXIT_VALIDACAO)
    longos = _strings_longas(d)
    if longos:
        # Texto livre longo quase sempre é conteúdo do usuário: não guardamos.
        raise ErroUso(f"campos com texto > {MAX_TEXTO} caracteres (não guardamos conteúdo): {', '.join(longos)}",
                      EXIT_VALIDACAO)
    extras = [k for k in d if k not in CAMPOS_EPISODIO]
    if extras:
        raise ErroUso(f"campos não permitidos: {', '.join(extras)}", EXIT_VALIDACAO)
    faltam = [k for k in OBRIGATORIOS_EPISODIO if d.get(k) in (None, "", [])]
    if faltam:
        raise ErroUso(f"campos obrigatórios ausentes: {', '.join(faltam)}", EXIT_VALIDACAO)
    for k in ("modo", "modelo", "tarefa", "effort", "superficie", "patamar", "origem_skill"):
        if k in d and d[k] is not None and not isinstance(d[k], str):
            raise ErroUso(f"{k} deve ser texto", EXIT_VALIDACAO)
    decs = d["decisoes"]
    if not isinstance(decs, list) or not all(isinstance(x, str) and x.strip() for x in decs):
        raise ErroUso("decisoes deve ser lista de ids", EXIT_VALIDACAO)
    # '|' separa as partes da chave do placar; '*' é a chave agregada.
    for v in [d["modelo"], d["tarefa"], *decs]:
        if "|" in v:
            raise ErroUso(f"'|' não permitido em modelo/tarefa/decisões: {v}", EXIT_VALIDACAO)
    if d["tarefa"] == "*":
        raise ErroUso("tarefa '*' é reservada para o agregado", EXIT_VALIDACAO)
    if "lint" in d and d["lint"] is not None:
        li = d["lint"]
        if not isinstance(li, dict) or any(not isinstance(li.get(k, 0), int) for k in ("hard", "soft")):
            raise ErroUso("lint deve ser {hard: int, soft: int}", EXIT_VALIDACAO)
    if d.get("rubrica") is not None:
        _num01(d["rubrica"], "rubrica")
    ep = {k: d[k] for k in CAMPOS_EPISODIO if k in d}
    ep["decisoes"] = list(dict.fromkeys(decs))
    return ep


def cmd_episodio(args) -> tuple[dict, int]:
    try:
        d = json.loads(ler_entrada(args.arquivo))
    except json.JSONDecodeError as e:
        raise ErroUso(f"JSON inválido: {e}", EXIT_VALIDACAO)
    ep = validar_episodio(d)
    agora = _dt.datetime.now(_dt.timezone.utc)
    ep_id = f"ep-{agora.strftime('%Y%m%dT%H%M%S')}-{secrets.token_hex(2)}"
    ep.update({"id": ep_id, "criado_em": agora_iso(), "pendente": True,
               "sinais": {}, "decisoes_editadas": [], "contribuicao": {}, "R": None})
    anexar_episodio(ep)
    return {"id": ep_id}, EXIT_OK


def caminho_placar() -> Path:
    return state_dir() / "placar.json"


def chave(modelo: str, tarefa: str, decisao: str) -> str:
    return f"{modelo}|{tarefa}|{decisao}"


def calcular_R(sinais: dict) -> float | None:
    """Média ponderada renormalizada: sinais ausentes não puxam R para zero."""
    pres = {k: v for k, v in sinais.items() if k in PESOS and v is not None}
    if not pres:
        return None
    return sum(PESOS[k] * v for k, v in pres.items()) / sum(PESOS[k] for k in pres)


def _sinais_novos(args) -> dict:
    s = {}
    if args.nota is not None:
        if not 1 <= args.nota <= 5:
            raise ErroUso("--nota deve estar entre 1 e 5", EXIT_VALIDACAO)
        s["nota"] = (args.nota - 1) / 4
    if args.eval is not None:
        s["eval"] = _num01(args.eval, "--eval")
    if args.iteracoes is not None:
        if args.iteracoes < 0:
            raise ErroUso("--iteracoes deve ser >= 0", EXIT_VALIDACAO)
        s["iteracoes"] = 1 / (1 + args.iteracoes)
    if args.edicao is not None:
        s["edicao"] = _num01(args.edicao, "--edicao")
    elif args.editado or args.entregue:
        if not (args.editado and args.entregue):
            raise ErroUso("--editado e --entregue vão juntos", EXIT_VALIDACAO)
        # Os arquivos só são lidos para a razão de similaridade; nada deles é guardado.
        ent, edi = ler_entrada(args.entregue), ler_entrada(args.editado)
        s["edicao"] = 1 - (1 - difflib.SequenceMatcher(None, ent, edi).ratio())
    if args.rubrica is not None:
        s["rubrica"] = _num01(args.rubrica, "--rubrica")
    return s


def _aplicar_placar(placar: dict, modelo: str, tarefa: str, velha: dict, nova: dict) -> None:
    """Idempotente: desfaz a contribuição anterior do episódio antes de somar a nova."""
    agora = agora_iso()
    for d, rd in nova.items():
        for t in (tarefa, "*"):
            k = chave(modelo, t, d)
            e = placar.setdefault(k, {"alfa": 0.0, "beta": 0.0, "n": 0, "atualizado_em": agora})
            if d in velha:
                e["alfa"] -= velha[d]
                e["beta"] -= 1 - velha[d]
            else:
                e["n"] += 1
            e["alfa"] = round(e["alfa"] + rd, 12)
            e["beta"] = round(e["beta"] + 1 - rd, 12)
            e["atualizado_em"] = agora


def cmd_recompensa(args) -> tuple[dict, int]:
    eps = carregar_episodios()
    ep = eps.get(args.id)
    if ep is None:
        raise ErroUso(f"episódio não encontrado: {args.id}", EXIT_INSUFICIENTE)
    novos = _sinais_novos(args)
    sinais = dict(ep.get("sinais") or {})
    sinais.update(novos)  # a última chamada de cada sinal vale
    efetivos = dict(sinais)
    if "rubrica" not in efetivos and ep.get("rubrica") is not None:
        efetivos["rubrica"] = float(ep["rubrica"])
    if args.decisoes_editadas is not None:
        ep["decisoes_editadas"] = lista_csv(args.decisoes_editadas)
    R = calcular_R(efetivos)
    if R is None:
        if args.fechar:
            ep["pendente"] = False
            anexar_episodio(ep)
        raise ErroUso("nenhum sinal de recompensa (use --nota/--eval/--iteracoes/--edicao/--rubrica)",
                      EXIT_INSUFICIENTE, {"id": ep["id"], "R": None, "fechado": bool(args.fechar)})
    editadas = set(ep.get("decisoes_editadas") or [])
    nova = {d: (0.0 if d in editadas else R) for d in ep["decisoes"]}
    placar = ler_json(caminho_placar(), {}) or {}
    _aplicar_placar(placar, ep["modelo"], ep["tarefa"], ep.get("contribuicao") or {}, nova)
    escrever_json(caminho_placar(), placar)
    ep.update({"sinais": sinais, "contribuicao": nova, "R": R, "recompensado_em": agora_iso()})
    if args.fechar:
        ep["pendente"] = False
    anexar_episodio(ep)
    return {"id": ep["id"], "R": R, "sinais": efetivos, "decisoes": nova}, EXIT_OK


def _estat(placar: dict, k: str) -> tuple[float, float, int]:
    e = placar.get(k) or {}
    return float(e.get("alfa", 0)), float(e.get("beta", 0)), int(e.get("n", 0))


def cmd_politica(args) -> tuple[dict, int]:
    if not modelo_conhecido(args.modelo):
        raise ErroUso(f"modelo desconhecido: {args.modelo}", EXIT_INSUFICIENTE)
    placar = ler_json(caminho_placar(), {}) or {}
    recomendadas = set(lista_csv(args.recomendadas))
    cands = lista_csv(args.candidatas)
    if not cands:
        vistos = {k.split("|", 2)[2] for k in placar if k.split("|", 2)[0] == args.modelo}
        cands = sorted(vistos | recomendadas)
    decisoes = []
    for d in dict.fromkeys(cands):
        fonte = "prior"
        a, b, n = 0.0, 0.0, 0
        if args.tarefa:
            ta, tb, tn = _estat(placar, chave(args.modelo, args.tarefa, d))
            if tn >= 3:
                a, b, n, fonte = ta, tb, tn, "tarefa"
        if fonte == "prior":
            ga, gb, gn = _estat(placar, chave(args.modelo, "*", d))
            if gn > 0:
                a, b, n, fonte = ga, gb, gn, "agregada"
        rec = d in recomendadas
        a0, b0 = (2, 1) if rec else (1, 1)  # prior otimista só para o que o guia recomenda
        media = (a + a0) / (a + b + a0 + b0)
        if d.startswith(("api.", "hard.")):
            acao = "fixa"  # restrição de API/regra dura: a memória nunca desliga
        elif n >= 3 and media < 0.35:
            acao = "rebaixar"
        elif n >= 3 and media >= 0.75:
            acao = "promover"
        else:
            acao = "manter"
        decisoes.append({"id": d, "media": media, "n": n, "fonte_estatistica": fonte,
                         "recomendada": rec, "acao": acao})
    decisoes.sort(key=lambda x: (-x["media"], x["id"]))
    return {"modelo": args.modelo, "tarefa": args.tarefa, "decisoes": decisoes}, EXIT_OK


def caminho_promovidos() -> Path:
    return state_dir() / "promovidos.json"


def cmd_candidatos(args) -> tuple[dict, int]:
    placar = ler_json(caminho_placar(), {}) or {}
    promovidos = ler_json(caminho_promovidos(), {}) or {}
    marcado = None
    if args.marcar_promovido:
        k = args.marcar_promovido
        if k not in placar:
            raise ErroUso(f"chave não está no placar: {k}", EXIT_INSUFICIENTE)
        promovidos[k] = {"marcado_em": agora_iso()}
        escrever_json(caminho_promovidos(), promovidos)
        marcado = k
    hoje = hoje_utc()
    out = []
    for k in sorted(placar):
        modelo, tarefa, dec = k.split("|", 2)
        if tarefa == "*" or k in promovidos:
            continue
        a, _b, n = _estat(placar, k)
        if n < args.min_n:
            continue
        media = a / n
        if media >= args.alto:
            direcao = "reforçar"
        elif media <= args.baixo:
            direcao = "evitar"
        else:
            continue
        media_txt = f"{media:.2f}".replace(".", ",")
        linha = (f"- [{hoje} · {modelo} · {tarefa}] {dec}: {direcao} — Aplicar: <preencher>. "
                 f"Evidência: n={n}, R̄={media_txt}")
        out.append({"chave": k, "modelo": modelo, "tarefa": tarefa, "decisao": dec, "n": n,
                    "media": media, "direcao": direcao, "linha": linha})
    res = {"candidatos": out}
    if marcado:
        res["marcado"] = marcado
    return res, EXIT_OK


def cmd_pendentes(args) -> tuple[dict, int]:
    limite = _dt.datetime.now(_dt.timezone.utc) - _dt.timedelta(days=args.dias)
    lista = []
    for ep in carregar_episodios().values():
        if not ep.get("pendente"):
            continue
        criado = parse_iso(ep.get("criado_em", ""))
        if criado is None or criado < limite:
            continue
        lista.append({k: ep.get(k) for k in ("id", "criado_em", "modo", "modelo", "tarefa", "decisoes", "R")})
    lista.sort(key=lambda e: e["criado_em"], reverse=True)
    return {"dias": args.dias, "total": len(lista), "pendentes": lista}, EXIT_OK


def cmd_stats(args) -> tuple[dict, int]:
    eps = list(carregar_episodios().values())
    por_modelo: dict[str, list[float]] = {}
    por_tarefa: dict[str, list[float]] = {}
    for ep in eps:
        if ep.get("R") is None:
            continue
        por_modelo.setdefault(ep["modelo"], []).append(ep["R"])
        por_tarefa.setdefault(ep["tarefa"], []).append(ep["R"])
    media = lambda xs: sum(xs) / len(xs)  # noqa: E731
    placar = ler_json(caminho_placar(), {}) or {}
    decs = []
    for k in placar:
        modelo, tarefa, dec = k.split("|", 2)
        a, _b, n = _estat(placar, k)
        if tarefa == "*" and n >= 3:
            decs.append({"modelo": modelo, "decisao": dec, "n": n, "media": a / n})
    decs.sort(key=lambda x: (-x["media"], x["modelo"], x["decisao"]))
    return {
        "episodios": len(eps),
        "com_recompensa": sum(len(v) for v in por_modelo.values()),
        "pendentes": sum(1 for e in eps if e.get("pendente")),
        "R_medio_por_modelo": {m: {"media": media(v), "n": len(v)} for m, v in sorted(por_modelo.items())},
        "R_medio_por_tarefa": {t: {"media": media(v), "n": len(v)} for t, v in sorted(por_tarefa.items())},
        "melhores": decs[:5],
        "piores": list(reversed(decs[-5:])) if decs else [],
    }, EXIT_OK


# ---------------------------------------------------------------------------
# doctor
# ---------------------------------------------------------------------------

def _check(nome, ok, detalhe, nivel="erro") -> dict:
    return {"nome": nome, "ok": bool(ok), "nivel": nivel, "detalhe": detalhe}


def cmd_doctor(args) -> tuple[dict, int]:
    checks = [_check("python>=3.9", sys.version_info >= (3, 9), sys.version.split()[0])]
    try:
        sd = state_dir()
        with tempfile.NamedTemporaryFile(dir=str(sd), prefix=".doctor.", delete=True):
            pass
        checks.append(_check("state_dir gravável", True, str(sd)))
    except OSError as e:
        checks.append(_check("state_dir gravável", False, str(e)))
    fontes = None
    try:
        fontes, _ = carregar_fontes()
        checks.append(_check("fontes.json", True, f"{len(fontes['paginas'])} páginas"))
    except ErroUso as e:
        checks.append(_check("fontes.json", False, str(e)))
    for nome, val in (("cruft.json", validar_cruft), ("restricoes-api.json", validar_restricoes)):
        p = skill_dir() / "references" / nome
        if not p.exists():
            checks.append(_check(nome, True, "ausente (opcional até ser gerado)", "aviso"))
            continue
        try:
            erros = val(ler_json(p, {}))
        except json.JSONDecodeError as e:
            erros = [str(e)]
        checks.append(_check(nome, not erros, "; ".join(erros) if erros else "válido"))
    if fontes and fontes["paginas"]:
        url = fontes["paginas"][0]["url"]
        try:
            validar_url(url, fontes["dominio_permitido"])
            n = len(fetch(url, 5))
            checks.append(_check("rede", True, f"GET {url} ({n} bytes)", "aviso"))
        except ErroRede as e:
            checks.append(_check("rede", False, f"{e} (fontes-check vai reportar offline)", "aviso"))
    essenciais_ok = all(c["ok"] for c in checks if c["nivel"] == "erro")
    return {"ok": essenciais_ok, "versao": VERSION, "skill_dir": str(skill_dir()), "checks": checks}, \
        EXIT_OK if essenciais_ok else EXIT_INSUFICIENTE


# ---------------------------------------------------------------------------
# selftest
# ---------------------------------------------------------------------------

FIX_CRUFT = {"regras": [
    {"id": "fx.anti_markdown", "modelos": ["fable-5-1", "mythos-5-1"],
     "padrao": r"avoid_excessive_markdown|do not use (ordered|unordered) lists", "severidade": "hard",
     "motivo_pt": "m", "sugestao_pt": "s", "fonte": {"page_id": "pag-x", "section": "S"},
     "exemplo": "Please do not use unordered lists here.", "contra_exemplo": "Use ordered steps when helpful."},
    {"id": "fx.think_step", "modelos": ["all-4-6-plus"], "padrao": r"\bthink step[- ]by[- ]step\b",
     "severidade": "soft", "motivo_pt": "m", "sugestao_pt": "s", "fonte": {"page_id": "pag-x", "section": "S"},
     "exemplo": "Think step by step before answering.", "contra_exemplo": "Take a step back and consider."},
]}
FIX_RESTR = {"regras": [
    {"id": "api.sampling_params", "modelos": ["sonnet-5", "opus-4-7"],
     "checagem": {"tipo": "campo_presente", "campos": ["temperature", "top_p", "top_k"]},
     "severidade": "hard", "motivo_pt": "m", "sugestao_pt": "s", "fonte": {"page_id": "pag-x", "section": "S"}},
    {"id": "api.prefill", "modelos": ["all-4-6-plus"], "checagem": {"tipo": "ultimo_role", "valores": ["assistant"]},
     "severidade": "hard", "motivo_pt": "m", "sugestao_pt": "s", "fonte": {"page_id": "pag-x", "section": "S"}},
    {"id": "api.thinking_disabled_high_effort", "modelos": ["opus-5"],
     "checagem": {"tipo": "combinacao", "todas": [{"caminho": "thinking.type", "valores": ["disabled"]},
                                                  {"caminho": "output_config.effort", "valores": ["xhigh", "max"]}]},
     "severidade": "hard", "motivo_pt": "m", "sugestao_pt": "s", "fonte": {"page_id": "pag-x", "section": "S"}},
    {"id": "api.forced_tool_choice", "modelos": ["opus-5-5"],
     "checagem": {"tipo": "valor_igual", "caminho": "tool_choice.type", "valores": ["any", "tool"]},
     "severidade": "soft", "motivo_pt": "m", "sugestao_pt": "s", "fonte": {"page_id": "pag-x", "section": "S"}},
]}

FIX_INDICE = ("# Guia\n\nVeja [x](/docs/en/build-with-claude/prompt-engineering/prompting-claude-x) e\n"
              "[novo](/docs/en/build-with-claude/prompt-engineering/prompting-claude-novo).\n")
FIX_X = ("# Prompting Claude X\n\nUse clear instructions.\n\n"
         "Tell Claude what to do instead of what not to do.\n  Keep prompts short.\n")
URL_BASE = "https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/"


class _Selftest:
    """Roda os subcomandos em processo, com diretórios temporários isolados."""

    def __init__(self):
        self.testes: list[dict] = []
        self.tmp = Path(tempfile.mkdtemp(prefix="pcm-selftest-"))

    def t(self, nome: str, ok: bool, detalhe="") -> None:
        self.testes.append({"nome": nome, "ok": bool(ok), "detalhe": detalhe if not ok else ""})

    def run(self, argv: list[str], stdin: str | None = None) -> tuple[dict, int]:
        velho_in = sys.stdin
        try:
            if stdin is not None:
                sys.stdin = io.StringIO(stdin)
            with contextlib.redirect_stderr(io.StringIO()):
                return despachar(argv)
        finally:
            sys.stdin = velho_in

    def arq(self, nome: str, conteudo: str) -> str:
        p = self.tmp / "entradas" / nome
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(conteudo, encoding="utf-8")
        return str(p)


def _pagina(pid: str, conteudo: str) -> dict:
    return {"id": pid, "url": URL_BASE + pid + ".md", "sha256": sha256_bytes(conteudo.encode()),
            "bytes": len(conteudo.encode()), "verificado_em": "2026-01-01", "tipo": "prompting",
            "modelos": [], "alimenta": []}


def _st_fontes(st: _Selftest, sk: Path, fetch_dir: Path) -> None:
    (fetch_dir / "claude-prompting-best-practices.md").write_text(FIX_INDICE, encoding="utf-8")
    (fetch_dir / "prompting-claude-x.md").write_text(FIX_X, encoding="utf-8")
    (fetch_dir / "prompting-claude-novo.md").write_text("# novo\n", encoding="utf-8")
    fontes = {"dominio_permitido": "platform.claude.com",
              "descoberta": {"pagina": "claude-prompting-best-practices",
                             "padrao": "/docs/en/build-with-claude/prompt-engineering/(prompting-claude-[a-z0-9-]+)"},
              "paginas": [_pagina("claude-prompting-best-practices", FIX_INDICE),
                          _pagina("prompting-claude-x", FIX_X),
                          _pagina("pag-sumida", "qualquer")]}
    fora = _pagina("pag-fora", "x")
    fora["url"] = "https://evil.example.com/pag-fora.md"
    (sk / "fontes.json").write_text(json.dumps(fontes, indent=2), encoding="utf-8")
    out, code = st.run(["fontes-check"])
    st_ = {p["id"]: p for p in out.get("paginas", [])}
    st.t("fontes: exit 0", code == 0, str(code))
    st.t("fontes: 1a checagem inalterado", st_.get("prompting-claude-x", {}).get("status") == "inalterado", str(st_))
    st.t("fontes: página ausente → erro", st_.get("pag-sumida", {}).get("status") == "erro", str(st_.get("pag-sumida")))
    st.t("fontes: descoberta → novas", [n["id"] for n in out.get("novas", [])] == ["prompting-claude-novo"],
         str(out.get("novas")))
    st.t("fontes: estado gravado", (state_dir() / "fontes-estado.json").exists())
    # Domínio fora do permitido: a página vira "erro" sem ser buscada.
    ruim = json.loads(json.dumps(fontes))
    ruim["paginas"].append(fora)
    (sk / "fontes.json").write_text(json.dumps(ruim), encoding="utf-8")
    (fetch_dir / "pag-fora.md").write_text("x", encoding="utf-8")
    out, code = st.run(["fontes-check", "--so", "pag-fora"])
    pf = out["paginas"][0]
    st.t("fontes: URL fora do domínio → erro", code == 0 and pf["status"] == "erro" and "fora" in (pf["nota"] or ""), str(pf))
    st.t("fontes: validar_fontes estrito acusa domínio", any("pag-fora" in e for e in validar_fontes(ruim)))
    st.t("fontes: validar_url recusa http", _recusa("http://platform.claude.com/x.md"))
    (sk / "fontes.json").write_text(json.dumps(fontes, indent=2), encoding="utf-8")
    # Conteúdo alterado → mudou com diff.
    (fetch_dir / "prompting-claude-x.md").write_text(FIX_X + "\nNova seção sobre effort.\n", encoding="utf-8")
    out, _ = st.run(["fontes-check", "--so", "prompting-claude-x"])
    px = out["paginas"][0]
    diff_ok = bool(px.get("diff")) and "Nova seção" in Path(px["diff"]).read_text(encoding="utf-8")
    st.t("fontes: mudou com diff não vazio", px["status"] == "mudou" and diff_ok, str(px))
    out, _ = st.run(["fontes-check", "--so", "prompting-claude-x"])
    st.t("fontes: diff persiste na 2a checagem", out["paginas"][0]["status"] == "mudou" and bool(out["paginas"][0]["diff"]))
    _o, code = st.run(["fontes-aplicar", "--ids", "pag-sumida"])
    st.t("fontes-aplicar: sem cache → exit 2", code == EXIT_INSUFICIENTE, str(code))
    out, code = st.run(["fontes-aplicar", "--todas-mudadas"])
    st.t("fontes-aplicar: aplica mudadas", code == 0 and [a["id"] for a in out.get("alteradas", [])] == ["prompting-claude-x"],
         str(out))
    out, _ = st.run(["fontes-check"])
    st_ = {p["id"]: p for p in out["paginas"]}
    st.t("fontes: após aplicar → inalterado", st_["prompting-claude-x"]["status"] == "inalterado", str(st_["prompting-claude-x"]))
    out, code = st.run(["fontes-aplicar", "--adicionar", f"prompting-claude-novo={URL_BASE}prompting-claude-novo.md"])
    nf = json.loads((sk / "fontes.json").read_text(encoding="utf-8"))
    st.t("fontes-aplicar: --adicionar", code == 0 and nf["paginas"][-1]["id"] == "prompting-claude-novo"
         and nf["paginas"][-1]["tipo"] == "prompting", str(out))
    out, _ = st.run(["fontes-check"])
    st.t("fontes: adicionada some de novas", out["novas"] == [], str(out["novas"]))
    # Offline: nenhuma página disponível.
    vazio = st.tmp / "fetch-vazio"
    vazio.mkdir()
    velho = os.environ["PCM_FETCH_DIR"]
    os.environ["PCM_FETCH_DIR"] = str(vazio)
    try:
        out, code = st.run(["fontes-check"])
    finally:
        os.environ["PCM_FETCH_DIR"] = velho
    st.t("fontes: tudo erro → offline, exit 0", out.get("offline") is True and code == 0, str(out.get("resumo")))


def _recusa(url: str) -> bool:
    try:
        validar_url(url, "platform.claude.com")
    except ErroRede:
        return True
    return False


def _st_snippets(st: _Selftest, sk: Path) -> None:
    ref = sk / "references" / "modelos"
    ref.mkdir(parents=True, exist_ok=True)
    fiel = ("# X\n\n```text verbatim fonte=prompting-claude-x id=x.instead\n"
            "Tell Claude what to do instead of what not to do.\n```\n\n"
            "   ```text verbatim fonte=prompting-claude-x id=x.recuo\n"
            "      Keep prompts short.\n   ```\n")
    (ref / "x.md").write_text(fiel, encoding="utf-8")
    out, code = st.run(["snippets-verificar"])
    st.t("snippets: fiel e recuo diferente ok", code == 0 and out["ok"] == 2 and out["total"] == 2, str(out))
    st.t("snippets: ids com hash8", set(out.get("ids", {})) == {"x.instead", "x.recuo"}
         and all(len(v) == 8 for v in out["ids"].values()), str(out.get("ids")))
    adult = fiel + "\n```text verbatim fonte=prompting-claude-x id=x.falso\nTell Claude to always shout.\n```\n"
    (ref / "x.md").write_text(adult, encoding="utf-8")
    out, code = st.run(["snippets-verificar"])
    st.t("snippets: adulterado falha (exit 3)", code == EXIT_VALIDACAO and len(out["falhas"]) == 1
         and out["falhas"][0]["id"] == "x.falso" and out["falhas"][0]["linha"] == 11, str(out))
    sem = fiel + "\n```text verbatim fonte=pagina-sem-cache id=y.1\nqualquer\n```\n"
    (ref / "x.md").write_text(sem, encoding="utf-8")
    out, code = st.run(["snippets-verificar"])
    st.t("snippets: sem cache → exit 2", code == EXIT_INSUFICIENTE and out["sem_cache"] == ["pagina-sem-cache"], str(out))
    (ref / "x.md").write_text(fiel, encoding="utf-8")


def _st_lint(st: _Selftest, sk: Path) -> None:
    refs = sk / "references"
    (refs / "cruft.json").write_text(json.dumps(FIX_CRUFT), encoding="utf-8")
    (refs / "restricoes-api.json").write_text(json.dumps(FIX_RESTR), encoding="utf-8")
    for r in FIX_CRUFT["regras"]:
        modelo = sorted(expandir_modelos(r["modelos"]))[0]
        out, _ = st.run(["lint", "--modelo", modelo, st.arq("ex.txt", r["exemplo"])])
        st.t(f"lint: {r['id']} casa exemplo", any(a["regra"] == r["id"] for a in out["achados"]), str(out))
        out, _ = st.run(["lint", "--modelo", modelo, st.arq("ce.txt", r["contra_exemplo"])])
        st.t(f"lint: {r['id']} não casa contra_exemplo", not any(a["regra"] == r["id"] for a in out["achados"]), str(out))
    out, _ = st.run(["lint", "--modelo", "haiku-4-5", st.arq("h.txt", "Think step by step.")])
    st.t("lint: regra fora do grupo não aplica", out["achados"] == [], str(out))
    req = {"model": "claude-sonnet-5", "temperature": 0.7, "messages": [{"role": "user", "content": "Oi"}]}
    out, code = st.run(["lint", "--modelo", "sonnet-5", "-"], json.dumps(req))
    st.t("lint: temperature em sonnet-5 → hard", code == EXIT_VALIDACAO and out["entrada"] == "request"
         and any(a["regra"] == "api.sampling_params" for a in out["achados"]), str(out))
    req = {"messages": [{"role": "user", "content": "Oi"}, {"role": "assistant", "content": "{"}]}
    out, code = st.run(["lint", "--modelo", "opus-5-5", "-"], json.dumps(req))
    st.t("lint: prefill → hard", code == EXIT_VALIDACAO and any(a["regra"] == "api.prefill" for a in out["achados"]), str(out))
    req = {"thinking": {"type": "disabled"}, "output_config": {"effort": "max"},
           "messages": [{"role": "user", "content": "Oi"}]}
    out, _ = st.run(["lint", "--modelo", "opus-5", "-"], json.dumps(req))
    st.t("lint: combinacao dispara", any(a["regra"] == "api.thinking_disabled_high_effort" for a in out["achados"]), str(out))
    req["output_config"]["effort"] = "low"
    out, _ = st.run(["lint", "--modelo", "opus-5", "-"], json.dumps(req))
    st.t("lint: combinacao parcial não dispara", out["achados"] == [], str(out))
    req = {"tool_choice": {"type": "any"}, "system": "Think step by step.",
           "messages": [{"role": "user", "content": [{"type": "text", "text": "Oi"}]}]}
    out, code = st.run(["lint", "--modelo", "opus-5-5", "-"], json.dumps(req))
    st.t("lint: valor_igual soft + texto do system", code == 0 and {a["regra"] for a in out["achados"]}
         == {"api.forced_tool_choice", "fx.think_step"}, str(out))
    limpo = "You are a careful reviewer.\n\n<instructions>\nSummarize the diff in two sentences.\n</instructions>\n"
    out, code = st.run(["lint", "--modelo", "fable-5-1", st.arq("limpo.txt", limpo)])
    st.t("lint: prompt limpo → 0 achados", code == 0 and out["achados"] == [], str(out))
    _o, code = st.run(["lint", "--modelo", "gpt-9", st.arq("limpo.txt", limpo)])
    st.t("lint: modelo desconhecido → exit 2", code == EXIT_INSUFICIENTE, str(code))

    def regras(texto):
        return {a["regra"] for a in st.run(["lint", "--modelo", "opus-5-5", st.arq("h.txt", texto)])[0]["achados"]}

    st.t("heur a: caixa alta dispara", "heur.enfase_caixa_alta" in regras("You MUST do it. NEVER skip."))
    st.t("heur a: uma só não dispara", "heur.enfase_caixa_alta" not in regras("You must do it. NEVER skip."))
    ex = "<example>a</example>\n"
    st.t("heur b: 2 exemplos dispara", "heur.qtd_exemplos" in regras(ex * 2))
    st.t("heur b: 3 exemplos ok", "heur.qtd_exemplos" not in regras(ex * 3))
    st.t("heur b: 6 exemplos dispara", "heur.qtd_exemplos" in regras(ex * 6))
    st.t("heur c: tag sem fechamento", "heur.tag_sem_fechamento" in regras("<instructions>\nfaça x\n"))
    st.t("heur c: tag citada em crase ignorada",
         "heur.tag_sem_fechamento" not in regras("Use a tag `<answer>` no fim. <br/> ok"))
    instr = "Analyze the contracts carefully and list every clause about liability. " * 8
    docs = "<documents>\n<document>texto longo do contrato</document>\n</documents>\n"
    st.t("heur d: documentos depois da instrução", "heur.documentos_no_fim" in regras(instr + docs))
    st.t("heur d: documentos no topo ok", "heur.documentos_no_fim" not in regras(docs + instr))


def _st_memoria(st: _Selftest) -> None:
    ep = {"modo": "criar", "modelo": "opus-5-5", "tarefa": "codigo", "decisoes": ["xml_tags", "exemplos", "api.no_prefill"],
          "rubrica": 0.5, "lint": {"hard": 0, "soft": 1}}
    out, code = st.run(["episodio", "-"], json.dumps(ep))
    ep_id = out.get("id", "")
    st.t("memória: episodio cria id", code == 0 and re.match(r"^ep-\d{8}T\d{6}-[0-9a-f]{4}$", ep_id or "") is not None, str(out))
    _o, code = st.run(["recompensa", "--id", ep_id])
    st.t("memória: sem sinal novo usa rubrica do episódio", code == 0 and abs(_o["R"] - 0.5) < 1e-9, str(_o))
    ent = st.arq("entregue.txt", "abcdefghij")
    edi = st.arq("editado.txt", "abcdefghXY")
    ratio = difflib.SequenceMatcher(None, "abcdefghij", "abcdefghXY").ratio()
    argv = ["recompensa", "--id", ep_id, "--nota", "4", "--eval", "0.8", "--iteracoes", "1",
            "--editado", edi, "--entregue", ent, "--rubrica", "0.6", "--decisoes-editadas", "exemplos"]
    out, code = st.run(argv)
    esperado = (0.30 * 0.8 + 0.25 * 0.75 + 0.20 * 0.5 + 0.15 * ratio + 0.10 * 0.6) / 1.0
    st.t("memória: R com 5 sinais", code == 0 and abs(out["R"] - esperado) < 1e-9, f"{out.get('R')} vs {esperado}")
    st.t("memória: decisão editada recebe 0", out["decisoes"].get("exemplos") == 0.0
         and abs(out["decisoes"]["xml_tags"] - esperado) < 1e-9, str(out["decisoes"]))
    placar1 = ler_json(caminho_placar(), {})
    st.run(argv)
    placar2 = ler_json(caminho_placar(), {})
    k = chave("opus-5-5", "codigo", "xml_tags")
    idem = placar2[k]["n"] == 1 and all(abs(placar1[x]["alfa"] - placar2[x]["alfa"]) < 1e-9
                                        and abs(placar1[x]["beta"] - placar2[x]["beta"]) < 1e-9 for x in placar1)
    st.t("memória: 2a chamada idempotente", idem and abs(placar2[k]["alfa"] - esperado) < 1e-9, str(placar2.get(k)))
    st.t("memória: agregada registrada", placar2.get(chave("opus-5-5", "*", "xml_tags"), {}).get("n") == 1)
    ep2 = dict(ep, decisoes=["sem_sinal"])
    ep2_id = st.run(["episodio", "-"], json.dumps({k2: v for k2, v in ep2.items() if k2 != "rubrica"}))[0]["id"]
    _o, code = st.run(["recompensa", "--id", ep2_id])
    st.t("memória: nenhum sinal → exit 2", code == EXIT_INSUFICIENTE, str(code))
    # Três episódios ruins para 'prolixo' e 'api.no_prefill'.
    for _ in range(3):
        e = {"modo": "criar", "modelo": "opus-5-5", "tarefa": "codigo", "decisoes": ["prolixo", "api.no_prefill", "bom"]}
        eid = st.run(["episodio", "-"], json.dumps(e))[0]["id"]
        st.run(["recompensa", "--id", eid, "--nota", "1", "--eval", "0", "--decisoes-editadas", "", "--fechar"])
        st.run(["recompensa", "--id", eid, "--nota", "1", "--eval", "0"])
    out, _ = st.run(["politica", "--modelo", "opus-5-5", "--tarefa", "codigo", "--recomendadas", "xml_tags"])
    pol = {d["id"]: d for d in out["decisoes"]}
    st.t("politica: rebaixa decisão ruim n>=3", pol.get("prolixo", {}).get("acao") == "rebaixar"
         and pol["prolixo"]["fonte_estatistica"] == "tarefa" and pol["prolixo"]["n"] == 3, str(pol.get("prolixo")))
    st.t("politica: nunca rebaixa api.*", pol.get("api.no_prefill", {}).get("acao") == "fixa", str(pol.get("api.no_prefill")))
    st.t("politica: prior Beta(2,1) para recomendada", pol.get("xml_tags", {}).get("recomendada") is True)
    out, _ = st.run(["politica", "--modelo", "opus-5-5", "--candidatas", "inedita"])
    st.t("politica: sem dados → prior", out["decisoes"][0]["fonte_estatistica"] == "prior"
         and abs(out["decisoes"][0]["media"] - 0.5) < 1e-9, str(out))
    out, _ = st.run(["candidatos"])
    chaves = {c["chave"]: c for c in out["candidatos"]}
    kp = chave("opus-5-5", "codigo", "prolixo")
    st.t("candidatos: aparece após n>=3", kp in chaves and chaves[kp]["direcao"] == "evitar"
         and "n=3, R̄=0,00" in chaves[kp]["linha"], str(out))
    st.run(["candidatos", "--marcar-promovido", kp])
    out, _ = st.run(["candidatos"])
    st.t("candidatos: promovido some", kp not in {c["chave"] for c in out["candidatos"]}, str(out))
    out, _ = st.run(["pendentes"])
    st.t("pendentes: fechados saem", out["total"] == 2, str(out))
    out, code = st.run(["stats"])
    st.t("stats: roda", code == 0 and out["episodios"] == 5 and out["piores"], str(out))
    longo = dict(ep, tarefa="x" * 301)
    _o, code = st.run(["episodio", "-"], json.dumps(longo))
    st.t("episodio: recusa texto longo", code == EXIT_VALIDACAO, str(code))
    _o, code = st.run(["episodio", "-"], json.dumps({"modo": "criar", "modelo": "opus-5-5"}))
    st.t("episodio: obrigatórios", code == EXIT_VALIDACAO, str(code))


def _st_dados_reais(st: _Selftest, real: Path) -> None:
    """Valida os arquivos reais da skill, quando existem (outros agentes os geram)."""
    p = real / "fontes.json"
    if p.exists():
        try:
            erros = validar_fontes(json.loads(p.read_text(encoding="utf-8")))
        except json.JSONDecodeError as e:
            erros = [str(e)]
        st.t("dados: fontes.json válido", not erros, "; ".join(erros))
    for nome, val in (("cruft.json", validar_cruft), ("restricoes-api.json", validar_restricoes)):
        p = real / "references" / nome
        if not p.exists():
            continue
        try:
            erros = val(json.loads(p.read_text(encoding="utf-8")))
        except json.JSONDecodeError as e:
            erros = [str(e)]
        st.t(f"dados: {nome} válido (regex, exemplo, contra_exemplo)", not erros, "; ".join(erros[:20]))


def cmd_selftest(args) -> tuple[dict, int]:
    real = skill_dir()
    st = _Selftest()
    chaves = ("PCM_STATE_DIR", "PCM_SKILL_DIR", "PCM_FETCH_DIR")
    velhos = {k: os.environ.get(k) for k in chaves}
    sk, fetch_dir = st.tmp / "skill", st.tmp / "fetch"
    (sk / "references").mkdir(parents=True)
    fetch_dir.mkdir()
    os.environ.update({"PCM_STATE_DIR": str(st.tmp / "state"), "PCM_SKILL_DIR": str(sk),
                       "PCM_FETCH_DIR": str(fetch_dir)})
    try:
        for nome, fn in (("fontes", lambda: _st_fontes(st, sk, fetch_dir)), ("snippets", lambda: _st_snippets(st, sk)),
                         ("lint", lambda: _st_lint(st, sk)), ("memória", lambda: _st_memoria(st))):
            try:
                fn()
            except Exception as e:  # um bloco quebrado não pode esconder os outros
                st.t(f"{nome}: exceção", False, f"{e.__class__.__name__}: {e}")
    finally:
        for k, v in velhos.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        shutil.rmtree(st.tmp, ignore_errors=True)
    _st_dados_reais(st, real)
    ok = all(t["ok"] for t in st.testes)
    falhas = sum(1 for t in st.testes if not t["ok"])
    return {"ok": ok, "total": len(st.testes), "falhas": falhas, "testes": st.testes}, EXIT_OK if ok else EXIT_BUG


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def construir_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="pcm.py",
        description="Ferramentas determinísticas da skill prompt-claude-models: fontes, snippets, lint e memória. "
                    "JSON no stdout; exit 0 ok · 1 bug · 2 dado insuficiente · 3 falha de validação.",
    )
    ap.add_argument("--json", action="store_true", help="saída JSON (já é o padrão; aceito por compatibilidade)")
    ap.add_argument("--version", action="version", version=f"pcm {VERSION}")
    sub = ap.add_subparsers(dest="cmd", metavar="<subcomando>")
    sub.required = True

    def add(nome, ajuda, fn):
        p = sub.add_parser(nome, help=ajuda, description=ajuda)
        p.add_argument("--json", action="store_true", help=argparse.SUPPRESS)
        p.set_defaults(fn=fn)
        return p

    p = add("fontes-check", "busca as páginas de fontes.json, compara sha256, gera diff e descobre páginas novas",
            cmd_fontes_check)
    p.add_argument("--timeout", type=float, default=15.0, help="timeout por página em segundos (padrão 15)")
    p.add_argument("--so", help="só estes ids, separados por vírgula")

    p = add("fontes-aplicar", "grava em fontes.json o sha do cache atual depois que as references foram atualizadas",
            cmd_fontes_aplicar)
    g = p.add_mutually_exclusive_group()
    g.add_argument("--ids", help="ids a aplicar, separados por vírgula")
    g.add_argument("--todas-mudadas", action="store_true", help="aplica todas cujo cache difere do sha registrado")
    p.add_argument("--adicionar", action="append", metavar="ID=URL", help="cria entrada nova (repetível)")
    p.add_argument("--timeout", type=float, default=15.0, help="timeout para buscar página nova sem cache")

    add("snippets-verificar", "confere se cada bloco ```text verbatim``` existe na página-fonte em cache", cmd_snippets)

    p = add("lint", "lint de prompt (texto) ou de request JSON para um modelo", cmd_lint)
    p.add_argument("--modelo", required=True, help=f"um de: {', '.join(MODELOS_CONHECIDOS)}")
    p.add_argument("arquivo", nargs="?", default="-", help="arquivo com o prompt/request; '-' ou omitido = stdin")

    p = add("episodio", "registra um episódio (JSON sem conteúdo do usuário) como pendente", cmd_episodio)
    p.add_argument("arquivo", nargs="?", default="-", help="JSON do episódio; '-' ou omitido = stdin")

    p = add("recompensa", "aplica sinais de recompensa a um episódio e atualiza o placar (idempotente)",
            cmd_recompensa)
    p.add_argument("--id", required=True, help="id do episódio (ep-...)")
    p.add_argument("--nota", type=float, help="nota do usuário de 1 a 5")
    p.add_argument("--eval", type=float, help="resultado de eval, 0 a 1")
    p.add_argument("--iteracoes", type=int, help="rodadas de ajuste até aceitar (0 = de primeira)")
    p.add_argument("--edicao", type=float, help="similaridade entregue×editado, 0 a 1")
    p.add_argument("--editado", help="arquivo editado pelo usuário (lido só para a razão; não é guardado)")
    p.add_argument("--entregue", help="arquivo entregue por Claude (lido só para a razão; não é guardado)")
    p.add_argument("--decisoes-editadas", help="decisões que o usuário desfez (recebem 0), por vírgula")
    p.add_argument("--rubrica", type=float, help="nota de rubrica 0 a 1 (sobrepõe a do episódio)")
    p.add_argument("--fechar", action="store_true", help="tira o episódio de pendentes")

    p = add("politica", "média Beta por decisão e ação sugerida (fixa/promover/manter/rebaixar)", cmd_politica)
    p.add_argument("--modelo", required=True)
    p.add_argument("--tarefa", help="tipo de tarefa; usada se n>=3, senão cai no agregado")
    p.add_argument("--candidatas", help="decisões a avaliar, por vírgula (padrão: todas do placar)")
    p.add_argument("--recomendadas", help="decisões recomendadas pelo guia (prior Beta(2,1)), por vírgula")

    p = add("candidatos", "decisões com evidência para virar linha do MEMORY.md", cmd_candidatos)
    p.add_argument("--min-n", type=int, default=3)
    p.add_argument("--alto", type=float, default=0.75)
    p.add_argument("--baixo", type=float, default=0.25)
    p.add_argument("--marcar-promovido", metavar="CHAVE", help="chave modelo|tarefa|decisao já promovida")

    p = add("pendentes", "episódios pendentes recentes (mais novo primeiro)", cmd_pendentes)
    p.add_argument("--dias", type=int, default=14)

    add("stats", "resumo da memória: episódios, R médio, melhores e piores decisões", cmd_stats)
    add("selftest", "testes embutidos em diretórios temporários + validação dos dados reais", cmd_selftest)
    add("doctor", "verifica ambiente, arquivos de dados e rede", cmd_doctor)
    return ap


def despachar(argv: list[str]) -> tuple[dict, int]:
    """Executa um subcomando e devolve (payload, exit); usado pelo main e pelo selftest."""
    args = construir_parser().parse_args(argv)
    try:
        return args.fn(args)
    except ErroUso as e:
        diag(str(e))
        payload = {"erro": str(e)}
        if e.payload:
            payload.update(e.payload)
        return payload, e.code


def main(argv: list[str] | None = None) -> int:
    try:
        payload, code = despachar(sys.argv[1:] if argv is None else argv)
    except SystemExit:
        raise
    except Exception as e:  # bug: exit 1 com diagnóstico, nunca traceback cru no stdout
        diag(f"erro inesperado: {e.__class__.__name__}: {e}")
        print(json.dumps({"erro": f"{e.__class__.__name__}: {e}"}, ensure_ascii=False))
        return EXIT_BUG
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    sys.exit(main())

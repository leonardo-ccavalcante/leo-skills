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
import bisect
import concurrent.futures
import contextlib
import datetime as _dt
import difflib
import hashlib
import http.client
import io
import json
import math
import os
import re
import secrets
import shutil
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

try:  # trava entre processos; sem fcntl (Windows) seguimos sem trava
    import fcntl
except ImportError:  # pragma: no cover
    fcntl = None

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
# Cerca de código linha a linha: a regex única com .*? e \1 retrocedia de forma
# catastrófica (46 KB de cercas sem fechamento levavam 9 s no lint).
RE_FENCE_LINHA = re.compile(r"^[ \t]*(`{3,}|~{3,})(.*)$")
# Sequências de crases: um code span abre e fecha com o mesmo comprimento
# (CommonMark), então ``<answer>`` também é código e não tag solta.
RE_CRASES = re.compile(r"`+")
RE_DOC_ABRE = re.compile(r"<documents?\b")
RE_DOC_FECHA = re.compile(r"</documents?\s*>")
# Info string de uma cerca (o que vem depois de ``` ou ~~~): CommonMark aceita
# espaço entre a cerca e a info string, então "``` text verbatim" também é bloco.
RE_INFO_VERBATIM = re.compile(r"^[ \t]*text[ \t]+verbatim\b(.*)$")
RE_ATRIB = re.compile(r"(\w+)=(\S+)")
RE_WS = re.compile(r"\s+")
RE_SHA = re.compile(r"^[0-9a-f]{64}$")
# Id de página vira nome de arquivo no cache: sem '/' nem '.' inicial, nada de
# '../../x' escrevendo fora de STATE_DIR/cache.
RE_ID_PAGINA = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
RE_TOKEN = re.compile(r"\S+\s*|\s+")

# Limites de rede: --timeout é prazo total por página (não só por leitura de
# socket) e uma página maior que isso não é documentação.
MAX_PAGINA = 20 * 1024 * 1024
# Similaridade da edição: abaixo disso compara caractere a caractere (exato);
# acima, por tokens, para não virar O(n·m) em Python.
LIMITE_SIM_CHARS = 20000
LIMITE_SIM_TOKENS = 40000

# umask lida uma vez, na importação (ainda sem threads): arquivo novo nasce com
# o modo que um open() normal daria, não com o 0600 do mkstemp.
_UMASK = os.umask(0o022)
os.umask(_UMASK)

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


def id_pagina_valido(pid) -> bool:
    return isinstance(pid, str) and RE_ID_PAGINA.match(pid) is not None


def caminho_cache(pid: str, sufixo: str = ".md") -> Path:
    """Único ponto que monta caminho de cache: recusa id que escaparia do diretório."""
    if not id_pagina_valido(pid):
        raise ErroUso(f"id de página inválido (use [A-Za-z0-9._-], sem '/' nem '.' inicial): {pid!r}",
                      EXIT_VALIDACAO)
    return cache_dir() / f"{pid}{sufixo}"


@contextlib.contextmanager
def trava_estado():
    """Trava exclusiva do STATE_DIR: dois `recompensa` simultâneos perdiam updates do placar."""
    if fcntl is None:  # pragma: no cover
        yield
        return
    with (state_dir() / ".trava").open("a") as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)


def agora_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def hoje_utc() -> str:
    return _dt.datetime.now(_dt.timezone.utc).date().isoformat()


def parse_iso(s: str) -> _dt.datetime | None:
    """Data ISO sempre com fuso: sem fuso vale UTC, senão comparar com um limite
    aware levantava TypeError e uma linha editada à mão derrubava o pendentes."""
    try:
        d = _dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
    except (ValueError, AttributeError, TypeError):
        return None
    return d if d.tzinfo is not None else d.replace(tzinfo=_dt.timezone.utc)


def diag(msg: str) -> None:
    print(f"pcm: {msg}", file=sys.stderr)


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def escrever_atomico(path: Path, data: bytes) -> None:
    """Temporário + os.replace: um crash no meio nunca deixa arquivo pela metade.

    Segue symlink (substituir o link por arquivo quebraria quem o criou) e mantém
    o modo do arquivo existente: fontes.json é do repo e não pode virar 0600.
    """
    path = Path(os.path.realpath(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        modo = path.stat().st_mode & 0o7777
    except FileNotFoundError:
        modo = 0o666 & ~_UMASK
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        with contextlib.suppress(OSError):
            os.chmod(tmp, modo)
        os.replace(tmp, path)
    except BaseException:
        with contextlib.suppress(OSError):
            os.unlink(tmp)
        raise


def escrever_json(path: Path, obj, final_nl: bool = True, eol: str = "\n", bom: bool = False) -> None:
    """eol/bom: fontes.json é do repo; reescrever CRLF como LF mudava todas as linhas no diff."""
    txt = json.dumps(obj, indent=2, ensure_ascii=False) + ("\n" if final_nl else "")
    if eol != "\n":
        txt = txt.replace("\n", eol)
    escrever_atomico(path, (("﻿" if bom else "") + txt).encode("utf-8"))


def tem_surrogate(obj) -> bool:
    """Surrogate solto (\\ud800 num JSON, emoji truncado) não vira UTF-8: gravar
    o episódio ou o placar levantava UnicodeEncodeError (exit 1)."""
    if isinstance(obj, str):
        return any("\ud800" <= ch <= "\udfff" for ch in obj)
    if isinstance(obj, dict):
        return any(tem_surrogate(k) or tem_surrogate(v) for k, v in obj.items())
    if isinstance(obj, list):
        return any(tem_surrogate(v) for v in obj)
    return False


def ler_json(path: Path, padrao=None):
    """Arquivo de estado ausente ou vazio vale o padrão (primeiro uso).

    utf-8-sig: editor do Windows grava BOM e o json.loads recusaria o arquivo.
    """
    try:
        txt = path.read_text(encoding="utf-8-sig")
    except FileNotFoundError:
        return padrao
    if not txt.strip():
        return padrao
    try:
        return json.loads(txt)
    except RecursionError:
        # '[' aninhado demais: é JSON ruim, não bug (exit 1).
        raise ValueError("JSON aninhado demais")


# Tudo que um arquivo de dados ruim levanta ao ser lido: JSON inválido e
# não UTF-8 (ValueError), diretório ou permissão (OSError).
ERROS_LEITURA = (ValueError, OSError)


def ler_estado(path: Path, padrao: dict) -> dict:
    """Estado da memória: corrompido vira diagnóstico (exit 3) e nunca é sobrescrito."""
    try:
        d = ler_json(path, padrao)
    except ERROS_LEITURA as e:  # JSONDecodeError e UnicodeDecodeError são ValueError
        raise ErroUso(f"{path} corrompido ({e.__class__.__name__}: {e}); corrija ou remova o arquivo",
                      EXIT_VALIDACAO)
    if d is None:
        return padrao
    if not isinstance(d, dict):
        raise ErroUso(f"{path} corrompido: esperado objeto JSON; corrija ou remova o arquivo", EXIT_VALIDACAO)
    return d


def ler_entrada(arg: str | None) -> str:
    """Lê arquivo ou stdin do mesmo jeito: UTF-8 estrito, BOM descartado e quebras
    de linha universais (como o read_text de antes, para CRLF não mudar o lint)."""
    if arg in (None, "-"):
        if sys.stdin is None:  # stdin fechado (<&-): sem isto, AttributeError e exit 1
            raise ErroUso("sem entrada: stdin está fechado (passe um arquivo)", EXIT_INSUFICIENTE)
        buf = getattr(sys.stdin, "buffer", None)
        if buf is None:  # stdin trocado por StringIO (selftest)
            return sys.stdin.read().lstrip("\ufeff")
        dados, nome = buf.read(), "stdin"
    else:
        nome = arg
        try:
            dados = Path(arg).read_bytes()
        except FileNotFoundError:
            raise ErroUso(f"arquivo não encontrado: {arg}", EXIT_INSUFICIENTE)
        except OSError as e:  # diretório, permissão...
            raise ErroUso(f"não foi possível ler {arg}: {e.strerror or e}", EXIT_INSUFICIENTE)
    try:
        return dados.decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
    except UnicodeDecodeError as e:
        raise ErroUso(f"{nome} não é UTF-8 (byte inválido na posição {e.start})", EXIT_VALIDACAO)


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


def _mesmo_host_https(url: str, novo: str) -> bool:
    a, b = urllib.parse.urlparse(url), urllib.parse.urlparse(novo)
    return b.scheme == "https" and (b.hostname or "").lower() == (a.hostname or "").lower()


class _RedirecionamentoRestrito(urllib.request.HTTPRedirectHandler):
    """Só segue redirect para o mesmo host https: validar_url vê só a URL inicial,
    e um 302 para outro domínio viraria cache e sha "oficiais"."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not _mesmo_host_https(req.full_url, newurl):
            with contextlib.suppress(Exception):
                fp.close()
            raise ErroRede(f"redirecionamento para fora de {urllib.parse.urlparse(req.full_url).hostname}: {newurl}")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _ler_com_prazo(r, url: str, prazo: float) -> bytes:
    """Lê em pedaços conferindo o prazo total: o timeout do urlopen vale por recv,
    e um servidor pingando 1 byte/s segurava o fontes-check indefinidamente."""
    partes, total = [], 0
    while True:
        if time.monotonic() > prazo:
            raise ErroRede(f"prazo esgotado lendo {url}")
        pedaco = r.read1(65536)
        if not pedaco:
            # read1 não levanta IncompleteRead: sem isto uma conexão cortada no meio
            # do corpo virava página "mudou" com conteúdo truncado no cache.
            faltam = getattr(r, "length", None)
            if faltam:
                raise ErroRede(f"resposta truncada em {url}: faltaram {faltam} bytes")
            return b"".join(partes)
        total += len(pedaco)
        if total > MAX_PAGINA:
            raise ErroRede(f"página maior que {MAX_PAGINA} bytes: {url}")
        partes.append(pedaco)


def fetch(url: str, timeout: float = 15.0) -> bytes:
    """Busca a página; com PCM_FETCH_DIR lê fixture local (testes sem rede)."""
    fdir = os.environ.get("PCM_FETCH_DIR")
    if fdir:
        p = Path(fdir) / f"{id_da_url(url)}.md"
        try:
            return p.read_bytes()
        except OSError as e:
            raise ErroRede(f"rede simulada: {p.name} ausente ({e.__class__.__name__})")
    prazo = time.monotonic() + timeout
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    opener = urllib.request.build_opener(_RedirecionamentoRestrito)
    try:
        with opener.open(req, timeout=timeout) as r:
            if not _mesmo_host_https(url, r.geturl()):
                raise ErroRede(f"resposta veio de fora de {urllib.parse.urlparse(url).hostname}: {r.geturl()}")
            return _ler_com_prazo(r, url, prazo)
    except urllib.error.HTTPError as e:
        raise ErroRede(f"HTTP {e.code} em {url}")
    # HTTPException (IncompleteRead, BadStatusLine...) não é OSError e o urllib não a
    # embrulha: sem isto uma resposta truncada derrubava o fontes-check inteiro (exit 1).
    except (urllib.error.URLError, http.client.HTTPException, OSError, ValueError) as e:
        motivo = " ".join(str(getattr(e, "reason", e)).split())
        raise ErroRede(f"falha de rede em {url}: {e.__class__.__name__}: {motivo}")


# ---------------------------------------------------------------------------
# fontes.json
# ---------------------------------------------------------------------------

def caminho_fontes() -> Path:
    return skill_dir() / "fontes.json"


def carregar_fontes() -> tuple[dict, dict]:
    """Devolve (dados, formato) para reescrever sem ruído no diff.

    formato = {final_nl, eol, bom}: lido em bytes porque read_text traduz CRLF e
    o fontes-aplicar reescrevia um arquivo CRLF inteiro como LF.
    """
    p = caminho_fontes()
    try:
        bruto = p.read_bytes()
    except FileNotFoundError:
        raise ErroUso(f"fontes.json ausente em {p}", EXIT_INSUFICIENTE)
    except OSError as e:
        raise ErroUso(f"fontes.json ilegível: {e.strerror or e}", EXIT_VALIDACAO)
    try:
        raw = bruto.decode("utf-8-sig")
    except UnicodeDecodeError as e:
        raise ErroUso(f"fontes.json não é UTF-8: {e}", EXIT_VALIDACAO)
    try:
        dados = json.loads(raw)
    except (ValueError, RecursionError) as e:
        raise ErroUso(f"fontes.json inválido: {e}", EXIT_VALIDACAO)
    # URL fora do domínio não invalida o arquivo aqui: vira status "erro" da página.
    # sha provisório ("...", "") também não: a página sai "mudou" e o fontes-aplicar o preenche.
    erros = validar_fontes(dados, checar_urls=False, sha_estrito=False)
    if erros:
        raise ErroUso("fontes.json inválido: " + "; ".join(erros), EXIT_VALIDACAO)
    formato = {"final_nl": raw.endswith("\n"), "eol": "\r\n" if b"\r\n" in bruto else "\n",
               "bom": bruto.startswith(b"\xef\xbb\xbf")}
    return dados, formato


def shas_pendentes(d: dict) -> list[str]:
    """Páginas com sha provisório (o modelo do spec usa "..."): falta um fontes-aplicar."""
    return [p["id"] for p in d.get("paginas", [])
            if isinstance(p, dict) and not (isinstance(p.get("sha256"), str) and RE_SHA.match(p["sha256"]))]


@contextlib.contextmanager
def trava_fontes():
    """Trava exclusiva do SKILL_DIR para o read-modify-write de fontes.json.

    Trava o diretório (flock num fd de diretório) em vez de criar um .lock: o
    SKILL_DIR é o repo e não pode ganhar arquivo solto. Sem ela, 12 fontes-aplicar
    simultâneos terminavam com exit 0 e metade das páginas perdidas.
    """
    if fcntl is None:  # pragma: no cover
        yield
        return
    try:
        fd = os.open(str(skill_dir()), os.O_RDONLY)
    except OSError:
        yield  # sem como abrir o diretório: carregar_fontes dará o erro certo
        return
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        os.close(fd)  # fechar o fd solta a trava


def validar_fontes(d, checar_urls: bool = True, sha_estrito: bool = True) -> list[str]:
    """Checagem estrutural: outros agentes editam o arquivo, então conferimos a forma.

    sha_estrito=False aceita sha provisório (texto qualquer ou null): uma página
    recém-adicionada à mão bloqueava fontes-check e fontes-aplicar de todas.
    """
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
        if not id_pagina_valido(pid):
            erros.append(f"paginas[{i}]: id inválido {pid!r} (use [A-Za-z0-9._-], sem '/' nem '.' inicial)")
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
        sha = p.get("sha256")
        if sha_estrito and not (isinstance(sha, str) and RE_SHA.match(sha)):
            erros.append(f"{pid}: sha256 inválido")
        elif not (sha is None or isinstance(sha, str)):
            erros.append(f"{pid}: sha256 deve ser texto")
        if not isinstance(p.get("bytes"), int):
            erros.append(f"{pid}: bytes não é inteiro")
        for campo in ("modelos", "alimenta"):
            if not isinstance(p.get(campo, []), list):
                erros.append(f"{pid}: {campo} não é lista")
    return erros


def ler_cache(pid: str, sufixo: str = ".md") -> bytes | None:
    p = caminho_cache(pid, sufixo)
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
    atual, anterior = caminho_cache(pid), caminho_cache(pid, ".anterior.md")
    velho, velho_ant = ler_cache(pid), ler_cache(pid, ".anterior.md")
    # Procura a baseline (conteúdo com o sha registrado) antes de mexer no cache.
    baseline = None
    for cand in (velho, velho_ant):
        if cand is not None and sha256_bytes(cand) == sha_reg:
            baseline = cand
            break
    if velho is not None and sha256_bytes(velho) != sha:
        # A baseline já guardada em .anterior não é trocada por uma versão
        # intermediária: com duas mudanças antes do fontes-aplicar o diff sumia.
        if not (baseline is not None and baseline is velho_ant):
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
    dpath = caminho_cache(pid, ".diff")
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
        # Grupo opcional que não casou dá None; id que não serve de nome de
        # arquivo também não vira página nova (a URL sairia .../None.md).
        if not id_pagina_valido(nid) or nid in conhecidos or nid in vistos:
            continue
        vistos.add(nid)
        novas.append({"id": nid, "url": URL_NOVA_TMPL.format(id=nid)})
    return novas, None


def validar_timeout(t: float) -> float:
    """Timeout 0, negativo ou nan virava 'falha de rede' e offline=true, como se a rede tivesse caído."""
    if not (isinstance(t, (int, float)) and math.isfinite(t) and t > 0):
        raise ErroUso(f"--timeout deve ser um número de segundos > 0: {t}", EXIT_VALIDACAO)
    return float(t)


def cmd_fontes_check(args) -> tuple[dict, int]:
    validar_timeout(args.timeout)
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
    validar_timeout(args.timeout)
    # Ler, alterar e gravar fontes.json sob trava: duas execuções simultâneas
    # sobrescreviam uma a outra e ambas diziam exit 0.
    with trava_fontes():
        return _fontes_aplicar(args)


def _fontes_aplicar(args) -> tuple[dict, int]:
    fontes, formato = carregar_fontes()
    dominio = fontes["dominio_permitido"]
    por_id = {p["id"]: p for p in fontes["paginas"]}
    ids = lista_csv(args.ids)
    if args.todas_mudadas:
        for p in fontes["paginas"]:
            c = ler_cache(p["id"])
            if c is not None and sha256_bytes(c) != p.get("sha256") and p["id"] not in ids:
                ids.append(p["id"])
    adicionar: list[tuple[str, str]] = []
    for spec in args.adicionar or []:
        if "=" not in spec:
            raise ErroUso(f"--adicionar espera id=url: {spec}", EXIT_VALIDACAO)
        nid, url = spec.split("=", 1)
        nid, url = nid.strip(), url.strip()
        # Tudo que validar_fontes recusaria é barrado aqui, antes de escrever:
        # senão o próprio fontes-aplicar deixava fontes.json quebrado para todo comando.
        if not id_pagina_valido(nid):
            raise ErroUso(f"--adicionar: id inválido {nid!r} (use [A-Za-z0-9._-], sem '/' nem '.' inicial)",
                          EXIT_VALIDACAO)
        if nid in por_id:
            raise ErroUso(f"id já existe em fontes.json: {nid}", EXIT_VALIDACAO)
        if any(nid == a for a, _u in adicionar):
            raise ErroUso(f"--adicionar repetido para o mesmo id: {nid}", EXIT_VALIDACAO)
        try:
            validar_url(url, dominio)
        except ErroRede as e:
            raise ErroUso(str(e), EXIT_VALIDACAO)
        adicionar.append((nid, url))
    if not ids and not adicionar:
        if args.todas_mudadas:
            # Nada mudou é o caso normal depois de um fontes-check limpo, não erro.
            return {"arquivo": str(caminho_fontes()), "alteradas": [], "adicionadas": []}, EXIT_OK
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
            escrever_atomico(caminho_cache(nid), c)
        novos_conteudos[nid] = c
    if sem_cache:
        raise ErroUso(f"sem cache (rode fontes-check antes): {', '.join(sem_cache)}", EXIT_INSUFICIENTE,
                      {"sem_cache": sem_cache, "alteradas": [], "adicionadas": []})
    hoje = hoje_utc()
    alteradas = []
    for i in ids:
        c = ler_cache(i)
        p = por_id[i]
        antes = p.get("sha256")
        p["sha256"], p["bytes"], p["verificado_em"] = sha256_bytes(c), len(c), hoje
        alteradas.append({"id": i, "sha_anterior": antes, "sha_novo": p["sha256"], "bytes": p["bytes"]})
    adicionadas = []
    for nid, url in adicionar:
        c = novos_conteudos[nid]
        entrada = {"id": nid, "url": url, "sha256": sha256_bytes(c), "bytes": len(c), "verificado_em": hoje,
                   "tipo": "prompting", "modelos": [], "alimenta": []}
        fontes["paginas"].append(entrada)
        adicionadas.append({"id": nid, "sha_novo": entrada["sha256"], "bytes": len(c)})
    escrever_json(caminho_fontes(), fontes, final_nl=formato["final_nl"], eol=formato["eol"], bom=formato["bom"])
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


def fecha_cerca(linha: str, cerca: str) -> bool:
    """CommonMark: fecha com o mesmo caractere, comprimento >= o da abertura, sem info string.

    Exigir comprimento igual deixava uma abertura de 4 crases fechada por 5 sem fechar,
    e o bloco engolia os blocos verbatim seguintes, que ficavam sem verificação.
    """
    s = linha.strip()
    return len(s) >= len(cerca) and s == cerca[0] * len(s)


def extrair_blocos(texto: str) -> list[dict]:
    """Blocos ```text verbatim fonte=... id=...```; bloco sem fechamento vira erro.

    Acompanha todas as cercas (``` e ~~~), não só as verbatim: dentro de um bloco
    ```` que mostra a sintaxe, a linha ```text verbatim é conteúdo (CommonMark) e
    era verificada como citação de verdade.
    """
    linhas = texto.split("\n")
    blocos, i = [], 0
    # Menor cerca sem fechamento já vista, por caractere: uma cerca igual ou mais
    # longa depois dela também não fecha, e reprocurar deixaria a varredura quadrática.
    sem_fecho: dict[str, int] = {}
    while i < len(linhas):
        m = RE_FENCE_LINHA.match(linhas[i])
        if not m or (m.group(1)[0] == "`" and "`" in m.group(2)):
            i += 1
            continue
        cerca, info = m.group(1), m.group(2)
        mv = RE_INFO_VERBATIM.match(info)
        if len(cerca) >= sem_fecho.get(cerca[0], len(cerca) + 1):
            j = len(linhas)
        else:
            j = i + 1
            while j < len(linhas) and not fecha_cerca(linhas[j], cerca):
                j += 1
            if j >= len(linhas):
                sem_fecho[cerca[0]] = len(cerca)
        if mv:
            attrs = dict(RE_ATRIB.findall(mv.group(1)))
            blocos.append({"linha": i + 1, "fonte": attrs.get("fonte"), "id": attrs.get("id"),
                           "conteudo": "\n".join(linhas[i + 1:j]), "fechado": j < len(linhas)})
        elif j >= len(linhas):
            # Cerca comum sem fechamento: pelo CommonMark engoliria o resto do
            # arquivo, e os blocos verbatim seguintes ficariam sem verificação.
            i += 1
            continue
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
        try:
            texto = arq.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError as e:
            # Um .md ruim vira falha dele; não pode derrubar a verificação dos outros.
            falhas.append({"arquivo": rel, "linha": None, "fonte": None, "id": None, "inicio": "",
                           "motivo": f"arquivo não é UTF-8 (byte inválido na posição {e.start})"})
            continue
        for b in extrair_blocos(texto):
            total += 1
            falha = {"arquivo": rel, "linha": b["linha"], "fonte": b["fonte"], "id": b["id"],
                     "inicio": normalizar(b["conteudo"])[:80]}
            if not b["fonte"] or not b["id"]:
                falhas.append({**falha, "motivo": "atributos fonte= e id= obrigatórios"})
                continue
            if not id_pagina_valido(b["fonte"]):
                # fonte= vira nome de arquivo no cache: '../x' leria fora dele.
                falhas.append({**falha, "motivo": "fonte= inválida (use o id da página em fontes.json)"})
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
    elif not all(isinstance(m, str) for m in mods):
        # Lista aninhada é inalcançável e ainda levantava TypeError (unhashable) aqui.
        erros.append(f"{tag}: modelos deve ser lista de textos")
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
    if t == "campo_presente" and not (isinstance(c.get("campos"), list) and c["campos"]
                                      and all(isinstance(x, str) and x for x in c["campos"])):
        # Caminho não texto passava aqui e quebrava o lint no split (exit 1).
        return [f"{tag}: campo_presente exige campos (lista de caminhos em texto)"]
    if t in ("valor_igual", "combinacao") and isinstance(c.get("caminho"), str) and not c["caminho"]:
        return [f"{tag}: caminho vazio"]
    if t == "valor_igual" and not (isinstance(c.get("caminho"), str) and isinstance(c.get("valores"), list)):
        return [f"{tag}: valor_igual exige caminho e valores"]
    if t == "ultimo_role" and not isinstance(c.get("valores"), list):
        return [f"{tag}: ultimo_role exige valores"]
    if t == "combinacao":
        todas = c.get("todas")
        if not isinstance(todas, list) or not todas:
            return [f"{tag}: combinacao exige todas"]
        for s in todas:
            if not (isinstance(s, dict) and isinstance(s.get("caminho"), str) and s["caminho"]
                    and isinstance(s.get("valores"), list)):
                return [f"{tag}: subcondição de combinacao exige caminho e valores"]
    return []


def validar_arquivo_regras(p: Path, validador) -> tuple[dict | None, list[str]]:
    """Lê e valida um arquivo de regras; (None, []) se ausente.

    Único caminho de leitura para lint, doctor e selftest: cada um lia de um jeito
    (BOM aceito num, recusado no outro) e davam veredictos diferentes do mesmo arquivo.
    """
    try:
        d = ler_json(p)
    except ERROS_LEITURA as e:  # JSON inválido, não UTF-8, diretório no lugar do arquivo
        motivo = f"não é UTF-8 (byte inválido na posição {e.start})" if isinstance(e, UnicodeDecodeError) \
            else f"{e.__class__.__name__}: {e}"
        return None, [motivo]
    if d is None:
        return None, []
    return d, validador(d)


def carregar_regras(nome: str, validador) -> list[dict]:
    """Arquivo ausente = sem regras (a skill ainda está sendo montada)."""
    d, erros = validar_arquivo_regras(skill_dir() / "references" / nome, validador)
    if erros:
        raise ErroUso(f"{nome} inválido: " + "; ".join(erros), EXIT_VALIDACAO)
    if d is None:
        diag(f"{nome} ausente: regras dele não aplicadas")
        return []
    return d["regras"]


# ---------------------------------------------------------------------------
# Lint
# ---------------------------------------------------------------------------

def _linha_de(texto: str, pos: int) -> int:
    return texto.count("\n", 0, pos) + 1


def indice_linhas(texto: str) -> list[int]:
    """Posições de cada '\\n', para achar a linha de um casamento por busca binária.

    Contar do início a cada casamento deixava o lint quadrático (1,5 MB, 26 s).
    """
    return [m.start() for m in re.finditer("\n", texto)]


def _linha_idx(idx: list[int], pos: int) -> int:
    return bisect.bisect_left(idx, pos) + 1


def _trecho(texto: str, pos: int) -> str:
    ini = texto.rfind("\n", 0, pos) + 1
    fim = texto.find("\n", pos)
    return texto[ini: fim if fim >= 0 else len(texto)].strip()[:160]


def _mascarar_cercas(texto: str) -> str:
    """Troca blocos de código cercados por espaços, em tempo linear.

    Segue o CommonMark: info string de cerca com crase não pode conter crase (então
    ```inline``` não abre bloco), fecha com cerca do mesmo caractere de comprimento
    >= e, sem fechamento, o bloco vai até o fim do texto.
    """
    linhas = texto.split("\n")
    i = 0
    while i < len(linhas):
        m = RE_FENCE_LINHA.match(linhas[i])
        if not m or (m.group(1)[0] == "`" and "`" in m.group(2)):
            i += 1
            continue
        cerca, j = m.group(1), i + 1
        while j < len(linhas) and not fecha_cerca(linhas[j], cerca):
            j += 1
        fim = min(j, len(linhas) - 1)
        for k in range(i, fim + 1):
            linhas[k] = " " * len(linhas[k])
        i = fim + 1
    return "\n".join(linhas)


def _mascarar_crases_linha(linha: str) -> str:
    """Code spans de uma linha viram espaços, em tempo linear.

    CommonMark: abre com N crases e fecha na próxima sequência de exatamente N
    crases; sem par, as crases são texto. A regex antiga só via `x` e, em
    ``<answer>``, casava os pares vazios e deixava a tag exposta.
    """
    seqs = [(m.start(), m.end()) for m in RE_CRASES.finditer(linha)]
    if len(seqs) < 2:
        return linha
    proximo: list[int | None] = [None] * len(seqs)
    ultimo: dict[int, int] = {}
    for k in range(len(seqs) - 1, -1, -1):
        n = seqs[k][1] - seqs[k][0]
        proximo[k] = ultimo.get(n)
        ultimo[n] = k
    partes, cursor, k = [], 0, 0
    while k < len(seqs):
        par = proximo[k]
        if par is None:
            k += 1
            continue
        ini, fim = seqs[k][0], seqs[par][1]
        partes.append(linha[cursor:ini])
        partes.append(" " * (fim - ini))
        cursor, k = fim, par + 1
    partes.append(linha[cursor:])
    return "".join(partes)


def _mascarar_codigo(texto: str) -> str:
    """Troca código (cercas e crases) por espaços, preservando posições e linhas."""
    return "\n".join(_mascarar_crases_linha(ln) for ln in _mascarar_cercas(texto).split("\n"))


def _achado(regra, sev, linha, trecho, motivo, sugestao, fonte, origem=None) -> dict:
    a = {"regra": regra, "severidade": sev, "linha": linha, "trecho": trecho,
         "motivo_pt": motivo, "sugestao_pt": sugestao, "fonte": fonte}
    if origem:
        a["origem"] = origem
    return a


def lint_texto(texto: str, modelo: str, regras: list[dict], compiladas: dict, origem=None) -> list[dict]:
    achados = []
    idx: list[int] | None = None
    for r in regras:
        if modelo not in expandir_modelos(r["modelos"]):
            continue
        rx = compiladas[r["id"]]
        linhas_vistas: set[int] = set()
        for m in rx.finditer(texto):
            if idx is None:
                idx = indice_linhas(texto)
            ln = _linha_idx(idx, m.start())
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
    # Pela ordem, não pela contagem: um </foo> solto antes não "fecha" um <foo> posterior.
    eventos = [(m.start(), m.group(1), True) for m in RE_TAG_ABRE.finditer(semcod) if not m.group(0).endswith("/>")]
    eventos += [(m.start(), m.group(1), False) for m in RE_TAG_FECHA.finditer(semcod)]
    eventos.sort(key=lambda e: e[0])
    pilhas: dict[str, list[int]] = {}
    for pos, nome, abre in eventos:
        pilha = pilhas.setdefault(nome, [])
        if abre:
            pilha.append(pos)
        elif pilha:
            pilha.pop()
    for nome, pilha in sorted(((n, p) for n, p in pilhas.items() if p), key=lambda x: x[1][0]):
        if pilha:
            pos = pilha[0]
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
    """Extrai o texto de system e de cada mensagem para o lint de texto.

    Os blocos de texto de uma mesma mensagem são juntados: um <documents> aberto
    num bloco e fechado no seguinte é uma estrutura só, não uma tag sem fechamento.
    """
    out = []

    def coletar(conteudo, origem):
        if isinstance(conteudo, str):
            out.append((origem, conteudo))
            return
        if not isinstance(conteudo, list):
            return
        partes = []
        for k, b in enumerate(conteudo):
            if isinstance(b, dict) and isinstance(b.get("text"), str):
                partes.append((f"{origem}[{k}]", b["text"]))
            elif isinstance(b, str):
                partes.append((f"{origem}[{k}]", b))
        if len(partes) == 1:
            out.append(partes[0])
        elif partes:
            out.append((origem, "\n".join(t for _o, t in partes)))

    coletar(req.get("system"), "system")
    msgs = req.get("messages")
    for i, m in enumerate(msgs if isinstance(msgs, list) else []):
        if isinstance(m, dict):
            coletar(m.get("content"), f"messages[{i}]")
    return out


def executar_lint(texto: str, modelo: str) -> dict:
    cruft = carregar_regras("cruft.json", validar_cruft)
    restr = carregar_regras("restricoes-api.json", validar_restricoes)
    compiladas = {r["id"]: re.compile(r["padrao"], re.I | re.M) for r in cruft}
    req = None
    # RecursionError: '[' aninhado demais não é JSON utilizável; vira texto de prompt.
    with contextlib.suppress(ValueError, RecursionError):
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
        # errors="replace": um byte ruim estraga só a própria linha (ignorada abaixo).
        with caminho_episodios().open(encoding="utf-8-sig", errors="replace") as f:
            for n, linha in enumerate(f, 1):
                if not linha.strip():
                    continue
                try:
                    ep = json.loads(linha)
                except (ValueError, RecursionError):
                    diag(f"episodios.jsonl linha {n} ilegível; ignorada")
                    continue
                # id não texto (lista, número) derrubava todo comando que lê episódios.
                if isinstance(ep, dict) and isinstance(ep.get("id"), str) and ep["id"]:
                    eps[ep["id"]] = ep
                elif isinstance(ep, dict):
                    diag(f"episodios.jsonl linha {n} sem id válido; ignorada")
    except FileNotFoundError:
        pass
    return eps


def anexar_episodio(ep: dict) -> None:
    """Anexa um retrato; chame sob trava_estado().

    Se um append anterior foi interrompido (disco cheio, crash), a última linha
    ficou sem '\\n' e o retrato novo seria colado nela e perdido: termina a linha antes.
    """
    p = caminho_episodios()
    with p.open("ab") as f:
        if f.tell() > 0:
            with p.open("rb") as r:
                r.seek(-1, os.SEEK_END)
                if r.read(1) != b"\n":
                    f.write(b"\n")
        f.write((json.dumps(ep, ensure_ascii=False) + "\n").encode("utf-8"))
        f.flush()
        os.fsync(f.fileno())


def _strings_longas(obj, caminho="") -> list[str]:
    if isinstance(obj, str):
        return [caminho] if len(obj) > MAX_TEXTO else []
    if isinstance(obj, dict):
        # Chaves também: {"lint": {"<texto do usuário>": 1}} guardaria conteúdo. A
        # chave longa sai como <chave longa> para não ecoar o conteúdo na mensagem.
        out = []
        for k, v in obj.items():
            longa = len(str(k)) > MAX_TEXTO
            nome = "<chave longa>" if longa else str(k)
            c = f"{caminho}.{nome}" if caminho else nome
            if longa:
                out.append(c)
            out.extend(_strings_longas(v, c))
        return out
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
    if tem_surrogate(d):
        raise ErroUso("episódio com texto que não é UTF-8 válido (surrogate solto, ex.: \\ud800)", EXIT_VALIDACAO)
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
    if not modelo_conhecido(d["modelo"]):
        # politica recusa modelo desconhecido: aceitar aqui juntaria recompensa que nunca é lida.
        raise ErroUso(f"modelo desconhecido: {d['modelo']} (conhecidos: {', '.join(MODELOS_CONHECIDOS)})",
                      EXIT_VALIDACAO)
    decs = d["decisoes"]
    if not isinstance(decs, list) or not all(isinstance(x, str) and x.strip() for x in decs):
        raise ErroUso("decisoes deve ser lista de ids", EXIT_VALIDACAO)
    # Sem espaço nas pontas, como o lista_csv do --decisoes-editadas: senão "a "
    # nunca casava com "a" e a decisão editada recebia crédito cheio.
    decs = [x.strip() for x in decs]
    # '|' separa as partes da chave do placar; '*' é a chave agregada.
    for v in [d["modelo"], d["tarefa"], *decs]:
        if "|" in v:
            raise ErroUso(f"'|' não permitido em modelo/tarefa/decisões: {v}", EXIT_VALIDACAO)
    if d["tarefa"] == "*":
        raise ErroUso("tarefa '*' é reservada para o agregado", EXIT_VALIDACAO)
    if "lint" in d and d["lint"] is not None:
        li = d["lint"]
        # Só as duas contagens: chave extra seria canal para texto livre.
        if (not isinstance(li, dict) or set(li) - {"hard", "soft"}
                or any(isinstance(v, bool) or not isinstance(v, int) or v < 0 for v in li.values())):
            raise ErroUso("lint deve ser {hard: int, soft: int}", EXIT_VALIDACAO)
    if d.get("rubrica") is not None:
        _num01(d["rubrica"], "rubrica")
    ep = {k: d[k] for k in CAMPOS_EPISODIO if k in d}
    ep["decisoes"] = list(dict.fromkeys(decs))
    return ep


def cmd_episodio(args) -> tuple[dict, int]:
    try:
        d = json.loads(ler_entrada(args.arquivo))
    except (ValueError, RecursionError) as e:  # RecursionError: '[' aninhado demais
        raise ErroUso(f"JSON inválido: {e.__class__.__name__}: {e}", EXIT_VALIDACAO)
    ep = validar_episodio(d)
    with trava_estado():
        ep_id, agora = _novo_id_episodio()
        ep.update({"id": ep_id, "criado_em": agora.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
                   "pendente": True, "sinais": {}, "decisoes_editadas": [], "contribuicao": {}, "R": None})
        anexar_episodio(ep)
    return {"id": ep_id}, EXIT_OK


def _novo_id_episodio() -> tuple[str, _dt.datetime]:
    """Id que ainda não está em episodios.jsonl; chame sob trava_estado().

    O sufixo tem só 4 hex: dois episódios no mesmo segundo podiam colidir e virar
    um só (o segundo tratado como nova recompensa do primeiro). Com o sorteio
    esgotado, espera o próximo segundo.
    """
    try:
        existentes = caminho_episodios().read_bytes()
    except FileNotFoundError:
        existentes = b""
    for tentativa in range(200):
        agora = _dt.datetime.now(_dt.timezone.utc)
        ep_id = f"ep-{agora.strftime('%Y%m%dT%H%M%S')}-{secrets.token_hex(2)}"
        if f'"{ep_id}"'.encode() not in existentes:
            return ep_id, agora
        if tentativa % 20 == 19:
            time.sleep(1.0 - agora.microsecond / 1e6 + 0.01)
    raise ErroUso("não foi possível gerar id de episódio único; tente de novo", EXIT_BUG)


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


def similaridade(a: str, b: str) -> float:
    """Razão de similaridade entregue×editado (0–1).

    autojunk=False: com o padrão, acima de 200 caracteres o difflib trata letras
    comuns como lixo e apagar 100 de 8 000 caracteres dava 0,43. Textos grandes
    comparam por tokens (palavra + espaço) com peso em caracteres, porque o
    caractere a caractere sem autojunk é O(n·m) e levaria minutos.
    """
    if a == b:
        return 1.0
    if not a or not b:
        return 0.0
    if len(a) + len(b) <= LIMITE_SIM_CHARS:
        return difflib.SequenceMatcher(None, a, b, autojunk=False).ratio()
    ta, tb = RE_TOKEN.findall(a), RE_TOKEN.findall(b)
    sm = difflib.SequenceMatcher(None, ta, tb, autojunk=len(ta) + len(tb) > LIMITE_SIM_TOKENS)
    iguais = sum(len(t) for i, _j, n in sm.get_matching_blocks() for t in ta[i:i + n])
    return 2 * iguais / (len(a) + len(b))


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
        if args.editado == "-" and args.entregue == "-":
            # O segundo '-' lia um stdin já vazio: edição 0,0 e recompensa péssima gravada.
            raise ErroUso("--editado e --entregue não podem ser ambos '-' (stdin só é lido uma vez)",
                          EXIT_VALIDACAO)
        # Os arquivos só são lidos para a razão de similaridade; nada deles é guardado.
        ent, edi = ler_entrada(args.entregue), ler_entrada(args.editado)
        s["edicao"] = similaridade(ent, edi)
    if args.rubrica is not None:
        s["rubrica"] = _num01(args.rubrica, "--rubrica")
    return s


def _aplicar_placar(placar: dict, ep_id: str, modelo: str, tarefa: str, velha: dict, nova: dict) -> None:
    """Idempotente: desfaz a contribuição anterior do episódio antes de somar a nova.

    Quem diz se a contribuição já está somada é a própria entrada do placar
    (`episodios`: {ep_id: R_d}), gravada no mesmo arquivo atômico. Confiar só no
    retrato do episódio (outro arquivo) contava duas vezes quando o append falhava
    depois do placar gravado, e zerava n / negativava alfa quando placar.json sumia.
    """
    agora = agora_iso()
    for d, rd in nova.items():
        for t in (tarefa, "*"):
            k = chave(modelo, t, d)
            e = placar.get(k)
            if e is None:
                e = placar[k] = {"alfa": 0.0, "beta": 0.0, "n": 0, "atualizado_em": agora}
            _conferir_entrada(k, e)
            aplicados = e.get("episodios")
            if not isinstance(aplicados, dict):
                aplicados = e["episodios"] = {}
            n = int(e.get("n", 0))
            antiga = aplicados.get(ep_id)
            if antiga is None and d in velha and n > len(aplicados):
                # Entrada anterior a este registro: há contribuições sem id e o
                # retrato diz que esta foi uma delas.
                antiga = velha[d]
            if antiga is None:
                n += 1
                a, b = float(e.get("alfa", 0)), float(e.get("beta", 0))
            else:
                a, b = float(e.get("alfa", 0)) - antiga, float(e.get("beta", 0)) - (1 - antiga)
            e["alfa"] = max(0.0, round(a + rd, 12))
            e["beta"] = max(0.0, round(b + 1 - rd, 12))
            e["n"] = n
            aplicados[ep_id] = rd
            e["atualizado_em"] = agora


def _conferir_entrada(k: str, e) -> None:
    """Entrada do placar com alfa/beta/n não numéricos: parar (exit 3) em vez de
    sobrescrever às cegas ou levantar ValueError (exit 1)."""
    ok = isinstance(e, dict)
    if ok:
        for campo in ("alfa", "beta", "n"):
            v = e.get(campo, 0)
            if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
                ok = False
    if not ok:
        raise ErroUso(f"{caminho_placar()} corrompido na chave {k!r}; corrija ou remova a entrada", EXIT_VALIDACAO)


def _conferir_episodio(ep: dict) -> None:
    """Retrato editado à mão sem modelo/tarefa/decisões não pode virar KeyError (exit 1)."""
    decs = ep.get("decisoes")
    if not (isinstance(ep.get("modelo"), str) and isinstance(ep.get("tarefa"), str) and isinstance(decs, list)
            and all(isinstance(x, str) for x in decs)):
        raise ErroUso(f"episódio {ep.get('id')} corrompido em episodios.jsonl (modelo/tarefa/decisoes)",
                      EXIT_VALIDACAO)


def cmd_recompensa(args) -> tuple[dict, int]:
    # Sinais (inclusive a similaridade, que pode ser lenta) antes da trava: com
    # ela tomada, uma comparação longa travava todo episodio/recompensa.
    novos = _sinais_novos(args)
    editadas = None
    if args.decisoes_editadas is not None:
        editadas = lista_csv(args.decisoes_editadas)
        if tem_surrogate(editadas):
            raise ErroUso("--decisoes-editadas com texto que não é UTF-8 válido", EXIT_VALIDACAO)
    # Ler episódio + placar, somar e gravar é um read-modify-write: sem trava, dois
    # processos simultâneos perdiam contribuições (12 recompensas → n=9).
    with trava_estado():
        return _recompensa(args, novos, editadas)


def _recompensa(args, novos: dict, editadas_arg: list[str] | None) -> tuple[dict, int]:
    eps = carregar_episodios()
    ep = eps.get(args.id)
    if ep is None:
        raise ErroUso(f"episódio não encontrado: {args.id}", EXIT_INSUFICIENTE)
    _conferir_episodio(ep)
    if editadas_arg is not None:
        conhecidas = {d.strip() for d in ep["decisoes"]}
        fora = [d for d in editadas_arg if d not in conhecidas]
        if fora:
            # Um erro de digitação dava crédito cheio à decisão que o usuário desfez.
            raise ErroUso(f"--decisoes-editadas fora do episódio: {', '.join(fora)} "
                          f"(decisões: {', '.join(ep['decisoes'])})", EXIT_VALIDACAO)
        ep["decisoes_editadas"] = editadas_arg
    sinais = dict(ep.get("sinais") or {})
    sinais.update(novos)  # a última chamada de cada sinal vale
    efetivos = dict(sinais)
    if "rubrica" not in efetivos and ep.get("rubrica") is not None:
        efetivos["rubrica"] = float(ep["rubrica"])
    R = calcular_R(efetivos)
    if R is None:
        # Sem sinal ainda, mas a lista de editadas (e o --fechar) valem para a próxima
        # chamada: antes só eram gravadas com --fechar e a decisão desfeita levava R cheio.
        if args.fechar:
            ep["pendente"] = False
        if args.fechar or editadas_arg is not None:
            anexar_episodio(ep)
        raise ErroUso("nenhum sinal de recompensa (use --nota/--eval/--iteracoes/--edicao/--rubrica)",
                      EXIT_INSUFICIENTE, {"id": ep["id"], "R": None, "fechado": bool(args.fechar),
                                          "decisoes_editadas_gravadas": editadas_arg is not None})
    editadas = set(ep.get("decisoes_editadas") or [])
    nova = {d: (0.0 if d.strip() in editadas else R) for d in ep["decisoes"]}
    placar = ler_estado(caminho_placar(), {})
    _aplicar_placar(placar, ep["id"], ep["modelo"], ep["tarefa"], ep.get("contribuicao") or {}, nova)
    escrever_json(caminho_placar(), placar)
    ep.update({"sinais": sinais, "contribuicao": nova, "R": R, "recompensado_em": agora_iso()})
    if args.fechar:
        ep["pendente"] = False
    anexar_episodio(ep)
    return {"id": ep["id"], "R": R, "sinais": efetivos, "decisoes": nova}, EXIT_OK


def _estat(placar: dict, k: str) -> tuple[float, float, int]:
    e = placar.get(k)
    if not isinstance(e, dict):
        return 0.0, 0.0, 0
    try:
        return float(e.get("alfa", 0)), float(e.get("beta", 0)), int(e.get("n", 0))
    except (TypeError, ValueError):
        return 0.0, 0.0, 0


def partes_chave(k: str) -> tuple[str, str, str] | None:
    """modelo|tarefa|decisao; chave em outro formato é ignorada (não derruba leitura)."""
    partes = k.split("|", 2)
    return (partes[0], partes[1], partes[2]) if len(partes) == 3 else None


def carregar_placar() -> dict:
    placar = ler_estado(caminho_placar(), {})
    ruins = [k for k in placar if partes_chave(k) is None]
    if ruins:
        diag(f"placar.json: {len(ruins)} chave(s) fora do formato modelo|tarefa|decisao ignorada(s)")
    return {k: v for k, v in placar.items() if k not in ruins}


def cmd_politica(args) -> tuple[dict, int]:
    if not modelo_conhecido(args.modelo):
        raise ErroUso(f"modelo desconhecido: {args.modelo}", EXIT_INSUFICIENTE)
    placar = carregar_placar()
    recomendadas = set(lista_csv(args.recomendadas))
    cands = lista_csv(args.candidatas)
    if not cands:
        vistos = {partes_chave(k)[2] for k in placar if partes_chave(k)[0] == args.modelo}
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
    placar = carregar_placar()
    marcado = None
    if args.marcar_promovido:
        k = args.marcar_promovido
        if k not in placar:
            raise ErroUso(f"chave não está no placar: {k}", EXIT_INSUFICIENTE)
        with trava_estado():  # read-modify-write de promovidos.json
            promovidos = ler_estado(caminho_promovidos(), {})
            promovidos[k] = {"marcado_em": agora_iso()}
            escrever_json(caminho_promovidos(), promovidos)
        marcado = k
    promovidos = ler_estado(caminho_promovidos(), {})
    hoje = hoje_utc()
    out, omitidos = [], []
    for k in sorted(placar):
        modelo, tarefa, dec = partes_chave(k)
        if tarefa == "*" or k in promovidos:
            continue
        a, _b, n = _estat(placar, k)
        if n < args.min_n or n <= 0:  # n=0 não tem média (e --min-n 0 dividia por zero)
            continue
        media = a / n
        if media >= args.alto:
            direcao = "reforçar"
        elif media <= args.baixo:
            direcao = "evitar"
        else:
            continue
        if direcao == "evitar" and dec.startswith(("api.", "hard.")):
            # politica trata api./hard. como fixas: a memória nunca afrouxa restrição da API.
            # Sai em omitidos_fixos para a omissão ficar visível, não silenciosa.
            omitidos.append({"chave": k, "n": n, "media": media, "motivo": "decisão fixa (api./hard.): nunca 'evitar'"})
            continue
        media_txt = f"{media:.2f}".replace(".", ",")
        linha = (f"- [{hoje} · {modelo} · {tarefa}] {dec}: {direcao} — Aplicar: <preencher>. "
                 f"Evidência: n={n}, R̄={media_txt}")
        out.append({"chave": k, "modelo": modelo, "tarefa": tarefa, "decisao": dec, "n": n,
                    "media": media, "direcao": direcao, "linha": linha})
    res = {"candidatos": out, "omitidos_fixos": omitidos}
    if marcado:
        res["marcado"] = marcado
    return res, EXIT_OK


def cmd_pendentes(args) -> tuple[dict, int]:
    if args.dias < 0:
        raise ErroUso("--dias deve ser >= 0", EXIT_VALIDACAO)
    try:
        limite = _dt.datetime.now(_dt.timezone.utc) - _dt.timedelta(days=args.dias)
    except OverflowError:  # --dias enorme = sem limite de idade
        limite = _dt.datetime.min.replace(tzinfo=_dt.timezone.utc)
    ordenados = []
    # A ordem do dict é a de criação (1ª linha de cada id): desempata episódios do
    # mesmo segundo, que antes saíam do mais velho para o mais novo.
    for ordem, ep in enumerate(carregar_episodios().values()):
        if not ep.get("pendente"):
            continue
        criado = parse_iso(ep.get("criado_em", ""))
        if criado is None or criado < limite:
            continue
        item = {k: ep.get(k) for k in ("id", "criado_em", "modo", "modelo", "tarefa", "decisoes", "R")}
        ordenados.append((criado, ordem, item))
    ordenados.sort(key=lambda x: (x[0], x[1]), reverse=True)
    lista = [item for _c, _o, item in ordenados]
    return {"dias": args.dias, "total": len(lista), "pendentes": lista}, EXIT_OK


def cmd_stats(args) -> tuple[dict, int]:
    eps = list(carregar_episodios().values())
    por_modelo: dict[str, list[float]] = {}
    por_tarefa: dict[str, list[float]] = {}
    for ep in eps:
        R = ep.get("R")
        if isinstance(R, bool) or not isinstance(R, (int, float)):
            continue
        por_modelo.setdefault(str(ep.get("modelo")), []).append(R)
        por_tarefa.setdefault(str(ep.get("tarefa")), []).append(R)
    media = lambda xs: sum(xs) / len(xs)  # noqa: E731
    placar = carregar_placar()
    decs = []
    for k in placar:
        modelo, tarefa, dec = partes_chave(k)
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
        pend = shas_pendentes(fontes)
        if pend:
            checks.append(_check("fontes.json: sha provisório", False,
                                 f"{', '.join(pend)}: rode fontes-check e fontes-aplicar --ids <id>", "aviso"))
    except ErroUso as e:
        checks.append(_check("fontes.json", False, str(e)))
    for nome, val in (("cruft.json", validar_cruft), ("restricoes-api.json", validar_restricoes)):
        p = skill_dir() / "references" / nome
        d, erros = validar_arquivo_regras(p, val)
        if d is None and not erros:
            checks.append(_check(nome, True, "ausente (opcional até ser gerado)", "aviso"))
            continue
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


class _RespostaFalsa:
    """Resposta HTTP de mentira para testar fetch sem rede."""

    def __init__(self, pedacos=(), length=None, erro=None, url="https://platform.claude.com/x.md"):
        self.pedacos, self.length, self.erro, self.url = list(pedacos), length, erro, url

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def geturl(self):
        return self.url

    def read1(self, _n):
        if self.erro:
            raise self.erro
        return self.pedacos.pop(0) if self.pedacos else b""


def _fetch_falso(resposta) -> str:
    """Roda fetch() com build_opener trocado; devolve 'ok' ou a mensagem de ErroRede."""
    velho_fetch, velho_opener = os.environ.pop("PCM_FETCH_DIR", None), urllib.request.build_opener

    class _Opener:
        def open(self, _req, timeout=None):
            if isinstance(resposta, BaseException):
                raise resposta
            return resposta

    urllib.request.build_opener = lambda *_a: _Opener()
    try:
        fetch("https://platform.claude.com/x.md", 5)
        return "ok"
    except ErroRede as e:
        return f"ErroRede: {e}"
    finally:
        urllib.request.build_opener = velho_opener
        if velho_fetch is not None:
            os.environ["PCM_FETCH_DIR"] = velho_fetch


def _st_rede(st: _Selftest) -> None:
    """Falhas de rede viram ErroRede (status 'erro'), nunca exceção solta (exit 1)."""
    ir = _fetch_falso(_RespostaFalsa(erro=http.client.IncompleteRead(b"parcial", 100)))
    st.t("rede: IncompleteRead → ErroRede", ir.startswith("ErroRede"), ir)
    bs = _fetch_falso(http.client.BadStatusLine("GARBAGE"))
    st.t("rede: BadStatusLine → ErroRede", bs.startswith("ErroRede"), bs)
    tr = _fetch_falso(_RespostaFalsa([b"so dez b"], length=990))
    st.t("rede: corpo truncado (read1 sem erro) → ErroRede", "truncada" in tr, tr)
    fora = _fetch_falso(_RespostaFalsa([b"x"], url="https://evil.example.org/x.md"))
    st.t("rede: resposta de outro host → ErroRede", fora.startswith("ErroRede"), fora)
    st.t("rede: conteúdo normal passa", _fetch_falso(_RespostaFalsa([b"ab", b"cd"])) == "ok")
    req = urllib.request.Request("https://platform.claude.com/docs/a.md")
    try:
        _RedirecionamentoRestrito().redirect_request(req, None, 302, "Found", {}, "https://evil.example.org/x.md")
        redir = "seguiu"
    except ErroRede:
        redir = "recusou"
    st.t("rede: redirect para outro domínio recusado", redir == "recusou", redir)
    try:
        _ler_com_prazo(_RespostaFalsa([b"x"] * 5), "u", time.monotonic() - 1)
        prazo = "leu"
    except ErroRede:
        prazo = "prazo"
    st.t("rede: prazo total vale entre leituras", prazo == "prazo", prazo)


def _st_robustez(st: _Selftest, sk: Path, fetch_dir: Path) -> None:
    """Casos de borda que já quebraram: cada um tem o defeito original no nome."""
    os.environ["PCM_STATE_DIR"] = str(st.tmp / "state-robustez")
    fontes = {"dominio_permitido": "platform.claude.com", "paginas": [_pagina("prompting-claude-x", FIX_X)]}
    (fetch_dir / "prompting-claude-x.md").write_text(FIX_X, encoding="utf-8")
    (fetch_dir / "nova1.md").write_text("# nova\n", encoding="utf-8")
    fj = sk / "fontes.json"
    fj.write_text(json.dumps(fontes, indent=2), encoding="utf-8")
    if os.name == "posix":
        os.chmod(fj, 0o644)
    u = URL_BASE + "nova1.md"
    antes = fj.read_bytes()
    _o, c1 = st.run(["fontes-aplicar", "--adicionar", f"nova1={u}", "--adicionar", f"nova1={u}"])
    _o, c2 = st.run(["fontes-aplicar", "--adicionar", f"={u}"])
    _o, c3 = st.run(["fontes-aplicar", "--adicionar", f"../../fora={u}"])
    st.t("fontes-aplicar: id repetido/vazio/'../' → exit 3 sem escrever",
         (c1, c2, c3) == (3, 3, 3) and fj.read_bytes() == antes and not (st.tmp / "fora.md").exists(), f"{c1} {c2} {c3}")
    ruim = json.loads(json.dumps(fontes))
    ruim["paginas"][0]["id"] = "../../x"
    st.t("fontes: validar_fontes recusa id com '../'", any("id inválido" in e for e in validar_fontes(ruim)))
    st.run(["fontes-check"])
    out, code = st.run(["fontes-aplicar", "--todas-mudadas"])
    st.t("fontes-aplicar: --todas-mudadas sem mudança → exit 0 vazio",
         code == 0 and out.get("alteradas") == [] and out.get("adicionadas") == [], f"{code} {out}")
    _o, code = st.run(["fontes-aplicar", "--adicionar", f"nova1={u}"])
    if os.name == "posix":
        st.t("fontes-aplicar: preserva o modo de fontes.json", code == 0 and (fj.stat().st_mode & 0o777) == 0o644,
             oct(fj.stat().st_mode))
    # Snippets: cerca de fechamento mais longa, fonte com '../', arquivo não UTF-8.
    rob = sk / "references" / "robustez"
    rob.mkdir(parents=True, exist_ok=True)
    (rob / "a.md").write_text("````text verbatim fonte=prompting-claude-x id=r.longa\nUse clear instructions.\n`````\n\n"
                              "```text verbatim fonte=prompting-claude-x id=r.inventado\nLinha inventada.\n```\n\n"
                              "```text verbatim fonte=../../x id=r.fora\nfoo\n```\n", encoding="utf-8")
    (rob / "b.md").write_bytes(b"caf\xe9\n")
    out, code = st.run(["snippets-verificar"])
    motivos = {f["id"]: f["motivo"] for f in out.get("falhas", [])}
    st.t("snippets: cerca de fechamento mais longa fecha o bloco",
         "r.longa" not in motivos and "r.inventado" in motivos
         and {"r.longa", "r.inventado"} <= set(out.get("ids", {})), str(out))
    st.t("snippets: fonte= com '../' recusada", "inválida" in motivos.get("r.fora", ""), str(motivos))
    st.t("snippets: .md não UTF-8 vira falha sem derrubar", code == EXIT_VALIDACAO and any(
        f["arquivo"].endswith("b.md") for f in out.get("falhas", [])), str(out))
    shutil.rmtree(rob)
    # Lint: BOM, messages não-lista, XML entre blocos, cercas patológicas, entrada ruim.
    req = '\ufeff' + json.dumps({"temperature": 0.5, "messages": [{"role": "user", "content": "hi"}]})
    out, code = st.run(["lint", "--modelo", "sonnet-5", "-"], req)
    st.t("lint: request com BOM ainda é request", code == 3 and out.get("entrada") == "request", str(out))
    bom = st.tmp / "entradas" / "bom.json"
    bom.write_bytes(req.encode("utf-8"))
    out, code = st.run(["lint", "--modelo", "sonnet-5", str(bom)])
    st.t("lint: arquivo com BOM ainda é request", code == 3 and out.get("entrada") == "request", str(out))
    _o, code = st.run(["lint", "--modelo", "sonnet-5", "-"], '{"messages": 5}')
    st.t("lint: messages não-lista não derruba", code == 0, str(code))
    req = {"messages": [{"role": "user", "content": [{"type": "text", "text": "<documents>\n<document>a</document>"},
                                                     {"type": "text", "text": "</documents>\nResuma."}]}]}
    out, _ = st.run(["lint", "--modelo", "opus-5-5", "-"], json.dumps(req))
    st.t("lint: XML fechado em outro bloco da mesma mensagem",
         not any(a["regra"] == "heur.tag_sem_fechamento" for a in out["achados"]), str(out))
    cercas = "".join("`" * (k + 3) + "\n" for k in range(600)) + "```inline``` uso\n" * 2000
    t0 = time.monotonic()
    st.run(["lint", "--modelo", "opus-5-5", st.arq("cercas.txt", cercas)])
    dt = time.monotonic() - t0
    st.t("lint: cercas patológicas em tempo linear", dt < 3, f"{dt:.1f}s")
    st.t("lint: cerca sem fechamento mascara até o fim (CommonMark)",
         _mascarar_cercas("a\n```\n<x>\n") == "a\n   \n   \n")
    st.t("lint: ```inline``` não abre bloco", _mascarar_cercas("```inline``` <x>\n") == "```inline``` <x>\n")
    ruim = st.tmp / "entradas" / "latin.txt"
    ruim.write_bytes(b"caf\xe9\n")
    _o, c1 = st.run(["lint", "--modelo", "opus-5-5", str(ruim)])
    _o, c2 = st.run(["lint", "--modelo", "opus-5-5", str(st.tmp)])
    st.t("lint: arquivo não UTF-8 → 3, diretório → 2", (c1, c2) == (3, 2), f"{c1} {c2}")
    # Memória.
    base = {"modo": "criar", "modelo": "opus-5-5", "tarefa": "codigo", "decisoes": ["a"]}
    ep_id = st.run(["episodio", "-"], json.dumps(base))[0]["id"]
    st.run(["recompensa", "--id", ep_id, "--nota", "5"])
    caminho_placar().unlink()
    st.run(["recompensa", "--id", ep_id, "--nota", "1"])
    e = ler_json(caminho_placar(), {}).get(chave("opus-5-5", "codigo", "a"), {})
    st.t("memória: placar.json perdido → reconta o episódio uma vez",
         (e.get("alfa"), e.get("beta"), e.get("n")) == (0.0, 1.0, 1), str(e))
    _o, code = st.run(["candidatos", "--min-n", "0"])
    st.t("candidatos: --min-n 0 não divide por zero", code == 0, str(code))
    # Retrato perdido depois do placar gravado (append falhou): o retry não pode contar de novo.
    linhas = caminho_episodios().read_text(encoding="utf-8").splitlines(keepends=True)
    caminho_episodios().write_text("".join(linhas[:-1]), encoding="utf-8")
    st.run(["recompensa", "--id", ep_id, "--nota", "1"])
    e = ler_json(caminho_placar(), {}).get(chave("opus-5-5", "codigo", "a"), {})
    st.t("memória: retry após append perdido não conta duas vezes", e.get("n") == 1 and e.get("beta") == 1.0, str(e))
    with caminho_episodios().open("a", encoding="utf-8") as f:
        f.write('{"id": "ep-truncado", "modo": "c"')
    novo = st.run(["episodio", "-"], json.dumps(base))[0]["id"]
    _o, code = st.run(["recompensa", "--id", novo, "--nota", "5", "--fechar"])
    st.t("memória: linha truncada não engole o episódio seguinte", code == 0, str(_o))
    longo = dict(base, lint={"hard": 0, "soft": 0, "x" * 400: 1})
    _o, c1 = st.run(["episodio", "-"], json.dumps(longo))
    _o, c2 = st.run(["episodio", "-"], json.dumps(dict(base, lint={"hard": 0, "soft": 0, "nota": "segredo"})))
    _o, c3 = st.run(["episodio", "-"], json.dumps(dict(base, modelo="gpt-9")))
    st.t("episodio: recusa texto em chave de lint, chave extra e modelo desconhecido", (c1, c2, c3) == (3, 3, 3),
         f"{c1} {c2} {c3}")
    for _ in range(3):
        eid = st.run(["episodio", "-"], json.dumps(dict(base, decisoes=["api.x", "hard.y"])))[0]["id"]
        st.run(["recompensa", "--id", eid, "--nota", "1"])
    out, _ = st.run(["candidatos"])
    st.t("candidatos: nunca sugere 'evitar' para api./hard.",
         not any(c["decisao"].startswith(("api.", "hard.")) for c in out["candidatos"]), str(out))
    # Palavras em ordem pseudoaleatória fixa: texto periódico confundiria o próprio difflib.
    vocab = "the model should write clear instructions for each task and avoid excessive markdown".split()
    texto = " ".join(vocab[hashlib.sha256(str(i).encode()).digest()[0] % len(vocab)] for i in range(1200))
    sim = similaridade(texto, texto[:3000] + texto[3100:])
    st.t("recompensa: edição pequena em texto longo ≈ similar", sim > 0.95, f"{sim:.4f}")
    grande = texto * 10
    st.t("recompensa: similaridade de texto grande (por tokens)", similaridade(grande, grande[:-100]) > 0.95)
    _o, code = st.run(["pendentes", "--dias", "999999999"])
    st.t("pendentes: --dias enorme não estoura", code == 0, str(code))
    caminho_placar().write_text("corrompido", encoding="utf-8")
    _o, c1 = st.run(["politica", "--modelo", "opus-5-5"])
    _o, c2 = st.run(["recompensa", "--id", novo, "--nota", "3"])
    st.t("memória: placar corrompido → exit 3 e não é sobrescrito",
         (c1, c2) == (3, 3) and caminho_placar().read_text(encoding="utf-8") == "corrompido", f"{c1} {c2}")


def _st_dados_reais(st: _Selftest, real: Path) -> None:
    """Valida os arquivos reais da skill, quando existem (outros agentes os geram)."""
    # Mesma leitura (utf-8-sig) e mesma validação do lint/doctor: o veredicto tem de bater.
    p = real / "fontes.json"
    if p.exists():
        try:
            d = ler_json(p, {})
            # sha provisório é aviso no doctor, não arquivo inválido (fontes-check o aceita).
            erros = validar_fontes(d, sha_estrito=False)
        except ERROS_LEITURA as e:
            erros = [f"{e.__class__.__name__}: {e}"]
        st.t("dados: fontes.json válido", not erros, "; ".join(erros))
    for nome, val in (("cruft.json", validar_cruft), ("restricoes-api.json", validar_restricoes)):
        d, erros = validar_arquivo_regras(real / "references" / nome, val)
        if d is None and not erros:
            continue
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
                         ("lint", lambda: _st_lint(st, sk)), ("memória", lambda: _st_memoria(st)),
                         ("rede", lambda: _st_rede(st)),
                         ("robustez", lambda: _st_robustez(st, sk, fetch_dir))):
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
    try:
        _st_dados_reais(st, real)
    except Exception as e:  # dado real malformado não pode esconder o {ok, testes}
        st.t("dados: exceção", False, f"{e.__class__.__name__}: {e}")
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
    p.add_argument("--timeout", type=float, default=15.0,
                   help="prazo total por página em segundos, > 0 (padrão 15)")
    p.add_argument("--so", help="só estes ids, separados por vírgula")

    p = add("fontes-aplicar", "grava em fontes.json o sha do cache atual depois que as references foram atualizadas",
            cmd_fontes_aplicar)
    g = p.add_mutually_exclusive_group()
    g.add_argument("--ids", help="ids a aplicar, separados por vírgula")
    g.add_argument("--todas-mudadas", action="store_true", help="aplica todas cujo cache difere do sha registrado")
    p.add_argument("--adicionar", action="append", metavar="ID=URL", help="cria entrada nova (repetível)")
    p.add_argument("--timeout", type=float, default=15.0,
                   help="prazo em segundos (> 0) para buscar página nova sem cache (padrão 15)")

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
    p.add_argument("--editado", help="arquivo editado pelo usuário ('-' = stdin); lido só para a razão de "
                                     "similaridade (SequenceMatcher com autojunk=False; acima de 20 000 "
                                     "caracteres, por tokens) e não é guardado")
    p.add_argument("--entregue", help="arquivo entregue por Claude ('-' = stdin, mas não os dois); lido só para a "
                                      "razão e não é guardado")
    p.add_argument("--decisoes-editadas", help="decisões do episódio que o usuário desfez (recebem 0), por vírgula; "
                                               "id fora do episódio é recusado")
    p.add_argument("--rubrica", type=float, help="nota de rubrica 0 a 1 (sobrepõe a do episódio)")
    p.add_argument("--fechar", action="store_true", help="tira o episódio de pendentes")

    p = add("politica", "média Beta por decisão e ação sugerida (fixa/promover/manter/rebaixar)", cmd_politica)
    p.add_argument("--modelo", required=True, help=f"modelo cuja política consultar; um de: {', '.join(MODELOS_CONHECIDOS)}")
    p.add_argument("--tarefa", help="tipo de tarefa; usada se n>=3, senão cai no agregado")
    p.add_argument("--candidatas", help="decisões a avaliar, por vírgula (padrão: todas do placar)")
    p.add_argument("--recomendadas", help="decisões recomendadas pelo guia (prior Beta(2,1)), por vírgula")

    p = add("candidatos", "decisões com evidência para virar linha do MEMORY.md (decisões api./hard. nunca saem "
                          "como 'evitar'; ficam em omitidos_fixos)", cmd_candidatos)
    p.add_argument("--min-n", type=int, default=3, help="mínimo de episódios na chave (padrão 3)")
    p.add_argument("--alto", type=float, default=0.75,
                   help="média R >= este valor (0 a 1) sugere 'reforçar' (padrão 0.75)")
    p.add_argument("--baixo", type=float, default=0.25,
                   help="média R <= este valor (0 a 1) sugere 'evitar' (padrão 0.25)")
    p.add_argument("--marcar-promovido", metavar="CHAVE", help="chave modelo|tarefa|decisao já promovida")

    p = add("pendentes", "episódios pendentes recentes (mais novo primeiro)", cmd_pendentes)
    p.add_argument("--dias", type=int, default=14, help="só episódios criados nos últimos N dias, N >= 0 (padrão 14)")

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
        payload, code = {"erro": f"{e.__class__.__name__}: {e}"}, EXIT_BUG
    imprimir_json(payload)
    return code


def imprimir_json(payload) -> None:
    """JSON no stdout mesmo quando o texto não cabe na codificação dele.

    Surrogate solto vindo da entrada, ou stdout cp1252 (Windows redirecionado) com
    R̄ ou →, levantavam UnicodeEncodeError fora do try: traceback cru e exit 1.
    Cair para ensure_ascii dá JSON equivalente só com escapes \\uXXXX.
    """
    try:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    except UnicodeEncodeError:
        print(json.dumps(payload, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    sys.exit(main())

"""
Script de inicialização de dev: roda backend (FastAPI) e frontend (Next.js) em paralelo.

Uso:
    python scripts/dev.py              # inicia ambos
    python scripts/dev.py --backend    # só backend
    python scripts/dev.py --frontend   # só frontend
    python scripts/dev.py --install    # instala deps antes de iniciar
    python scripts/dev.py --port 9000  # custom port (default: 8000)
    python scripts/dev.py --clean      # mata processos órfãos nas portas
    python scripts/dev.py --help       # help

Comportamento:
    - Detecta Windows / Unix automaticamente
    - Ativa venv do backend se existir (./backend/.venv)
    - Roda uvicorn no backend
    - Roda next dev no frontend
    - Encerramento limpo com Ctrl+C (mata ambos os processos)
    - Detecta portas ocupadas e mata processos órfãos (--clean)
    - Cores ANSI em terminais que suportam
"""

from __future__ import annotations

import argparse
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

# Força UTF-8 no stdout/stderr (Windows PowerShell usa cp125 por padrão)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"

# Cores ANSI
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"


def color(text: str, c: str) -> str:
    if sys.stdout.isatty() and os.environ.get("NO_COLOR") is None:
        return f"{c}{text}{RESET}"
    return text


def find_venv_python(backend_dir: Path) -> str | None:
    """Retorna path do Python no venv do backend, se existir."""
    if sys.platform == "win32":
        candidate = backend_dir / ".venv" / "Scripts" / "python.exe"
    else:
        candidate = backend_dir / ".venv" / "bin" / "python"
    if candidate.exists():
        return str(candidate)
    return None


def find_node() -> str | None:
    return "node" if _which("node") else None


def _which(cmd: str) -> bool:
    from shutil import which

    return which(cmd) is not None


def _resolve_cmd(name: str) -> str:
    """Resolve o executável correto no Windows (.cmd, .bat, .exe)."""
    from shutil import which

    if sys.platform != "win32":
        return name
    found = which(name)
    if found:
        return found
    for ext in (".cmd", ".bat", ".exe", ".ps1"):
        candidate = name + ext
        if which(candidate):
            return candidate
    return name  # deixa o Popen falhar com erro claro


def _is_port_in_use(port: int) -> bool:
    """Retorna True se a porta estiver bindada.

    No Windows, sockets em TIME_WAIT/zombie podem aparecer como "in use" mesmo
    sem processo associado. Nestes casos, tentamos limpar via SO_REUSEADDR hack
    ou reportamos como ocupada para o usuário decidir.
    """
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0


def _port_owner_pid(port: int) -> int | None:
    """Retorna o PID que está bindando a porta, ou None se não há owner real."""
    if sys.platform != "win32":
        return None
    try:
        r = subprocess.run(
            ["netstat", "-ano"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        for line in r.stdout.splitlines():
            if f":{port} " not in line and not line.endswith(f":{port}"):
                continue
            if "LISTENING" not in line:
                continue
            parts = line.split()
            if len(parts) < 5:
                continue
            try:
                pid = int(parts[-1])
            except ValueError:
                continue
            if pid == 0:
                return None
            # Verifica se o PID existe
            p = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if str(pid) in p.stdout:
                return pid
    except Exception:
        pass
    return None


def _port_has_zombie(port: int) -> bool:
    """Retorna True se a porta está bindada mas sem owner real (Windows TIME_WAIT/zombie)."""
    return _is_port_in_use(port) and _port_owner_pid(port) is None


def _kill_port(port: int) -> list[int]:
    """Mata processos que estão usando a porta. Retorna PIDs mortos."""
    killed: list[int] = []
    if sys.platform == "win32":
        # taskkill é mais permissivo que Stop-Process
        try:
            result = subprocess.run(
                ["netstat", "-ano"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            for line in result.stdout.splitlines():
                if f":{port} " not in line and not line.endswith(f":{port}"):
                    continue
                if "LISTENING" not in line and "ESTABLISHED" not in line:
                    continue
                parts = line.split()
                if len(parts) < 5:
                    continue
                try:
                    pid = int(parts[-1])
                except ValueError:
                    continue
                if pid == 0 or pid in killed:
                    continue
                # taskkill /F = force, /T = mata child processes
                r = subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(pid)],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if r.returncode == 0:
                    killed.append(pid)
        except Exception as e:
            print(color(f"⚠ Erro ao matar porta {port}: {e}", YELLOW))
    else:
        # Unix: fuser/lsof
        for cmd in (["fuser", "-k", f"{port}/tcp"], ["lsof", "-ti", f":{port}"]):
            try:
                r = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                for line in r.stdout.strip().splitlines():
                    line = line.strip()
                    if line.isdigit():
                        os.kill(int(line), signal.SIGTERM)
                        killed.append(int(line))
                if killed:
                    break
            except FileNotFoundError:
                continue
            except Exception as e:
                print(color(f"⚠ Erro ao matar porta {port}: {e}", YELLOW))
    return killed


def clean_ports(ports: list[int]) -> None:
    """Tenta liberar as portas matando processos órfãos."""
    any_killed = False
    for port in ports:
        if _is_port_in_use(port):
            print(color(f"→ Limpando porta {port}...", YELLOW))
            killed = _kill_port(port)
            if killed:
                print(color(f"  ✓ PIDs mortos: {killed}", GREEN))
                any_killed = True
            else:
                print(
                    color(
                        f"  ✗ Não foi possível liberar porta {port}. Feche o processo manualmente.",
                        RED,
                    )
                )
            time.sleep(0.5)
    if not any_killed:
        print(color("✓ Nenhum processo órfão encontrado", GREEN))


def install_deps(only: str | None = None, force: bool = False) -> None:
    """Instala deps do backend (pip) e/ou frontend (npm).

    Se `force=False`, pula se já estiver instalado (checa com `pip show` / `node_modules`).
    """
    if only != "frontend":
        print(color("→ Verificando deps do backend...", BLUE))
        py = find_venv_python(BACKEND) or sys.executable
        try:
            result = subprocess.run(
                [py, "-m", "pip", "show", "regionalizador-backend"],
                cwd=BACKEND,
                capture_output=True,
                text=True,
            )
            already_installed = result.returncode == 0
        except Exception:
            already_installed = False

        if already_installed and not force:
            print(color("✓ Backend já instalado (use --install-backend para forçar)", GREEN))
        else:
            print(color("→ Instalando deps do backend (pip)...", BLUE))
            env = os.environ.copy()
            env["PYTHONUNBUFFERED"] = "1"
            result = subprocess.run(
                [py, "-m", "pip", "install", "-e", ".[dev]"],
                cwd=BACKEND,
                env=env,
            )
            if result.returncode != 0:
                print(color("✗ pip install falhou", RED))
                sys.exit(1)
            print(color("✓ Backend OK", GREEN))

    if only != "backend":
        print(color("→ Verificando deps do frontend...", BLUE))
        if not _which("npm"):
            print(color("✗ npm não encontrado no PATH", RED))
            sys.exit(1)
        node_modules = FRONTEND / "node_modules"
        if node_modules.exists() and not force:
            print(color("✓ Frontend já instalado (use --install-frontend para forçar)", GREEN))
        else:
            print(color("→ Instalando deps do frontend (npm)...", BLUE))
            env = os.environ.copy()
            env["FORCE_COLOR"] = "1"
            env["NPM_CONFIG_UPDATE_NOTIFIER"] = "false"
            npm_cmd = _resolve_cmd("npm")
            result = subprocess.run(
                [npm_cmd, "install", "--legacy-peer-deps", "--no-audit", "--no-fund"],
                cwd=FRONTEND,
                env=env,
            )
            if result.returncode != 0:
                print(color("✗ npm install falhou", RED))
                sys.exit(1)
            print(color("✓ Frontend OK", GREEN))


def start_backend(port: int) -> subprocess.Popen:
    py = find_venv_python(BACKEND) or sys.executable
    if py is None:
        print(color("⚠ venv do backend não encontrado, usando python do sistema", YELLOW))
        py = sys.executable

    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"

    print(color(f"→ Backend: http://localhost:{port}", CYAN))
    return subprocess.Popen(
        # Sem --reload para evitar ECONNRESET durante watchfiles
        # Reinicie manualmente: Ctrl+C no script + python scripts/dev.py
        [py, "-m", "uvicorn", "app.main:app", "--port", str(port)],
        cwd=BACKEND,
        env=env,
        # Permite que Ctrl+C no script mate o uvicorn (Windows)
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0,
    )


def start_frontend(port: int = 3000) -> subprocess.Popen:
    if not _which("npm"):
        print(color("✗ npm não encontrado no PATH", RED))
        sys.exit(1)
    env = os.environ.copy()
    env["NEXT_PUBLIC_API_URL"] = f"http://localhost:8000"
    env["BROWSER"] = "none"
    env["FORCE_COLOR"] = "1"
    npm_cmd = _resolve_cmd("npm")

    print(color(f"→ Frontend: http://localhost:{port}", MAGENTA))
    # No Windows, .cmd não pode ser executado sem shell=True
    use_shell = sys.platform == "win32"
    return subprocess.Popen(
        [npm_cmd, "run", "dev", "--", "-p", str(port)] if not use_shell
        else f'"{npm_cmd}" run dev -- -p {port}',
        cwd=FRONTEND,
        env=env,
        shell=use_shell,
    )


def wait_health(url: str, timeout: int = 30) -> bool:
    """Espera a URL retornar 2xx."""
    import urllib.request

    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as r:
                if 200 <= r.status < 500:
                    return True
        except Exception:
            pass
        time.sleep(1.0)
    return False


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Inicia backend + frontend para dev local.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--backend", action="store_true", help="Roda só o backend"
    )
    parser.add_argument(
        "--frontend", action="store_true", help="Roda só o frontend"
    )
    parser.add_argument(
        "--install", action="store_true", help="Instala deps antes de iniciar"
    )
    parser.add_argument(
        "--install-backend", action="store_true", help="Instala só deps do backend (força)"
    )
    parser.add_argument(
        "--install-frontend", action="store_true", help="Instala só deps do frontend (força)"
    )
    parser.add_argument(
        "--port", type=int, default=8000, help="Porta do backend (default: 8000)"
    )
    parser.add_argument(
        "--frontend-port", type=int, default=3000, help="Porta do frontend (default: 3000)"
    )
    parser.add_argument(
        "--no-wait", action="store_true", help="Não espera healthcheck"
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Mata processos órfãos nas portas antes de iniciar",
    )
    args = parser.parse_args()

    only_backend = args.backend
    only_frontend = args.frontend
    if only_backend and only_frontend:
        print(color("✗ --backend e --frontend são mutuamente exclusivos", RED))
        sys.exit(1)

    run_backend = not only_frontend
    run_frontend = not only_backend

    # Detectar portas ocupadas e (opcionalmente) matar processos órfãos
    ports_to_check = []
    if run_backend:
        ports_to_check.append(args.port)
    if run_frontend:
        ports_to_check.append(args.frontend_port)

    busy = [p for p in ports_to_check if _is_port_in_use(p)]
    # Separar portas com owner real vs zombie (kernel TIME_WAIT no Windows)
    has_real_owner = [p for p in busy if _port_owner_pid(p) is not None]
    has_zombie = [p for p in busy if _port_owner_pid(p) is None]

    if has_real_owner:
        if args.clean:
            print(
                color(
                    f"→ Matando processos órfãos em {has_real_owner}...",
                    YELLOW,
                )
            )
            clean_ports(has_real_owner)
            still = [p for p in has_real_owner if _is_port_in_use(p)]
            if still:
                print(
                    color(
                        f"✗ Ainda ocupada(s) após cleanup: {still}",
                        RED,
                    )
                )
                sys.exit(1)
        else:
            print(
                color(
                    f"⚠ Porta(s) em uso: {has_real_owner} (com processo ativo).",
                    YELLOW,
                )
            )
            print(
                color(
                    "  Use --clean para matar processos órfãos automaticamente,",
                    YELLOW,
                )
            )
            print(
                color(
                    "  ou feche o processo manualmente (ex: Ctrl+C na sessão anterior).",
                    YELLOW,
                )
            )
            sys.exit(1)

    if has_zombie:
        # Sockets em TIME_WAIT sem processo (Windows bug). Esperar liberar.
        print(
            color(
                f"⚠ Porta(s) {has_zombie} bindadas por socket órfão (TIME_WAIT).",
                YELLOW,
            )
        )
        print(color("  Isso acontece quando o Windows não libera o socket imediatamente após Ctrl+C.", YELLOW))
        print(color("  Aguardando até 60s para o sistema liberar...", YELLOW))
        for _ in range(60):
            time.sleep(1)
            still_zombie = [p for p in has_zombie if _port_owner_pid(p) is None and _is_port_in_use(p)]
            if not still_zombie:
                print(color("✓ Portas liberadas", GREEN))
                break
        else:
            print(
                color(
                    "✗ TIME_WAIT não liberou em 60s. Reiniciando pode ajudar.",
                    RED,
                )
            )
            print(
                color(
                    "  Soluções manuais (escolha uma):",
                    YELLOW,
                )
            )
            print(
                color(
                    "    1) Reiniciar o serviço Winsock (PowerShell como Admin):",
                    YELLOW,
                )
            )
            print(
                color(
                    "       netsh winsock reset",
                    YELLOW,
                )
            )
            print(
                color(
                    "    2) Aguardar ~4 minutos (default TIME_WAIT no Windows)",
                    YELLOW,
                )
            )
            print(
                color(
                    "    3) Usar uma porta diferente: python scripts/dev.py --port 8001",
                    YELLOW,
                )
            )
            sys.exit(1)

    if args.install:
        if only_backend:
            install_deps(only="backend")
        elif only_frontend:
            install_deps(only="frontend")
        else:
            install_deps()
    if args.install_backend:
        install_deps(only="backend")
    if args.install_frontend:
        install_deps(only="frontend")

    print(color("=" * 60, BOLD))
    print(color("  Regionalizador — dev mode", BOLD))
    print(color("=" * 60, BOLD))
    print(f"  Backend:  http://localhost:{args.port}" + (" (skipped)" if not run_backend else ""))
    print(f"  Frontend: http://localhost:{args.frontend_port}" + (" (skipped)" if not run_frontend else ""))
    print(color("  Ctrl+C para encerrar", DIM))
    print()

    procs: list[tuple[str, subprocess.Popen]] = []
    if run_backend:
        procs.append(("backend", start_backend(args.port)))
    if run_frontend:
        procs.append(("frontend", start_frontend(args.frontend_port)))

    if not args.no_wait:
        if run_backend:
            print(color("→ Aguardando backend inicializar...", DIM))
            if wait_health(f"http://localhost:{args.port}/health", timeout=30):
                print(color("✓ Backend pronto", GREEN))
            else:
                print(color("⚠ Backend não respondeu em 30s (continua rodando)", YELLOW))
        if run_frontend:
            print(color("→ Aguardando frontend inicializar...", DIM))
            if wait_health(f"http://localhost:{args.frontend_port}", timeout=60):
                print(color("✓ Frontend pronto", GREEN))
            else:
                print(color("⚠ Frontend não respondeu em 60s (continua rodando)", YELLOW))

    print()
    print(color("Logs (Ctrl+C para sair):", DIM))
    print(color("-" * 60, DIM))

    try:
        while True:
            for name, proc in procs:
                ret = proc.poll()
                if ret is not None:
                    print(
                        color(f"✗ {name} saiu com código {ret}", RED),
                        file=sys.stderr,
                    )
                    for _, other in procs:
                        if other.poll() is None:
                            other.terminate()
                    sys.exit(1)
            time.sleep(0.5)
    except KeyboardInterrupt:
        print()
        print(color("Encerrando processos...", YELLOW))
        for name, proc in procs:
            if proc.poll() is None:
                if sys.platform == "win32":
                    proc.terminate()
                else:
                    proc.send_signal(signal.SIGTERM)
        for _, proc in procs:
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
        print(color("✓ Encerrado", GREEN))


if __name__ == "__main__":
    main()

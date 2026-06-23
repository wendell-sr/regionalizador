"""
Script de inicialização de dev: roda backend (FastAPI) e frontend (Next.js) em paralelo.

Uso:
    python scripts/dev.py              # inicia ambos
    python scripts/dev.py --backend    # só backend
    python scripts/dev.py --frontend   # só frontend
    python scripts/dev.py --install    # instala deps antes de iniciar
    python scripts/dev.py --port 9000  # custom port (default: 8000)
    python scripts/dev.py --help       # help

Comportamento:
    - Detecta Windows / Unix automaticamente
    - Ativa venv do backend se existir (./backend/.venv)
    - Roda uvicorn com reload no backend
    - Roda next dev no frontend
    - Encerramento limpo com Ctrl+C (mata ambos os processos)
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
    py = find_venv_python(BACKEND)
    if py is None:
        print(color("⚠ venv do backend não encontrado, usando python do sistema", YELLOW))
        py = sys.executable

    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"

    print(color(f"→ Backend: http://localhost:{port}", CYAN))
    return subprocess.Popen(
        [py, "-m", "uvicorn", "app.main:app", "--reload", "--port", str(port)],
        cwd=BACKEND,
        env=env,
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
            with urllib.request.urlopen(url, timeout=1) as r:
                if 200 <= r.status < 500:
                    return True
        except Exception:
            pass
        time.sleep(0.5)
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
    args = parser.parse_args()

    only_backend = args.backend
    only_frontend = args.frontend
    if only_backend and only_frontend:
        print(color("✗ --backend e --frontend são mutuamente exclusivos", RED))
        sys.exit(1)

    run_backend = not only_frontend
    run_frontend = not only_backend

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

"""
Spec validation script.
Valida a estrutura de uma spec: arquivos obrigatórios, ACs, status de tasks.
Uso: python .specify/scripts/validate_spec.py specs/001-regionalizador-mvp
"""

import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


REQUIRED_FILES = ["spec.md", "plan.md", "tasks.md"]


def fail(msg: str) -> None:
    print(f"  ✗ {msg}")


def ok(msg: str) -> None:
    print(f"  ✓ {msg}")


def validate_spec(spec_dir: Path) -> int:
    print(f"Validating {spec_dir}...")
    errors = 0

    for f in REQUIRED_FILES:
        path = spec_dir / f
        if not path.exists():
            fail(f"Missing required file: {f}")
            errors += 1
        else:
            ok(f"Found {f}")

    spec_path = spec_dir / "spec.md"
    if spec_path.exists():
        text = spec_path.read_text(encoding="utf-8")
        ac_count = len(re.findall(r"^### AC\d+", text, re.MULTILINE))
        if ac_count == 0:
            fail("spec.md: no acceptance criteria found (### AC1, ### AC2, ...)")
            errors += 1
        else:
            ok(f"spec.md: {ac_count} acceptance criteria")
        if "## Fora de Escopo" not in text and "## Fora de Escopo (MVP)" not in text:
            fail("spec.md: missing 'Fora de Escopo' section")
            errors += 1
        else:
            ok("spec.md: has 'Fora de Escopo' section")

    tasks_path = spec_dir / "tasks.md"
    if tasks_path.exists():
        text = tasks_path.read_text(encoding="utf-8")
        total = len(re.findall(r"^- \[[ x]\]", text, re.MULTILINE))
        done = len(re.findall(r"^- \[x\]", text, re.MULTILINE))
        print(f"  ℹ tasks.md: {done}/{total} tasks complete")
        if total == 0:
            fail("tasks.md: no tasks defined")
            errors += 1

    contracts = spec_dir / "contracts"
    if contracts.exists():
        for f in contracts.iterdir():
            ok(f"contract: {f.name}")
    else:
        print("  ℹ contracts/ not present (optional for non-API specs)")

    return errors


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python validate_spec.py <spec-dir>")
        return 1
    spec_dir = Path(sys.argv[1])
    if not spec_dir.is_dir():
        print(f"Not a directory: {spec_dir}")
        return 1
    errors = validate_spec(spec_dir)
    if errors == 0:
        print("\n✓ Spec is valid")
        return 0
    print(f"\n✗ {errors} error(s)")
    return 1


if __name__ == "__main__":
    sys.exit(main())

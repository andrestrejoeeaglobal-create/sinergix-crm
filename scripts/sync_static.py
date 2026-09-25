#!/usr/bin/env python3
"""scripts/sync_static.py — Sincronización Canónica y Verificación Fail-Fast SHA-256.

Gobernanza de Fuente Única (SSOT):
  La raíz del repositorio (index.html, sw.js) es la única fuente de verdad.
  Este script replica los archivos hacia /static/ y valida la paridad estricta
  mediante hashes SHA-256. Si se detecta cualquier discrepancia en modo --check,
  el proceso falla inmediatamente con código de salida 1 (Fail-Fast).

Uso:
  python scripts/sync_static.py          # Sincroniza raíz -> /static/ y valida paridad
  python scripts/sync_static.py --check  # Modo auditoría/CI: falla si hay desincronización
"""

import sys
import hashlib
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"

CANONICAL_FILES = [
    "index.html",
    "sw.js",
]


def calcular_sha256(filepath: Path) -> str:
    """Calcula el hash SHA-256 de un archivo en bloques."""
    if not filepath.exists():
        return ""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def sincronizar_archivos() -> bool:
    """Copia los archivos canónicos de la raíz a /static/ y verifica paridad."""
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    todo_correcto = True

    print(f"[*] Sincronizando Fuente Única (SSOT) -> {STATIC_DIR}")
    for fname in CANONICAL_FILES:
        src = BASE_DIR / fname
        dst = STATIC_DIR / fname

        if not src.exists():
            print(f"[-] ERROR: Archivo canónico faltante en raíz: {src}")
            return False

        # Copiar contenido binario exacto
        content = src.read_bytes()
        dst.write_bytes(content)

        hash_src = calcular_sha256(src)
        hash_dst = calcular_sha256(dst)

        if hash_src != hash_dst:
            print(f"[-] ERROR DE PARIDAD en {fname}: {hash_src} != {hash_dst}")
            todo_correcto = False
        else:
            print(f"[+] Sincronizado OK: {fname} (SHA-256: {hash_src[:12]}...)")

    return todo_correcto


def verificar_paridad() -> bool:
    """Modo auditoría: Comprueba que /static/ sea idéntico a la raíz."""
    print(f"[*] Auditando paridad SHA-256 entre raíz y {STATIC_DIR}")
    discrepancias = 0

    for fname in CANONICAL_FILES:
        src = BASE_DIR / fname
        dst = STATIC_DIR / fname

        if not src.exists():
            print(f"[-] Archivo origen no existe: {src}")
            discrepancias += 1
            continue

        if not dst.exists():
            print(f"[-] Archivo destino no existe: {dst}")
            discrepancias += 1
            continue

        hash_src = calcular_sha256(src)
        hash_dst = calcular_sha256(dst)

        if hash_src != hash_dst:
            print(f"[-] DESINCRONIZACIÓN DETECTADA en {fname}:")
            print(f"    Raíz:     {hash_src}")
            print(f"    /static/: {hash_dst}")
            discrepancias += 1
        else:
            print(f"[+] Paridad verificada: {fname} (SHA-256: {hash_src[:12]}...)")

    if discrepancias > 0:
        print(f"\n[!] FALLO FAIL-FAST: {discrepancias} archivo(s) desincronizado(s).")
        return False

    print("\n[+] ÉXITO: Paridad 100% verificada entre raíz y /static/.")
    return True


def main():
    if "--check" in sys.argv:
        if not verificar_paridad():
            sys.exit(1)
    else:
        if not sincronizar_archivos():
            sys.exit(1)
        if not verificar_paridad():
            sys.exit(1)


if __name__ == "__main__":
    main()

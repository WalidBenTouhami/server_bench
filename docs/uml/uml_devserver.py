#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
uml_devserver.py
----------------
Dev server EXTREME DEVOPS pour les UML :

- Sert les fichiers UML (viewer.html, *.svg, *.puml) via HTTP (port 9999)
- WebSocket (port 8765) pour notifier le navigateur des changements
- Watcher sur les fichiers .puml : lance generate_uml.py à chaque modification
- Auto-reload des SVG dans viewer.html (sans recharger toute la page)

Usage :
  cd server_project/docs/uml
  python3 uml_devserver.py

Dépendances Python recommandées :
  pip install websockets watchdog

Si watchdog n'est pas dispo, un fallback en mode polling est prévu.
"""

import asyncio
import threading
import time
import subprocess
from pathlib import Path
from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer

try:
    import watchdog.events
    import watchdog.observers
    HAVE_WATCHDOG = True
except ImportError:
    HAVE_WATCHDOG = False

import websockets

ROOT = Path(__file__).resolve().parent
DOCS_ROOT = ROOT  # docs/uml
PROJECT_ROOT = ROOT.parents[1]  # server_project/

HTTP_PORT = 9999
WS_PORT = 8765

# Liste des clients WebSocket connectés
CONNECTED_CLIENTS = set()


def run_generate_uml():
    """
    Lance generate_uml.py depuis docs/uml.
    """
    script = ROOT / "generate_uml.py"
    if not script.exists():
        print(f"[WARN] generate_uml.py introuvable : {script}")
        return
    print("[DEVSERVER] Regénération UML via generate_uml.py ...")
    try:
        subprocess.run(
            ["python3", str(script)],
            cwd=str(ROOT),
            check=True
        )
        print("[DEVSERVER] UML générés avec succès.")
    except subprocess.CalledProcessError as e:
        print(f"[DEVSERVER][ERROR] generate_uml.py a échoué : {e}")


async def broadcast_reload(changed=None):
    """
    Envoie un message de reload à tous les clients WS.
    Payload simple : "reload" ou "reload:<filename.svg>"
    """
    if not CONNECTED_CLIENTS:
        return
    msg = "reload"
    if changed:
        msg = f"reload:{changed}"
    print(f"[DEVSERVER] Broadcast : {msg} à {len(CONNECTED_CLIENTS)} client(s)")
    await asyncio.gather(
        *[client.send(msg) for client in list(CONNECTED_CLIENTS)],
        return_exceptions=True
    )


async def ws_handler(websocket, path):
    """
    Gestion des connexions WebSocket.
    """
    print(f"[WS] Client connecté depuis {websocket.remote_address}")
    CONNECTED_CLIENTS.add(websocket)
    try:
        # Petit message de bienvenue
        await websocket.send("hello:uml_devserver")
        # Boucle de réception (même si on n'attend rien pour l'instant)
        async for _ in websocket:
            pass
    except Exception as e:
        print(f"[WS] Exception : {e}")
    finally:
        CONNECTED_CLIENTS.discard(websocket)
        print("[WS] Client déconnecté")


def start_http_server():
    """
    Démarre un serveur HTTP simple sur HTTP_PORT,
    avec comme racine docs/uml.
    """
    class UMLHandler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(DOCS_ROOT), **kwargs)

        def log_message(self, fmt, *args):
            print("[HTTP]", fmt % args)

    with TCPServer(("0.0.0.0", HTTP_PORT), UMLHandler) as httpd:
        print(f"[HTTP] Server UML en écoute sur http://0.0.0.0:{HTTP_PORT}/viewer.html")
        httpd.serve_forever()


class PumlEventHandler(watchdog.events.FileSystemEventHandler):
    """
    Handler watchdog : surveille les .puml et déclenche la régénération.
    """
    def __init__(self, loop):
        super().__init__()
        self.loop = loop

    def on_modified(self, event):
        if event.is_directory:
            return
        path = Path(event.src_path)
        if path.suffix.lower() == ".puml":
            print(f"[WATCHDOG] Modification détectée : {path.name}")
            # Regénère et notifie en tâche asynchrone dans l'event loop
            def task():
                run_generate_uml()
                asyncio.run_coroutine_threadsafe(broadcast_reload(), self.loop)

            threading.Thread(target=task, daemon=True).start()


def start_watchdog(loop):
    """
    Démarre watchdog sur le dossier docs/uml (ROOT).
    """
    event_handler = PumlEventHandler(loop)
    observer = watchdog.observers.Observer()
    observer.schedule(event_handler, str(ROOT), recursive=False)
    observer.start()
    print(f"[WATCHDOG] Surveillance des .puml dans {ROOT}")
    return observer


def start_polling(loop, interval=2.0):
    """
    Fallback si watchdog n'est pas installé :
    poll sur les mtimes des fichiers .puml.
    """
    print(f"[POLL] Watchdog absent, fallback polling chaque {interval}s")

    def poll_loop():
        known_mtimes = {}
        while True:
            time.sleep(interval)
            changed = False
            for puml in ROOT.glob("*.puml"):
                mtime = puml.stat().st_mtime
                if puml not in known_mtimes:
                    known_mtimes[puml] = mtime
                    continue
                if mtime != known_mtimes[puml]:
                    print(f"[POLL] Changement détecté : {puml.name}")
                    known_mtimes[puml] = mtime
                    changed = True
            if changed:
                run_generate_uml()
                asyncio.run_coroutine_threadsafe(broadcast_reload(), loop)

    t = threading.Thread(target=poll_loop, daemon=True)
    t.start()


async def main_async():
    """
    Event loop principal : lance le server HTTP, le WS et le watcher.
    """
    # 1) HTTP server dans un thread séparé
    http_thread = threading.Thread(target=start_http_server, daemon=True)
    http_thread.start()

    # 2) WebSocket server
    ws_server = await websockets.serve(ws_handler, "0.0.0.0", WS_PORT)
    print(f"[WS] WebSocket en écoute sur ws://0.0.0.0:{WS_PORT}")

    # 3) Watcher .puml (watchdog ou polling)
    loop = asyncio.get_running_loop()
    if HAVE_WATCHDOG:
        observer = start_watchdog(loop)
    else:
        start_polling(loop)

    # Exécution infinie
    try:
        await asyncio.Future()
    finally:
        ws_server.close()
        await ws_server.wait_closed()
        if HAVE_WATCHDOG:
            observer.stop()
            observer.join()


def main():
    print("=== UML DEVSERVER EXTREME DEVOPS ===")
    print(f"Racine UML : {ROOT}")
    print(f"HTTP      : http://localhost:{HTTP_PORT}/viewer.html")
    print(f"WebSocket : ws://localhost:{WS_PORT}")
    print("Ctrl+C pour arrêter.\n")

    # Première génération à froid
    run_generate_uml()

    asyncio.run(main_async())


if __name__ == "__main__":
    main()


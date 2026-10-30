"""
Read-only Ollama memory check: resident models (/api/ps) and the summed working set of the
ollama.exe / ollama process tree (server + model runners).

Why: Ollama 0.40 starts its llama-server runner without --cache-ram, so llama.cpp's default
host prompt cache (up to 8 GiB) applies and runner memory grows with every distinct prompt
(revalidation RQ5-M: llama3.2:3b ~2.5 GB after load, ~8.8 GB after 500 prompts).
This command only reports; it never unloads a model, because unloading resets the prompt cache
and can change later outputs.

Usage: python manage.py ollama_status [--warn-mb 6000]
"""
import requests
from django.conf import settings
from django.core.management.base import BaseCommand


def ollama_tree_working_set_mb():
    """Summed RSS (Windows: working set) of every ollama process and its children, or None without psutil."""
    try:
        import psutil
    except ImportError:
        return None
    total, seen = 0, set()
    for p in psutil.process_iter(["name"]):
        name = (p.info["name"] or "").lower()
        if name not in ("ollama.exe", "ollama"):
            continue
        try:
            for q in [p] + p.children(recursive=True):
                if q.pid not in seen:
                    seen.add(q.pid)
                    total += q.memory_info().rss
        except psutil.Error:
            pass
    return total / 2**20


class Command(BaseCommand):
    help = "Report Ollama resident models and process-tree memory (read-only)."

    def add_arguments(self, parser):
        parser.add_argument("--warn-mb", type=float, default=6000.0,
                            help="Print a warning when the Ollama tree working set exceeds this (MB).")

    def handle(self, *args, **options):
        url = getattr(settings, "OLLAMA_BASE_URL", "http://localhost:11434")
        try:
            models = requests.get(f"{url}/api/ps", timeout=5).json().get("models", [])
        except requests.RequestException as e:
            self.stderr.write(f"Ollama not reachable at {url}: {e}")
            models = []
        for m in models:
            self.stdout.write(f"model {m.get('name')}: size {m.get('size', 0) / 2**20:,.0f} MB, "
                              f"vram {m.get('size_vram', 0) / 2**20:,.0f} MB, expires {m.get('expires_at')}")
        if not models:
            self.stdout.write("no model resident")
        mb = ollama_tree_working_set_mb()
        if mb is None:
            self.stdout.write("psutil not installed: process memory not measured")
            return
        self.stdout.write(f"ollama process tree working set: {mb:,.0f} MB")
        if mb > options["warn_mb"]:
            self.stdout.write(self.style.WARNING(
                f"above {options['warn_mb']:,.0f} MB: the runner's prompt cache has grown; "
                "restarting Ollama (or letting keep_alive expire) frees it"))

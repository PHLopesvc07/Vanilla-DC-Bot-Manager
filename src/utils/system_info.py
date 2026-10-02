import pygetwindow as gw
import win32process

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


def get_active_windows_with_process() -> list:
    """Retorna uma lista formatada de janelas visíveis com o nome do aplicativo/processo associado."""
    window_list = []
    seen = set()
    
    for w in gw.getAllWindows():
        title = w.title.strip()
        if title and w.visible:
            try:
                hwnd = w._hWnd
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                if HAS_PSUTIL:
                    proc_name = psutil.Process(pid).name()
                    entry = f"{title[:45]} ({proc_name})"
                else:
                    entry = title[:50]
                if entry not in seen:
                    seen.add(entry)
                    window_list.append(entry)
            except Exception:
                if title not in seen:
                    seen.add(title)
                    window_list.append(title)
                    
    return sorted(window_list) if window_list else ["Nenhuma janela ativa encontrada"]

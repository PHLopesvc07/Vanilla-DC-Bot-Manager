import os
import shutil
import subprocess
import re

def find_ffmpeg() -> str:
    """Busca o executável do FFmpeg no PATH ou em locais comuns do Windows."""
    if shutil.which("ffmpeg"):
        return "ffmpeg"
    
    common_paths = [
        r"C:\Program Files\Virtual Desktop Streamer\ffmpeg.exe",
        r"C:\Program Files\Krita (x64)\bin\ffmpeg.exe",
        r"C:\Program Files\Altered Studio\resources\ffmpeg.exe",
        r"C:\ffmpeg\bin\ffmpeg.exe",
        r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
        os.path.join(os.getenv("LOCALAPPDATA", ""), "Programs", "ffmpeg", "bin", "ffmpeg.exe"),
        os.path.join(os.getenv("PROGRAMFILES", ""), "ffmpeg", "bin", "ffmpeg.exe"),
    ]
    for path in common_paths:
        if os.path.exists(path):
            return path
    return "ffmpeg"


def get_dshow_audio_devices(ffmpeg_bin: str = "ffmpeg") -> list:
    """Mapeia os nomes de dispositivos de áudio DirectShow suportados pelo FFmpeg."""
    devices = []
    if not ffmpeg_bin:
        ffmpeg_bin = "ffmpeg"
    
    bin_path = ffmpeg_bin if os.path.isabs(ffmpeg_bin) else shutil.which(ffmpeg_bin)
    if not bin_path and os.path.exists(ffmpeg_bin):
        bin_path = ffmpeg_bin

    if bin_path:
        try:
            cmd = [bin_path, "-list_devices", "true", "-f", "dshow", "-i", "dummy"]
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                errors="ignore",
                startupinfo=startupinfo
            )
            matches = re.findall(r'"([^"]+)"\s*\(audio\)', res.stderr)
            for m in matches:
                if m not in devices:
                    devices.append(m)
        except Exception as e:
            print(f"Aviso ao consultar dispositivos via FFmpeg DirectShow: {e}")
            
    return devices

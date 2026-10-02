import queue
import discord
import sounddevice as sd

class SoundDeviceAudioSource(discord.AudioSource):
    """
    Fonte de áudio nativa do Discord.py utilizando sounddevice (PortAudio).
    Lê amostras de áudio em tempo real de qualquer dispositivo selecionado
    e as fornece em pacotes PCM 16-bit 48kHz stereo (20ms / 3840 bytes) para a voz do Discord.
    """
    def __init__(self, device_name=None, samplerate=48000, channels=2):
        self.q = queue.Queue(maxsize=150)
        self.samplerate = samplerate
        self.channels = channels
        
        device_idx = None
        if device_name:
            devices = sd.query_devices()
            for idx, dev in enumerate(devices):
                if dev['max_input_channels'] > 0:
                    clean_dev = dev['name'].split(", ")[0].strip().lower()
                    if device_name.lower() in clean_dev or clean_dev in device_name.lower():
                        device_idx = idx
                        break
                        
        def audio_callback(indata, frames, time, status):
            data = bytes(indata)
            try:
                self.q.put_nowait(data)
            except queue.Full:
                pass

        self.stream = sd.RawInputStream(
            device=device_idx,
            samplerate=self.samplerate,
            blocksize=960,
            channels=self.channels,
            dtype='int16',
            callback=audio_callback
        )
        self.stream.start()

    def read(self):
        try:
            return self.q.get_nowait()
        except queue.Empty:
            return b'\x00' * 3840

    def cleanup(self):
        if hasattr(self, 'stream') and self.stream:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception as e:
                print(f"Erro ao fechar stream de áudio nativa: {e}")

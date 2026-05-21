from __future__ import annotations

import base64
import io
import wave
from array import array


class VoiceEngine:
    """Offline-friendly voice output with simple wav synthesis fallback."""

    def _beep_wave(self, text: str, sample_rate: int = 22050) -> bytes:
        duration = max(0.8, min(5.0, 0.04 * len(text)))
        frames = int(sample_rate * duration)
        freq = 440
        amp = 12000
        samples = array("h")
        for i in range(frames):
            phase = (i * freq * 2 * 3.141592653589793) / sample_rate
            val = int(amp * (0.5 if (phase % (2 * 3.141592653589793)) < 3.141592653589793 else -0.5))
            samples.append(val)

        buff = io.BytesIO()
        with wave.open(buff, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(samples.tobytes())
        return buff.getvalue()

    def synthesize(self, text: str) -> dict:
        wav = self._beep_wave(text)
        b64 = base64.b64encode(wav).decode("ascii")
        return {"audio_base64": b64, "format": "wav", "voice": "aether-fallback"}

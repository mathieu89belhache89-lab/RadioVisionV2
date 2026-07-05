import tempfile
import wave

from faster_whisper import WhisperModel


class Whisper:

    def __init__(self):

        self.model = WhisperModel(
            "base",
            device="cpu",
            compute_type="int8",
        )

    def transcribe_bytes(self, pcm_bytes):

        with tempfile.NamedTemporaryFile(
            suffix=".wav",
            delete=False,
        ) as f:

            with wave.open(f.name, "wb") as wav:

                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(16000)
                wav.writeframes(pcm_bytes)

            segments, _ = self.model.transcribe(
                f.name,
                language="fr",
                beam_size=1,
                vad_filter=True,
            )

        text = " ".join(
            segment.text.strip()
            for segment in segments
        )

        return text.strip()
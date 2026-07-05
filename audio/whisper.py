import tempfile
import wave

from faster_whisper import WhisperModel


class Whisper:

    def __init__(self):

        print("Chargement Whisper...")

        self.model = WhisperModel(
            "base",
            device="cpu",
            compute_type="int8",
        )

        print("Whisper prêt.")

    def transcribe_bytes(self, pcm):

        with tempfile.NamedTemporaryFile(
            suffix=".wav",
            delete=False,
        ) as tmp:

            with wave.open(tmp.name, "wb") as wav:

                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(16000)
                wav.writeframes(pcm)

            segments, _ = self.model.transcribe(
                tmp.name,
                language="fr",
                beam_size=1,
                vad_filter=False,
            )

        return " ".join(
            s.text.strip()
            for s in segments
        )
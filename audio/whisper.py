from faster_whisper import WhisperModel


class Whisper:

    def __init__(self):

        self.model = WhisperModel(
            "base",
            device="cpu",
            compute_type="int8"
        )

    def transcribe(self, audio_file):

        segments, _ = self.model.transcribe(
            audio_file,
            language="fr",
            beam_size=5
        )

        text = ""

        for segment in segments:
            text += segment.text.strip() + " "

        return text.strip()
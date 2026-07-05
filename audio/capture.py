import soundcard as sc
import soundfile as sf


class AudioCapture:

    def __init__(self):
        self.speaker = sc.default_speaker()
        self.microphone = sc.get_microphone(
            self.speaker.name,
            include_loopback=True
        )

    def record(self, filename="temp/capture.wav", seconds=3):

        samplerate = 48000

        with self.microphone.recorder(samplerate=samplerate) as recorder:
            data = recorder.record(
                numframes=samplerate * seconds
            )

        sf.write(filename, data, samplerate)

        return filename
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(relative):
    path = ROOT / relative
    if not path.exists():
        raise AssertionError(f"Fichier introuvable : {relative}")
    return path.read_text(encoding="utf-8")


def must_contain(name, source, expected):
    if expected not in source:
        raise AssertionError(f"{name} ne contient pas : {expected}")


def main():
    checks = []

    capture = read("audio/capture.py")
    audio_worker = read("workers/audio_worker.py")
    whisper_worker = read("workers/whisper_worker.py")
    whisper = read("audio/whisper.py")

    tests = [
        ("capture bloc 0.20", capture, "self.block_seconds = 0.20"),
        ("capture queue 160", capture, "queue.Queue(maxsize=160)"),
        ("audio silence plus long", audio_worker, "self.silence_limit = 6"),
        ("audio segment long", audio_worker, "self.max_blocks = 90"),
        ("audio pre-roll", audio_worker, "self.pre_roll_blocks = 5"),
        ("audio démarrage confirmé", audio_worker, "self.speech_start_blocks = 2"),
        ("audio seuil dynamique", audio_worker, "dynamic_start_threshold"),
        ("whisper queue plus grande", whisper_worker, "queue.Queue(maxsize=8)"),
        ("whisper tampon texte", whisper_worker, "self.pending_text"),
        ("whisper merge code OD", whisper_worker, "code od"),
        ("whisper beam 5", whisper, "beam_size=5"),
        ("whisper prompt Mission Row", whisper, "Mission Row"),
        ("whisper prompt BMW M4", whisper, "BMW M4"),
    ]

    for label, source, expected in tests:
        must_contain(label, source, expected)
        checks.append(label)
        print(f"OK - {label}")

    print("=" * 70)
    print(f"Résultat : {len(checks)}/{len(tests)} tests OK")
    print("V8.5 audio fiabilité prêt.")


if __name__ == "__main__":
    main()

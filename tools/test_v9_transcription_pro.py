from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

TESTS = [
    ("audio/whisper.py", "large-v3-turbo", "modèle large-v3-turbo"),
    ("audio/whisper.py", "cuda", "support CUDA"),
    ("audio/whisper.py", "float16", "support float16"),
    ("audio/whisper.py", "beam_size=self.beam_size", "beam dynamique"),
    ("audio/whisper.py", "engine_label", "label moteur"),
    ("workers/audio_worker.py", "max_blocks = 90", "segments longs"),
    ("workers/audio_worker.py", "silence_limit = 6", "silence plus tolérant"),
    ("workers/whisper_worker.py", "pending_text", "tampon texte"),
    ("workers/whisper_worker.py", "merge_forced_audio_continuation", "fusion coupure forcée"),
    ("core/app.py", "whisper_device", "paramètre device"),
    ("core/app.py", "whisper_compute_type", "paramètre calcul"),
    ("ui/main_window.py", "Large V3 Turbo", "option UI large turbo"),
    ("ui/main_window.py", "setting_whisper_device", "option UI GPU"),
]


def main():
    ok = 0
    errors = []

    for relative_path, needle, label in TESTS:
        path = ROOT / relative_path

        if not path.exists():
            errors.append(f"MANQUANT - {relative_path} ({label})")
            continue

        text = path.read_text(encoding="utf-8", errors="ignore")

        if needle not in text:
            errors.append(f"ERREUR - {relative_path} : {label}")
            continue

        ok += 1
        print(f"OK - {label}")

    print("=" * 70)
    print(f"Résultat : {ok}/{len(TESTS)} tests OK")

    if errors:
        for error in errors:
            print(error)
        raise SystemExit("V9 Transcription Pro incomplet.")

    print("V9 Transcription Pro prêt.")


if __name__ == "__main__":
    main()

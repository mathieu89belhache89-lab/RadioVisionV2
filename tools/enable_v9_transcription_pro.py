import json
from pathlib import Path

SETTINGS_FILE = Path("data") / "radiovision_settings.json"


def main():
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)

    if SETTINGS_FILE.exists():
        try:
            data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                data = {}
        except Exception:
            data = {}
    else:
        data = {}

    data.update({
        "whisper_model": "large-v3-turbo",
        "whisper_device": "auto",
        "whisper_compute_type": "auto",
        "whisper_beam_size": 5,
        "pending_delay": 10,
        "merge_window": 18,
    })

    SETTINGS_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=4),
        encoding="utf-8",
    )

    print("V9 Transcription Pro activée.")
    print("Modèle : large-v3-turbo")
    print("Accélération : auto GPU CUDA puis CPU secours")
    print("Précision : beam 5")
    print("Redémarre RadioVision pour appliquer le moteur.")


if __name__ == "__main__":
    main()

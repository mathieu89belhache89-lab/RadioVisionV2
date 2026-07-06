from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


def main():
    print("Vérification GPU V9.1")

    try:
        from audio.whisper import add_nvidia_dll_dirs, NVIDIA_DLL_DIRS
        added = add_nvidia_dll_dirs()
        folders = sorted(set(NVIDIA_DLL_DIRS + added))

        if folders:
            print("Dossiers DLL NVIDIA ajoutés :")
            for folder in folders:
                print(f"- {folder}")
        else:
            print("Aucun dossier DLL NVIDIA trouvé dans le venv / CUDA_PATH.")
    except Exception as exc:
        print("Impossible d'ajouter automatiquement les dossiers DLL NVIDIA.")
        print(exc)

    try:
        import ctranslate2
    except Exception as exc:
        print("ERREUR : ctranslate2 introuvable ou cassé.")
        print(exc)
        return

    count = None

    try:
        if hasattr(ctranslate2, "get_cuda_device_count"):
            count = ctranslate2.get_cuda_device_count()
    except Exception as exc:
        print("CUDA non disponible pour ctranslate2.")
        print(exc)
        count = 0

    if count is None:
        print("Impossible de lire le nombre de GPU CUDA avec cette version de ctranslate2.")
        print("Le vrai test se fera au lancement de RadioVision.")
        return

    if count > 0:
        print(f"OK : GPU CUDA détecté ({count}).")
        print("Si RadioVision bascule quand même en CPU, il manque encore une DLL cuBLAS/cuDNN.")
    else:
        print("GPU CUDA non détecté par ctranslate2.")
        print("RadioVision utilisera le secours CPU si CUDA échoue.")


if __name__ == "__main__":
    main()

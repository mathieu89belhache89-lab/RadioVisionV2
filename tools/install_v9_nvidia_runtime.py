import subprocess
import sys

PACKAGES = [
    "nvidia-cublas-cu12",
    "nvidia-cudnn-cu12",
    "nvidia-cuda-runtime-cu12",
]


def main():
    print("Installation runtime NVIDIA CUDA 12 dans le venv...")
    cmd = [sys.executable, "-m", "pip", "install", "--upgrade"] + PACKAGES
    print("Commande :", " ".join(cmd))
    result = subprocess.run(cmd)

    if result.returncode == 0:
        print("OK : paquets NVIDIA installés / mis à jour.")
        print("Ferme et relance RadioVision, puis teste tools\\check_v9_gpu.py")
    else:
        print("ERREUR : pip n'a pas réussi à installer les paquets NVIDIA.")
        sys.exit(result.returncode)


if __name__ == "__main__":
    main()

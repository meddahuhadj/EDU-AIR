"""EDU-AIR — Windows desktop build (PyInstaller), build/work dirs on D: to spare C:."""
import os
import subprocess
import shutil
import sys


def main():
    root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(root)

    build_base = r"D:\edu_air_build"
    temp_dir = r"D:\edu_air_temp"
    os.makedirs(temp_dir, exist_ok=True)
    os.environ["TEMP"] = temp_dir
    os.environ["TMP"] = temp_dir
    os.environ["TMPDIR"] = temp_dir

    dist_dir = os.path.join(build_base, "dist")
    work_dir = os.path.join(build_base, "build")
    for d in [dist_dir, work_dir]:
        if os.path.exists(d):
            shutil.rmtree(d, ignore_errors=True)
    os.makedirs(dist_dir, exist_ok=True)
    os.makedirs(work_dir, exist_ok=True)

    main_script = os.path.join(root, "edu_air_main.py")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onedir",
        "--windowed",
        "--name=EDU-AIR",
        f"--distpath={dist_dir}",
        f"--workpath={work_dir}",
        f"--specpath={build_base}",
        "--collect-submodules=PySide6.QtCore",
        "--collect-submodules=PySide6.QtGui",
        "--collect-submodules=PySide6.QtWidgets",
        "--collect-all=mediapipe",
        "--collect-all=cv2",
        "--collect-all=edu_air",
        "--collect-all=hadj_no_touch",
        "--exclude-module=torch",
        "--exclude-module=torchvision",
        "--exclude-module=jax",
        "--exclude-module=jaxlib",
        "--exclude-module=scipy",
        "--exclude-module=pandas",
        "--exclude-module=matplotlib",
        "--exclude-module=pyarrow",
        "--exclude-module=sqlalchemy",
        "--exclude-module=h5py",
        "--exclude-module=pytest",
        "--exclude-module=PySide6.Qt3DAnimation",
        "--exclude-module=PySide6.Qt3DCore",
        "--exclude-module=PySide6.Qt3DExtras",
        "--exclude-module=PySide6.Qt3DInput",
        "--exclude-module=PySide6.Qt3DLogic",
        "--exclude-module=PySide6.Qt3DRender",
        "--exclude-module=PySide6.QtBluetooth",
        "--exclude-module=PySide6.QtQml",
        "--exclude-module=PySide6.QtQuick",
        "--exclude-module=PySide6.QtWebEngine",
        "--exclude-module=PySide6.QtWebEngineWidgets",
        main_script,
    ]

    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(f"\n[ERROR] PyInstaller exit code {result.returncode}.", flush=True)
        sys.exit(result.returncode)

    app_dir = os.path.join(dist_dir, "EDU-AIR")
    exe = os.path.join(app_dir, "EDU-AIR.exe")
    if not os.path.exists(exe):
        print(f"[ERROR] {exe} introuvable.", flush=True)
        sys.exit(1)

    zip_path = os.path.join(dist_dir, "EDU-AIR-Windows.zip")
    print("[packing zip]", zip_path, flush=True)
    shutil.make_archive(os.path.join(dist_dir, "EDU-AIR-Windows"), "zip", app_dir)
    size_mb = os.path.getsize(zip_path) / (1024**2)
    print(f"[OK] ZIP: {zip_path} ({size_mb:.1f} MB)", flush=True)


if __name__ == "__main__":
    main()
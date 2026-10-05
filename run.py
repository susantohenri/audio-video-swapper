"""Orkestrator: 1 foto + 1 suara + 1 video -> video face swap + voice clone.
Dijalankan oleh Python milik env facefusion (lihat run.bat). Hanya pakai stdlib."""
import argparse, glob, os, shutil, subprocess, sys

ROOT   = os.path.dirname(os.path.abspath(__file__))
FF_ENV = os.path.join(ROOT, "envs", "facefusion")
SV_ENV = os.path.join(ROOT, "envs", "seedvc")
FF_DIR = os.path.join(ROOT, "apps", "facefusion")
SV_DIR = os.path.join(ROOT, "apps", "seed-vc")
WORK   = os.path.join(ROOT, "work")
FFMPEG = os.path.join(FF_ENV, "Library", "bin", "ffmpeg.exe")

ENV = os.environ.copy()
ENV["PATH"] = os.pathsep.join([os.path.join(FF_ENV, "Library", "bin"), FF_ENV, ENV["PATH"]])
ENV["PYTHONIOENCODING"] = "utf-8"


def run(cmd, cwd=None):
    print("\n>", " ".join(f'"{c}"' if " " in c else c for c in cmd), flush=True)
    r = subprocess.run(cmd, cwd=cwd, env=ENV)
    if r.returncode != 0:
        sys.exit(f"Gagal (kode {r.returncode}): {cmd[0]}")


def seedvc(source, target, outdir, steps, fp16=True):
    py = os.path.join(SV_ENV, "python.exe")
    run([py, "inference.py", "--source", source, "--target", target, "--output", outdir,
         "--diffusion-steps", str(steps), "--fp16", str(fp16)], cwd=SV_DIR)


def prefetch():
    """Unduh model Seed-VC dengan menjalankan 2 detik audio dummy."""
    os.makedirs(WORK, exist_ok=True)
    dummy = os.path.join(WORK, "dummy.wav")
    run([FFMPEG, "-y", "-f", "lavfi", "-i", "sine=frequency=220:duration=2", "-ar", "22050", dummy])
    seedvc(dummy, dummy, os.path.join(WORK, "prefetch"), 4)
    print("Model Seed-VC siap.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--photo"); ap.add_argument("--voice"); ap.add_argument("--video")
    ap.add_argument("--output", default="hasil.mp4")
    ap.add_argument("--steps", type=int, default=25, help="diffusion steps Seed-VC")
    ap.add_argument("--max-height", type=int, default=720, help="video diperkecil ke tinggi ini (hemat VRAM 4GB); 0 = jangan")
    ap.add_argument("--swapper", default="inswapper_128_fp16")
    ap.add_argument("--keep-work", action="store_true")
    ap.add_argument("--prefetch", action="store_true")
    a = ap.parse_args()

    if a.prefetch:
        return prefetch()
    if not (a.photo and a.voice and a.video):
        ap.error("--photo, --voice, dan --video wajib")
    for p in (a.photo, a.voice, a.video):
        if not os.path.isfile(p):
            sys.exit(f"File tidak ditemukan: {p}")
    for p in (FFMPEG, os.path.join(SV_ENV, "python.exe")):
        if not os.path.isfile(p):
            sys.exit("Belum terinstall. Jalankan install.ps1 dulu.")

    shutil.rmtree(WORK, ignore_errors=True)
    os.makedirs(WORK)
    src_wav = os.path.join(WORK, "speech.wav")   # ucapan dari video
    ref_wav = os.path.join(WORK, "ref.wav")      # suara yang ditiru (maks 25 dtk)
    small   = os.path.join(WORK, "video_small.mp4")
    swapped = os.path.join(WORK, "swapped.mp4")
    vc_dir  = os.path.join(WORK, "vc")
    out = os.path.abspath(a.output)

    print("\n[1/5] Siapkan audio & video")
    run([FFMPEG, "-y", "-i", a.video, "-vn", "-ac", "1", "-ar", "22050", src_wav])
    run([FFMPEG, "-y", "-i", a.voice, "-t", "25", "-ac", "1", "-ar", "22050", ref_wav])
    vf = f"scale=-2:'min({a.max_height},ih)'" if a.max_height else "null"
    run([FFMPEG, "-y", "-i", a.video, "-vf", vf, "-c:v", "libx264", "-crf", "16", "-an", small])

    print("\n[2/5] Voice clone (Seed-VC)")
    seedvc(src_wav, ref_wav, vc_dir, a.steps)
    files = glob.glob(os.path.join(vc_dir, "*.wav"))
    if not files:
        sys.exit("Seed-VC tidak menghasilkan audio.")
    cloned = files[0]

    print("\n[3/5] Face swap (FaceFusion)")
    run([os.path.join(FF_ENV, "python.exe"), "facefusion.py", "headless-run",
         "-s", os.path.abspath(a.photo), "-t", small, "-o", swapped,
         "--processors", "face_swapper", "--face-swapper-model", a.swapper,
         "--execution-providers", "cuda", "--execution-thread-count", "2",
         "--video-memory-strategy", "strict", "--output-video-quality", "85"], cwd=FF_DIR)

    print("\n[4/5] Gabung video + suara hasil clone")
    run([FFMPEG, "-y", "-i", swapped, "-i", cloned, "-map", "0:v:0", "-map", "1:a:0",
         "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", out])

    print("\n[5/5] Selesai ->", out)
    if not a.keep_work:
        shutil.rmtree(WORK, ignore_errors=True)


if __name__ == "__main__":
    main()

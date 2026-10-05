# voice-face-swap

1 foto + 1 suara + 1 video -> video dengan wajah diganti dan suara di-clone.
Memakai FaceFusion 3.9.1 (face swap) dan Seed-VC (voice conversion). Hanya untuk wajah/suara yang sudah diizinkan pemiliknya.

Target: Windows + GPU NVIDIA (dirancang untuk RTX 3050 4GB).

## Pasang (sekali)
Syarat sistem: Windows, driver NVIDIA, **git**. Itu saja (Python, conda, ffmpeg, CUDA diunduh otomatis ke folder ini).

    git clone <url-repo-ini>
    cd voice-face-swap
    powershell -ExecutionPolicy Bypass -File .\install.ps1

Butuh beberapa GB download dan beberapa menit.

## Pakai
    run.bat --photo face.png --voice suara.wav --video video.mp4 --output hasil.mp4

- `--voice`: suara yang ditiru (dipotong otomatis 25 detik)
- Ucapan di hasil = ucapan dari audio video asli, dengan suara dari `--voice`
- Opsi: `--steps 25`, `--max-height 720` (0 = resolusi asli), `--swapper inswapper_128_fp16`, `--keep-work`
- Tes dulu dengan klip 10-20 detik. Proses berjalan berurutan (voice dulu, lalu face swap) agar muat di 4GB VRAM.

## Hapus bersih
Hapus folder repo ini. Tidak ada yang terpasang di luar folder (tidak menyentuh PATH/registry/conda lama).

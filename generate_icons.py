"""
Generates Neo-Brutalist OSINT tactical badge icons for PWA Builder.
Outputs: icon-192.png, icon-512.png, maskable-512.png
"""
from pathlib import Path
from PIL import Image, ImageDraw

# Target directory: web-app/public (or fallback to current folder)
OUTPUT_DIR = Path("public") if Path("public").exists() else Path(".")

# Canvas setup - Render at 2048x2048 for vector-grade crispness
BASE_SIZE = 2048
CENTER = BASE_SIZE // 2

# Neo-Brutalist Palette
COLOR_BG = (255, 230, 0)      # #FFE600 Acid Yellow
COLOR_BLACK = (10, 10, 10)     # #0A0A0A Deep Pitch Black
COLOR_WHITE = (255, 255, 255)  # Clean Monospace White
COLOR_RED = (255, 60, 60)      # High-contrast Target Red

def create_badge() -> Image.Image:
    # 1. Base Canvas
    img = Image.new("RGBA", (BASE_SIZE, BASE_SIZE), COLOR_BG)
    draw = ImageDraw.Draw(img)

    # 2. Brutalist Drop-Shadow & Main Badge Frame
    # Keeping inside the 80% circle safe zone for PWA maskable compliance
    box_inset = 220
    shadow_offset = 50

    # Black offset shadow
    draw.rectangle(
        [box_inset + shadow_offset, box_inset + shadow_offset,
         BASE_SIZE - box_inset + shadow_offset, BASE_SIZE - box_inset + shadow_offset],
        fill=COLOR_BLACK
    )

    # Main badge body (White background with thick black border)
    draw.rectangle(
        [box_inset, box_inset, BASE_SIZE - box_inset, BASE_SIZE - box_inset],
        fill=COLOR_WHITE,
        outline=COLOR_BLACK,
        width=36
    )

    # 3. Tactical Viewfinder Brackets (Corners)
    b_len = 120
    b_thick = 28
    corners = [
        # Top-left
        ((box_inset + 60, box_inset + 60), (box_inset + 60 + b_len, box_inset + 60)),
        ((box_inset + 60, box_inset + 60), (box_inset + 60, box_inset + 60 + b_len)),
        # Top-right
        ((BASE_SIZE - box_inset - 60, box_inset + 60), (BASE_SIZE - box_inset - 60 - b_len, box_inset + 60)),
        ((BASE_SIZE - box_inset - 60, box_inset + 60), (BASE_SIZE - box_inset - 60, box_inset + 60 + b_len)),
        # Bottom-left
        ((box_inset + 60, BASE_SIZE - box_inset - 60), (box_inset + 60 + b_len, BASE_SIZE - box_inset - 60)),
        ((box_inset + 60, BASE_SIZE - box_inset - 60), (box_inset + 60, BASE_SIZE - box_inset - 60 - b_len)),
        # Bottom-right
        ((BASE_SIZE - box_inset - 60, BASE_SIZE - box_inset - 60), (BASE_SIZE - box_inset - 60 - b_len, BASE_SIZE - box_inset - 60)),
        ((BASE_SIZE - box_inset - 60, BASE_SIZE - box_inset - 60), (BASE_SIZE - box_inset - 60, BASE_SIZE - box_inset - 60 - b_len)),
    ]
    for start, end in corners:
        draw.line([start, end], fill=COLOR_BLACK, width=b_thick)

    # 4. Center Recon Reticle / Surveillance Eye
    # Outer dashed radar ring
    r_outer = 480
    draw.ellipse(
        [CENTER - r_outer, CENTER - r_outer, CENTER + r_outer, CENTER + r_outer],
        outline=COLOR_BLACK,
        width=30
    )

    # Tactical Crosshair lines
    gap = 260
    length = 560
    crosshair_w = 26
    # Left, Right, Top, Bottom spikes
    draw.line([(CENTER - length, CENTER), (CENTER - gap, CENTER)], fill=COLOR_BLACK, width=crosshair_w)
    draw.line([(CENTER + gap, CENTER), (CENTER + length, CENTER)], fill=COLOR_BLACK, width=crosshair_w)
    draw.line([(CENTER, CENTER - length), (CENTER, CENTER - gap)], fill=COLOR_BLACK, width=crosshair_w)
    draw.line([(CENTER, CENTER + gap), (CENTER, CENTER + length)], fill=COLOR_BLACK, width=crosshair_w)

    # Tactical Eye Silhouette
    eye_w, eye_h = 360, 220
    # Top lid
    draw.arc(
        [CENTER - eye_w, CENTER - eye_h - 100, CENTER + eye_w, CENTER + eye_h + 100],
        start=30, end=150, fill=COLOR_BLACK, width=32
    )
    # Bottom lid
    draw.arc(
        [CENTER - eye_w, CENTER - eye_h - 100, CENTER + eye_w, CENTER + eye_h + 100],
        start=210, end=330, fill=COLOR_BLACK, width=32
    )

    # Center Iris (Tactical Red Bullseye)
    r_iris = 150
    draw.ellipse(
        [CENTER - r_iris, CENTER - r_iris, CENTER + r_iris, CENTER + r_iris],
        fill=COLOR_RED,
        outline=COLOR_BLACK,
        width=24
    )

    # Center Pupil & Core Lens Glint
    r_pupil = 65
    draw.ellipse(
        [CENTER - r_pupil, CENTER - r_pupil, CENTER + r_pupil, CENTER + r_pupil],
        fill=COLOR_BLACK
    )
    r_glint = 20
    draw.ellipse(
        [CENTER - 25, CENTER - 25, CENTER - 25 + r_glint * 2, CENTER - 25 + r_glint * 2],
        fill=COLOR_WHITE
    )

    return img

def main():
    print("[*] Generating master 2048x2048 Brutalist OSINT badge...")
    master = create_badge()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    sizes = {
        "icon-192.png": 192,
        "icon-512.png": 512,
        "maskable-512.png": 512,
    }

    for filename, sz in sizes.items():
        out_path = OUTPUT_DIR / filename
        # High quality Lanczos downsampling
        resized = master.resize((sz, sz), Image.Resampling.LANCZOS)
        resized.save(out_path, "PNG", optimize=True)
        print(f" -> Created {out_path} ({sz}x{sz})")

    print("\n[+] Done! Icons created successfully.")

if __name__ == "__main__":
    main()
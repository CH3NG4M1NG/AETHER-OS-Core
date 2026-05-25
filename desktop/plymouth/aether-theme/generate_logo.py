#!/usr/bin/env python3
"""
Generate AETHER boot logo for Plymouth theme.
Creates a neon AETHER logo PNG.
"""
import os
import math

def generate_logo():
    try:
        from PIL import Image, ImageDraw, ImageFont, ImageFilter
        generate_with_pil()
    except ImportError:
        generate_with_svg()

def generate_with_pil():
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
    import math

    W, H = 600, 200
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Hexagon
    cx, cy = 80, 100
    r = 55
    hex_pts = []
    for i in range(6):
        angle = math.pi / 6 + i * math.pi / 3
        hex_pts.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))

    # Glow effect - draw multiple times with decreasing opacity
    for glow_r in [r + 15, r + 10, r + 5]:
        glow_pts = []
        for i in range(6):
            angle = math.pi / 6 + i * math.pi / 3
            glow_pts.append((cx + glow_r * math.cos(angle),
                              cy + glow_r * math.sin(angle)))
        draw.polygon(glow_pts, outline=(168, 85, 247, 30))

    # Main hexagon
    draw.polygon(hex_pts, outline=(168, 85, 247, 200), fill=(168, 85, 247, 15))

    # Inner hexagon
    r2 = r * 0.7
    hex_pts2 = []
    for i in range(6):
        angle = math.pi / 6 + i * math.pi / 3
        hex_pts2.append((cx + r2 * math.cos(angle), cy + r2 * math.sin(angle)))
    draw.polygon(hex_pts2, outline=(168, 85, 247, 120))

    # Center dot
    draw.ellipse([cx-4, cy-4, cx+4, cy+4], fill=(192, 132, 252, 255))

    # Lines from center to vertices
    for pt in hex_pts2:
        draw.line([cx, cy, pt[0], pt[1]], fill=(168, 85, 247, 80), width=1)

    # AETHER text
    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-Bold.ttf", 52)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-Regular.ttf", 14)
    except Exception:
        try:
            font_large = ImageFont.truetype("/usr/share/fonts/truetype/ubuntu/Ubuntu-B.ttf", 52)
            font_small = ImageFont.truetype("/usr/share/fonts/truetype/ubuntu/Ubuntu-R.ttf", 14)
        except Exception:
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()

    text = "AETHER"
    tx = 155
    ty = 55

    # Text glow
    for offset in [(2,2),(−2,2),(2,−2),(−2,−2),(3,0),(−3,0),(0,3),(0,−3)]:
        draw.text((tx+offset[0], ty+offset[1]), text,
                  fill=(168, 85, 247, 40), font=font_large)

    # Main text - gradient effect (cyan to purple)
    draw.text((tx, ty), text, fill=(192, 132, 252, 255), font=font_large)

    # Subtitle
    sub = "AGI FOUNDATION OS"
    draw.text((tx, ty + 72), sub, fill=(100, 50, 150, 200), font=font_small)

    # Version
    draw.text((tx, ty + 95), "v1.0.0", fill=(80, 40, 120, 160), font=font_small)

    # Apply blur for glow
    img_blur = img.filter(ImageFilter.GaussianBlur(radius=2))
    final = Image.alpha_composite(img_blur, img)

    out = "/usr/share/plymouth/themes/aether/aether-logo.png"
    os.makedirs(os.path.dirname(out), exist_ok=True)
    final.save(out)
    print(f"Logo saved: {out}")

def generate_with_svg():
    """Fallback: generate SVG logo."""
    svg = '''<svg xmlns="http://www.w3.org/2000/svg" width="600" height="200">
  <defs>
    <radialGradient id="glow">
      <stop offset="0%" stop-color="#a855f7" stop-opacity="0.3"/>
      <stop offset="100%" stop-color="#a855f7" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <rect width="600" height="200" fill="none"/>
  <g transform="translate(80,100)">
    <polygon points="0,-55 47.6,-27.5 47.6,27.5 0,55 -47.6,27.5 -47.6,-27.5"
             fill="rgba(168,85,247,0.1)" stroke="#a855f7" stroke-width="1.5"/>
    <polygon points="0,-38.5 33.3,-19.25 33.3,19.25 0,38.5 -33.3,19.25 -33.3,-19.25"
             fill="none" stroke="rgba(168,85,247,0.6)" stroke-width="1"/>
    <circle r="4" fill="#c084fc"/>
    <g stroke="rgba(168,85,247,0.4)" stroke-width="0.8">
      <line x1="0" y1="0" x2="0" y2="-38.5"/>
      <line x1="0" y1="0" x2="33.3" y2="-19.25"/>
      <line x1="0" y1="0" x2="33.3" y2="19.25"/>
      <line x1="0" y1="0" x2="0" y2="38.5"/>
      <line x1="0" y1="0" x2="-33.3" y2="19.25"/>
      <line x1="0" y1="0" x2="-33.3" y2="-19.25"/>
    </g>
  </g>
  <text x="155" y="115" font-family="monospace" font-size="52"
        font-weight="bold" fill="#c084fc" letter-spacing="6">AETHER</text>
  <text x="158" y="140" font-family="monospace" font-size="13"
        fill="rgba(168,85,247,0.7)" letter-spacing="4">AGI FOUNDATION OS</text>
</svg>'''

    svg_path = "/tmp/aether-logo.svg"
    with open(svg_path, 'w') as f:
        f.write(svg)

    out_dir = "/usr/share/plymouth/themes/aether"
    os.makedirs(out_dir, exist_ok=True)

    # Convert SVG to PNG
    for cmd in [
        f"rsvg-convert -w 600 -h 200 {svg_path} -o {out_dir}/aether-logo.png",
        f"inkscape --export-type=png -w 600 -h 200 {svg_path} -o {out_dir}/aether-logo.png",
        f"convert {svg_path} -resize 600x200 {out_dir}/aether-logo.png",
    ]:
        if os.system(cmd + " 2>/dev/null") == 0:
            print(f"Logo generated: {out_dir}/aether-logo.png")
            return

    print("Logo generation failed - Plymouth will use text fallback")


if __name__ == "__main__":
    generate_logo()

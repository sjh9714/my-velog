#!/usr/bin/env python3
"""Generate Velog thumbnail images from local Markdown posts."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = ROOT / "assets" / "thumbnails"
SIZE = (1080, 565)
FONT_CANDIDATES = [
    "/System/Library/Fonts/AppleSDGothicNeo.ttc",
    "/System/Library/Fonts/Supplemental/AppleGothic.ttf",
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
]


@dataclass(frozen=True)
class Palette:
    background_top: str
    background_bottom: str
    panel: str
    text: str
    muted: str
    accent: str
    accent_2: str
    chip_fill: str
    chip_text: str


@dataclass(frozen=True)
class SeriesConfig:
    key: str
    name: str
    tagline: str
    source: Path
    output_dir: Path
    palette: Palette
    chips: tuple[str, ...]
    motif: str


SERIES: tuple[SeriesConfig, ...] = (
    SeriesConfig(
        key="realtime-chat",
        name="실시간 채팅 백엔드",
        tagline="Boundaries of realtime messaging",
        source=ROOT / "posts" / "velog" / "realtime-chat",
        output_dir=OUTPUT_ROOT / "posts" / "realtime-chat",
        palette=Palette(
            background_top="#07111f",
            background_bottom="#0f2b38",
            panel="#102336",
            text="#ecfeff",
            muted="#a5f3fc",
            accent="#2dd4bf",
            accent_2="#38bdf8",
            chip_fill="#143b4a",
            chip_text="#cffafe",
        ),
        chips=("Spring Boot", "WebSocket", "Kafka"),
        motif="network",
    ),
    SeriesConfig(
        key="concert-booking",
        name="콘서트 예매 시스템",
        tagline="Concurrency, queues, and reliable booking",
        source=ROOT / "posts" / "velog" / "concert-booking",
        output_dir=OUTPUT_ROOT / "posts" / "concert-booking",
        palette=Palette(
            background_top="#111827",
            background_bottom="#2b1720",
            panel="#231d25",
            text="#fff7ed",
            muted="#fed7aa",
            accent="#f59e0b",
            accent_2="#ef4444",
            chip_fill="#3b2630",
            chip_text="#ffedd5",
        ),
        chips=("Spring Boot", "Concurrency", "Kafka"),
        motif="seats",
    ),
    SeriesConfig(
        key="open-source",
        name="오픈소스 기여",
        tagline="Small diffs, tests, and maintainable PRs",
        source=ROOT / "posts" / "velog" / "open-source",
        output_dir=OUTPUT_ROOT / "posts" / "open-source",
        palette=Palette(
            background_top="#f8fafc",
            background_bottom="#dcfce7",
            panel="#ffffff",
            text="#0f172a",
            muted="#334155",
            accent="#16a34a",
            accent_2="#2563eb",
            chip_fill="#dcfce7",
            chip_text="#14532d",
        ),
        chips=("Open Source", "Regression Test", "PR"),
        motif="diff",
    ),
    SeriesConfig(
        key="programmers-python",
        name="프로그래머스 Python 코딩테스트",
        tagline="Daily algorithm notes in Python",
        source=ROOT / "programmers-python" / "posts" / "velog",
        output_dir=OUTPUT_ROOT / "posts" / "programmers-python",
        palette=Palette(
            background_top="#0f172a",
            background_bottom="#172554",
            panel="#111c38",
            text="#eff6ff",
            muted="#bfdbfe",
            accent="#facc15",
            accent_2="#60a5fa",
            chip_fill="#1e3a8a",
            chip_text="#dbeafe",
        ),
        chips=("Programmers", "Python", "Algorithm"),
        motif="code",
    ),
)


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))


def mix(a: tuple[int, int, int], b: tuple[int, int, int], ratio: float) -> tuple[int, int, int]:
    return tuple(int(x + (y - x) * ratio) for x, y in zip(a, b))


def with_alpha(value: str, alpha: int) -> tuple[int, int, int, int]:
    return (*hex_to_rgb(value), alpha)


def font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for candidate in FONT_CANDIDATES:
        if Path(candidate).exists():
            try:
                return ImageFont.truetype(candidate, size=size)
            except OSError:
                continue
    return ImageFont.load_default()


def text_size(draw: ImageDraw.ImageDraw, text: str, selected_font: ImageFont.ImageFont) -> tuple[int, int]:
    box = draw.textbbox((0, 0), text, font=selected_font)
    return box[2] - box[0], box[3] - box[1]


def wrap_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    selected_font: ImageFont.ImageFont,
    max_width: int,
    max_lines: int,
) -> list[str]:
    tokens = re.findall(r"\[[^\]]+\]|[A-Za-z0-9_.:/+-]+|[가-힣]+|[^\s]", text)
    lines: list[str] = []
    current = ""

    for token in tokens:
        needs_space = bool(current) and re.match(r"[A-Za-z0-9_.:/+-]+|\[[^\]]+\]|[가-힣]+", token)
        candidate = f"{current}{' ' if needs_space else ''}{token}" if current else token
        if text_size(draw, candidate, selected_font)[0] <= max_width:
            current = candidate
            continue
        if current:
            lines.append(current)
            current = token
        else:
            lines.append(token)
            current = ""
        if len(lines) == max_lines:
            break

    if current and len(lines) < max_lines:
        lines.append(current)

    if len(lines) > max_lines:
        lines = lines[:max_lines]

    if lines and text_size(draw, lines[-1], selected_font)[0] > max_width:
        line = lines[-1]
        while line and text_size(draw, f"{line}...", selected_font)[0] > max_width:
            line = line[:-1]
        lines[-1] = f"{line}..."

    return lines


def title_lines(draw: ImageDraw.ImageDraw, title: str, max_width: int, max_height: int) -> tuple[ImageFont.ImageFont, list[str], int]:
    for size in range(56, 33, -2):
        selected_font = font(size)
        line_gap = 14
        lines = wrap_text(draw, title, selected_font, max_width, 3)
        height = len(lines) * size + max(0, len(lines) - 1) * line_gap
        if height <= max_height and all(text_size(draw, line, selected_font)[0] <= max_width for line in lines):
            return selected_font, lines, line_gap
    selected_font = font(34)
    return selected_font, wrap_text(draw, title, selected_font, max_width, 3), 10


def rounded(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], radius: int, fill: str | tuple[int, int, int, int], outline: str | None = None, width: int = 1) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def gradient_background(palette: Palette) -> Image.Image:
    width, height = SIZE
    top = hex_to_rgb(palette.background_top)
    bottom = hex_to_rgb(palette.background_bottom)
    img = Image.new("RGB", SIZE)
    pixels = img.load()
    for y in range(height):
        ratio = y / max(1, height - 1)
        color = mix(top, bottom, ratio)
        for x in range(width):
            pixels[x, y] = color
    overlay = Image.new("RGBA", SIZE, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.ellipse((670, -140, 1250, 430), fill=with_alpha(palette.accent, 42))
    draw.ellipse((780, 260, 1190, 720), fill=with_alpha(palette.accent_2, 38))
    return Image.alpha_composite(img.convert("RGBA"), overlay)


def draw_header(draw: ImageDraw.ImageDraw, config: SeriesConfig) -> None:
    palette = config.palette
    small = font(24)
    pill_font = font(23)
    draw.text((64, 52), "sjh9714.log", fill=palette.muted, font=small)
    pill_text = config.name
    tw, th = text_size(draw, pill_text, pill_font)
    rounded(draw, (64, 90, 64 + tw + 34, 132), 21, with_alpha(palette.chip_fill, 220))
    draw.text((81, 99), pill_text, fill=palette.chip_text, font=pill_font)


def draw_chips(draw: ImageDraw.ImageDraw, config: SeriesConfig, extra: Iterable[str] = ()) -> None:
    x, y = 64, 467
    chip_font = font(22)
    for chip in (*extra, *config.chips):
        tw, th = text_size(draw, chip, chip_font)
        rounded(draw, (x, y, x + tw + 30, y + 40), 20, with_alpha(config.palette.chip_fill, 218))
        draw.text((x + 15, y + 9), chip, fill=config.palette.chip_text, font=chip_font)
        x += tw + 44
        if x > 710:
            break


def draw_title(draw: ImageDraw.ImageDraw, config: SeriesConfig, title: str, subtitle: str) -> None:
    selected_font, lines, line_gap = title_lines(draw, title, max_width=620, max_height=210)
    y = 182
    for line in lines:
        draw.text((64, y), line, fill=config.palette.text, font=selected_font)
        y += selected_font.size + line_gap
    if subtitle:
        draw.text((66, min(y + 14, 404)), subtitle, fill=config.palette.muted, font=font(25))


def draw_network(draw: ImageDraw.ImageDraw, config: SeriesConfig) -> None:
    p = config.palette
    nodes = [(802, 166), (934, 142), (902, 292), (760, 338), (976, 402)]
    for start, end in [(0, 1), (1, 2), (2, 3), (2, 4), (0, 3)]:
        draw.line((nodes[start], nodes[end]), fill=with_alpha(p.accent_2, 160), width=4)
    for x, y in nodes:
        draw.ellipse((x - 18, y - 18, x + 18, y + 18), fill=with_alpha(p.accent, 230))
        draw.ellipse((x - 7, y - 7, x + 7, y + 7), fill=p.text)
    for idx, y in enumerate((216, 248, 454)):
        rounded(draw, (760, y, 1010 - idx * 38, y + 26), 13, with_alpha(p.panel, 190), outline=p.accent)


def draw_seats(draw: ImageDraw.ImageDraw, config: SeriesConfig) -> None:
    p = config.palette
    start_x, start_y = 754, 160
    for row in range(6):
        for col in range(6):
            x = start_x + col * 42
            y = start_y + row * 38
            fill = p.accent if (row + col) % 4 == 0 else p.panel
            rounded(draw, (x, y, x + 27, y + 24), 7, with_alpha(fill, 230), outline=with_alpha(p.accent, 170))
    draw.arc((836, 360, 940, 468), 200, -20, fill=p.accent, width=8)
    rounded(draw, (806, 415, 970, 500), 18, with_alpha(p.panel, 230), outline=p.accent_2, width=3)
    draw.rectangle((876, 448, 900, 477), fill=p.accent)


def draw_diff(draw: ImageDraw.ImageDraw, config: SeriesConfig) -> None:
    p = config.palette
    rounded(draw, (736, 148, 1008, 440), 24, with_alpha(p.panel, 230), outline=with_alpha(p.accent, 130), width=2)
    diff_font = font(25)
    rows = [
        ("+", "test fails first", p.accent),
        ("+", "small code diff", p.accent),
        ("-", "hidden bug", "#ef4444"),
        ("+", "review ready", p.accent_2),
    ]
    y = 196
    for sign, text, color in rows:
        draw.text((770, y), sign, fill=color, font=diff_font)
        rounded(draw, (808, y + 5, 960, y + 25), 10, with_alpha(color, 70))
        draw.text((810, y - 25), text, fill=p.muted, font=font(18))
        y += 58
    draw.line((780, 395, 955, 395), fill=p.accent, width=5)
    draw.line((780, 395, 826, 350), fill=p.accent, width=5)


def draw_code(draw: ImageDraw.ImageDraw, config: SeriesConfig) -> None:
    p = config.palette
    rounded(draw, (724, 144, 1008, 430), 24, with_alpha(p.panel, 230), outline=with_alpha(p.accent_2, 150), width=2)
    line_y = 188
    widths = [210, 156, 230, 112, 196, 148]
    for idx, width in enumerate(widths):
        color = p.accent if idx in (1, 4) else p.accent_2
        rounded(draw, (766, line_y, 766 + width, line_y + 18), 9, with_alpha(color, 170))
        line_y += 38
    for x, y in [(788, 406), (864, 406), (940, 406)]:
        draw.ellipse((x - 13, y - 13, x + 13, y + 13), fill=p.accent)
        draw.line((x - 6, y, x - 1, y + 5, x + 8, y - 7), fill=p.background_top, width=3)


def draw_motif(draw: ImageDraw.ImageDraw, config: SeriesConfig) -> None:
    if config.motif == "network":
        draw_network(draw, config)
    elif config.motif == "seats":
        draw_seats(draw, config)
    elif config.motif == "diff":
        draw_diff(draw, config)
    elif config.motif == "code":
        draw_code(draw, config)


def read_title(path: Path) -> str:
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return path.stem.replace("-", " ").title()


def display_title(title: str) -> str:
    display = title.strip()
    prefixes = (
        r"\[DAY\d+\]",
        r"\[프로그래머스/Python\]",
        r"\[실시간 채팅 백엔드\]",
        r"\[콘서트 예매 시스템\]",
        r"\[오픈소스 기여\]",
    )
    changed = True
    while changed:
        changed = False
        for prefix in prefixes:
            next_display = re.sub(rf"^{prefix}\s*", "", display, flags=re.IGNORECASE).strip()
            if next_display != display:
                display = next_display
                changed = True
    return display or title


def post_extra_chips(path: Path, title: str) -> tuple[str, ...]:
    chips: list[str] = []
    day_match = re.search(r"\[DAY(\d+)\]", title, re.IGNORECASE)
    if day_match:
        chips.append(f"DAY{day_match.group(1)}")
    prefix_match = re.match(r"(\d+)", path.stem)
    if prefix_match:
        chips.append(f"#{prefix_match.group(1)}")
    return tuple(chips[:2])


def render_card(config: SeriesConfig, title: str, subtitle: str, out_path: Path, extra_chips: tuple[str, ...] = ()) -> None:
    img = gradient_background(config.palette)
    draw = ImageDraw.Draw(img)
    draw_header(draw, config)
    draw_motif(draw, config)
    draw_title(draw, config, title, subtitle)
    draw_chips(draw, config, extra_chips)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.convert("RGB").save(out_path, quality=95, optimize=True)


def markdown_posts(config: SeriesConfig) -> list[Path]:
    return sorted(path for path in config.source.glob("*.md") if path.name != "README.md")


def generate() -> list[Path]:
    generated: list[Path] = []
    for config in SERIES:
        series_out = OUTPUT_ROOT / "series" / f"{config.key}.png"
        render_card(config, config.name, config.tagline, series_out, ("Series",))
        generated.append(series_out)

        for post in markdown_posts(config):
            title = read_title(post)
            out = config.output_dir / f"{post.stem}.png"
            render_card(config, display_title(title), config.name, out, post_extra_chips(post, title))
            generated.append(out)
    return generated


def check_images(paths: list[Path]) -> None:
    expected_size = SIZE
    failures: list[str] = []
    for path in paths:
        if not path.exists():
            failures.append(f"missing: {path}")
            continue
        with Image.open(path) as img:
            if img.size != expected_size:
                failures.append(f"bad size: {path} -> {img.size}")
    if failures:
        raise SystemExit("\n".join(failures))


def expected_count() -> int:
    return len(SERIES) + sum(len(markdown_posts(config)) for config in SERIES)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Velog thumbnail PNGs.")
    parser.add_argument("--check", action="store_true", help="Check generated images without rewriting them.")
    args = parser.parse_args()

    if args.check:
        paths = [OUTPUT_ROOT / "series" / f"{config.key}.png" for config in SERIES]
        for config in SERIES:
            paths.extend(config.output_dir / f"{post.stem}.png" for post in markdown_posts(config))
        check_images(paths)
        print(f"Checked {len(paths)} thumbnails at {SIZE[0]}x{SIZE[1]}.")
        return

    generated = generate()
    check_images(generated)
    print(f"Generated {len(generated)} thumbnails at {SIZE[0]}x{SIZE[1]}.")
    print(f"Expected count from Markdown sources: {expected_count()}.")


if __name__ == "__main__":
    main()

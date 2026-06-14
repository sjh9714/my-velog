#!/usr/bin/env python3
"""Generate Velog thumbnail images from local Markdown posts.

This renderer uses AI-generated, text-free bitmap backgrounds and overlays
crisp Korean/English text with a local HTML/CSS template captured by Chrome.
"""

from __future__ import annotations

import argparse
import base64
import html
import mimetypes
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = ROOT / "assets" / "thumbnails"
AI_ROOT = OUTPUT_ROOT / "ai-backgrounds"
SIZE = (1080, 565)
CHROME = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")


@dataclass(frozen=True)
class Palette:
    accent: str
    accent_2: str
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


SERIES: tuple[SeriesConfig, ...] = (
    SeriesConfig(
        key="realtime-chat",
        name="실시간 채팅 백엔드",
        tagline="Realtime messaging boundaries",
        source=ROOT / "posts" / "velog" / "realtime-chat",
        output_dir=OUTPUT_ROOT / "posts" / "realtime-chat",
        palette=Palette(accent="#2dd4bf", accent_2="#38bdf8", chip_text="#d8fbff"),
        chips=("Spring Boot", "WebSocket", "Kafka"),
    ),
    SeriesConfig(
        key="concert-booking",
        name="콘서트 예매 시스템",
        tagline="Concurrency and reliable booking",
        source=ROOT / "posts" / "velog" / "concert-booking",
        output_dir=OUTPUT_ROOT / "posts" / "concert-booking",
        palette=Palette(accent="#f59e0b", accent_2="#ef4444", chip_text="#ffedd5"),
        chips=("Spring Boot", "Concurrency", "Kafka"),
    ),
    SeriesConfig(
        key="open-source",
        name="오픈소스 기여",
        tagline="Small diffs, tests, trusted PRs",
        source=ROOT / "posts" / "velog" / "open-source",
        output_dir=OUTPUT_ROOT / "posts" / "open-source",
        palette=Palette(accent="#16a34a", accent_2="#2563eb", chip_text="#dcfce7"),
        chips=("Open Source", "Regression Test", "PR"),
    ),
    SeriesConfig(
        key="programmers-python",
        name="프로그래머스 Python 코딩테스트",
        tagline="Daily algorithm notes in Python",
        source=ROOT / "programmers-python" / "posts" / "velog",
        output_dir=OUTPUT_ROOT / "posts" / "programmers-python",
        palette=Palette(accent="#facc15", accent_2="#60a5fa", chip_text="#dbeafe"),
        chips=("Programmers", "Python", "Algorithm"),
    ),
)


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


def markdown_posts(config: SeriesConfig) -> list[Path]:
    return sorted(path for path in config.source.glob("*.md") if path.name != "README.md")


def post_extra_chips(path: Path, title: str) -> tuple[str, ...]:
    chips: list[str] = []
    day_match = re.search(r"\[DAY(\d+)\]", title, re.IGNORECASE)
    if day_match:
        chips.append(f"DAY{day_match.group(1)}")
    prefix_match = re.match(r"(\d+)", path.stem)
    if prefix_match:
        chips.append(f"#{prefix_match.group(1)}")
    return tuple(chips[:2])


def esc(value: str) -> str:
    return html.escape(value, quote=True)


def chip_markup(chips: tuple[str, ...]) -> str:
    return "\n".join(f'<span class="chip">{esc(chip)}</span>' for chip in chips)


def ai_background_path(config: SeriesConfig, stem: str | None = None) -> Path:
    return AI_ROOT / "series" / f"{config.key}.png"


def expected_background_paths() -> list[Path]:
    return [ai_background_path(config) for config in SERIES]


def image_data_url(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Missing AI background: {path}")
    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def html_document(
    config: SeriesConfig,
    title: str,
    subtitle: str,
    extra_chips: tuple[str, ...],
    background_url: str,
) -> str:
    p = config.palette
    chips = chip_markup((*extra_chips, *config.chips))
    return f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=1080, initial-scale=1">
<style>
  :root {{
    --accent: {p.accent};
    --accent2: {p.accent_2};
    --chipText: {p.chip_text};
  }}
  * {{ box-sizing: border-box; }}
  html, body {{
    margin: 0;
    width: 1080px;
    height: 565px;
    overflow: hidden;
    background: #020714;
  }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Apple SD Gothic Neo", "Noto Sans KR", "Pretendard", "Segoe UI", sans-serif;
    color: #f8fbff;
    -webkit-font-smoothing: antialiased;
    text-rendering: geometricPrecision;
  }}
  .card {{
    position: relative;
    width: 1080px;
    height: 565px;
    overflow: hidden;
    isolation: isolate;
    background-image:
      linear-gradient(90deg, rgba(2, 7, 20, .79) 0%, rgba(3, 10, 25, .60) 31%, rgba(4, 13, 32, .22) 52%, rgba(2, 7, 20, .03) 100%),
      linear-gradient(0deg, rgba(0, 0, 0, .15), rgba(0, 0, 0, 0) 46%, rgba(0, 0, 0, .05)),
      url("{background_url}");
    background-position: center;
    background-size: cover;
  }}
  .glass {{
    position: absolute;
    left: 44px;
    top: 54px;
    width: 560px;
    height: 452px;
    border: 1px solid rgba(153, 203, 255, .18);
    border-radius: 28px;
    background: linear-gradient(135deg, rgba(4, 11, 29, .34), rgba(4, 10, 24, .10));
    box-shadow: 0 26px 80px rgba(0, 0, 0, .22), inset 0 1px 0 rgba(255, 255, 255, .06);
    backdrop-filter: blur(1.8px);
  }}
  .content {{
    position: absolute;
    left: 74px;
    top: 84px;
    width: 500px;
    height: 390px;
  }}
  .brand {{
    color: rgba(213, 228, 255, .84);
    font-size: 20px;
    font-weight: 650;
    line-height: 1;
    margin-bottom: 24px;
  }}
  .meta {{
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 36px;
  }}
  .pill {{
    display: inline-flex;
    align-items: center;
    height: 36px;
    padding: 0 16px;
    border: 1px solid rgba(255, 255, 255, .20);
    border-radius: 999px;
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, .13), 0 8px 22px rgba(0, 0, 0, .18);
    font-size: 19px;
    font-weight: 730;
    line-height: 1;
    white-space: nowrap;
  }}
  .series-pill {{
    background: color-mix(in srgb, var(--accent2) 76%, #0f172a);
    color: #f4f9ff;
  }}
  .day-pill {{
    background: var(--accent);
    color: #10192a;
  }}
  .title {{
    max-width: 500px;
    max-height: 150px;
    margin: 0;
    overflow: hidden;
    color: #fff;
    font-size: 74px;
    font-weight: 860;
    letter-spacing: 0;
    line-height: .98;
    overflow-wrap: anywhere;
    text-shadow: 0 8px 28px rgba(0, 0, 0, .66), 0 2px 2px rgba(0, 0, 0, .38);
    text-wrap: balance;
    word-break: keep-all;
  }}
  .accent-lines {{
    display: flex;
    gap: 13px;
    margin: 22px 0 23px;
  }}
  .accent-lines span {{
    display: block;
    height: 7px;
    border-radius: 999px;
  }}
  .accent-lines .primary {{
    width: 154px;
    background: var(--accent2);
    box-shadow: 0 0 28px color-mix(in srgb, var(--accent2) 48%, transparent);
  }}
  .accent-lines .secondary {{
    width: 92px;
    background: var(--accent);
    box-shadow: 0 0 26px color-mix(in srgb, var(--accent) 42%, transparent);
  }}
  .subtitle {{
    max-width: 500px;
    max-height: 88px;
    margin: 0;
    overflow: hidden;
    color: rgba(241, 248, 255, .98);
    font-size: 34px;
    font-weight: 760;
    letter-spacing: 0;
    line-height: 1.30;
    text-shadow: 0 5px 20px rgba(0, 0, 0, .66), 0 2px 2px rgba(0, 0, 0, .35);
    word-break: keep-all;
  }}
  .chips {{
    position: absolute;
    left: 0;
    bottom: 0;
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    max-width: 500px;
  }}
  .chip {{
    display: inline-flex;
    height: 34px;
    align-items: center;
    padding: 0 15px;
    border-radius: 999px;
    color: var(--chipText);
    background: color-mix(in srgb, var(--accent2) 34%, rgba(3, 7, 18, .74));
    box-shadow: 0 10px 24px rgba(0, 0, 0, .24);
    font-size: 18px;
    font-weight: 780;
    line-height: 1;
    white-space: nowrap;
  }}
</style>
</head>
<body>
  <main class="card">
    <div class="glass"></div>
    <section class="content">
      <div class="brand">sjh9714.log</div>
      <div class="meta">
        <span class="pill series-pill">{esc(config.name)}</span>
        <span class="pill day-pill">{esc(extra_chips[0] if extra_chips else "Series")}</span>
      </div>
      <h1 class="title" id="title">{esc(title)}</h1>
      <div class="accent-lines"><span class="primary"></span><span class="secondary"></span></div>
      <p class="subtitle" id="subtitle">{esc(subtitle)}</p>
      <section class="chips">{chips}</section>
    </section>
  </main>
  <script>
    const title = document.getElementById("title");
    let titleSize = Number.parseFloat(getComputedStyle(title).fontSize);
    while ((title.scrollHeight > title.clientHeight || title.scrollWidth > title.clientWidth) && titleSize > 38) {{
      titleSize -= 2;
      title.style.fontSize = titleSize + "px";
    }}

    const subtitle = document.getElementById("subtitle");
    let subtitleSize = Number.parseFloat(getComputedStyle(subtitle).fontSize);
    while ((subtitle.scrollHeight > subtitle.clientHeight || subtitle.scrollWidth > subtitle.clientWidth) && subtitleSize > 24) {{
      subtitleSize -= 1;
      subtitle.style.fontSize = subtitleSize + "px";
    }}
  </script>
</body>
</html>
"""


def screenshot_command(html_path: Path, out_path: Path) -> list[str]:
    return [
        "npx",
        "playwright",
        "screenshot",
        "--browser",
        "chromium",
        "--channel",
        "chrome",
        "--viewport-size",
        f"{SIZE[0]},{SIZE[1]}",
        "--wait-for-selector",
        ".card",
        "--wait-for-timeout",
        "160",
        "--timeout",
        "15000",
        html_path.as_uri(),
        str(out_path),
    ]


def render_card(
    config: SeriesConfig,
    title: str,
    subtitle: str,
    out_path: Path,
    extra_chips: tuple[str, ...],
    background_path: Path,
    tmp_dir: Path,
) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    html_path = tmp_dir / f"{out_path.stem}.html"
    html_path.write_text(
        html_document(config, title, subtitle, extra_chips, image_data_url(background_path)),
        encoding="utf-8",
    )
    subprocess.run(
        screenshot_command(html_path, out_path),
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=35,
    )


def generate() -> list[Path]:
    if not CHROME.exists():
        raise SystemExit(f"Google Chrome not found: {CHROME}")
    if not shutil.which("npx"):
        raise SystemExit("npx not found; Playwright CLI is required for screenshot rendering.")

    check_backgrounds(expected_background_paths())

    generated: list[Path] = []
    with tempfile.TemporaryDirectory(prefix="velog-thumbnails-") as tmp:
        tmp_dir = Path(tmp)
        for config in SERIES:
            series_out = OUTPUT_ROOT / "series" / f"{config.key}.png"
            render_card(
                config,
                config.name,
                config.tagline,
                series_out,
                ("Series",),
                ai_background_path(config),
                tmp_dir,
            )
            generated.append(series_out)

            for post in markdown_posts(config):
                title = read_title(post)
                out = config.output_dir / f"{post.stem}.png"
                render_card(
                    config,
                    display_title(title),
                    config.name,
                    out,
                    post_extra_chips(post, title),
                    ai_background_path(config),
                    tmp_dir,
                )
                generated.append(out)
    return generated


def all_expected_paths() -> list[Path]:
    paths = [OUTPUT_ROOT / "series" / f"{config.key}.png" for config in SERIES]
    for config in SERIES:
        paths.extend(config.output_dir / f"{post.stem}.png" for post in markdown_posts(config))
    return paths


def check_backgrounds(paths: list[Path]) -> None:
    missing = [f"missing background: {path}" for path in paths if not path.exists()]
    if missing:
        raise SystemExit("\n".join(missing))


def check_images(paths: list[Path]) -> None:
    failures: list[str] = []
    for path in paths:
        if not path.exists():
            failures.append(f"missing: {path}")
            continue
        with Image.open(path) as img:
            if img.size != SIZE:
                failures.append(f"bad size: {path} -> {img.size}")
    if failures:
        raise SystemExit("\n".join(failures))


def expected_count() -> int:
    return len(SERIES) + sum(len(markdown_posts(config)) for config in SERIES)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Velog thumbnail PNGs.")
    parser.add_argument("--check", action="store_true", help="Check generated images without rewriting them.")
    parser.add_argument("--check-backgrounds", action="store_true", help="Check required AI backgrounds.")
    parser.add_argument("--chrome-version", action="store_true", help="Print the Chrome version used by the renderer.")
    args = parser.parse_args()

    if args.chrome_version:
        if not CHROME.exists():
            raise SystemExit(f"Google Chrome not found: {CHROME}")
        result = subprocess.run([str(CHROME), "--version"], check=True, capture_output=True, text=True)
        print(result.stdout.strip())
        return

    if args.check_backgrounds:
        paths = expected_background_paths()
        check_backgrounds(paths)
        print(f"Checked {len(paths)} AI backgrounds.")
        return

    if args.check:
        paths = all_expected_paths()
        check_images(paths)
        print(f"Checked {len(paths)} thumbnails at {SIZE[0]}x{SIZE[1]}.")
        return

    generated = generate()
    check_images(generated)
    print(f"Generated {len(generated)} thumbnails at {SIZE[0]}x{SIZE[1]}.")
    print(f"Expected count from Markdown sources: {expected_count()}.")


if __name__ == "__main__":
    main()

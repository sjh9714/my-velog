#!/usr/bin/env python3
"""Generate Velog thumbnail images from local Markdown posts.

The renderer uses a local HTML/CSS poster template and captures it with
Headless Chrome. This keeps Korean text crisp while making the thumbnails feel
closer to designed blog covers than plain generated cards.
"""

from __future__ import annotations

import argparse
import html
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = ROOT / "assets" / "thumbnails"
SIZE = (1080, 565)
CHROME = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")


@dataclass(frozen=True)
class Palette:
    bg: str
    bg_2: str
    text: str
    muted: str
    accent: str
    accent_2: str
    accent_3: str
    panel: str
    chip: str
    chip_text: str
    grid: str


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
        tagline="Realtime messaging boundaries",
        source=ROOT / "posts" / "velog" / "realtime-chat",
        output_dir=OUTPUT_ROOT / "posts" / "realtime-chat",
        palette=Palette(
            bg="#07111f",
            bg_2="#0f3440",
            text="#f0fdff",
            muted="#9de8f5",
            accent="#2dd4bf",
            accent_2="#38bdf8",
            accent_3="#f8fafc",
            panel="rgba(12, 31, 48, 0.74)",
            chip="rgba(45, 212, 191, 0.16)",
            chip_text="#d8fbff",
            grid="rgba(148, 240, 255, 0.09)",
        ),
        chips=("Spring Boot", "WebSocket", "Kafka"),
        motif="realtime",
    ),
    SeriesConfig(
        key="concert-booking",
        name="콘서트 예매 시스템",
        tagline="Concurrency and reliable booking",
        source=ROOT / "posts" / "velog" / "concert-booking",
        output_dir=OUTPUT_ROOT / "posts" / "concert-booking",
        palette=Palette(
            bg="#111827",
            bg_2="#371820",
            text="#fff7ed",
            muted="#fed7aa",
            accent="#f59e0b",
            accent_2="#ef4444",
            accent_3="#fef3c7",
            panel="rgba(42, 30, 34, 0.78)",
            chip="rgba(245, 158, 11, 0.16)",
            chip_text="#ffedd5",
            grid="rgba(253, 186, 116, 0.08)",
        ),
        chips=("Spring Boot", "Concurrency", "Kafka"),
        motif="concert",
    ),
    SeriesConfig(
        key="open-source",
        name="오픈소스 기여",
        tagline="Small diffs, tests, trusted PRs",
        source=ROOT / "posts" / "velog" / "open-source",
        output_dir=OUTPUT_ROOT / "posts" / "open-source",
        palette=Palette(
            bg="#f8fafc",
            bg_2="#dff9e8",
            text="#0f172a",
            muted="#334155",
            accent="#16a34a",
            accent_2="#2563eb",
            accent_3="#059669",
            panel="rgba(255, 255, 255, 0.82)",
            chip="rgba(22, 163, 74, 0.13)",
            chip_text="#14532d",
            grid="rgba(15, 23, 42, 0.07)",
        ),
        chips=("Open Source", "Regression Test", "PR"),
        motif="opensource",
    ),
    SeriesConfig(
        key="programmers-python",
        name="프로그래머스 Python 코딩테스트",
        tagline="Daily algorithm notes in Python",
        source=ROOT / "programmers-python" / "posts" / "velog",
        output_dir=OUTPUT_ROOT / "posts" / "programmers-python",
        palette=Palette(
            bg="#0f172a",
            bg_2="#172554",
            text="#eff6ff",
            muted="#bfdbfe",
            accent="#facc15",
            accent_2="#60a5fa",
            accent_3="#34d399",
            panel="rgba(17, 28, 56, 0.80)",
            chip="rgba(96, 165, 250, 0.17)",
            chip_text="#dbeafe",
            grid="rgba(191, 219, 254, 0.08)",
        ),
        chips=("Programmers", "Python", "Algorithm"),
        motif="programmers",
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


def motif_markup(kind: str) -> str:
    if kind == "realtime":
        return """
        <div class="visual realtime-visual">
          <div class="route-card">
            <div class="route-line top"></div>
            <div class="route-line middle"></div>
            <div class="route-line bottom"></div>
            <div class="route-node client">CLIENT</div>
            <div class="route-node stomp">STOMP</div>
            <div class="route-node kafka">KAFKA</div>
            <div class="route-node db">DB</div>
            <div class="pulse one"></div>
            <div class="pulse two"></div>
          </div>
          <div class="terminal">
            <span>/app/chat.send</span>
            <span>/topic/rooms/{id}</span>
            <span>ACK -> PERSISTED</span>
          </div>
        </div>
        """
    if kind == "concert":
        seats = "\n".join(f'<i class="seat s{i}"></i>' for i in range(42))
        return f"""
        <div class="visual concert-visual">
          <div class="stage">CONCERT</div>
          <div class="seat-map">{seats}</div>
          <div class="queue-card">
            <span>WAITING QUEUE</span>
            <b>LOCK</b>
            <em>payment boundary</em>
          </div>
        </div>
        """
    if kind == "opensource":
        return """
        <div class="visual opensource-visual">
          <div class="pr-card">
            <div class="pr-head"><b>Pull Request</b><span>review ready</span></div>
            <p class="add">+ regression test</p>
            <p class="add">+ small implementation diff</p>
            <p class="del">- hidden bug path</p>
            <p class="add">+ documented edge case</p>
            <div class="status-row"><span>tests passing</span><b>MERGEABLE</b></div>
          </div>
        </div>
        """
    return """
    <div class="visual programmers-visual">
      <div class="editor">
        <div class="dots"><i></i><i></i><i></i></div>
        <code><b>def</b> solution(data):</code>
        <code>    seen = set(data)</code>
        <code>    return min(limit, len(seen))</code>
        <div class="checks"><span>input</span><span>edge</span><span>O(n)</span></div>
      </div>
      <div class="day-orbit">DAILY</div>
    </div>
    """


def html_document(config: SeriesConfig, title: str, subtitle: str, extra_chips: tuple[str, ...]) -> str:
    p = config.palette
    chips = chip_markup((*extra_chips, *config.chips))
    return f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=1080, initial-scale=1">
<style>
  :root {{
    --bg: {p.bg};
    --bg2: {p.bg_2};
    --text: {p.text};
    --muted: {p.muted};
    --accent: {p.accent};
    --accent2: {p.accent_2};
    --accent3: {p.accent_3};
    --panel: {p.panel};
    --chip: {p.chip};
    --chipText: {p.chip_text};
    --grid: {p.grid};
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    width: 1080px;
    height: 565px;
    overflow: hidden;
    font-family: -apple-system, BlinkMacSystemFont, "Apple SD Gothic Neo", "Noto Sans KR", "Pretendard", "Segoe UI", sans-serif;
    background: var(--bg);
  }}
  .card {{
    position: relative;
    width: 1080px;
    height: 565px;
    padding: 52px 62px;
    color: var(--text);
    isolation: isolate;
    background:
      radial-gradient(circle at 86% 14%, color-mix(in srgb, var(--accent) 38%, transparent), transparent 34%),
      radial-gradient(circle at 92% 82%, color-mix(in srgb, var(--accent2) 32%, transparent), transparent 38%),
      linear-gradient(135deg, var(--bg) 0%, var(--bg2) 100%);
  }}
  .card::before {{
    content: "";
    position: absolute;
    inset: 0;
    z-index: -2;
    opacity: .95;
    background-image:
      linear-gradient(var(--grid) 1px, transparent 1px),
      linear-gradient(90deg, var(--grid) 1px, transparent 1px);
    background-size: 34px 34px;
    mask-image: linear-gradient(90deg, rgba(0,0,0,.75), rgba(0,0,0,.2) 58%, rgba(0,0,0,.65));
  }}
  .card::after {{
    content: "";
    position: absolute;
    inset: -40px;
    z-index: -1;
    opacity: .22;
    background:
      repeating-linear-gradient(115deg, rgba(255,255,255,.12) 0 1px, transparent 1px 9px);
    mix-blend-mode: overlay;
  }}
  .topline {{
    display: flex;
    align-items: center;
    gap: 18px;
    color: var(--muted);
    font-size: 23px;
    letter-spacing: 0;
  }}
  .brand {{
    font-weight: 700;
  }}
  .series-pill {{
    padding: 9px 18px 10px;
    border: 1px solid color-mix(in srgb, var(--accent) 40%, transparent);
    border-radius: 999px;
    color: var(--chipText);
    background: var(--chip);
    box-shadow: 0 12px 28px rgba(0, 0, 0, .16);
  }}
  .content {{
    position: relative;
    z-index: 2;
    width: 572px;
    height: 370px;
    margin-top: 47px;
  }}
  .kicker {{
    display: inline-flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 22px;
    color: var(--accent);
    font-size: 22px;
    font-weight: 800;
    text-transform: uppercase;
  }}
  .kicker::before {{
    content: "";
    width: 42px;
    height: 2px;
    border-radius: 99px;
    background: var(--accent);
  }}
  .title {{
    max-width: 572px;
    max-height: 210px;
    overflow: hidden;
    color: var(--text);
    font-size: 58px;
    line-height: 1.12;
    font-weight: 860;
    letter-spacing: -0.01em;
    text-wrap: balance;
    word-break: keep-all;
    overflow-wrap: anywhere;
    text-shadow: 0 20px 48px rgba(0, 0, 0, .24);
  }}
  .subtitle {{
    margin-top: 23px;
    color: var(--muted);
    font-size: 24px;
    line-height: 1.35;
    font-weight: 600;
  }}
  .chips {{
    position: absolute;
    left: 62px;
    right: 390px;
    bottom: 50px;
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
  }}
  .chip {{
    display: inline-flex;
    height: 39px;
    align-items: center;
    padding: 0 17px;
    border: 1px solid color-mix(in srgb, var(--accent) 32%, transparent);
    border-radius: 999px;
    color: var(--chipText);
    background: var(--chip);
    font-size: 20px;
    font-weight: 650;
    box-shadow: 0 12px 28px rgba(0, 0, 0, .12);
  }}
  .visual {{
    position: absolute;
    right: 55px;
    top: 104px;
    width: 352px;
    height: 365px;
    border: 1px solid color-mix(in srgb, var(--accent) 50%, transparent);
    border-radius: 34px;
    background: color-mix(in srgb, var(--panel) 90%, transparent);
    box-shadow: 0 34px 90px rgba(0, 0, 0, .28), inset 0 1px 0 rgba(255,255,255,.16);
    backdrop-filter: blur(18px);
    overflow: hidden;
  }}
  .visual::before {{
    content: "";
    position: absolute;
    inset: 0;
    background:
      radial-gradient(circle at 30% 10%, color-mix(in srgb, var(--accent) 30%, transparent), transparent 30%),
      linear-gradient(135deg, rgba(255,255,255,.08), transparent 38%);
    pointer-events: none;
  }}
  .route-card {{
    position: absolute;
    inset: 32px 32px 178px;
  }}
  .route-line {{
    position: absolute;
    height: 4px;
    border-radius: 99px;
    background: linear-gradient(90deg, var(--accent), var(--accent2));
    box-shadow: 0 0 24px color-mix(in srgb, var(--accent2) 70%, transparent);
    transform-origin: left center;
  }}
  .route-line.top {{ left: 46px; top: 44px; width: 162px; transform: rotate(-10deg); }}
  .route-line.middle {{ left: 78px; top: 102px; width: 140px; transform: rotate(12deg); }}
  .route-line.bottom {{ left: 74px; top: 134px; width: 132px; transform: rotate(-12deg); }}
  .route-node {{
    position: absolute;
    width: 78px;
    height: 42px;
    display: grid;
    place-items: center;
    border: 1px solid color-mix(in srgb, var(--accent) 60%, transparent);
    border-radius: 999px;
    color: var(--text);
    background: color-mix(in srgb, var(--bg) 58%, transparent);
    font-size: 13px;
    font-weight: 900;
  }}
  .client {{ left: 0; top: 22px; }}
  .stomp {{ right: 10px; top: 0; }}
  .kafka {{ left: 44px; bottom: 10px; }}
  .db {{ right: 0; bottom: 0; }}
  .pulse {{
    position: absolute;
    width: 16px;
    height: 16px;
    border-radius: 50%;
    background: var(--accent);
    box-shadow: 0 0 0 10px color-mix(in srgb, var(--accent) 15%, transparent);
  }}
  .pulse.one {{ left: 136px; top: 39px; }}
  .pulse.two {{ right: 78px; top: 118px; background: var(--accent2); }}
  .terminal {{
    position: absolute;
    left: 28px;
    right: 28px;
    bottom: 23px;
    display: grid;
    gap: 11px;
    color: var(--muted);
    font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
    font-size: 15px;
  }}
  .terminal span {{
    padding: 9px 12px;
    border-radius: 12px;
    background: rgba(0,0,0,.22);
    border: 1px solid color-mix(in srgb, var(--accent2) 24%, transparent);
  }}
  .stage {{
    position: absolute;
    left: 55px;
    top: 28px;
    width: 242px;
    height: 40px;
    display: grid;
    place-items: center;
    border-radius: 0 0 24px 24px;
    background: linear-gradient(90deg, var(--accent2), var(--accent));
    color: #111827;
    font-size: 15px;
    font-weight: 1000;
  }}
  .seat-map {{
    position: absolute;
    left: 57px;
    top: 92px;
    display: grid;
    grid-template-columns: repeat(7, 20px);
    gap: 8px;
  }}
  .seat {{
    width: 20px;
    height: 20px;
    border: 1px solid var(--accent);
    border-radius: 7px 7px 10px 10px;
    background: rgba(0,0,0,.16);
  }}
  .seat:nth-child(5n+1), .seat:nth-child(7n+3) {{
    background: var(--accent);
    box-shadow: 0 0 20px color-mix(in srgb, var(--accent) 45%, transparent);
  }}
  .queue-card {{
    position: absolute;
    left: 42px;
    right: 42px;
    bottom: 32px;
    padding: 14px 18px;
    border: 1px solid color-mix(in srgb, var(--accent2) 60%, transparent);
    border-radius: 24px;
    background: color-mix(in srgb, var(--bg) 72%, transparent);
    box-shadow: 0 22px 44px rgba(0,0,0,.24);
  }}
  .queue-card span, .queue-card em {{
    display: block;
    color: var(--muted);
    font-size: 14px;
    font-style: normal;
  }}
  .queue-card b {{
    display: block;
    margin: 4px 0;
    color: var(--accent);
    font-size: 30px;
    letter-spacing: .1em;
  }}
  .pr-card {{
    position: absolute;
    inset: 28px 30px;
    padding: 22px;
    border-radius: 28px;
    background: rgba(255,255,255,.72);
    box-shadow: inset 0 0 0 1px rgba(15,23,42,.08);
  }}
  .pr-head {{
    display: flex;
    justify-content: space-between;
    color: var(--text);
    font-size: 17px;
  }}
  .pr-head span {{
    color: var(--accent);
    font-size: 13px;
    font-weight: 900;
  }}
  .pr-card p {{
    margin: 12px 0 0;
    padding: 9px 13px;
    border-radius: 13px;
    font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
    font-size: 14px;
  }}
  .pr-card .add {{ color: #14532d; background: rgba(22,163,74,.13); }}
  .pr-card .del {{ color: #991b1b; background: rgba(239,68,68,.13); }}
  .status-row {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 14px;
    color: var(--muted);
    font-size: 13px;
  }}
  .status-row b {{
    color: white;
    background: var(--accent);
    padding: 8px 10px;
    border-radius: 999px;
    font-size: 12px;
  }}
  .editor {{
    position: absolute;
    inset: 34px 28px 74px;
    padding: 26px 22px;
    border-radius: 26px;
    background: rgba(3, 7, 18, .43);
    border: 1px solid color-mix(in srgb, var(--accent2) 45%, transparent);
    font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  }}
  .dots {{
    display: flex;
    gap: 8px;
    margin-bottom: 28px;
  }}
  .dots i {{
    width: 11px;
    height: 11px;
    border-radius: 50%;
    background: var(--accent);
  }}
  .editor code {{
    display: block;
    margin: 17px 0;
    color: var(--muted);
    font-size: 16px;
  }}
  .editor code b {{
    color: var(--accent);
  }}
  .checks {{
    display: flex;
    gap: 10px;
    margin-top: 24px;
  }}
  .checks span {{
    color: var(--bg);
    background: var(--accent);
    border-radius: 999px;
    padding: 7px 10px;
    font-size: 13px;
    font-weight: 900;
  }}
  .day-orbit {{
    position: absolute;
    right: 24px;
    bottom: 20px;
    width: 116px;
    height: 38px;
    display: grid;
    place-items: center;
    border-radius: 999px;
    color: var(--bg);
    background: var(--accent);
    font-size: 16px;
    font-weight: 1000;
    box-shadow: 0 0 30px color-mix(in srgb, var(--accent) 38%, transparent);
  }}
</style>
</head>
<body>
  <main class="card">
    <div class="topline">
      <span class="brand">sjh9714.log</span>
      <span class="series-pill">{esc(config.name)}</span>
    </div>
    <section class="content">
      <div class="kicker">{esc(config.key.replace("-", " "))}</div>
      <div class="title" id="title">{esc(title)}</div>
      <div class="subtitle">{esc(subtitle)}</div>
    </section>
    <section class="chips">{chips}</section>
    {motif_markup(config.motif)}
  </main>
  <script>
    const title = document.getElementById("title");
    let size = Number.parseFloat(getComputedStyle(title).fontSize);
    while ((title.scrollHeight > title.clientHeight || title.scrollWidth > title.clientWidth) && size > 34) {{
      size -= 2;
      title.style.fontSize = size + "px";
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
        "120",
        "--timeout",
        "15000",
        html_path.as_uri(),
        str(out_path),
    ]


def render_card(config: SeriesConfig, title: str, subtitle: str, out_path: Path, extra_chips: tuple[str, ...], tmp_dir: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    html_path = tmp_dir / f"{out_path.stem}.html"
    html_path.write_text(html_document(config, title, subtitle, extra_chips), encoding="utf-8")
    subprocess.run(screenshot_command(html_path, out_path), check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=35)


def generate() -> list[Path]:
    if not CHROME.exists():
        raise SystemExit(f"Google Chrome not found: {CHROME}")
    if not shutil.which("npx"):
        raise SystemExit("npx not found; Playwright CLI is required for screenshot rendering.")

    generated: list[Path] = []
    with tempfile.TemporaryDirectory(prefix="velog-thumbnails-") as tmp:
        tmp_dir = Path(tmp)
        for config in SERIES:
            series_out = OUTPUT_ROOT / "series" / f"{config.key}.png"
            render_card(config, config.name, config.tagline, series_out, ("Series",), tmp_dir)
            generated.append(series_out)

            for post in markdown_posts(config):
                title = read_title(post)
                out = config.output_dir / f"{post.stem}.png"
                render_card(config, display_title(title), config.name, out, post_extra_chips(post, title), tmp_dir)
                generated.append(out)
    return generated


def all_expected_paths() -> list[Path]:
    paths = [OUTPUT_ROOT / "series" / f"{config.key}.png" for config in SERIES]
    for config in SERIES:
        paths.extend(config.output_dir / f"{post.stem}.png" for post in markdown_posts(config))
    return paths


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
    parser.add_argument("--chrome-version", action="store_true", help="Print the Chrome version used by the renderer.")
    args = parser.parse_args()

    if args.chrome_version:
        if not CHROME.exists():
            raise SystemExit(f"Google Chrome not found: {CHROME}")
        result = subprocess.run([str(CHROME), "--version"], check=True, capture_output=True, text=True)
        print(result.stdout.strip())
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

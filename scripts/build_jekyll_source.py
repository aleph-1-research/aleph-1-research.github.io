"""Prepare the Obsidian vault as a Jekyll source tree for GitHub Pages."""
from pathlib import Path
from urllib.parse import quote
import re
import shutil

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "_build"

if DEST.exists():
    shutil.rmtree(DEST)
DEST.mkdir()

# Copy the generated landing page and site assets created for GitHub Pages.
for special in (ROOT / "index.md", ROOT / "_config.yml", ROOT / "_layouts", ROOT / "assets"):
    if not special.exists():
        continue
    target = DEST / special.relative_to(ROOT)
    if special.is_dir():
        shutil.copytree(special, target)
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(special, target)

SKIP_DIRS = {".git", ".obsidian", "_build", "_site", "vendor", ".bundle"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp"}

def slug(value: str) -> str:
    value = value.removeprefix("#").removeprefix("^").lower()
    return re.sub(r"[^a-z0-9]+", "-", value).strip("-")

def page_url(target: str) -> str:
    path, _, fragment = target.partition("#")
    if path:
        name = Path(path).stem
        url = f"/{slug(name)}/"
    else:
        url = ""
    if fragment:
        url += f"#{slug(fragment)}"
    return url or "#"

def transform(text: str) -> str:
    def image(match: re.Match[str]) -> str:
        file = match.group(1)
        alt = match.group(2) or Path(file).stem
        relative = file if "/" in file else f"Resources/{file}"
        encoded = "/".join(quote(part) for part in Path(relative).parts)
        return f"![{alt}]({encoded})"

    text = re.sub(r"!\[\[([^\]|]+)(?:\|([^\]]+))?\]\]", image, text)

    def link(match: re.Match[str]) -> str:
        target = match.group(1)
        label = match.group(2) or target.split("#")[-1]
        return f"[{label}]({page_url(target)})"

    return re.sub(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]", link, text)

for source in ROOT.rglob("*"):
    if not source.is_file() or any(part in SKIP_DIRS for part in source.parts):
        continue
    relative = source.relative_to(ROOT)
    if relative.parts and relative.parts[0] in {"scripts", "_plugins"}:
        continue
    destination = DEST / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    if source.suffix.lower() == ".md":
        body = transform(source.read_text())
        if relative.name != "index.md":
            title = source.stem
            permalink = "/" + slug(title) + "/"
            front_matter = f"---\nlayout: default\ntitle: {title}\npermalink: {permalink}\n---\n\n"
            body = front_matter + body
        destination.write_text(body, encoding="utf-8")
    elif source.suffix.lower() in IMAGE_EXTENSIONS:
        shutil.copy2(source, destination)
    elif source.name in {"_config.yml", "Gemfile", "Gemfile.lock"} or relative.parts[0] in {"_layouts", "assets"}:
        shutil.copy2(source, destination)

# The generated source does not need the local-only bundle configuration.
for local_file in (DEST / "Gemfile", DEST / "Gemfile.lock"):
    local_file.unlink(missing_ok=True)

print(f"Prepared {sum(1 for _ in DEST.rglob('*.md'))} Markdown pages in {DEST}")
_append = DEST / "_config.yml"
if _append.exists():
    config = _append.read_text()
    if "safe:" not in config:
        _append.write_text(config + "\nsafe: true\n", encoding="utf-8")
else:
    raise SystemExit("_config.yml was not copied")

# Jekyll uses the generated tree as the publishing source.

for path in [DEST / "_plugins", DEST / "scripts"]:
    if path.exists():
        shutil.rmtree(path)

# The generated index is the site homepage; the vault's own In Vivo note is empty.
print("Obsidian wikilinks converted to Markdown links")

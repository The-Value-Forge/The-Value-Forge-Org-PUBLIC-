"""digest_build.py — assemble the weekly email digest from the pipeline's own artefacts.

The board's audience seat: for this readership the email digest is the product and
the site is the archive that makes it citable. The Saturday pipeline already emits
everything the digest needs; this script just assembles it. Zero pipeline changes.

Usage:
  python3 scripts/digest_build.py                # latest intelligence week
  python3 scripts/digest_build.py 2026-07-10     # the week ending that Friday

Output: markdown to stdout (pipe to a file, paste into MailerLite, or feed a
future automation once the MailerLite connector is authenticated). Links are
site-absolute paths; prefix with the production origin when sending.
"""
import re
import sys
from pathlib import Path

SITE = "https://tvf-pipeline-spike.netlify.app"  # swap for the custom domain at launch


def frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\s*\n(.*?)\n---", text, re.S)
    if not m:
        return {}
    fm = {}
    for line in m.group(1).splitlines():
        kv = re.match(r"^(\w[\w_]*):\s*(.*)$", line)
        if kv:
            fm[kv.group(1)] = kv.group(2).strip().strip('"')
    return fm


def main():
    syntheses = sorted(
        (p for p in Path("content/synthesis").glob("*.md")
         if re.match(r"^\d{4}-\d{2}-\d{2}", p.name)),
        reverse=True,
    )
    if not syntheses:
        sys.exit("No syntheses found.")
    if len(sys.argv) > 1:
        wanted = [p for p in syntheses if p.name.startswith(sys.argv[1])]
        if not wanted:
            sys.exit(f"No synthesis for week {sys.argv[1]}.")
        synth = wanted[0]
    else:
        synth = syntheses[0]

    week_end = synth.name[:10]
    sfm = frontmatter(synth)

    # Signals from the same intelligence week (Sat–Fri window ending week_end)
    from datetime import date, timedelta
    end = date.fromisoformat(week_end)
    start = end - timedelta(days=6)
    signals = []
    for p in sorted(Path("content/signal").glob("*.md")):
        try:
            d = date.fromisoformat(p.name[:10])
        except ValueError:
            continue
        if start <= d <= end:
            signals.append((d, p, frontmatter(p)))

    slug = synth.stem
    print(f"Subject: {sfm.get('title', 'This week from The Value Forge')}")
    print()
    print(f"# The Value Forge — week ending {end.strftime('%-d %B %Y')}")
    print()
    print(sfm.get("description", ""))
    print()
    print(f"**[Read the full synthesis →]({SITE}/synthesis/{slug}/)**")
    if signals:
        print()
        print("## This week's signals")
        for d, p, fm in signals:
            print()
            print(f"**{fm.get('title', p.stem)}**  ")
            print(f"{fm.get('description', '')}  ")
            print(f"[{d.strftime('%-d %b')} · read the signal →]({SITE}/signal/{p.stem}/)")
    print()
    print("## The register")
    print()
    print(f"Cross-domain patterns, tracked longitudinally with their evidence: "
          f"[the pattern register →]({SITE}/patterns/)")
    print()
    print("---")
    print("The Value Forge · independent clinical intelligence · CC BY 4.0  ")
    print(f"Archive, method and sources: {SITE}")


if __name__ == "__main__":
    main()

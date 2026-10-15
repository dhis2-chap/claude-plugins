"""Build the pan/zoom diagram page from a Mermaid file.

Usage: python3 build.py <diagram.mmd> <version> <out.html>
"""
import pathlib
import sys

mmd, version, out = sys.argv[1], sys.argv[2], sys.argv[3]
template = (pathlib.Path(__file__).parent / "view-template.html").read_text()
source = pathlib.Path(mmd).read_text().strip()
pathlib.Path(out).write_text(template.replace("%%MERMAID%%", source).replace("%%VERSION%%", version))

"""Draw a language legend from the snapshot used by git-koi's Action."""

import colorsys
import json
import sys
from collections import Counter
from html import escape
from pathlib import Path


def pigment(color):
    """Match git-koi v1's hue thresholds and white-body pigment palette.

    Source: https://github.com/yalongwastaken/git-koi/blob/v1/src/coat.rs
    Actual fish shades also vary with lighting, growth, and streaks.
    """
    if color is None:
        return "#262b44"
    channels = [int(color[index:index + 2], 16) / 255 for index in (1, 3, 5)]
    hue, _, saturation = colorsys.rgb_to_hls(*channels)
    if max(channels) - min(channels) < 0.12 or saturation < 0.2:
        return "#262b44"
    degrees = hue * 360
    if degrees < 18 or degrees >= 330:
        return "#e43b44"
    if degrees < 45:
        return "#f77622"
    if degrees < 160:
        return "#feae34"
    return "#124e89"


def render(snapshot):
    """Count each public, non-fork repository once by its primary language."""
    repositories = {}
    for repository in snapshot["repositories"]:
        repository_id = repository["repository_id"]
        if repository_id in repositories and repositories[repository_id] != repository:
            raise ValueError(f"Conflicting repository observations: {repository_id}")
        repositories[repository_id] = repository
    counts = Counter(
        repository["primary_language"]
        for repository in repositories.values()
        if repository["visibility"] == "public"
        and not repository["is_fork"]
        and repository["primary_language"] is not None
    )
    languages = sorted(counts, key=lambda language: (-counts[language], language))
    total = sum(counts.values())
    rows = max(1, (len(languages) + 1) // 2)
    height = rows * 30 + 12
    labels = [f"{language}: {counts[language] / total:.1%}" for language in languages]
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="560" height="{height}" '
        f'viewBox="0 0 560 {height}" role="img" aria-labelledby="title">',
        f'<title id="title">{escape("Languages by repository. " + ", ".join(labels))}</title>',
        '<style>text { fill: #1f2328; font: 14px -apple-system, BlinkMacSystemFont, '
        '"Segoe UI", sans-serif; } circle { stroke: #8c959f; stroke-width: .5; } '
        '@media (prefers-color-scheme: dark) { text { fill: #e6edf3; } }</style>',
    ]
    for index, language in enumerate(languages):
        x = (index // rows) * 280 + 8
        y = (index % rows) * 30 + 21
        color = pigment(snapshot["language_colors"][language])
        parts.extend([
            f'<circle cx="{x + 5}" cy="{y - 5}" r="5" fill="{color}"/>',
            f'<text x="{x + 19}" y="{y}">{escape(language)}</text>',
            f'<text x="{x + 250}" y="{y}" text-anchor="end">'
            f'{counts[language] / total:.1%}</text>',
        ])
    if not languages:
        parts.append('<text x="8" y="21">No languages to display yet.</text>')
    parts.append('</svg>\n')
    return "\n".join(parts)


if __name__ == "__main__":
    snapshot = json.loads(Path(sys.argv[1]).read_text())
    Path(sys.argv[2]).write_text(render(snapshot))

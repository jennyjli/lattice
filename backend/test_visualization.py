#!/usr/bin/env python3
"""
Visualization module test — exercises render_spec() with real, captured Gemini
output WITHOUT calling Gemini (no API credits, no network, no server).

The fixtures in sample_specs/ were produced by AnimationDirector and frozen, so
this runs the full spec → SVG path deterministically and offline.

Run:  python test_visualization.py
"""

import json
import sys
import xml.dom.minidom as minidom
from pathlib import Path

from animation_spec import AnimationSpec
from renderer import SVGRenderer

SAMPLE_DIR = Path(__file__).parent / "sample_specs"


def _check(name: str, cond: bool, detail: str = "") -> bool:
    mark = "✅" if cond else "❌"
    print(f"  {mark} {name}" + (f" — {detail}" if detail and not cond else ""))
    return cond


def test_spec_file(path: Path) -> bool:
    print(f"\n▶ {path.name}")
    raw = json.loads(path.read_text())

    ok = True
    # 1. The captured JSON still validates against the current schema.
    try:
        spec = AnimationSpec.model_validate(raw)
        ok &= _check("spec validates against schema", True)
    except Exception as e:  # noqa: BLE001
        _check("spec validates against schema", False, str(e))
        return False

    # 2. It renders to a non-trivial string.
    svg = SVGRenderer().render_spec(spec)
    ok &= _check("renders to SVG", len(svg) > 500, f"len={len(svg)}")

    # 3. Output is well-formed XML.
    try:
        minidom.parseString(svg)
        ok &= _check("output is well-formed XML", True)
    except Exception as e:  # noqa: BLE001
        ok &= _check("output is well-formed XML", False, str(e))

    # 4. Structural expectations.
    ok &= _check("wrapped in <svg>", svg.startswith("<svg") and svg.rstrip().endswith("</svg>"))
    ok &= _check("has CSS keyframe animations", "@keyframes kf_" in svg)
    ok &= _check("title is rendered", spec.title.split(":")[0][:10] in svg or spec.title[:10] in svg)
    ok &= _check("an actor is drawn per spec", svg.count('class="act_') >= len(spec.actors) - 1)

    # 5. If the process includes a completion step (repair / final disappear),
    #    the rendered output should reflect it — the animation must finish, not
    #    stop mid-process. (This is the regression the spec renderer fixed.)
    has_repair = any(e.action == "repair" for e in spec.events)
    if has_repair:
        ok &= _check(
            "completion (repair) is rendered",
            any(tok in svg for tok in ("HDR", "NHEJ", "Repaired", "precise edit", "knockout")),
        )

    return ok


def main() -> int:
    fixtures = sorted(SAMPLE_DIR.glob("*.json"))
    if not fixtures:
        print(f"No fixtures found in {SAMPLE_DIR}")
        return 1

    print(f"Testing render_spec() against {len(fixtures)} captured Gemini spec(s)")
    all_ok = all(test_spec_file(p) for p in fixtures)

    print("\n" + ("🎉 ALL PASSED" if all_ok else "💥 FAILURES — see above"))
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())

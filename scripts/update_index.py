#!/usr/bin/env python3
from html import escape
from html.parser import HTMLParser
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
INDEX_PATH = ROOT / "index.html"

DEMO_ORDER = [
    "POC_to_Cynapsa.html",
    "4_issues.html",
    "healthcare_agents.html",
    "legal_doc_agent.html",
    "identity_based_routing.html",
    "distributed_agentic_segmentation.html",
    "microsegmentation.html",
]

DEMO_OVERRIDES = {
    "POC_to_Cynapsa.html": {
        "eyebrow": "Start here",
        "title": "The Evolution of Agentic Networking",
        "description": "Shows the shift from a simple single-environment proof of concept to production reality, where load balancers, API gateways, VPNs, and firewalls create bottlenecks. The final stage introduces the Cynapsa mesh as an identity-native alternative with native agent load balancing.",
    },
    "4_issues.html": {
        "eyebrow": "Framework barriers",
        "title": "The 4 Barriers to Agentic AI",
        "description": "Walks through security, privacy, accessibility, and scalability problems that appear when lab-built agent frameworks move into enterprise production. Each stage lets the viewer compare legacy infrastructure behavior with a Cynapsa mesh approach.",
    },
    "healthcare_agents.html": {
        "eyebrow": "Healthcare use case",
        "title": "Healthcare AI and HIPAA Compliance",
        "description": "Demonstrates a hospital sepsis-detection workflow. The legacy path sends protected health information toward the cloud, while the Cynapsa path keeps the health agent and raw EHR data inside the hospital network.",
    },
    "legal_doc_agent.html": {
        "eyebrow": "Legal use case",
        "title": "Legal Data Confidentiality",
        "description": "Explains how a law firm can use an AI document agent without uploading confidential client files to the cloud. The Cynapsa version places the document agent next to the private VectorDB and returns only the final answer.",
    },
    "identity_based_routing.html": {
        "eyebrow": "Routing concept",
        "title": "Identity-Based Routing",
        "description": "Compares IP-based networking with Cynapsa routing by cryptographic identity. It highlights mobile agent roaming, IP changes, out-of-band authorization through the control plane, and zero-trust connectivity that survives network changes.",
    },
    "distributed_agentic_segmentation.html": {
        "eyebrow": "Distributed segmentation",
        "title": "Proximity Does Not Equal Trust",
        "description": "Shows agentic microsegmentation across AWS, GCP, on-premise, and local networks. The legacy hub-and-spoke VPN connects locations with any-to-any access, while Cynapsa uses identity-based P2P routing and mesh contexts to contain breaches and block shadow agents.",
    },
    "microsegmentation.html": {
        "eyebrow": "Security simulation",
        "title": "Kubernetes Blast Radius Simulation",
        "description": "Simulates a compromised AI agent inside a shared Kubernetes namespace. The current network topology allows lateral movement, while Cynapsa agentic microsegmentation contains the compromise through identity-based cryptographic isolation.",
    },
}


class DemoTextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = ""
        self.heading = ""
        self.paragraph = ""
        self._tag_stack = []
        self._buffer = []

    def handle_starttag(self, tag, attrs):
        if tag in {"title", "h1", "p"}:
            self._tag_stack.append(tag)
            self._buffer = []

    def handle_data(self, data):
        if self._tag_stack:
            self._buffer.append(data)

    def handle_endtag(self, tag):
        if not self._tag_stack or self._tag_stack[-1] != tag:
            return

        text = clean_text(" ".join(self._buffer))
        self._tag_stack.pop()
        self._buffer = []

        if tag == "title" and not self.title:
            self.title = text
        elif tag == "h1" and not self.heading:
            self.heading = text
        elif tag == "p" and not self.paragraph and len(text) > 30:
            self.paragraph = text


def clean_text(value):
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def title_from_filename(path):
    stem = path.stem.replace("_", " ").replace("-", " ")
    return " ".join(word.capitalize() for word in stem.split())


def infer_demo(path):
    parser = DemoTextParser()
    parser.feed(path.read_text(encoding="utf-8"))

    title = parser.heading or parser.title or title_from_filename(path)
    title = re.sub(r"\s*\|\s*Cynapsa$", "", title)
    title = re.sub(r"^Cynapsa:\s*", "", title)
    title = re.sub(r"^Cynapsa Use Case:\s*", "", title)

    description = parser.paragraph or (
        "Interactive Cynapsa demo page. Open it to explore the scenario and compare the legacy networking behavior with the Cynapsa approach."
    )

    return {
        "eyebrow": "New demo",
        "title": title,
        "description": description,
    }


def get_demos():
    html_files = [
        path for path in ROOT.glob("*.html")
        if path.name != "index.html"
    ]
    known_names = [name for name in DEMO_ORDER if (ROOT / name).exists()]
    new_names = sorted(path.name for path in html_files if path.name not in DEMO_ORDER)

    demos = []
    for name in [*known_names, *new_names]:
        path = ROOT / name
        data = DEMO_OVERRIDES.get(name, infer_demo(path))
        demos.append({"filename": name, **data})

    return demos


def card_html(demo, index):
    number = f"{index:02d}"
    filename = escape(demo["filename"])
    eyebrow = escape(demo["eyebrow"])
    title = escape(demo["title"])
    description = escape(demo["description"])

    return f"""                <a href="./{filename}" class="group rounded-lg border border-slate-700 bg-slate-900/75 p-5 transition hover:-translate-y-0.5 hover:border-cyan-400 hover:bg-slate-900 focus:outline-none focus:ring-2 focus:ring-cyan-400">
                    <div class="mb-4 flex items-start justify-between gap-4">
                        <div>
                            <p class="text-xs font-semibold uppercase tracking-[0.2em] text-cyan-300">{eyebrow}</p>
                            <h3 class="mt-2 text-xl font-semibold text-white">{title}</h3>
                        </div>
                        <span class="rounded border border-cyan-400/40 px-2 py-1 text-xs font-bold text-cyan-200">{number}</span>
                    </div>
                    <p class="text-sm leading-6 text-slate-300">
                        {description}
                    </p>
                    <span class="mt-5 inline-flex text-sm font-semibold text-cyan-300 group-hover:text-cyan-200">Open {filename}</span>
                </a>"""


def render_index(demos):
    cards = "\n\n".join(card_html(demo, index) for index, demo in enumerate(demos, start=1))
    demo_count = len(demos)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cynapsa Public Web Demos</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        :root {{
            color-scheme: dark;
        }}

        body {{
            background:
                radial-gradient(circle at top left, rgba(34, 211, 238, 0.18), transparent 34rem),
                radial-gradient(circle at bottom right, rgba(168, 85, 247, 0.12), transparent 30rem),
                #050811;
        }}

        .mesh-line {{
            background-image:
                linear-gradient(rgba(148, 163, 184, 0.08) 1px, transparent 1px),
                linear-gradient(90deg, rgba(148, 163, 184, 0.08) 1px, transparent 1px);
            background-size: 34px 34px;
            mask-image: linear-gradient(to bottom, black, transparent);
        }}
    </style>
</head>
<body class="min-h-screen text-slate-200 font-sans">
    <div class="mesh-line fixed inset-0 pointer-events-none"></div>

    <main class="relative mx-auto max-w-7xl px-5 py-8 sm:px-8 lg:px-10 lg:py-12">
        <header class="mb-10 grid gap-8 lg:grid-cols-[1.05fr_0.95fr] lg:items-end">
            <div>
                <p class="mb-4 text-xs font-bold uppercase tracking-[0.28em] text-cyan-300">Cynapsa public web</p>
                <h1 class="max-w-3xl text-4xl font-bold tracking-tight text-white sm:text-5xl lg:text-6xl">
                    Interactive demos for agentic networking.
                </h1>
                <p class="mt-5 max-w-2xl text-base leading-7 text-slate-300 sm:text-lg">
                    This repo contains standalone HTML demos that explain why enterprise agentic AI needs secure, identity-aware networking. Each page compares legacy network patterns against Cynapsa concepts such as portless mesh connectivity, local agents, identity-based routing, and microsegmentation.
                </p>
            </div>

            <section class="rounded-lg border border-slate-700 bg-slate-900/70 p-5 shadow-2xl shadow-cyan-950/20 backdrop-blur">
                <h2 class="text-sm font-semibold uppercase tracking-[0.2em] text-slate-400">How to use this index</h2>
                <p class="mt-3 text-sm leading-6 text-slate-300">
                    Open a demo, use its sidebar controls, and compare the failure mode with the Cynapsa approach. The pages are static, so they can run directly in a browser without a build step.
                </p>
                <div class="mt-5 grid grid-cols-3 gap-3 text-center text-xs text-slate-400">
                    <div class="rounded border border-slate-700 bg-slate-950/70 p-3">
                        <div class="text-lg font-bold text-cyan-300">{demo_count}</div>
                        demos
                    </div>
                    <div class="rounded border border-slate-700 bg-slate-950/70 p-3">
                        <div class="text-lg font-bold text-cyan-300">0</div>
                        build steps
                    </div>
                    <div class="rounded border border-slate-700 bg-slate-950/70 p-3">
                        <div class="text-lg font-bold text-cyan-300">HTML</div>
                        only
                    </div>
                </div>
            </section>
        </header>

        <section aria-labelledby="demo-list-title">
            <div class="mb-5 flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
                <div>
                    <p class="text-xs font-bold uppercase tracking-[0.24em] text-cyan-300">Demo map</p>
                    <h2 id="demo-list-title" class="mt-2 text-2xl font-semibold text-white">Choose a walkthrough</h2>
                </div>
                <p class="max-w-xl text-sm text-slate-400">
                    The suggested order starts with the broad agentic networking story, then moves into specific security, privacy, routing, and blast-radius scenarios.
                </p>
            </div>

            <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
{cards}
            </div>
        </section>
    </main>
</body>
</html>
"""


def main():
    INDEX_PATH.write_text(render_index(get_demos()), encoding="utf-8")


if __name__ == "__main__":
    main()

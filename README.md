# AEO Analyzer ERA — Linux Edition
### by SA Era

> **SEO · AEO · Crawl · Rank Prediction · E-E-A-T · NLP · Structured Data**
> Built for Kali Linux & all Debian-based systems

A powerful multi-layer website analysis tool for SEO professionals. Runs as a **rich terminal CLI** or a **modern desktop GUI** — both included.

---

## Features

| Layer | What It Analyzes |
|---|---|
| 📡 **Page Crawl** | Title, meta, headings, word count, links, images, schema types |
| 🔍 **SEO Analysis** | Title length, meta desc, keyword density, alt tags, readability (Flesch) |
| 🤖 **AEO Analysis** | Question headings, FAQ sections, short answers, NLP entities |
| 🧠 **E-E-A-T Signals** | Author byline, publish date, citations, expertise language |
| 🏆 **Rank Prediction** | Weighted score across all signals with priority action list |

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/Sa-era/aeo-analyzer-era-linux.git
cd aeo-analyzer-era-linux

# 2. Install (one time only)
bash install.sh

# 3. Launch GUI
bash run_gui.sh

<img width="940" height="527" alt="image" src="https://github.com/user-attachments/assets/71027e03-49f0-4b7b-a377-57f75f47a9cf" />


# 4. Or launch CLI
bash run_cli.sh

<img width="940" height="503" alt="image" src="https://github.com/user-attachments/assets/b36d89b5-1cbd-4112-a3fd-3751bb1ffb3d" />


```

---

## Files

```
aeo-analyzer-era-linux/
│
├── aeo_analyzer_gui.py   ← Desktop GUI (Flet)
├── aeo_analyzer_era.py   ← Terminal CLI (Rich)
│
├── install.sh            ← One-time setup (creates venv, installs packages)
├── run_gui.sh            ← Launch GUI
├── run_cli.sh            ← Launch CLI
│
├── requirements.txt      ← Python dependencies
├── reports/              ← JSON reports saved here after analysis
├── exports/              ← Export files
└── assets/               ← Assets
```

---

## Requirements

- Python 3.9+
- Kali Linux / Ubuntu / Debian (any distro with Python 3)

| Package | Purpose |
|---|---|
| `requests` | HTTP crawling |
| `beautifulsoup4` + `lxml` | HTML parsing |
| `rich` | CLI terminal output |
| `textstat` | Readability scoring |
| `flet` + `flet-desktop` | GUI framework |

---

## Optional: spaCy NLP

For named entity recognition in AEO analysis:

```bash
source venv/bin/activate
pip install spacy
python3 -m spacy download en_core_web_sm
```

---

## How to Use

### GUI Mode
1. Run `bash run_gui.sh`
2. Enter a **Target URL**
3. (Optional) Enter a **Target Keyword**
4. Set **Backlink Score** (0–100, default 50)
5. Click **Analyze** — results appear across 4 tabs
6. Click **Save JSON Report** to export results

### CLI Mode
1. Run `bash run_cli.sh`
2. Follow the prompts in the terminal

---

## Troubleshooting

**Permission denied on venv:**
```bash
sudo rm -rf venv
bash install.sh
```

**flet-desktop not found:**
```bash
source venv/bin/activate
pip install flet-desktop
```

**Timeout error (site too slow):**
> The target website is blocking bots or responding too slowly. Try a different URL.

---

## Rank Score Formula

```
Rank Score = SEO × 0.35 + AEO × 0.35 + Backlinks × 0.15 + Content Depth × 0.15
```

| Score | Result |
|---|---|
| 90–100 | 🟢 HIGH — Strong ranking potential |
| 70–89 | 🟡 MEDIUM — Moderate ranking potential |
| 0–69 | 🔴 LOW — Needs significant improvement |

---

## License

MIT — free to use and modify.

---

**Built by SA Era** · Linux Edition

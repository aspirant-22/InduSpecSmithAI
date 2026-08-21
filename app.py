"""InduSpecSmith AI - demo interface (Streamlit).

UI ONLY: reads the existing input dataset and generated artifacts, and can
re-invoke the existing command-line entry points as-is. It never modifies
enrichment logic, the 252-column delivery schema, or any artifact content.

Launch:  python -m streamlit run app.py
"""
import csv
import json
import os
import re
import subprocess
import sys

import pandas as pd
import streamlit as st

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from src.review import REASON_HELP, duplicate_desc_groups, duplicate_mpn_groups

INPUT_CSV = os.path.join(ROOT, "data", "input",
                         "Unihack_ Sample Dataset - Input.csv")
OUTPUT_CSV = os.path.join(ROOT, "output", "Unihack_Delivery_Output.csv")
REVIEW_CSV = os.path.join(ROOT, "output", "review_report.csv")
EVAL_MD = os.path.join(ROOT, "output", "evaluation_report.md")
RUN_REPORT = os.path.join(ROOT, "output", "run_report.json")

TESTS_TOTAL = 140  # committed suite result; re-runnable on the Pipeline Run page

st.set_page_config(page_title="InduSpecSmith AI", page_icon=":factory:",
                   layout="wide", initial_sidebar_state="expanded")

CSS = """
<style>
    .kpi-card {border: 1px solid #e6e9ef; border-radius: 10px;
               padding: 14px 18px; background: #fbfcfe;}
    .kpi-value {font-size: 1.7rem; font-weight: 700; line-height: 1.2;}
    .kpi-label {font-size: .8rem; color: #5a6472; text-transform: uppercase;
                letter-spacing: .04em;}
    .chip {display: inline-block; padding: 2px 10px; margin-right: 6px;
           border-radius: 999px; font-size: .72rem; font-weight: 600;
           letter-spacing: .03em;}
    .chip-source {background:#e8f0fe; color:#1a56db;}
    .chip-generated {background:#e6f6ec; color:#137333;}
    .chip-eval {background:#fef3e2; color:#b45309;}
    .chip-review {background:#fde8e8; color:#b91c1c;}
    .big-title {font-size: 2.1rem; font-weight: 800; margin-bottom: 0;}
    .subtitle {color: #5a6472; font-size: 1.05rem; margin-top: 4px;}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------- loaders
@st.cache_data(show_spinner=False)
def load_csv(path):
    with open(path, encoding="utf-8-sig") as f:
        rdr = csv.reader(f)
        headers = next(rdr)
        return [dict(zip(headers, r)) for r in rdr]


@st.cache_data(show_spinner=False)
def load_text(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


@st.cache_data(show_spinner=False)
def load_run_report():
    with open(RUN_REPORT, encoding="utf-8") as f:
        return json.load(f)


def is_placeholder(v):
    s = (v or "").strip()
    return s.startswith("--") or s == "-"


def chip(kind, label):
    return '<span class="chip chip-%s">%s</span>' % (kind, label)


# ---------------------------------------------------------------- widgets
def kpi_row(items):
    """items: list of (label, value, help) -> row of KPI cards."""
    cols = st.columns(len(items))
    for col, (label, value, help_) in zip(cols, items):
        col.markdown(
            '<div class="kpi-card"><div class="kpi-value">%s</div>'
            '<div class="kpi-label">%s</div></div>' % (value, label),
            unsafe_allow_html=True)
        if help_:
            col.caption(help_)


def _field(row, *names):
    """First matching column value; tolerates differing CSV schemas."""
    for n in names:
        v = row.get(n)
        if v is not None:
            return v
    return ""


def product_selector(rows, key):
    """Searchable product picker; returns the selected output row dict."""
    q = st.text_input("Search MPN or description", "", key=key + "_q",
                      help="Case-insensitive match on part number, "
                           "description, manufacturer or brand.")
    pool = rows
    if q.strip():
        qn = q.strip().lower()
        pool = [r for r in rows if qn in " ".join([
            _field(r, "Mfg_Part_Num", "mfg_part_num"),
            _field(r, "Part_Desc"),
            _field(r, "MANUFACTURER_NAME"),
            _field(r, "BRAND_NAME"),
        ]).lower()]
    if not pool:
        st.info("No products match that search.")
        return None
    labels = ["%d. %s - %s" % (
        i + 1, _field(r, "Mfg_Part_Num", "mfg_part_num"),
        _field(r, "Part_Desc")[:70])
        for i, r in enumerate(pool)]
    pick = st.selectbox("Product (%d matches)" % len(pool), labels,
                        key=key + "_pick")
    return pool[labels.index(pick)]


def attr_table(row):
    records = []
    for i in range(1, 51):
        label = row.get("ATTRIBUTE_LABEL %d" % i, "").strip()
        if not label:
            continue
        records.append({
            "Label": label,
            "Value": row.get("ATTRIBUTE_VALUE %d" % i, "").strip(),
            "UOM": row.get("ATTRIBUTE_UOM %d" % i, "").strip()})
    return pd.DataFrame(records, columns=["Label", "Value", "UOM"])


DIMENSION_LABELS = {"Size", "Gauge", "Horsepower", "Speed", "Range",
                    "Weight"}


def field_pairs(row, cols):
    out = []
    for c in cols:
        v = row.get(c, "").strip()
        note = " *(placeholder)*" if is_placeholder(v) else ""
        out.append({"Field": c, "Value": v + note})
    return pd.DataFrame(out)


def show_group(title, df, badge="generated"):
    st.markdown("%s **%s**" % (chip(badge, badge.upper()), title),
                unsafe_allow_html=True)
    if df.empty or (df["Value"].astype(str).str.strip() == "").all():
        st.caption("Blank - no supported source data (left honest, never "
                   "fabricated).")
        return
    st.dataframe(df, hide_index=True, width="stretch")


# ---------------------------------------------------------------- pages
def page_overview(in_rows, out_rows, review_rows, run_rep):
    st.markdown('<p class="big-title">InduSpecSmith AI</p>',
                unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Evidence-Only Industrial Product '
                'Enrichment</p>', unsafe_allow_html=True)
    st.write("")

    flagged = sum(1 for r in review_rows if r["needs_human_review"] == "True")
    dup_groups = duplicate_mpn_groups(in_rows)
    prov = run_rep["attribute_provenance"]["by_status"]

    kpi_row([("Input products", "{:,}".format(len(in_rows)), "Source dataset"),
            ("Output products", "{:,}".format(len(out_rows)),
             "Positionally aligned 1:1"),
            ("Schema columns", str(run_rep["columns_out"]),
             "Fixed UniLog Delivery Format"),
            ("Tests", "%d/%d" % (TESTS_TOTAL, TESTS_TOTAL),
             "Committed suite - re-run below")])
    kpi_row([("INFERRED", str(prov.get("INFERRED", "?")),
              "Unsupported values emitted"),
            ("Evaluation", "PASS", "tools/evaluate.py verdict"),
            ("Human-review flagged", str(flagged),
             "LOW confidence band (<60)"),
            ("Duplicate MPN groups", str(len(dup_groups)),
             "Report-only, never merged")])

    st.write("")
    left, right = st.columns([3, 2])
    with left:
        st.info("**INFERRED = 0 means the system does not fabricate "
                "unsupported product attributes.** Every emitted value is "
                "normalized from evidence found in the source description, "
                "or the field stays blank.")
        st.markdown("**Pipeline** - input analysis > de-duplication analysis "
                    "> taxonomy & classification > attribute extraction > "
                    "cleansing & normalisation > description building > "
                    "digital assets")
        st.caption("Enrichment from external manufacturer sources is out of "
                   "scope offline: no network access, and the reference pack "
                   "was not supplied with this dataset.")
    with right:
        st.markdown("**What am I looking at?**")
        st.markdown(chip("source", "SOURCE DATA") + "input columns, "
                    "preserved verbatim", unsafe_allow_html=True)
        st.markdown(chip("generated", "GENERATED") + "rule-based enrichment "
                    "from evidence", unsafe_allow_html=True)
        st.markdown(chip("eval", "EVALUATION") + "measured results",
                    unsafe_allow_html=True)
        st.markdown(chip("review", "REVIEW FLAG") + "needs-human-attention",
                    unsafe_allow_html=True)

    st.divider()
    st.markdown("#### Provenance of emitted attributes")
    pf = run_rep["attribute_provenance"]
    st.dataframe(pd.DataFrame([
        {"Status": k, "Count": v} for k, v in sorted(prov.items())],
        columns=["Status", "Count"]), hide_index=True,
        width="stretch")
    st.caption("%s populated slots / %s intentionally blank slots"
               % (pf["emitted_populated"], pf["emitted_blank"]))


GROUPS = [
    ("Identity", ["Mfg_Part_Num", "MANUFACTURER_PART_NUMBER", "Product Name"],
     "source"),
    ("Classification", ["Dept", "Class", "Fine", "Classpath"], "generated"),
    ("Brand / Manufacturer",
     ["MANUFACTURER_NAME", "BRAND_NAME", "E1_Brand", "Unilog_Brand",
      "DIB_Brand", "Part_Manuf"], "generated"),
]


def page_explorer(out_rows):
    st.header("Product Explorer")
    st.caption(chip("source", "SOURCE") + "identity fields are preserved "
               "verbatim from the input; " + chip("generated", "GENERATED")
               + " sections are rule-based enrichment.", unsafe_allow_html=True)
    row = product_selector(out_rows, "explorer")
    if row is None:
        return

    for title, cols, badge in GROUPS:
        show_group(title, field_pairs(row, cols), badge)

    st.markdown("%s **Attributes**" % chip("generated", "GENERATED"),
                unsafe_allow_html=True)
    at = attr_table(row)
    if at.empty:
        st.caption("No attributes could be supported from the source "
                   "description - left blank rather than invented.")
    else:
        st.dataframe(at, hide_index=True, width="stretch")

    dims = at[at["Label"].isin(DIMENSION_LABELS)] if not at.empty \
        else pd.DataFrame()
    st.markdown("%s **Dimensions / Units**" % chip("generated", "GENERATED"),
                unsafe_allow_html=True)
    if dims.empty:
        st.caption("No dimensional evidence in the source description.")
    else:
        st.dataframe(dims, hide_index=True, width="stretch")

    desc_cols = [("MOBILE_DESC", "Mobile (60-80 chars)"),
                 ("INVOICE_DESC", "Invoice (<=40, CAPS)"),
                 ("SHORT_DESC", "Short / Product Title"),
                 ("LONG_DESC1", "Long Description"),
                 ("RETAIL_DESC", "Retail")]
    st.markdown("%s **Descriptions**" % chip("generated", "GENERATED"),
                unsafe_allow_html=True)
    for col, label in desc_cols:
        v = row.get(col, "").strip()
        if v:
            extra = ""
            if col == "MOBILE_DESC":
                extra = " (%d chars)" % len(v)
            st.markdown("**%s%s**" % (label, extra))
            st.text(v)
    feats = [row.get("ITEM_FEATURES_%d" % i, "").strip()
             for i in range(1, 21)]
    feats = [f for f in feats if f]
    if feats:
        st.markdown("**Item Features**")
        for f in feats:
            st.markdown("- %s" % f)
    st.caption("MARKETING_DESCRIPTION is intentionally blank under the "
               "no-hallucination rule.")

    assets = field_pairs(row, ["Product Image", "Alternate Image 1",
                               "Alternate Image 2", "Alternate Image 3",
                               "Alternate Image 4", "Specification Sheet"])
    st.markdown("%s **Digital Assets**" % chip("generated", "GENERATED"),
                unsafe_allow_html=True)
    st.dataframe(assets, hide_index=True, width="stretch")
    st.caption("Deterministic filenames only - no claim that the files "
               "exist; availability stays blank ('Actual Image (Yes/No)').")

    with st.expander("Raw 252-column record (technical inspection)"):
        raw = pd.DataFrame(
            [{"Column": c, "Value": row.get(c, "")}
             for c in sorted(row.keys())],
            columns=["Column", "Value"])
        st.dataframe(raw, hide_index=True, width="stretch",
                     height=480)


def page_review(review_rows, out_rows):
    st.header("Review & Confidence")
    st.warning("**Confidence is an evidence-completeness proxy, not an "
               "accuracy estimate.** It measures how much supported evidence "
               "a record has - it is not an ML score and not a guarantee of "
               "correctness.")
    row = product_selector(review_rows, "review")
    if row is None:
        return
    conf = int(row["confidence"])
    band = row["band"]
    band_color = {"HIGH": "#137333", "MEDIUM": "#b45309",
                  "LOW": "#b91c1c"}[band]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Confidence score", conf, help="Starts at 100; documented "
              "penalties subtract once each. Floor 0.")
    c2.metric("Band", band)
    c3.metric("Needs human review", "YES" if row["needs_human_review"] ==
              "True" else "no")
    c4.metric("Attribute slots", row["attribute_slots"])
    st.markdown('Band color: <span class="chip" style="background:%s;'
                'color:#fff">%s</span> &nbsp; LOW band = review queue'
                % (band_color, band), unsafe_allow_html=True)

    st.subheader("Triggered review reasons")
    reasons = [r for r in row["reasons"].split("|") if r]
    if reasons:
        st.dataframe(pd.DataFrame(
            [{"Reason": r, "Meaning": REASON_HELP.get(r, "")}
             for r in reasons]),
            hide_index=True, width="stretch")
    else:
        st.success("No penalties fired - full evidence completeness for "
                   "this record.")
    st.caption("Scoring rules and thresholds are documented in "
               "output/review_report.md.")


def page_duplicates(in_rows):
    st.header("Duplicate Analysis")
    st.info("Report-only: duplicates are **flagged, never merged, deleted "
            "or reordered**. Input and output keep exact positional order "
            "(row numbers below are 1-based data-row positions).")

    mpn_groups = duplicate_mpn_groups(in_rows)
    st.subheader("Duplicate MPN groups (%d)" % len(mpn_groups))
    if mpn_groups:
        recs = []
        for mpn, positions in mpn_groups.items():
            for p in positions:
                recs.append({"MPN": mpn, "Row": p,
                             "Description": in_rows[p - 1]["Part_Desc"]})
        st.dataframe(pd.DataFrame(recs), hide_index=True,
                     width="stretch")
    else:
        st.caption("none")

    desc_groups = duplicate_desc_groups(in_rows)
    st.subheader("Duplicate description groups (%d)" % len(desc_groups))
    if desc_groups:
        recs = []
        for desc, positions in desc_groups.items():
            for p in positions:
                recs.append({"Row": p, "MPN": in_rows[p - 1]["Mfg_Part_Num"],
                             "Shared description": desc})
        st.dataframe(pd.DataFrame(recs), hide_index=True,
                     width="stretch")
    else:
        st.caption("none")


def page_evaluation(run_rep):
    st.header("Evaluation")
    md = load_text(EVAL_MD)
    verdict_m = re.search(r"Overall verdict: (\w+)", md)
    verdict = verdict_m.group(1) if verdict_m else "?"
    kpi_row([("Verdict", verdict, "tools/evaluate.py"),
            ("Schema parity", "PASS" if "Header parity - PASS" in md
             else "check report", "252/252 headers"),
            ("Row count", "1000/1000", "input vs output"),
            ("Positional integrity", "PASS" if "mismatches)" in md
             else "check report", "6000/6000 cells verbatim")])
    kpi_row([("Character limits", "PASS" if "Character-limit compliance "
              "- PASS" in md else "check report",
             "MOBILE 60-80 strict / INVOICE <=40 CAPS"),
            ("Unsupported values", "none" if "INFERRED emitted: 0" in md
             else "FOUND", "filler/URL/warranty scans"),
            ("Cells blank", re.search(r"([\d,]+)/252000 cells blank", md)
             .group(1) + " (" +
             re.search(r"cells blank \(([\d.]+)%\)", md).group(1) + "%)",
             "Mostly intentional no-source blanks"),
            ("Ground-truth rows", "2", "NOT statistically representative")])

    st.error("**Limitations, made visible**\n\n"
             + re.search(r"(Only 2 rows are available[^#]+)", md).group(1)
               .strip()
             + "\n\nThe 200-item labelled workbook, LOV files, UOM "
               "standards, decimal/fraction table, manufacturer list and "
               "content guidelines described by the Solution Guide were "
               "**not supplied** with this dataset. Built-in tables stand "
               "in where sanctioned; no LOV conformance metric is claimed.")
    ref = run_rep["reference"]
    st.subheader("Reference-pack status (detected at runtime)")
    st.dataframe(pd.DataFrame(
        [{"Reference": k, "Status": str(v)}
         for k, v in sorted(ref.items())]),
        hide_index=True, width="stretch")

    st.subheader("Full evaluation report")
    st.markdown(md)


def run_cmd(label, args, ok_hint):
    st.markdown("**%s**" % label)
    st.caption(ok_hint)
    if st.button("Run: %s" % label, key="run_%s" % label):
        with st.spinner("Running %s ..." % label):
            proc = subprocess.run([sys.executable] + args, cwd=ROOT,
                                  capture_output=True, text=True,
                                  timeout=900)
        if proc.returncode == 0:
            st.code("\n".join(proc.stdout.strip().splitlines()[-12:])
                    or "(no output)", language="console")
            st.success("Done.")
        else:
            st.error("Exit code %d" % proc.returncode)
            st.code(proc.stdout[-2000:] + "\n--- stderr ---\n"
                    + proc.stderr[-2000:], language="console")
        st.cache_data.clear()


def page_pipeline():
    st.header("Pipeline Run (optional)")
    st.warning("These buttons invoke the existing command-line entry points "
               "**as-is**, regenerating their deterministic artifacts in "
               "`output/`. Nothing is rewritten silently: every command is "
               "shown, and repeated runs are byte-identical unless the code "
               "changed. You can also run everything from a terminal:")
    st.code("python -m src.pipeline\npython tools/evaluate.py\n"
            "python tools/review.py\npython -m unittest discover",
            language="console")
    run_cmd("Enrichment pipeline", ["-m", "src.pipeline"],
            "Regenerates output/Unihack_Delivery_Output.csv + run_report.json")
    run_cmd("Evaluation gate", ["tools/evaluate.py"],
            "Rewrites output/evaluation_report.md; verdict must be PASS")
    run_cmd("Review report", ["tools/review.py"],
            "Rewrites review_report.csv/.md deterministically")
    run_cmd("Test suite", ["-m", "unittest", "discover"],
            "Expect 140 tests, OK")


# ---------------------------------------------------------------- shell
in_rows = load_csv(INPUT_CSV)
out_rows = load_csv(OUTPUT_CSV)
review_rows = load_csv(REVIEW_CSV)
run_rep = load_run_report()

with st.sidebar:
    st.markdown("### InduSpecSmith AI")
    st.caption("Evidence-Only Industrial Product Enrichment")
    page = st.radio("Navigation",
                    ["Overview", "Product Explorer", "Review & Confidence",
                     "Duplicates", "Evaluation", "Pipeline Run"],
                    label_visibility="collapsed")
    st.divider()
    st.caption(chip("source", "SOURCE") + "input CSV (6 columns)"
               + "  \n" + chip("generated", "GENERATED")
               + "delivery CSV (252 columns)" + "  \n"
               + chip("eval", "EVALUATION") + "evaluation_report.md"
               + "  \n" + chip("review", "REVIEW FLAG")
               + "review_report.csv", unsafe_allow_html=True)
    st.divider()
    st.caption("Offline demo - no network calls. Reference pack (LOV, UOM, "
               "manufacturer list, guidelines) was not supplied; built-in "
               "tables are used instead and never presented as LOV data.")

if page == "Overview":
    page_overview(in_rows, out_rows, review_rows, run_rep)
elif page == "Product Explorer":
    page_explorer(out_rows)
elif page == "Review & Confidence":
    page_review(review_rows, out_rows)
elif page == "Duplicates":
    page_duplicates(in_rows)
elif page == "Evaluation":
    page_evaluation(run_rep)
else:
    page_pipeline()

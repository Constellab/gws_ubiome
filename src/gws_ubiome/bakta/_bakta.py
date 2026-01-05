#!/usr/bin/env python3

import os
import subprocess
import sys
from pathlib import Path

# Same mapping as the Task
TRANSLATION_TABLE_MAP = {
    "The Bacterial, Archaeal and Plant Plastid Code": "11",
    "The Mold, Protozoan, and Coelenterate Mitochondrial Code and the Mycoplasma/Spiroplasma Code": "4",
    "The Alternative Yeast Nuclear Code": "25",
}

def as_bool(x: str) -> bool:
    return str(x).strip().lower() in {"1", "true", "yes", "y"}

def ensure_file_exists(p: str, label: str):
    if p and not Path(p).is_file():
        print(f"[ERROR] {label} not found: {p}", flush=True)
        sys.exit(1)

def ensure_dir_exists(p: str, label: str):
    if not Path(p).is_dir():
        print(f"[ERROR] {label} not found: {p}", flush=True)
        sys.exit(1)

def _tt_to_code(s: str) -> str:
    """Accept either descriptive label or numeric code; default to '11'."""
    if not s:
        return "11"
    s = s.strip()
    if s in {"11", "4", "25"}:
        return s
    return TRANSLATION_TABLE_MAP.get(s, "11")

def _read_fasta_lengths(fp: Path) -> list[tuple[str, int]]:
    ids_lengths = []
    cur_id = None
    cur_len = 0
    with fp.open("rt", encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            if not line:
                continue
            if line.startswith(">"):
                if cur_id is not None:
                    ids_lengths.append((cur_id, cur_len))
                cur_id = line[1:].strip().split()[0]
                cur_len = 0
            else:
                cur_len += len(line.strip())
        if cur_id is not None:
            ids_lengths.append((cur_id, cur_len))
    return ids_lengths

def _write_replicons_for_all(
    fasta_path: Path, out_dir: Path, replicon_type: str | None, replicon_topology: str | None
) -> Path | None:
    rtype = (replicon_type or "").strip().lower()
    rtopo = (replicon_topology or "").strip().lower()
    if not rtype and not rtopo:
        return None
    if rtype and rtype not in {"chromosome", "plasmid"}:
        print(f"[WARN] Unknown replicon type '{rtype}', ignoring.")
        rtype = ""
    if rtopo and rtopo not in {"circular", "linear"}:
        print(f"[WARN] Unknown replicon topology '{rtopo}', ignoring.")
        rtopo = ""
    if not rtype and not rtopo:
        return None

    rows = _read_fasta_lengths(Path(fasta_path))
    if not rows:
        print("[WARN] No contigs found to build replicons.tsv")
        return None

    tsv = out_dir / "replicons_all.tsv"
    with tsv.open("wt", encoding="utf-8") as w:
        w.write("original_id\tlength\tnew_id\ttype\ttopology\tname\n")
        for cid, clen in rows:
            w.write(f"{cid}\t{clen}\t{cid}\t{rtype}\t{rtopo}\t\n")
    return tsv

def main():
    try:
        genome_fasta       = sys.argv[1]
        db_dir             = sys.argv[2]
        output_dir         = sys.argv[3]
        prefix             = sys.argv[4]
        min_contig_len     = int(sys.argv[5])
        threads            = int(sys.argv[6])
        complete_genome    = as_bool(sys.argv[7])
        keep_headers       = as_bool(sys.argv[8])
        compliant          = as_bool(sys.argv[9])

        translation_table_in = (sys.argv[10] if len(sys.argv) > 10 else "The Bacterial, Archaeal and Plant Plastid Code").strip()
        gram               = (sys.argv[11] if len(sys.argv) > 11 else "?").strip()

        genus              = (sys.argv[12] if len(sys.argv) > 12 else "").strip()
        species            = (sys.argv[13] if len(sys.argv) > 13 else "").strip()
        strain             = (sys.argv[14] if len(sys.argv) > 14 else "").strip()

        # Optional locus fields (kept for backward-compatibility)
        locus_prefix       = (sys.argv[15] if len(sys.argv) > 15 else "").strip()
        locus_tag_prefix   = (sys.argv[16] if len(sys.argv) > 16 else "").strip()

        force_overwrite    = as_bool(sys.argv[17]) if len(sys.argv) > 17 else False

        # NEW: optional global replicon metadata
        replicon_type      = (sys.argv[18] if len(sys.argv) > 18 else "").strip()
        replicon_topology  = (sys.argv[19] if len(sys.argv) > 19 else "").strip()

    except Exception as e:
        print(f"[ERROR] argument parsing failed: {e}", flush=True)
        sys.exit(2)

    ensure_file_exists(genome_fasta, "Input FASTA")
    ensure_dir_exists(db_dir, "Bakta database folder")
    os.makedirs(output_dir, exist_ok=True)

    if compliant and min_contig_len < 200:
        print(f"[INFO] INSDC compliant: raising min_contig_len from {min_contig_len} to 200", flush=True)
        min_contig_len = 200

    tt = _tt_to_code(translation_table_in)

    if gram not in {"+", "-", "?"}:
        print(f"[WARN] Invalid gram '{gram}', using '?'")
        gram = "?"

    # Build replicons file if Type/Topology provided
    replicons_path = _write_replicons_for_all(
        Path(genome_fasta), Path(output_dir), replicon_type, replicon_topology
    )

    cmd = [
        "bakta",
        "--db", db_dir,
        "--output", output_dir,
        "--prefix", prefix,
        "--min-contig-length", str(min_contig_len),
        "--threads", str(threads),
        "--translation-table", tt,
        "--gram", gram
    ]

    if genus:  cmd += ["--genus", genus]
    if species:cmd += ["--species", species]
    if strain: cmd += ["--strain", strain]

    if locus_prefix:     cmd += ["--locus", locus_prefix]
    if locus_tag_prefix: cmd += ["--locus-tag", locus_tag_prefix]

    if replicons_path:
        cmd += ["--replicons", str(replicons_path)]

    if complete_genome: cmd.append("--complete")
    if keep_headers:    cmd.append("--keep-contig-headers")
    if compliant:       cmd.append("--compliant")
    if force_overwrite: cmd.append("--force")

    cmd.append(genome_fasta)

    print("[INFO] Running:", " ".join(cmd), flush=True)

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] bakta failed: {e}", flush=True)
        sys.exit(1)

    expected_any = [
        f"{prefix}.gff3", f"{prefix}.gbff", f"{prefix}.embl",
        f"{prefix}.tsv", f"{prefix}.json",
        f"{prefix}.faa", f"{prefix}.ffn",
        f"{prefix}.png", f"{prefix}.svg"
    ]
    if not any((Path(output_dir) / x).exists() for x in expected_any):
        print("[WARN] No standard Bakta outputs found. Check logs & parameters.", flush=True)

    print(f"[INFO] Bakta outputs in: {output_dir}", flush=True)

if __name__ == "__main__":
    main()

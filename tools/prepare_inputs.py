"""Use immutable inputs only: the committed official snapshot EXE and the upstream 2.14 donor."""
from pathlib import Path
import hashlib, io, json, urllib.parse, urllib.request, zipfile

import dnfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build-inputs"
OUT.mkdir(exist_ok=True)

# The donor supplies the file-picker body that the official snapshot compiles away.
DONOR_COMMIT = "5ef81e490ae46b1100d61e33d0183094c7a80ca8"
DONOR_HASH = "5582952ded3b443503f66c23b810802bd20f1a3e847b54d9e09653a825859a36"
# Official PCL 2.99.0.0 snapshot (build 414), committed as input/official-snapshot.exe.
SNAPSHOT_HASH = "5b64d6d540c376390470cea3ab99d47661e8bca81be2ba647ea83e7d2e9428fa"


def write_input(filename: str, data: bytes, expected: str) -> dict:
    actual = hashlib.sha256(data).hexdigest()
    if actual != expected:
        raise RuntimeError(f"Input checksum mismatch: {filename}: {actual}")
    (OUT / filename).write_bytes(data)
    return {"file": filename, "sha256": actual, "size": len(data)}


def donor_from_upstream() -> bytes:
    url = f"https://raw.githubusercontent.com/Meloong-Git/PCL/{DONOR_COMMIT}/" + urllib.parse.quote("最新正式版.zip")
    with urllib.request.urlopen(url, timeout=60) as response:
        raw = response.read()
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        names = [name for name in archive.namelist() if name.lower().endswith(".exe")]
        if len(names) != 1:
            raise RuntimeError("Unexpected upstream archive contents")
        return archive.read(names[0])


inputs = [
    write_input("original.exe", (ROOT / "input" / "official-snapshot.exe").read_bytes(), SNAPSHOT_HASH),
    write_input("donor-2.14.exe", donor_from_upstream(), DONOR_HASH),
]

# Cecil needs enum definitions from the original embedded dependencies when it serializes
# optional-parameter constants. Parse resources without executing them.
pe = dnfile.dnPE(str(OUT / "original.exe"))
for resource in pe.net.resources:
    for entry in resource.data.entries:
        data = entry.value
        if not isinstance(data, bytes) or not data.startswith(b"MZ"):
            continue
        embedded = dnfile.dnPE(data=data)
        if embedded.net is None:
            continue
        name = str(entry.name) + ".dll"
        if Path(name).name != name:
            raise RuntimeError("Unexpected embedded assembly resource name")
        (OUT / name).write_bytes(data)

(OUT / "inputs.json").write_text(json.dumps(inputs, indent=2), encoding="utf-8")
print(json.dumps(inputs, indent=2))

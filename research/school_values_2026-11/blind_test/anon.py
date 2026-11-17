import re, sys, random, pathlib, json
V = pathlib.Path(sys.argv[1]); out = pathlib.Path(sys.argv[2])
SL = ['harvard','yale','princeton','stanford','mit','caltech','penn','columbia','uchicago','brown','cornell','duke','northwestern','dartmouth','cmu']
def sec(t, name):
    m = re.search(r"^## " + name + r"\s*\n(.*?)(?=^## |\Z)", t, re.S | re.M); return m.group(1) if m else ""
terms, quotes = set(), {}
EXTRA = "Massachusetts,Cambridge,New Haven,Pasadena,Philadelphia,Morningside,Manhattan,Chicago,Hyde Park,Providence,Ithaca,Durham,Evanston,Hanover,Pittsburgh,Palo Alto,Ivy,Quaker,Quakers,Tiger,Tigers,Bulldog,Bulldogs,Beaver,Beavers,Cardinal,Big Red,Blue Devil,Blue Devils,Wildcat,Wildcats,Big Green,Tartan,Tartans,Bruno,Lion,Lions,Maroon,Maroons,Crimson,Brewster,Dialogues".split(",")
for s in SL:
    t = (V / f"{s}.md").read_text()
    terms |= {x.strip() for x in re.split(r"[,，;；\n]", sec(t, "identifying_terms")) if len(x.strip()) >= 2}
    qs = re.findall(r'^\s*(?:\d+\.\s*|-\s*)(?:Q\d+\.\s*)?["“](.+?)["”]\s*(?:—|–|-{1,2})', sec(t, "quotes"), re.M)
    quotes[s] = qs
terms |= set(EXTRA)
pat = re.compile(r"(?<![A-Za-z])(" + "|".join(sorted(map(re.escape, terms), key=len, reverse=True)) + r")(?:'s|’s)?(?![A-Za-z])", re.I)
random.seed(20261117); order = SL[:]; random.shuffle(order)
key, lines = {}, []
for i, s in enumerate(order, 1):
    lab = f"S{i:02d}"; key[lab] = s; lines.append(f"## {lab}")
    for q in quotes[s]: lines.append("- " + pat.sub("[X]", q))
    lines.append("")
out.write_text("\n".join(lines)); (out.parent / "blind_key.json").write_text(json.dumps(key))
print({s: len(q) for s, q in quotes.items()}, "terms:", len(terms))

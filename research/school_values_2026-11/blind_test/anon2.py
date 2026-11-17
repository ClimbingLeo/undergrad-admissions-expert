"""用法：anon2.py <证据目录…用冒号分隔> <输出目录> <组名> <slug,slug,...>
每组单独编号 G-01…，答案写到 <输出目录>/../blind2_key/<组名>.json"""
import re, sys, random, pathlib, json
dirs = [pathlib.Path(d) for d in sys.argv[1].split(":")]
out = pathlib.Path(sys.argv[2]); grp = sys.argv[3]; SL = sys.argv[4].split(",")
def sec(t, name):
    m = re.search(r"^## " + name + r"\s*\n(.*?)(?=^## |\Z)", t, re.S | re.M); return m.group(1) if m else ""
terms, quotes = set(), {}
for d in dirs:
    for f in d.glob("*.md"):
        if f.stem in ("BRIEF", "PREDICTION"): continue
        terms |= {x.strip() for x in re.split(r"[,，;；\n]", sec(f.read_text(), "identifying_terms")) if len(x.strip()) >= 2}
EXTRA = ("Massachusetts,Cambridge,New Haven,Pasadena,Philadelphia,Morningside,Manhattan,Chicago,Hyde Park,Providence,Ithaca,Durham,Evanston,Hanover,Pittsburgh,Palo Alto,"
 "Baltimore,Houston,Nashville,St. Louis,South Bend,Atlanta,Washington,D.C.,Medford,Somerville,Los Angeles,New York,Boston,Chestnut Hill,Berkeley,San Diego,La Jolla,Irvine,Davis,Santa Barbara,"
 "Ann Arbor,Chapel Hill,Charlottesville,Urbana,Champaign,Austin,Madison,Seattle,College Park,Gainesville,West Lafayette,Columbus,New Brunswick,New Jersey,Texas,Wisconsin,Michigan,Virginia,Illinois,Maryland,Florida,Ohio,Indiana,Georgia,California,Carolina,"
 "Oxford,London,Edinburgh,Manchester,Zurich,Zürich,Switzerland,Swiss,Scotland,Hong Kong,Kowloon,"
 "Ivy,Quaker,Quakers,Tiger,Tigers,Bulldog,Bulldogs,Beaver,Beavers,Cardinal,Big Red,Blue Devil,Blue Devils,Wildcat,Wildcats,Big Green,Tartan,Tartans,Bruno,Lion,Lions,Maroon,Maroons,Crimson,Brewster,Dialogues,"
 "Blue Jay,Blue Jays,Owl,Owls,Commodore,Commodores,Bear,Bears,Fighting Irish,Eagle,Eagles,Hoya,Hoyas,Jumbo,Jumbos,Trojan,Trojans,Violet,Violets,Terrier,Terriers,Husky,Huskies,Golden Bear,Golden Bears,Bruin,Bruins,Triton,Tritons,Anteater,Anteaters,Aggie,Aggies,Gaucho,Gauchos,"
 "Wolverine,Wolverines,Tar Heel,Tar Heels,Cavalier,Cavaliers,Wahoo,Wahoos,Yellow Jacket,Yellow Jackets,Illini,Longhorn,Longhorns,Badger,Badgers,Terrapin,Terrapins,Terps,Gator,Gators,Boilermaker,Boilermakers,Buckeye,Buckeyes,Scarlet Knight,Scarlet Knights").split(",")
terms |= set(EXTRA)
pat = re.compile(r"(?<![A-Za-z])(" + "|".join(sorted(map(re.escape, terms), key=len, reverse=True)) + r")(?:'s|’s)?(?![A-Za-z])", re.I)
for s in SL:
    f = next(d / f"{s}.md" for d in dirs if (d / f"{s}.md").exists())
    quotes[s] = re.findall(r'^\s*(?:\d+\.\s*|-\s*)(?:Q\d+\.\s*)?["“](.+?)["”]\s*(?:—|–|-{1,2})', sec(f.read_text(), "quotes"), re.M)
random.seed("20261117" + grp); order = SL[:]; random.shuffle(order)
key, lines = {}, []
for i, s in enumerate(order, 1):
    lab = f"{grp}-{i:02d}"; key[lab] = s; lines.append(f"## {lab}")
    lines += ["- " + pat.sub("[X]", q) for q in quotes[s]] + [""]
out.mkdir(parents=True, exist_ok=True); (out / f"{grp}.md").write_text("\n".join(lines))
kd = out.parent / "blind2_key"; kd.mkdir(exist_ok=True); (kd / f"{grp}.json").write_text(json.dumps(key))
print(grp, {s: len(q) for s, q in quotes.items()})

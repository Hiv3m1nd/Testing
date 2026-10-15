"""Copy selected real images into the project folder and write one sidecar JSON per file.

Usage: python3 -I build_real_images.py <scratch_dl_dir> <dest_dir>
"""
import hashlib, json, os, shutil, subprocess, sys
from PIL import Image

Image.MAX_IMAGE_PIXELS = None
DL, DEST = sys.argv[1], sys.argv[2]
os.makedirs(DEST, exist_ok=True)
RETRIEVED = "2026-10-15"

CC0 = ("CC0 1.0 Universal (public domain dedication)", "https://creativecommons.org/publicdomain/zero/1.0/")
CCBY2 = ("CC BY 2.0", "https://creativecommons.org/licenses/by/2.0/")

met_meta = json.load(open(os.path.join(DL, "met", "selected_met.json"), encoding="utf-8"))
oi_meta = json.load(open(os.path.join(DL, "oi", "selected_oi.json"), encoding="utf-8"))


def info(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    w = hh = None
    try:
        with Image.open(path) as im:
            w, hh = im.size
    except Exception:
        pass
    return dict(width=w, height=hh, bytes=os.path.getsize(path), sha256=h.hexdigest())


def write(name, src, side, rotate=0):
    dst = os.path.join(DEST, name)
    if rotate:
        with Image.open(src) as im:
            im.rotate(rotate, expand=True).save(dst, quality=95, subsampling=0)
    else:
        shutil.copyfile(src, dst)
    side = dict(file=name, retrieved=RETRIEVED, **side, **info(dst))
    with open(os.path.splitext(dst)[0] + ".json", "w", encoding="utf-8") as f:
        json.dump(side, f, indent=2, ensure_ascii=False)
    print("wrote", name, side["width"], side["height"])


# ---------------- The Met (CC0) via gcs-public-data--met mirror ----------------
MET = [
    # (object id, image index, category, slug, accuracy note)
    ("258543", 0, "3_portrait", "met_possibly-gaius-caesar_head_front-dark",
     "Met title: 'Stone head of a Julio-Claudian youth, possibly of Gaius Caesar'. Identification is the Met's tentative one; narrate as 'possibly' / 'thought to be'."),
    ("258543", 1, "3_portrait", "met_possibly-gaius-caesar_head_three-quarter",
     "Same object as above; identification tentative."),
    ("258543", 2, "3_portrait", "met_possibly-gaius-caesar_head_front-grey",
     "Same object as above; identification tentative."),
    ("258543", 3, "3_portrait", "met_possibly-gaius-caesar_head_profile",
     "Same object as above; identification tentative."),
    ("258543", 7, "3_portrait", "met_possibly-gaius-caesar_head_three-quarter-dark",
     "Same object as above; identification tentative."),
    ("248891", 0, "3_portrait", "met_bronze-aristocratic-boy_full",
     "Met object name: 'Statue of a boy, Gaius Caesar ?'. Title: 'Bronze statue of an aristocratic boy'. Identification as Gaius is speculative; caption as 'a Roman boy of Augustus's time' unless attributed."),
    ("248891", 4, "3_portrait", "met_bronze-aristocratic-boy_head_profile",
     "Speculative Gaius identification (see full-figure sidecar)."),
    ("248891", 6, "3_portrait", "met_bronze-aristocratic-boy_head_front",
     "Speculative Gaius identification (see full-figure sidecar)."),
    ("247993", 0, "3_portrait", "met_augustus_marble-portrait_07-286-115_dark", "Portrait of Augustus, carved ca. AD 14-37 (posthumous)."),
    ("247993", 3, "3_portrait", "met_augustus_marble-portrait_07-286-115_grey", "Portrait of Augustus, carved ca. AD 14-37 (posthumous)."),
    ("248119", 0, "3_portrait", "met_augustus_marble-portrait_08-258-47", "Portrait of Augustus, carved ca. AD 14-37 (posthumous)."),
    ("248119", 5, "3_portrait", "met_augustus_marble-portrait_08-258-47_studio", "Portrait of Augustus, carved ca. AD 14-37 (posthumous)."),
    ("251114", 0, "3_portrait", "met_augustus_colossal-head", "Colossal head of Augustus, ca. AD 14-30 (posthumous)."),
    ("251411", 0, "3_portrait", "met_augustus_ivory-head", "Ivory portrait head of Augustus, 27 BC-AD 14."),
    ("254473", 0, "3_portrait", "met_augustus_sardonyx-cameo", "Cameo portrait of Augustus, made ca. AD 41-54 (posthumous)."),
    ("250706", 0, "3_portrait", "met_livia_marble-portrait", "Met title: 'Marble portrait of Livia' (object name 'Livia ?')."),
    ("246866", 0, "2_coin", "met_coin_aureus-of-augustus_20-19bc", "Gold aureus of Augustus, 20-19 BC. NOT the Gaius & Lucius (RIC I 207) type."),
    ("246872", 0, "2_coin", "met_coin_aureus-of-octavian_39bc", "Gold aureus of Octavian, 39 BC. NOT the Gaius & Lucius type."),
    ("248036", 0, "2_coin", "met_coin_denarius-of-octavian_29-27bc_obverse", "Silver denarius of Octavian, 29-27 BC (obverse). NOT the Gaius & Lucius type."),
    ("248036", 1, "2_coin", "met_coin_denarius-of-octavian_29-27bc_reverse", "Same coin, reverse."),
    ("248037", 0, "2_coin", "met_coin_denarius-of-octavian-augustus_29-27bc", "Silver denarius of Octavian (Augustus), ca. 29-27 BC."),
    ("322355", 0, "x_extra", "met_coin_parthian-drachm_38-2bc",
     "Parthian drachm dated ca. 38-2 BC, i.e. the reign of Phraates IV (father of Phraates V/Phraataces, the king Gaius met). Do not caption as Phraataces."),
    ("336117", 0, "x_extra", "met_print_mausoleum-of-augustus_reconstruction_goeree",
     "Pre-1704 print by Jan Goeree: a reconstruction plus a view of the ruins. Reconstruction is conjectural; mark as an early-modern illustration."),
    ("363317", 0, "5_lycia", "met_print_rock-tombs-at-telmissus_19thc",
     "19th-century British print of the rock tombs at Telmessos (modern Fethiye), Lycia. Illustration, not Limyra."),
]
for oid, idx, cat, slug, note in MET:
    m = met_meta[oid]
    obj = json.load(open(os.path.join(DL, "met", "img", f"{oid}.object.json")))
    rec = [x for x in obj if x["gcsUrl"] == f"{oid}/{idx}.jpg"][0]
    side = dict(
        category=cat,
        title=m["Title"],
        creator=m["Artist Display Name"] or f"Unknown ({m['Culture'] or m['Department']})",
        object_date=m["Object Date"],
        institution="The Metropolitan Museum of Art, New York",
        accession_number=m["Object Number"],
        met_object_id=oid,
        credit_line=m["Credit Line"],
        medium=m["Medium"],
        source_page_url=m["Link Resource"].replace("http://", "https://"),
        source_image_url=rec["originalImageUrl"].replace("http://", "https://"),
        downloaded_from=f"https://storage.googleapis.com/gcs-public-data--met/{oid}/{idx}.jpg",
        licence=CC0[0], licence_url=CC0[1],
        attribution_required=False,
        attribution_text=f"The Metropolitan Museum of Art, {m['Credit Line']} (Open Access, CC0)",
        how_verified=("'Is Public Domain' = True for this Object ID in the Met's own open-access CSV "
                      "(github.com/metmuseum/openaccess MetObjects.csv, fetched via media.githubusercontent.com on 2026-10-15), "
                      "and isOasc = true for this exact image in the Met/Google public mirror object.json "
                      f"(storage.googleapis.com/gcs-public-data--met/{oid}/object.json). images.metmuseum.org itself is blocked from this container."),
        accuracy_note=note,
        mirror_note="Mirror is the Met/Google 2017 snapshot; pixels are the Met's original-resolution file as of 2017.",
    )
    write(f"{cat.split('_')[0]}_{slug}.jpg", os.path.join(DL, "met", "img", f"{oid}_{idx}.jpg"), side)

# ---------------- Smithsonian (CC0) via smithsonian-open-access S3 ----------------
si_src = os.path.join(DL, "si", "CHSDM-D849C082CAE72-000001.jpg")
if not os.path.exists(si_src):
    subprocess.run(["curl", "-sS", "-f", "-o", si_src,
                    "https://smithsonian-open-access.s3-us-west-2.amazonaws.com/media/chsdm/CHSDM-D849C082CAE72-000001.jpg"], check=True)
write("x_si_piranesi_ruins-of-the-mausoleum-of-augustus_1756.jpg", si_src, dict(
    category="x_extra",
    title='Ruins of the Mausoleum of Octavian Augustus, "Le Antichita Romane" II, 1756',
    creator="Giovanni Battista Piranesi (Italian, 1720-1778)",
    object_date="1756", medium="Etching",
    institution="Cooper Hewitt, Smithsonian Design Museum",
    accession_number="1931-94-85", credit_line="Gift of Eleanor and Sarah Hewitt",
    source_page_url="https://collection.cooperhewitt.org/view/objects/asitem/id/52280",
    source_image_url="https://ids.si.edu/ids/download?id=CHSDM-D849C082CAE72-000001.jpg",
    downloaded_from="https://smithsonian-open-access.s3-us-west-2.amazonaws.com/media/chsdm/CHSDM-D849C082CAE72-000001.jpg",
    licence=CC0[0], licence_url=CC0[1], attribution_required=False,
    attribution_text="Cooper Hewitt, Smithsonian Design Museum, Gift of Eleanor and Sarah Hewitt (Smithsonian Open Access, CC0)",
    how_verified=("metadata_usage.access = 'CC0' and media usage.access = 'CC0' for idsId CHSDM-D849C082CAE72-000001 in the "
                  "Smithsonian Open Access EDAN metadata on the AWS open-data bucket (metadata/edan/chndm/*.txt). ids.si.edu is blocked here; "
                  "the identical file name is published in the bucket's media/chsdm/ prefix."),
    accuracy_note=("Piranesi's 1756 view of the Mausoleum of Augustus area. Gaius's remains were placed in this mausoleum (CIL VI 895 urn inscription; "
                   "confirm in research.md before narrating). Mark as an 18th-century illustration."),
))

# ---------------- Open Images (Flickr, CC BY 2.0) via open-images-dataset S3 ----------------
OI = [
    ("87a29b988fe99104", "4_arapacis", "oi_ara-pacis_isaw", "Whole altar in the Meier pavilion; south-side procession frieze visible obliquely, not a close-up."),
    ("8421b93fc06b3e73", "4_arapacis", "oi_ara-pacis_mcad-library", "Whole altar (older pavilion); procession frieze visible on the right-hand side wall."),
    ("ad3b9eaae6693f1f", "3_portrait", "oi_augustus-prima-porta_vatican", "Augustus of Prima Porta, Vatican Museums."),
    ("f8d03dba00206630", "3_portrait", "oi_augustus-via-labicana", "Augustus as pontifex (Via Labicana type) per photographer's title 'Octavian - the Emperor Augustus'."),
    ("2780f9ef1b4e3504", "3_portrait", "oi_augustus-portrait-head_efthimiadis", "Photographer's title: 'Portrait head of the emperor Augustus (29 BC-AD 14)'. Museum not stated in metadata."),
    ("6e91f05fd3bc035f", "3_portrait", "oi_augustus-bust_waits", "Photographer's title: 'Caesar Augustus'. Museum not stated in metadata."),
    ("a3a9f2c5a556e65a", "3_portrait", "oi_livia-portrait-head_efthimiadis", "Photographer's title: 'Portrait head of the empress Livia'."),
    ("7cbfd8e1d1e232e7", "2_coin", "oi_imperial-roman-coins_display", "Museum display of Imperial Roman coins; types not identified. Do not caption as Gaius & Lucius."),
    ("95b8da309827d2e0", "5_lycia", "oi_kings-tomb-dalyan_rock-tombs", "Rock-cut temple tombs at Kaunos (Dalyan), Caria/Lycia border. Not Limyra."),
    ("a31023297d3767cc", "5_lycia", "oi_lycian-sarcophagus_fethiye", "Lycian sarcophagus in Fethiye (Telmessos). Not Limyra."),
    ("0f8a47c603d85c11", "5_lycia", "oi_lycian-graves_fethiye", "Lycian tombs, Fethiye. Not Limyra."),
    ("a8dbef669edbd8ec", "5_lycia", "oi_olympos-ruins_tomb", "Ruins/tomb at Olympos, eastern Lycia (about 30 km from Limyra). Not Limyra."),
    ("bae1bc9517907795", "5_lycia", "oi_sunset-off-turkey_sea", "Dusk at sea off Turkey; exact location not stated. Ship rail and winch in foreground: crop to sky/sea/coast."),
    ("bdd48751ee0452b7", "5_lycia", "oi_sunset-turkey_red", "Red sunset, Turkey; exact location not stated."),
    ("18728411c87db815", "5_lycia", "oi_olympos-beach_coast", "Olympos beach and Lycian coast with mountains (daylight; can be graded to dusk)."),
    ("90c47b86b130258a", "5_lycia", "oi_turquoise-coast_fethiye", "Turquoise Coast near Fethiye (daylight)."),
    ("cd95ba95c327ba9e", "5_lycia", "oi_coast-road-to-patara", "Lycian coastal cliffs on the road to Patara; overcast, moody."),
    ("bab9673ffa88534c", "5_lycia", "oi_patara-flooded-ruins", "Flooded ruins at Patara, Lycia."),
    ("dbc146d2bb650cb6", "5_lycia", "oi_xanthos-theatre_aerial", "Xanthos theatre, Lycia, from above."),
    ("feed6a67722b08b6", "5_lycia", "oi_patara-theatre", "Patara theatre, Lycia."),
    ("0052856853e92471", "x_extra", "oi_euphrates-at-dura-europos_isaw",
     "Euphrates with river islands at Dura-Europos, Syria. The AD 1/2 meeting island's location is not known: use only as an illustrative view of the Euphrates."),
]
for iid, cat, slug, note in OI:
    m = oi_meta[iid]
    rot = 0
    try:
        rot = int(float(m["Rotation"]))
    except ValueError:
        rot = 0
    author = m["Author"].replace("&amp;", "&").replace("&quot;", '"')
    side = dict(
        category=cat,
        title=m["Title"].replace("&amp;", "&").replace("&quot;", '"'),
        creator=f"{author} (Flickr)",
        creator_profile_url=m["AuthorProfileURL"],
        institution=None,
        source_page_url=m["OriginalLandingURL"],
        source_image_url=m["OriginalURL"],
        original_size_bytes=int(m["OriginalSize"]) if m["OriginalSize"].isdigit() else None,
        downloaded_from=f"https://open-images-dataset.s3.amazonaws.com/{m['Subset']}/{iid}.jpg",
        open_images_id=iid,
        licence=CCBY2[0], licence_url=CCBY2[1],
        attribution_required=True,
        attribution_text=f"\"{m['Title'].replace('&amp;', '&').replace('&quot;', chr(34))}\" by {author}, {m['OriginalLandingURL']}, CC BY 2.0 (cropped/graded)",
        how_verified=("License column = https://creativecommons.org/licenses/by/2.0/ for this ImageID in Google's Open Images metadata "
                      "(storage.googleapis.com/openimages/2018_04/image_ids_and_rotation.csv), which records the Flickr licence at collection time. "
                      "Flickr itself is blocked from this container, so the licence was NOT re-checked live; re-check the Flickr page before publishing."),
        rotation_applied_deg_ccw=rot,
        resolution_note="Open Images S3 mirror is downscaled to 1024 px on the long side; original on Flickr is larger. Use as inset/parallax plate or upscale.",
        accuracy_note=note,
    )
    write(f"{cat.split('_')[0]}_{slug}.jpg", os.path.join(DL, "oi", "img", f"{iid}.jpg"), side, rotate=rot)

# ---------------- Copernicus Sentinel-2 crop ----------------
write("1_s2_limyra-finike-kumluca_2025-07-06_10m_7680x4320.jpg", os.path.join(DL, "s2", "s2_crop.jpg"), dict(
    category="1_limyra",
    title="Sentinel-2 true-colour (TCI) crop: Limyra, Finike bay, Kumluca plain and Gelidonya, 6 July 2025",
    creator="European Union / ESA Copernicus Sentinel-2A (L2A processing by ESA; COG by Element 84 / AWS Open Data)",
    institution="Copernicus programme",
    source_page_url="https://registry.opendata.aws/sentinel-2-l2a-cogs/",
    source_image_url="https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/36/S/TF/2025/7/S2A_36STF_20250706_0_L2A/TCI.tif",
    downloaded_from="https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/36/S/TF/2025/7/S2A_36STF_20250706_0_L2A/TCI.tif",
    crop=dict(utm_zone="36N (EPSG:32636)", pixel_size_m=10, ul_easting=211530, ul_northing=4047380, width_px=7680, height_px=4320,
              limyra_px=[3456, 2160], finike_px=[3218, 2671],
              note="Limyra (36.3436 N, 30.1708 E) sits at the exact centre of the crop."),
    scene_cloud_cover_percent=0.004823,
    licence="Copernicus Sentinel data terms and conditions (free, full and open; commercial use and modification allowed)",
    licence_url="https://sentinels.copernicus.eu/documents/247904/690755/Sentinel_Data_Legal_Notice",
    attribution_required=True,
    attribution_text="Contains modified Copernicus Sentinel data [2025]",
    how_verified=("Scene STAC item S2A_36STF_20250706_0_L2A.json read from the bucket (cloud cover 0.005 %). Licence per EU Regulation 1159/2013 "
                  "and the Sentinel Data Legal Notice (not fetchable here; well-established terms). Modern land use visible (greenhouses, towns)."),
    accuracy_note="Modern satellite view. Use for the establishing 'descend from orbit to Limyra' move; label 'today'.",
))

"""Cold open narration (script v3, verbatim). (id, text with phoneme overrides, pause after in s)."""
VOICE = "bm_lewis"
SPEED = 0.95
LEAD_IN = 3.2  # torch crackle and drone before the first word

# Pronunciations shared with the rest of the series (HANDOFF §8 + the long-form thread).
GAIUS = "[Gaius](/ɡˈIəs/)"
LIMYRA = "[Limyra](/lˈɪməɹə/)"

LINES = [
    ("l1", "Near the southern coast of Turkey, among the ruins of an ancient town, stands a tomb built for a Roman prince.", 1.0),
    ("l2", "The young man it was built for was supposed to inherit the Roman world.", 0.45),
    ("l3", "His grandfather, Augustus, the master of that world, had planned his entire life for him: his name, his titles, his future.", 0.55),
    ("l4", "Rome even put his name on its coins.", 1.3),
    ("l5", "And then, at twenty-two, with all of it finally within reach, he asked to walk away.", 1.1),
    ("l6", "He never made it home.", 1.6),
    ("l7", f"This is the story of {GAIUS} Caesar:", 0.55),
    ("l8", "the boy who was given everything, except a choice.", 4.0),
]

"""Narration for Episode AD 1, as structured data.

Each line: (scene, text, pause_after_seconds). Pronunciations are pinned with
misaki's inline phoneme syntax [word](/phonemes/), so the spoken text and the
subtitle text can differ (subtitles strip the markup).
"""

AD = "[AD](/ˌAdˈi/)"
BC = "[BC](/bˌisˈi/)"

LINES = [
    # --- cold open -----------------------------------------------------------
    ("open", f"No one alive in 1 {AD} knew it was 1 {AD}.", 0.9),
    # --- the calendar ----------------------------------------------------------
    ("calendar", "Our count of years was invented five centuries later, by a monk named "
                 "[Dionysius Exiguus](/dˌIənˈɪsiəs ɛɡzˈɪɡjuəs/).", 0.35),
    ("calendar", "He counted from the birth of Jesus, and probably got it wrong.", 0.3),
    ("calendar", f"Most historians place that birth a few years earlier, before King Herod died, around 4 {BC}.", 0.35),
    ("calendar", f"And there is no year zero. 1 {BC} runs straight into {AD} 1.", 0.8),
    # --- what people actually called it -----------------------------------
    ("names", "So what did people call this year?", 0.2),
    ("names", "In Rome, it was simply the year that [Gaius](/ɡˈIəs/) Caesar and "
              "[Lucius](/lˈusiəs/) [Aemilius](/imˈɪliəs/) [Paullus](/pˈɔləs/) were consuls.", 0.45),
    ("names_china", "But in China, the [Han](/hˈɑn/) court really did proclaim a beginning: "
                    "a new era, called [Yuanshi](/juˈɛn ʃˈɜɹ/). The Original Beginning.", 0.9),
    # --- two empires -------------------------------------------------------------
    ("empires", "Rome and [Han](/hˈɑn/) China lay at opposite ends of Eurasia, eight thousand kilometres apart.", 0.3),
    ("empires", "Between them, they ruled perhaps a hundred million people. A third or more of humanity.", 0.3),
    ("empires", "Yet each knew the other only as rumour. To Romans, the Chinese were the "
                "[Seres](/sˈɪɹiz/): the silk people.", 0.8),
    # --- Rome --------------------------------------------------------------------
    ("rome", "Rome's master, Augustus, was in his sixties, and he meant to pass his power down his own bloodline.", 0.3),
    ("rome", "His heirs were his grandsons, [Gaius](/ɡˈIəs/) and [Lucius](/lˈusiəs/), adopted as his sons.", 0.3),
    ("rome", "Their mother, his daughter Julia, had been banished to a tiny island.", 0.25),
    ("rome", "And his stepson Tiberius had withdrawn to Rhodes, and was refused permission to come home.", 0.7),
    # --- the East ------------------------------------------------------------------
    ("east", "This year, [Gaius](/ɡˈIəs/), barely twenty, was consul, and far to the east, facing Rome's great rival: Parthia.", 0.3),
    ("east", "Its young king ruled beside his mother, [Musa](/mˈusə/).", 0.2),
    ("east", "The historian Josephus says she had arrived as an Italian slave girl: "
             "a gift from Augustus himself.", 0.25),
    ("east", "Now her face was on Parthia's coins.", 0.7),
    # --- trade ---------------------------------------------------------------------
    ("trade", "Yet these worlds were linked. Chinese silk moved west, from trader to trader.", 0.25),
    ("trade", "And from Roman Egypt, ships rode the monsoon winds to India. "
              "[Strabo](/stɹˈAbO/) heard of as many as a hundred and twenty a year.", 0.7),
    # --- China -------------------------------------------------------------------
    ("china", "At the far end of the silk trade lay [Chang'an](/ʧˌɑŋˈɑn/), capital of the [Han](/hˈɑn/).", 0.25),
    ("china", "Its emperor was a boy of about nine. Real power lay with his regent: "
              "[Wang Mang](/wˈɑŋ mˈɑŋ/).", 0.4),
    ("pheasant", "Early this year, envoys from the far south presented a rare white pheasant.", 0.25),
    ("pheasant", "Such a bird was said to have once honoured the Duke of [Zhou](/ʤˈO/), "
                 "the legendary regent of a boy king.", 0.3),
    ("pheasant", "The hint was clear. [Wang Mang](/wˈɑŋ mˈɑŋ/) was named "
                 "Duke Who Secures the [Han](/hˈɑn/).", 0.3),
    ("pheasant", "And, the official history notes, he had arranged the pheasant himself.", 0.9),
    # --- close -----------------------------------------------------------------------
    ("close", "So Year One was no great beginning. Only a fragile calm.", 0.35),
    ("close", "In Rome, an ageing emperor and two young heirs. "
              "In China, a boy emperor and an ambitious regent.", 0.5),
    ("next", "Next year, the [Han](/hˈɑn/) will count their people: nearly sixty million.", 0.3),
    ("next", "And in Rome, one of the two heirs will not live to see the year's end.", 1.2),
]

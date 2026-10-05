#!/usr/bin/env python3
"""Generate 35-slide PowerPoint: The Noisy Neighbour Inside Your GPU."""

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn

# ── Constants ──────────────────────────────────────────────────────────────
BG      = RGBColor(0x0A, 0x0E, 0x27)
WHITE   = RGBColor(0xE8, 0xE8, 0xE8)
BLUE    = RGBColor(0x00, 0xD4, 0xFF)
GREEN   = RGBColor(0x39, 0xFF, 0x14)
AMBER   = RGBColor(0xFF, 0xB3, 0x47)
RED     = RGBColor(0xFF, 0x44, 0x44)
PURPLE  = RGBColor(0xB8, 0x77, 0xD9)
DARK_BOX = RGBColor(0x12, 0x17, 0x3D)

SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)

FONT_TITLE = "Calibri"
FONT_BODY  = "Calibri"
FONT_CODE  = "Consolas"


# ── Helpers ────────────────────────────────────────────────────────────────
def set_bg(slide):
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = BG


def add_textbox(slide, left, top, width, height):
    txBox = slide.shapes.add_textbox(left, top, width, height)
    txBox.text_frame.word_wrap = True
    return txBox.text_frame


def set_run(run, text, size=20, color=WHITE, bold=False, font_name=FONT_BODY):
    run.text = text
    run.font.size = Pt(size)
    run.font.color.rgb = color
    run.font.bold = bold
    run.font.name = font_name


def add_para(tf, text, size=20, color=WHITE, bold=False, font_name=FONT_BODY,
             alignment=PP_ALIGN.LEFT, space_before=Pt(4), space_after=Pt(4)):
    p = tf.add_paragraph()
    p.alignment = alignment
    p.space_before = space_before
    p.space_after = space_after
    r = p.add_run()
    set_run(r, text, size, color, bold, font_name)
    return p


def first_para(tf, text, size=20, color=WHITE, bold=False, font_name=FONT_BODY,
               alignment=PP_ALIGN.LEFT):
    p = tf.paragraphs[0]
    p.alignment = alignment
    r = p.add_run()
    set_run(r, text, size, color, bold, font_name)
    return p


def add_title(slide, text, size=36, color=WHITE, left=Inches(0.6), top=Inches(0.3),
              width=Inches(12), height=Inches(0.8)):
    tf = add_textbox(slide, left, top, width, height)
    first_para(tf, text, size=size, color=color, bold=True)
    return tf


def add_shape_box(slide, left, top, width, height, fill_color=DARK_BOX,
                  border_color=None):
    from pptx.enum.shapes import MSO_SHAPE
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill_color
    if border_color:
        shape.line.color.rgb = border_color
        shape.line.width = Pt(2)
    else:
        shape.line.fill.background()
    return shape


def add_box_with_text(slide, left, top, width, height, lines,
                      fill_color=DARK_BOX, border_color=None):
    """lines = list of (text, size, color, bold, font_name)"""
    shape = add_shape_box(slide, left, top, width, height, fill_color, border_color)
    tf = shape.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.15)
    tf.margin_right = Inches(0.15)
    tf.margin_top = Inches(0.1)
    tf.margin_bottom = Inches(0.1)
    for i, line in enumerate(lines):
        text, sz, clr, bld = line[0], line[1], line[2], line[3]
        fn = line[4] if len(line) > 4 else FONT_BODY
        if i == 0:
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()
        p.space_before = Pt(2)
        p.space_after = Pt(2)
        r = p.add_run()
        set_run(r, text, sz, clr, bld, fn)
    return shape


def set_notes(slide, text):
    notes_slide = slide.notes_slide
    notes_slide.notes_text_frame.text = text


# ── Presentation setup ────────────────────────────────────────────────────
prs = Presentation()
prs.slide_width = SLIDE_W
prs.slide_height = SLIDE_H
blank_layout = prs.slide_layouts[6]  # blank


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 1 — Title
# ═══════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank_layout); set_bg(s)
tf = add_textbox(s, Inches(1), Inches(1.2), Inches(11.3), Inches(5))
first_para(tf, "The Noisy Neighbour Inside Your GPU", size=44, color=BLUE, bold=True,
           alignment=PP_ALIGN.CENTER)
add_para(tf, "Observing Batched LLM Inference", size=28, color=WHITE, alignment=PP_ALIGN.CENTER,
         space_before=Pt(20))
add_para(tf, "Sagar Utekar  ·  Senior SRE, CrowdStrike", size=22, color=WHITE,
         alignment=PP_ALIGN.CENTER, space_before=Pt(30))
add_para(tf, "CNCF Ambassador  ·  Kubestronaut", size=18, color=WHITE,
         alignment=PP_ALIGN.CENTER, space_before=Pt(6))
add_para(tf, "Observability Summit Europe 2026", size=20, color=AMBER,
         alignment=PP_ALIGN.CENTER, space_before=Pt(30))
set_notes(s, "Hi, I'm Sagar. I run GPU infrastructure for AI at CrowdStrike. Today we're hunting a ghost — a latency spike you can see but can't explain.")


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 2 — The Noisy Neighbour You Already Know
# ═══════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank_layout); set_bg(s)
add_title(s, "The Noisy Neighbour You Already Know")

# Left column
add_box_with_text(s, Inches(0.6), Inches(1.4), Inches(5.8), Inches(5.2), [
    ("The CPU World", 24, RED, True),
    ("", 10, WHITE, False),
    ("Container B is a rogue batch job", 20, WHITE, False),
    ("", 6, WHITE, False),
    ("It eats all the CPU on the shared node", 20, WHITE, False),
    ("", 6, WHITE, False),
    ("Container A — your app — gets throttled", 20, WHITE, False),
    ("", 6, WHITE, False),
    ("Latency spikes. No errors. Sound familiar?", 20, WHITE, False),
])

# Right column
add_box_with_text(s, Inches(6.9), Inches(1.4), Inches(5.8), Inches(5.2), [
    ("Your Metrics", 24, GREEN, True),
    ("", 10, WHITE, False),
    ("container_cpu_cfs_throttled_seconds_total", 16, GREEN, False, FONT_CODE),
    ("", 10, WHITE, False),
    ("container_memory_working_set_bytes", 16, GREEN, False, FONT_CODE),
    ("", 14, WHITE, False),
    ("You've been debugging this for 10 years.", 20, WHITE, False),
])

set_notes(s, "You all know this problem. Container B steals CPU from Container A. Latency spikes, no errors. You've been debugging this for years.")


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 3 — How You Fixed It
# ═══════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank_layout); set_bg(s)
add_title(s, "How You Fixed It")

boxes = [
    (Inches(0.6),  Inches(1.5), GREEN,  "Resource Limits",
     'resources: { limits: { cpu: "2" } }'),
    (Inches(6.9),  Inches(1.5), BLUE,   "cgroups",
     "Kernel-level isolation.\nEach container gets its own box."),
    (Inches(0.6),  Inches(3.8), PURPLE, "Node Pools",
     "Dedicated nodes for batch jobs.\nPhysical separation."),
    (Inches(6.9),  Inches(3.8), AMBER,  "Anti-Affinity",
     "Keep troublemakers apart.\nScheduling rules."),
]
for left, top, clr, title, body in boxes:
    add_box_with_text(s, left, top, Inches(5.8), Inches(1.9), [
        (title, 22, clr, True),
        ("", 6, WHITE, False),
        (body, 18, WHITE, False),
    ], border_color=clr)

tf = add_textbox(s, Inches(0.6), Inches(6.2), Inches(12), Inches(0.7))
first_para(tf, "CPU noisy neighbours? Solved. You had soundproof walls.", size=22,
           color=GREEN, bold=True, alignment=PP_ALIGN.CENTER)
set_notes(s, "Resource limits, cgroups, node pools, anti-affinity. CPU noisy neighbours — solved. You had soundproof walls between tenants.")


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 4 — Now Forget Everything
# ═══════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank_layout); set_bg(s)
add_title(s, "Now Forget Everything", color=RED)

# Left column - CPU
add_box_with_text(s, Inches(0.6), Inches(1.4), Inches(5.8), Inches(3.2), [
    ("CPU World", 24, GREEN, True),
    ("", 6, WHITE, False),
    ("✓  cgroups (soundproof walls)", 20, GREEN, False),
    ("✓  Resource limits", 20, GREEN, False),
    ("✓  1 process = 1 core", 20, GREEN, False),
    ("✓  Isolation is cheap", 20, GREEN, False),
], border_color=GREEN)

# Right column - GPU
add_box_with_text(s, Inches(6.9), Inches(1.4), Inches(5.8), Inches(3.2), [
    ("GPU World", 24, RED, True),
    ("", 6, WHITE, False),
    ("✗  No cgroups (paper-thin walls)", 20, RED, False),
    ("✗  No per-request limits", 20, RED, False),
    ("✗  32 requests = 1 chip", 20, RED, False),
    ("✗  Isolation kills throughput", 20, RED, False),
], border_color=RED)

# Bottom box
add_box_with_text(s, Inches(0.6), Inches(5.0), Inches(12.1), Inches(1.8), [
    ("On a GPU, requests MUST share the chip.", 22, RED, True),
    ("The walls are paper-thin.", 22, RED, False),
    ("The fix isn't soundproofing — it's installing noise monitors.", 22, WHITE, True),
], fill_color=RGBColor(0x1A, 0x0A, 0x0A), border_color=RED)

set_notes(s, "GPUs don't have cgroups. No soundproof walls. 32 requests share one chip. Isolation kills throughput. The fix isn't soundproofing — it's observability.")


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 5 — Three Words You Need
# ═══════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank_layout); set_bg(s)
add_title(s, "Three Words You Need")

items = [
    (Inches(0.6), BLUE,   "REQUEST", "A tenant asking for something"),
    (Inches(4.8), GREEN,  "GPU",     "The apartment building"),
    (Inches(9.0), PURPLE, "BATCH",   "Everyone using the elevator at once"),
]
for left, clr, title, desc in items:
    add_box_with_text(s, left, Inches(2.2), Inches(3.8), Inches(3.0), [
        (title, 36, clr, True),
        ("", 14, WHITE, False),
        (desc, 22, WHITE, False),
    ], border_color=clr)

set_notes(s, "Request = tenant. GPU = the building. Batch = everyone sharing the elevator at the same time.")


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 6 — The Apartment Building
# ═══════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank_layout); set_bg(s)
add_title(s, "The Apartment Building")

lines_data = [
    ("GPU = The Building", BLUE),
    ("Batch = The Elevator (shared, one trip at a time)", PURPLE),
    ("KV Cache = The Storage Room (everyone's stuff piles up)", AMBER),
    ("Requests = Tenants (some quick, some... not)", WHITE),
    ("Preemption = 'Your stuff is being moved to the basement'", RED),
]
tf = add_textbox(s, Inches(0.8), Inches(1.5), Inches(11.5), Inches(4.5))
for i, (text, clr) in enumerate(lines_data):
    if i == 0:
        first_para(tf, text, size=24, color=clr, bold=True)
    else:
        add_para(tf, text, size=24, color=clr, bold=True, space_before=Pt(18))

tf2 = add_textbox(s, Inches(0.8), Inches(6.0), Inches(11.5), Inches(0.8))
first_para(tf2, "Keep this picture in mind. We'll come back to it.", size=22,
           color=GREEN, bold=False, alignment=PP_ALIGN.CENTER)
set_notes(s, "GPU is the building. Batch is the elevator. KV cache is the storage room. When the storage room fills up, someone's stuff gets moved to the basement.")


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 7 — What Is a Token?
# ═══════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank_layout); set_bg(s)
add_title(s, "What Is a Token?")

# Left side - tokenisation example
add_box_with_text(s, Inches(0.6), Inches(1.5), Inches(5.8), Inches(2.5), [
    ('"How are you?"', 24, WHITE, True),
    ("", 10, WHITE, False),
    ('["How", " are", " you", "?"]', 22, GREEN, False, FONT_CODE),
], border_color=BLUE)

# Right side - stats
tf = add_textbox(s, Inches(7.0), Inches(1.5), Inches(5.8), Inches(3.5))
first_para(tf, "1 token  ≈  ¾ of a word", size=22, color=BLUE, bold=True)
add_para(tf, "", size=10, color=WHITE)
add_para(tf, "64 tokens  ≈  a quick note under the door (Alex)", size=22, color=GREEN,
         bold=False, space_before=Pt(14))
add_para(tf, "", size=10, color=WHITE)
add_para(tf, "4,000 tokens  ≈  a 5-page renovation plan (Blake)", size=22, color=RED,
         bold=False, space_before=Pt(14))

# Bottom
add_box_with_text(s, Inches(0.6), Inches(5.5), Inches(12.1), Inches(1.2), [
    ("Every token = more stuff in the storage room.", 22, AMBER, True),
    ("Blake's 4,000 tokens = 4 GB.", 22, AMBER, False),
], border_color=AMBER)

set_notes(s, "A token is about three quarters of a word. Alex sends a quick note — 64 tokens. Blake sends a 5-page renovation plan — 4,000 tokens. Each token takes up storage.")


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 8 — Two Phases of Every Reply
# ═══════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank_layout); set_bg(s)
add_title(s, "Two Phases of Every Reply")

# Prefill box
add_box_with_text(s, Inches(0.6), Inches(1.5), Inches(5.8), Inches(3.0), [
    ("PREFILL — Reading the request", 22, BLUE, True),
    ("", 8, WHITE, False),
    ("Like reading a letter from a tenant", 18, WHITE, False),
    ("Happens once, up front", 18, WHITE, False),
    ("Compute-bound (building processes it fast)", 18, WHITE, False),
], border_color=BLUE)

# Decode box
add_box_with_text(s, Inches(6.9), Inches(1.5), Inches(5.8), Inches(3.0), [
    ("DECODE — Writing the reply", 22, PURPLE, True),
    ("", 8, WHITE, False),
    ("Like writing back, one word at a time", 18, WHITE, False),
    ("Happens N times (once per token)", 18, WHITE, False),
    ("Memory-bound (building slows down here)", 18, WHITE, False),
], border_color=PURPLE)

# Bottom timeline
add_box_with_text(s, Inches(0.6), Inches(5.0), Inches(12.1), Inches(1.8), [
    ("TTFT = time to start writing back", 22, BLUE, True),
    ("", 6, WHITE, False),
    ("ITL = gap between each word", 22, PURPLE, True),
])

set_notes(s, "Prefill reads the request — fast, once. Decode writes back one word at a time — slower, hundreds of times. TTFT is when you start writing. ITL is how fast you write.")


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 9 — TTFT
# ═══════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank_layout); set_bg(s)
add_title(s, "TTFT: How Long to Get in the Elevator", color=BLUE)

tf = add_textbox(s, Inches(0.8), Inches(1.4), Inches(11.5), Inches(5.5))
first_para(tf, "TTFT", size=60, color=BLUE, bold=True, alignment=PP_ALIGN.CENTER)
add_para(tf, "Time to First Token", size=28, color=WHITE, bold=False,
         alignment=PP_ALIGN.CENTER, space_before=Pt(6))
add_para(tf, "", size=14, color=WHITE)
add_para(tf, "[Wait in lobby]  →  [Ride up]  →  First word arrives", size=22,
         color=WHITE, alignment=PP_ALIGN.CENTER, space_before=Pt(20))
add_para(tf, "", size=10, color=WHITE)
add_para(tf, "TTFT  =  lobby_wait  +  elevator_ride", size=20, color=BLUE,
         font_name=FONT_CODE, alignment=PP_ALIGN.CENTER, space_before=Pt(16))
add_para(tf, "", size=14, color=WHITE)
add_para(tf, "< 200 ms  →  Tenant doesn't even notice", size=22, color=GREEN,
         space_before=Pt(16))
add_para(tf, "> 2 seconds  →  Tenant starts banging on the door", size=22, color=RED,
         space_before=Pt(10))

set_notes(s, "TTFT is how long before the first word arrives. Under 200ms, nobody notices. Over 2 seconds, they're banging on the door.")


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 10 — ITL
# ═══════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank_layout); set_bg(s)
add_title(s, "ITL: How Slow the Elevator Moves", color=AMBER)

tf = add_textbox(s, Inches(0.8), Inches(1.4), Inches(11.5), Inches(2.5))
first_para(tf, "ITL", size=60, color=AMBER, bold=True, alignment=PP_ALIGN.CENTER)
add_para(tf, "Inter-Token Latency", size=28, color=WHITE, bold=False,
         alignment=PP_ALIGN.CENTER, space_before=Pt(6))

tf2 = add_textbox(s, Inches(0.8), Inches(3.4), Inches(11.5), Inches(1.5))
first_para(tf2, "14 ms between floors — express elevator  ✓", size=22, color=GREEN,
           bold=False)
add_para(tf2, "45 ms between floors — loaded with Blake's furniture  ✗", size=22,
         color=RED, bold=False, space_before=Pt(14))

add_box_with_text(s, Inches(0.6), Inches(5.2), Inches(12.1), Inches(1.6), [
    ("ITL is THE noisy neighbour signal.", 24, AMBER, True),
    ("The elevator slows down when Blake loads his renovation materials in it.", 20, WHITE, False),
], border_color=AMBER)

set_notes(s, "ITL is how fast the elevator moves between floors. 14ms is express. 45ms means Blake loaded his furniture in there. ITL is THE noisy neighbour signal.")


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 11 — Why We Batch
# ═══════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank_layout); set_bg(s)
add_title(s, "Why We Batch")

add_box_with_text(s, Inches(0.6), Inches(1.5), Inches(5.8), Inches(3.5), [
    ("One Tenant in the Building", 24, RED, True),
    ("", 10, WHITE, False),
    ("Building 10% occupied", 22, WHITE, False),
    ("", 8, WHITE, False),
    ("You pay rent for 100% of the building", 22, RED, False),
], border_color=RED)

add_box_with_text(s, Inches(6.9), Inches(1.5), Inches(5.8), Inches(3.5), [
    ("Eight Tenants Batched", 24, GREEN, True),
    ("", 10, WHITE, False),
    ("Building 65% occupied", 22, WHITE, False),
    ("", 8, WHITE, False),
    ("Same building, 8x the revenue", 22, GREEN, False),
], border_color=GREEN)

tf = add_textbox(s, Inches(0.6), Inches(5.5), Inches(12.1), Inches(1.0))
first_para(tf, "Batching = filling the building. That's why every LLM server does it.",
           size=22, color=GREEN, bold=True, alignment=PP_ALIGN.CENTER)

set_notes(s, "One tenant in the building — 10% occupied, wasteful. Eight tenants — 65% occupied. Same building, 8x the value.")


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 12 — Static Batching
# ═══════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank_layout); set_bg(s)
add_title(s, "Static Batching: The Old Lease")

tf = add_textbox(s, Inches(0.8), Inches(1.4), Inches(11.5), Inches(0.6))
first_para(tf, "Lock all tenants in until the last one's lease expires", size=22,
           color=WHITE, bold=True)

tenants = [
    ("Tenant 1", BLUE,   "Short stay — done in March, sits empty until December"),
    ("Tenant 2", PURPLE, "Medium stay — done in June, sits empty"),
    ("Tenant 3", GREEN,  "Short stay — done in February, sits empty"),
    ("Tenant 4", RED,    "12-month lease — everyone waits for this one"),
]
y = Inches(2.2)
for name, clr, desc in tenants:
    add_box_with_text(s, Inches(0.6), y, Inches(12.1), Inches(0.85), [
        (f"{name}: {desc}", 18, clr, False),
    ], border_color=clr)
    y += Inches(1.0)

tf2 = add_textbox(s, Inches(0.6), Inches(6.3), Inches(12.1), Inches(0.7))
first_para(tf2, "65% of the building sits EMPTY waiting for Tenant 4", size=22,
           color=RED, bold=True, alignment=PP_ALIGN.CENTER)

set_notes(s, "Static batching locks everyone in until the last person finishes. 65% waste.")


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 13 — Continuous Batching
# ═══════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank_layout); set_bg(s)
add_title(s, "Continuous Batching: Month-to-Month")

tf = add_textbox(s, Inches(0.8), Inches(1.4), Inches(11.5), Inches(0.6))
first_para(tf, "Check after every month. Someone moved out? Fill the apartment immediately.",
           size=20, color=WHITE, bold=False)

steps = [
    ("Step 1:  Tenants 1, 2, 3 move in", BLUE),
    ("Step 2:  Tenant 3 moves out  →  Tenant 4 moves in immediately", GREEN),
    ("Step 3:  Tenant 1 moves out  →  Tenant 5 fills the spot", GREEN),
]
tf2 = add_textbox(s, Inches(0.8), Inches(2.3), Inches(11.5), Inches(2.5))
for i, (text, clr) in enumerate(steps):
    if i == 0:
        first_para(tf2, text, size=22, color=clr, bold=False)
    else:
        add_para(tf2, text, size=22, color=clr, space_before=Pt(14))

add_box_with_text(s, Inches(2.5), Inches(4.4), Inches(8.3), Inches(0.9), [
    ("<5% vacancy.  36x more tenants served (Orca, 2022)", 22, GREEN, True),
], border_color=GREEN)

add_box_with_text(s, Inches(0.6), Inches(5.7), Inches(12.1), Inches(1.2), [
    ("But now everyone shares the elevator.", 22, RED, True),
    ("Blake's furniture slows it for everyone.", 20, RED, False),
], fill_color=RGBColor(0x1A, 0x0A, 0x0A), border_color=RED)

set_notes(s, "Continuous batching checks after every step. Vacancy drops to 5%. 36x throughput. But now everyone shares the elevator.")


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 14 — The Building Manager Decides
# ═══════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank_layout); set_bg(s)
add_title(s, "The Building Manager Decides")

tf = add_textbox(s, Inches(0.8), Inches(1.5), Inches(11.5), Inches(3.8))
first_para(tf, "New tenant arrives  →", size=22, color=BLUE, bold=True)
add_para(tf, "", size=8, color=WHITE)
add_para(tf, "Storage room has space?", size=22, color=WHITE, bold=True, space_before=Pt(10))
add_para(tf, "  YES  →  Move in! (prefill)", size=20, color=GREEN, space_before=Pt(6))
add_para(tf, "  NO   →  Can we move someone's stuff to basement?", size=20, color=AMBER,
         space_before=Pt(6))
add_para(tf, "          YES  →  Evict, then move in", size=20, color=AMBER, space_before=Pt(4))
add_para(tf, "          NO   →  Wait in lobby (queue)", size=20, color=RED, space_before=Pt(4))

add_box_with_text(s, Inches(0.6), Inches(5.5), Inches(12.1), Inches(1.3), [
    ("--max-num-seqs 256", 20, RED, True, FONT_CODE),
    ("Default: 256 tenants sharing one elevator. Madness.", 20, WHITE, False),
], border_color=RED)

set_notes(s, "The building manager decides who moves in. Default is 256 tenants sharing one elevator. Who designed this building?")


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 15 — Meet Your Neighbours
# ═══════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank_layout); set_bg(s)
add_title(s, "Meet Your Neighbours")

# Alex
add_box_with_text(s, Inches(0.5), Inches(1.4), Inches(6.0), Inches(5.4), [
    ("ALEX", 40, BLUE, True),
    ("The Quiet Tenant", 22, BLUE, False),
    ("", 8, WHITE, False),
    ("'Can you summarise this Jira ticket?'", 18, WHITE, False),
    ("", 6, WHITE, False),
    ("64 tokens — a quick note", 18, WHITE, False),
    ("", 6, WHITE, False),
    ("In and out in minutes", 18, WHITE, False),
    ("", 12, WHITE, False),
    ("Alex will file the noise complaint.", 18, BLUE, True),
], border_color=BLUE)

# Blake
add_box_with_text(s, Inches(6.8), Inches(1.4), Inches(6.0), Inches(5.4), [
    ("BLAKE", 40, RED, True),
    ("The Renovator", 22, RED, False),
    ("", 8, WHITE, False),
    ("'Write a comprehensive capacity report'", 18, WHITE, False),
    ("", 6, WHITE, False),
    ("4,000 tokens — a 5-page renovation plan", 18, WHITE, False),
    ("", 6, WHITE, False),
    ("Same building, same elevator, same everything", 18, WHITE, False),
    ("", 12, WHITE, False),
    ("Blake is about to ruin Alex's morning.", 18, RED, True),
], border_color=RED)

set_notes(s, "Alex is the quiet tenant — quick note, in and out. Blake is renovating — 5-page plans, furniture in the elevator, stuff everywhere. Alex is about to have a bad morning.")


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 16 — The Storage Room Problem
# ═══════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank_layout); set_bg(s)
add_title(s, "The Storage Room Problem (KV Cache)")

add_box_with_text(s, Inches(0.6), Inches(1.4), Inches(12.1), Inches(0.7), [
    ("Building Storage Room — 100% capacity", 22, AMBER, True),
])

# Alex storage
add_box_with_text(s, Inches(0.6), Inches(2.4), Inches(5.8), Inches(1.4), [
    ("Alex's stuff: 3 small boxes", 20, BLUE, True),
    ("Takes up 8% of the room", 18, BLUE, False),
], border_color=BLUE)

# Blake storage
add_box_with_text(s, Inches(6.9), Inches(2.4), Inches(5.8), Inches(1.4), [
    ("Blake's stuff: Massive renovation materials", 20, RED, True),
    ("Takes up 79% of the room", 18, RED, False),
], border_color=RED)

# Warning
add_box_with_text(s, Inches(0.6), Inches(4.2), Inches(12.1), Inches(1.0), [
    ("When the storage room is full... someone's stuff gets moved to the basement.", 22, RED, True),
], fill_color=RGBColor(0x1A, 0x0A, 0x0A), border_color=RED)

# Eviction
add_box_with_text(s, Inches(0.6), Inches(5.5), Inches(12.1), Inches(1.3), [
    ("STORAGE FULL", 24, RED, True),
    ("ALEX'S BOXES MOVED TO BASEMENT (PREEMPTED)", 22, RED, True),
], fill_color=RGBColor(0x2A, 0x0A, 0x0A), border_color=RED)

set_notes(s, "KV cache is the storage room. Alex's 64 tokens — 3 small boxes. Blake's 4,000 tokens — fills 79% of the room. When it's full, Alex's stuff gets moved to the basement.")


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 17 — Step 1: Alex Moves In
# ═══════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank_layout); set_bg(s)
add_title(s, "Step 1: Alex Moves In")

tf = add_textbox(s, Inches(0.8), Inches(1.0), Inches(4), Inches(0.5))
first_para(tf, "WALKTHROUGH  ·  1 OF 4", size=14, color=AMBER, bold=True)

# Left
add_box_with_text(s, Inches(0.6), Inches(1.6), Inches(5.8), Inches(2.0), [
    ("The Building", 22, BLUE, True),
    ("1 tenant, 7 empty apartments", 20, WHITE, False),
    ("Quiet building.", 18, WHITE, False),
], border_color=BLUE)

# Right - metrics
metrics = [
    ("TTFT:  82 ms", GREEN), ("ITL:  14 ms", GREEN),
    ("Storage:  8%", GREEN), ("Occupancy:  1", GREEN),
]
y = Inches(1.6)
for text, clr in metrics:
    add_box_with_text(s, Inches(6.9), y, Inches(5.8), Inches(0.7), [
        (text, 20, clr, True),
    ], border_color=clr)
    y += Inches(0.85)

# Descriptions
descs = ["Elevator instant", "Express speed", "Almost empty", "Quiet building"]
y2 = Inches(1.65)
for d in descs:
    tf3 = add_textbox(s, Inches(9.5), y2, Inches(3.2), Inches(0.65))
    first_para(tf3, d, size=14, color=WHITE, bold=False)
    y2 += Inches(0.85)

# Bottom
tf4 = add_textbox(s, Inches(0.6), Inches(6.0), Inches(12.1), Inches(0.7))
first_para(tf4, "Quiet building. Fast elevator. Life is good.", size=24, color=GREEN,
           bold=True, alignment=PP_ALIGN.CENTER)

set_notes(s, "Alex moves in alone. Elevator is instant. Storage room empty. Life is good.")


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 18 — Step 2: Four More Alexes
# ═══════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank_layout); set_bg(s)
add_title(s, "Step 2: Four More Quiet Tenants")

tf = add_textbox(s, Inches(0.8), Inches(1.0), Inches(4), Inches(0.5))
first_para(tf, "WALKTHROUGH  ·  2 OF 4", size=14, color=AMBER, bold=True)

add_box_with_text(s, Inches(0.6), Inches(1.6), Inches(5.8), Inches(2.0), [
    ("The Building", 22, BLUE, True),
    ("5 tenants, 3 empty apartments", 20, WHITE, False),
    ("All quiet.", 18, WHITE, False),
], border_color=BLUE)

metrics = [
    ("TTFT:  85 ms", GREEN), ("ITL:  15 ms", GREEN),
    ("Storage:  18%", GREEN), ("Occupancy:  5", GREEN),
]
y = Inches(1.6)
for text, clr in metrics:
    add_box_with_text(s, Inches(6.9), y, Inches(5.8), Inches(0.7), [
        (text, 20, clr, True),
    ], border_color=clr)
    y += Inches(0.85)

tf4 = add_textbox(s, Inches(0.6), Inches(6.0), Inches(12.1), Inches(0.7))
first_para(tf4, "Five quiet tenants. Elevator still fast. Building barely notices.",
           size=24, color=GREEN, bold=True, alignment=PP_ALIGN.CENTER)

set_notes(s, "Four more Alexes. Elevator barely slower. Storage at 18%. The building handles this easily.")


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 19 — Step 3: Blake Moves In
# ═══════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank_layout); set_bg(s)
add_title(s, "Step 3: The Renovator Arrives")

tf = add_textbox(s, Inches(0.8), Inches(1.0), Inches(4), Inches(0.5))
first_para(tf, "WALKTHROUGH  ·  3 OF 4", size=14, color=AMBER, bold=True)

add_box_with_text(s, Inches(0.6), Inches(1.6), Inches(5.8), Inches(2.5), [
    ("The Building", 22, AMBER, True),
    ("5 quiet tenants + 1 RENOVATOR", 20, WHITE, False),
    ("Furniture in the elevator.", 18, RED, False),
    ("Drilling starts.", 18, RED, False),
], border_color=AMBER)

metrics = [
    ("TTFT:  85 → 180 ms", AMBER, "Elevator slower"),
    ("ITL:  15 → 32 ms", AMBER, "Furniture in the way"),
    ("Storage:  18 → 55%", AMBER, "Renovation materials"),
    ("Occupancy:  6", AMBER, ""),
]
y = Inches(1.6)
for text, clr, desc in metrics:
    add_box_with_text(s, Inches(6.9), y, Inches(5.8), Inches(0.7), [
        (text, 20, clr, True),
    ], border_color=clr)
    if desc:
        tf3 = add_textbox(s, Inches(9.8), y, Inches(3), Inches(0.65))
        first_para(tf3, desc, size=14, color=WHITE)
    y += Inches(0.85)

tf4 = add_textbox(s, Inches(0.6), Inches(5.8), Inches(12.1), Inches(1.0))
first_para(tf4, "ONE renovator. The experience changed for ALL five quiet tenants.",
           size=24, color=AMBER, bold=True, alignment=PP_ALIGN.CENTER)

set_notes(s, "One Blake moves in. Elevator slows down. Storage room half full. One renovator changed the experience for all five quiet tenants.")


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 20 — Step 4: The Nightmare
# ═══════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank_layout); set_bg(s)
add_title(s, "Step 4: Two More Renovators")

tf = add_textbox(s, Inches(0.8), Inches(1.0), Inches(4), Inches(0.5))
first_para(tf, "WALKTHROUGH  ·  4 OF 4", size=14, color=AMBER, bold=True)

add_box_with_text(s, Inches(0.6), Inches(1.6), Inches(5.8), Inches(2.5), [
    ("The Building", 22, RED, True),
    ("5 quiet + 3 RENOVATORS", 20, WHITE, False),
    ("Elevator full of furniture.", 18, RED, False),
    ("Storage overflowing.", 18, RED, False),
    ("Alex's stuff moved to basement.", 18, RED, False),
], border_color=RED)

metrics = [
    ("TTFT:  420 ms", RED),
    ("ITL:  43 ms", RED),
    ("Storage:  87%", RED),
    ("Occupancy:  8", RED),
    ("Lobby queue:  0", GREEN),
]
y = Inches(1.6)
descs = ["Elevator packed", "Crawling speed", "Almost full", "Full building", "Still zero!"]
for i, ((text, clr), desc) in enumerate(zip(metrics, descs)):
    add_box_with_text(s, Inches(6.9), y, Inches(3.8), Inches(0.6), [
        (text, 18, clr, True),
    ], border_color=clr)
    tf3 = add_textbox(s, Inches(10.9), y, Inches(2.2), Inches(0.6))
    first_para(tf3, desc, size=14, color=clr)
    y += Inches(0.72)

add_box_with_text(s, Inches(0.6), Inches(5.5), Inches(12.1), Inches(1.5), [
    ("Three renovators. Building is full.", 22, RED, True),
    ("But the lobby is EMPTY.", 22, GREEN, True),
    ("It's not a capacity problem. It's a neighbour problem.", 22, WHITE, True),
], fill_color=RGBColor(0x1A, 0x0A, 0x0A), border_color=RED)

set_notes(s, "Two more Blakes. Elevator packed. Storage 87%. But the lobby? Empty. Nobody is waiting to get in. This isn't a capacity problem. It's a noisy neighbour problem.")


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 21 — What Alex Experiences
# ═══════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank_layout); set_bg(s)
add_title(s, "What Alex Experiences")

# Alex alone
add_box_with_text(s, Inches(0.6), Inches(1.4), Inches(12.1), Inches(1.4), [
    ("Alex alone:  elevator 82 ms, each floor 14 ms, done in 210 ms.  Smooth.", 22, GREEN, True),
], border_color=GREEN)

# Alex + Blake
add_box_with_text(s, Inches(0.6), Inches(3.1), Inches(12.1), Inches(1.4), [
    ("Alex + Blake:  elevator 120 ms, each floor 45 ms, done in 482 ms.", 22, RED, True),
    ("Same errand.  2.3x slower.  No errors.", 20, RED, False),
], border_color=RED)

# ITL explanation
add_box_with_text(s, Inches(0.6), Inches(4.8), Inches(12.1), Inches(1.0), [
    ("ITL x floors = phantom delay. 3x slower elevator on 64 floors = +2 seconds you can't explain.", 20, RED, True),
], fill_color=RGBColor(0x1A, 0x0A, 0x0A), border_color=RED)

add_box_with_text(s, Inches(0.6), Inches(6.0), Inches(12.1), Inches(0.9), [
    ("The noisy neighbour slows the elevator. Monitor the elevator speed (ITL).", 20, AMBER, True),
], border_color=AMBER)

set_notes(s, "Alex alone: done in 210ms. With Blake: 482ms. Same errand, 2.3x slower, zero errors. The elevator is the signal.")


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 22 — Eviction Notice
# ═══════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank_layout); set_bg(s)
add_title(s, "Eviction Notice: Kicked Out of the Building")

steps = [
    ("1.  Storage room hits 95%", RED),
    ("2.  Building manager picks the smallest tenant", AMBER),
    ("3.  Moves their stuff to the basement (CPU/disk)", RED),
    ("4.  When they come back: must re-register from scratch", RED),
]
tf = add_textbox(s, Inches(0.8), Inches(1.5), Inches(11.5), Inches(3.0))
for i, (text, clr) in enumerate(steps):
    if i == 0:
        first_para(tf, text, size=24, color=clr, bold=True)
    else:
        add_para(tf, text, size=24, color=clr, bold=True, space_before=Pt(18))

# Code
add_box_with_text(s, Inches(0.6), Inches(4.6), Inches(12.1), Inches(0.9), [
    ("vllm:num_preemptions_total  # The complaint nobody tracks", 18, GREEN, False, FONT_CODE),
])

add_box_with_text(s, Inches(0.6), Inches(5.8), Inches(12.1), Inches(1.0), [
    ("Re-registration after eviction looks like a brand-new tenant.", 20, AMBER, True),
    ("That's your mystery TTFT spike.", 20, AMBER, True),
], border_color=AMBER)

set_notes(s, "When storage fills, someone gets evicted. They must re-register from scratch. That's your mystery TTFT spike.")


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 23 — Your Dashboard Lies
# ═══════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank_layout); set_bg(s)
add_title(s, "Your Dashboard Lies")

# Left - what dashboard shows
add_box_with_text(s, Inches(0.5), Inches(1.4), Inches(6.0), Inches(5.2), [
    ("What Your Dashboard Shows:", 22, RED, True),
    ("", 8, WHITE, False),
    ("RATE:  Normal  ✓", 20, WHITE, False),
    ("ERRORS:  0  ✓", 20, WHITE, False),
    ("DURATION P99:  1.8s  ✗", 20, RED, True),
    ("", 12, WHITE, False),
    ("Conclusion:", 20, WHITE, True),
    ("Slow tenants. Build more apartments.", 20, RED, True),
], border_color=RED)

# Right - what actually happened
add_box_with_text(s, Inches(6.8), Inches(1.4), Inches(6.0), Inches(5.2), [
    ("What Actually Happened:", 22, GREEN, True),
    ("", 8, WHITE, False),
    ("190 ms of actual work", 20, WHITE, False),
    ("1,610 ms WAITING", 20, RED, True),
    ("(evicted, re-registered, elevator delays)", 16, WHITE, False),
    ("", 8, WHITE, False),
    ("Storage: 94% full", 18, RED, False),
    ("Occupancy: 28 tenants", 18, AMBER, False),
    ("Blake: generating 3,000+ tokens", 18, RED, False),
    ("Alex: evicted twice", 18, RED, False),
    ("", 8, WHITE, False),
    ("The tenant was fine. The building was noisy.", 18, GREEN, True),
], border_color=GREEN)

set_notes(s, "Dashboard says build more apartments. Wrong. 190ms of work, 1,610ms waiting. The tenant was fine. The building was noisy.")


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 24 — Three Causes of Delays
# ═══════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank_layout); set_bg(s)
add_title(s, "Three Causes of Delays")

causes = [
    (BLUE,  "SCHEDULING — Waiting in the lobby",
     "Metric: vllm:num_requests_waiting",
     "Fix: Build more buildings (scale out)"),
    (AMBER, "MEMORY — Storage room full, evictions",
     "Metric: vllm:kv_cache_usage_perc",
     "Fix: Occupancy limits, shared storage (prefix caching)"),
    (RED,   "NEIGHBOUR — Elevator slowed by renovators",
     "Metric: vllm:inter_token_latency_seconds",
     "Fix: Send renovators to a different building"),
]
y = Inches(1.4)
for clr, title, metric, fix in causes:
    add_box_with_text(s, Inches(0.6), y, Inches(12.1), Inches(1.55), [
        (title, 22, clr, True),
        (metric, 16, WHITE, False, FONT_CODE),
        (fix, 18, WHITE, False),
    ], border_color=clr)
    y += Inches(1.7)

tf = add_textbox(s, Inches(0.6), Inches(6.5), Inches(12.1), Inches(0.6))
first_para(tf, "Your dashboard shows the complaint. These three tell you the cause.",
           size=20, color=AMBER, bold=True, alignment=PP_ALIGN.CENTER)

set_notes(s, "Three causes. Scheduling: lobby wait — build more buildings. Memory: storage full — occupancy limits. Neighbour: elevator slowed — separate building for renovators.")


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 25 — Inside One Elevator Trip
# ═══════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank_layout); set_bg(s)
add_title(s, "Inside One Elevator Trip")

tf_sub = add_textbox(s, Inches(0.8), Inches(0.95), Inches(11), Inches(0.5))
first_para(tf_sub, "Happens hundreds of times per second", size=16, color=WHITE)

steps_data = [
    ("1.  CHECK LOBBY — 3 people waiting", BLUE),
    ("2.  CHECK STORAGE — 79% full", AMBER),
    ("3.  EVICT IF NEEDED — 2 tenants moved to basement", RED),
    ("4.  ELEVATOR RIDE — 24 tenants share one trip", RED),
    ("     ← Blake's furniture is in here", RED),
    ("5.  DROP OFF — 1 tenant done, 23 continue", GREEN),
    ("↩  Repeat", WHITE),
]
tf = add_textbox(s, Inches(0.8), Inches(1.6), Inches(11.5), Inches(5.0))
for i, (text, clr) in enumerate(steps_data):
    bld = not text.startswith("  ")
    if i == 0:
        first_para(tf, text, size=22, color=clr, bold=bld)
    else:
        add_para(tf, text, size=22, color=clr, bold=bld, space_before=Pt(12))

set_notes(s, "Five steps per elevator trip. Check lobby, check storage, evict if needed, ride together — Blake's furniture is in here — drop off. Repeat hundreds of times per second.")


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 26 — The Monitoring System
# ═══════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank_layout); set_bg(s)
add_title(s, "The Monitoring System (Observability Stack)")

components = [
    ("GRAFANA — The building's security cameras", BLUE),
    ("↓ queries", WHITE),
    ("PROMETHEUS — The sensor network (checks every 15s)", GREEN),
    ("", WHITE),
    ("↓ scrapes                         ↓ scrapes", WHITE),
    ("", WHITE),
]
tf = add_textbox(s, Inches(1.5), Inches(1.4), Inches(10), Inches(3.0))
for i, (text, clr) in enumerate(components):
    sz = 14 if text.startswith("↓") or text == "" else 22
    bld = sz == 22
    if i == 0:
        first_para(tf, text, size=sz, color=clr, bold=bld, alignment=PP_ALIGN.CENTER)
    else:
        add_para(tf, text, size=sz, color=clr, bold=bld, alignment=PP_ALIGN.CENTER,
                 space_before=Pt(4))

# Two bottom boxes
add_box_with_text(s, Inches(1.0), Inches(4.0), Inches(5.2), Inches(2.0), [
    ("vLLM /metrics", 22, BLUE, True),
    ("Elevator speed, storage %,", 18, WHITE, False),
    ("lobby size, occupancy", 18, WHITE, False),
], border_color=BLUE)

add_box_with_text(s, Inches(7.0), Inches(4.0), Inches(5.2), Inches(2.0), [
    ("DCGM Exporter", 22, RED, True),
    ("Power usage, temperature,", 18, WHITE, False),
    ("structural load", 18, WHITE, False),
], border_color=RED)

tf2 = add_textbox(s, Inches(0.6), Inches(6.3), Inches(12.1), Inches(0.7))
first_para(tf2, "Four components. All open-source. No vendor lock-in.", size=20,
           color=BLUE, bold=True, alignment=PP_ALIGN.CENTER)

set_notes(s, "Grafana is the security camera. Prometheus is the sensor network. vLLM metrics for elevator and storage. DCGM for power and structural load.")


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 27 — Three Floors of Monitoring
# ═══════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank_layout); set_bg(s)
add_title(s, "Where to Look: Three Floors")

floors = [
    (BLUE,   "Penthouse — Application (vLLM /metrics)",
     "TTFT  ·  ITL  ·  storage %  ·  occupancy  ·  lobby  ·  shared-storage hits"),
    (RED,    "Mechanical Floor — GPU (DCGM Exporter)",
     "Tensor core %  ·  memory used/free  ·  power  ·  temperature"),
    (GREEN,  "Basement — Host (node_exporter)",
     "CPU  ·  network  ·  disk (overflow storage)"),
]
y = Inches(1.4)
for clr, title, detail in floors:
    add_box_with_text(s, Inches(0.6), y, Inches(12.1), Inches(1.4), [
        (title, 22, clr, True),
        (detail, 18, WHITE, False),
    ], border_color=clr)
    y += Inches(1.6)

add_box_with_text(s, Inches(2.0), Inches(6.2), Inches(9.3), Inches(0.8), [
    ("You need all three floors to diagnose a noisy neighbour.", 20, AMBER, True),
], border_color=AMBER)

set_notes(s, "Three floors of monitoring. Application, GPU hardware, host. You need all three.")


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 28 — Phase 1: Quiet Sunday Morning
# ═══════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank_layout); set_bg(s)
add_title(s, "[PRE-RECORDED] Phase 1: Quiet Sunday Morning")

tf_sub = add_textbox(s, Inches(0.8), Inches(1.0), Inches(11), Inches(0.5))
first_para(tf_sub, "[Replace with Grafana screenshot after pre-recording]", size=14,
           color=AMBER)

metric_boxes = [
    ("TTFT p99:  82 ms  ✓", GREEN), ("ITL p99:  14 ms  ✓", GREEN),
    ("Storage:  18%  ✓", GREEN),     ("Occupancy:  5", BLUE),
    ("Power:  38%", BLUE),                ("Lobby:  0  ✓", GREEN),
]
positions = [
    (Inches(0.6), Inches(1.8)), (Inches(4.6), Inches(1.8)),
    (Inches(8.6), Inches(1.8)), (Inches(0.6), Inches(3.4)),
    (Inches(4.6), Inches(3.4)), (Inches(8.6), Inches(3.4)),
]
for (text, clr), (left, top) in zip(metric_boxes, positions):
    add_box_with_text(s, left, top, Inches(3.6), Inches(1.2), [
        (text, 22, clr, True),
    ], border_color=clr)

tf2 = add_textbox(s, Inches(0.6), Inches(5.5), Inches(12.1), Inches(0.7))
first_para(tf2, "Everything quiet. Remember these numbers.", size=24, color=GREEN,
           bold=True, alignment=PP_ALIGN.CENTER)

set_notes(s, "Baseline. Quiet Sunday morning. Five tenants. Everything green. Remember these numbers.")


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 29 — Phase 2: The Renovators Arrive
# ═══════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank_layout); set_bg(s)
add_title(s, "[DEMO] Phase 2: The Renovators Arrive")

tf_sub = add_textbox(s, Inches(0.8), Inches(1.0), Inches(11), Inches(0.5))
first_para(tf_sub, "+3 renovators. Same building. Alex didn't change — the building did.",
           size=16, color=WHITE)

metric_boxes2 = [
    ("TTFT:  82 → 420 ms  ▲5x", RED),
    ("ITL:  14 → 43 ms  ▲3x", RED),
    ("Storage:  18 → 87%  DANGER", RED),
    ("Occupancy:  5 → 8  ▲", AMBER),
    ("Power:  38 → 74%  ▲", AMBER),
    ("Lobby:  0  ✓  STILL ZERO", GREEN),
]
for (text, clr), (left, top) in zip(metric_boxes2, positions):
    add_box_with_text(s, left, top, Inches(3.6), Inches(1.2), [
        (text, 20, clr, True),
    ], border_color=clr)

add_box_with_text(s, Inches(0.6), Inches(5.3), Inches(12.1), Inches(1.5), [
    ("Lobby is EMPTY. Nobody waiting to get in.", 22, GREEN, True),
    ("It's not a building shortage. It's a neighbour problem.", 22, RED, True),
], fill_color=RGBColor(0x1A, 0x0A, 0x0A), border_color=RED)

set_notes(s, "Renovators arrive. TTFT 5x slower. ITL 3x. Storage 87%. Lobby still zero. Not a building shortage — neighbours.")


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 30 — The Chain Reaction
# ═══════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank_layout); set_bg(s)
add_title(s, "The Chain Reaction")

# Chain
add_box_with_text(s, Inches(0.4), Inches(1.4), Inches(12.5), Inches(1.2), [
    ("Blake moves in → Occupancy 5→8 → Storage 18→87% → Evictions → Elevator 14→43ms → Alex: 210→482ms", 18, AMBER, True),
])

tf = add_textbox(s, Inches(0.8), Inches(3.0), Inches(11.5), Inches(0.8))
first_para(tf, "More renovators  x  more materials  =  slower for everyone", size=26,
           color=WHITE, bold=True, alignment=PP_ALIGN.CENTER)

# Wrong
add_box_with_text(s, Inches(0.6), Inches(4.0), Inches(12.1), Inches(1.2), [
    ("❌  Dashboard says:", 20, RED, True),
    ("Building 74% occupied, elevator slow →  BUILD MORE BUILDINGS", 20, RED, False),
], border_color=RED)

# Right
add_box_with_text(s, Inches(0.6), Inches(5.5), Inches(12.1), Inches(1.2), [
    ("✓  Reality:", 20, GREEN, True),
    ("Cap occupancy. Send renovators elsewhere →  FEWER NEIGHBOURS", 20, GREEN, False),
], border_color=GREEN)

set_notes(s, "The full chain. More neighbours times more stuff equals slower for everyone. Don't build more buildings. Send renovators elsewhere.")


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 31 — Six Sensors for Your Building
# ═══════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank_layout); set_bg(s)
add_title(s, "Six Sensors for Your Building")

tf_sub = add_textbox(s, Inches(0.8), Inches(1.0), Inches(11), Inches(0.5))
first_para(tf_sub, "Take a photo of this slide.", size=16, color=AMBER, bold=True)

sensors = [
    (BLUE,   "Elevator Wait (TTFT p99)",
     "histogram_quantile(0.99, rate(vllm:time_to_first_token_seconds_bucket[5m]))"),
    (AMBER,  "Elevator Speed (ITL p99) — THE SIGNAL",
     "histogram_quantile(0.99, rate(vllm:inter_token_latency_seconds_bucket[5m]))"),
    (RGBColor(0xFF, 0x88, 0x00), "Storage Fullness (KV Cache)",
     "vllm:kv_cache_usage_perc"),
    (PURPLE, "Shared Storage Hits (Prefix Cache)",
     "rate(vllm:prefix_cache_hits[5m]) / rate(vllm:prefix_cache_queries[5m])"),
    (PURPLE, "Occupancy (Batch Size)",
     "vllm:num_requests_running"),
    (RED,    "Power Load (Tensor Core)",
     "DCGM_FI_PROF_PIPE_TENSOR_ACTIVE"),
]
y = Inches(1.5)
for clr, label, query in sensors:
    add_box_with_text(s, Inches(0.5), y, Inches(12.3), Inches(0.82), [
        (label, 16, clr, True),
        (query, 13, WHITE, False, FONT_CODE),
    ], border_color=clr)
    y += Inches(0.92)

set_notes(s, "Six sensors. Elevator wait, elevator speed — THE noisy neighbour signal, storage, shared storage hits, occupancy, power load.")


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 32 — Three Fire Alarms
# ═══════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank_layout); set_bg(s)
add_title(s, "Three Fire Alarms That Work")

alarms = [
    (AMBER, "Storage > 90% for 2 minutes",
     "Evictions imminent. Cap occupancy."),
    (RED,   "Elevator wait > 2s for 5 minutes",
     "Tenants banging on doors. Scale or shed load."),
    (BLUE,  "Lobby > 0 for 3 minutes",
     "Real building shortage. Build more."),
]
y = Inches(1.5)
for clr, title, desc in alarms:
    add_box_with_text(s, Inches(0.6), y, Inches(12.1), Inches(1.4), [
        (title, 24, clr, True),
        (desc, 20, WHITE, False),
    ], border_color=clr)
    y += Inches(1.6)

tf = add_textbox(s, Inches(0.6), Inches(6.3), Inches(12.1), Inches(0.7))
first_para(tf, "Three alarms. Not thirty.", size=24, color=GREEN, bold=True,
           alignment=PP_ALIGN.CENTER)

set_notes(s, "Three alarms. Storage 90% — evictions coming. Elevator 2s — people banging doors. Lobby > 0 — real shortage.")


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 33 — Taming the Renovators
# ═══════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank_layout); set_bg(s)
add_title(s, "Taming the Renovators")

fixes = [
    (BLUE,   "1. Occupancy Cap",
     "--max-num-seqs 16",
     "Default is 256 tenants! Start at 16."),
    (PURPLE, "2. Separate Building",
     "Route by request length.",
     "Renovators get their own building. Alex keeps the express elevator."),
    (GREEN,  "3. Shared Storage",
     "--enable-prefix-caching",
     "Same system prompt = share the storage. 30-50% savings."),
    (AMBER,  "4. Scale on Lobby, Not Power",
     "Lobby count is a leading indicator.",
     "Scale when lobby > 0, not when power hits 80%."),
]
y = Inches(1.3)
for clr, title, line1, line2 in fixes:
    add_box_with_text(s, Inches(0.6), y, Inches(12.1), Inches(1.35), [
        (title, 20, clr, True),
        (line1, 16, WHITE, False, FONT_CODE),
        (line2, 16, WHITE, False),
    ], border_color=clr)
    y += Inches(1.45)

set_notes(s, "Four fixes. Cap occupancy at 16. Separate building for renovators. Shared storage for common items. Scale on lobby count, not power.")


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 34 — Monday Morning Checklist
# ═══════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank_layout); set_bg(s)
add_title(s, "Monday Morning Checklist")

items = [
    "Install elevator sensors (vLLM /metrics → Prometheus)",
    "Install power monitors (DCGM Exporter on GPU nodes)",
    "Build the 6-sensor dashboard (slide 31)",
    "Set the 3 fire alarms (slide 32)",
    "Cap occupancy  --max-num-seqs 16  (watch elevator speed)",
    "Enable shared storage  --enable-prefix-caching",
]
tf = add_textbox(s, Inches(0.8), Inches(1.5), Inches(11.5), Inches(4.5))
for i, item in enumerate(items):
    text = f"☐  {item}"
    if i == 0:
        first_para(tf, text, size=22, color=WHITE, bold=False)
    else:
        add_para(tf, text, size=22, color=WHITE, space_before=Pt(16))

tf2 = add_textbox(s, Inches(0.6), Inches(6.0), Inches(12.1), Inches(0.8))
first_para(tf2, "2-4 hours to install. 50-70% fewer complaints on mixed-tenant buildings.",
           size=22, color=GREEN, bold=True, alignment=PP_ALIGN.CENTER)

set_notes(s, "Monday morning. Six items. Two to four hours. 50 to 70 percent fewer complaints.")


# ═══════════════════════════════════════════════════════════════════════════
# SLIDE 35 — Close
# ═══════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(blank_layout); set_bg(s)

tf = add_textbox(s, Inches(1), Inches(1.0), Inches(11.3), Inches(5.5))
first_para(tf, "Next time your LLM p99 spikes...", size=32, color=WHITE, bold=True,
           alignment=PP_ALIGN.CENTER)
add_para(tf, "", size=16, color=WHITE)
add_para(tf, "don't ask 'which tenant is slow?'", size=28, color=RED,
         alignment=PP_ALIGN.CENTER, space_before=Pt(20))
add_para(tf, "", size=10, color=WHITE)
add_para(tf, "Ask: 'who else is in the building?'", size=28, color=GREEN, bold=True,
         alignment=PP_ALIGN.CENTER, space_before=Pt(12))
add_para(tf, "", size=24, color=WHITE)
add_para(tf, "github.com/Sagar2366/gpu-noisy-neighbour", size=20, color=BLUE,
         alignment=PP_ALIGN.CENTER, space_before=Pt(30))
add_para(tf, "@SaijUtekar", size=20, color=BLUE, alignment=PP_ALIGN.CENTER,
         space_before=Pt(8))
add_para(tf, "", size=16, color=WHITE)
add_para(tf, "Thank you.", size=36, color=BLUE, bold=True, alignment=PP_ALIGN.CENTER,
         space_before=Pt(20))

set_notes(s, "Next time your LLM p99 spikes, don't ask which tenant is slow. Ask: who else is in the building? Thank you.")


# ── Save ───────────────────────────────────────────────────────────────────
out = "/tmp/gpu-noisy-neighbour/slides.pptx"
prs.save(out)
print(f"Saved {len(prs.slides)} slides to {out}")

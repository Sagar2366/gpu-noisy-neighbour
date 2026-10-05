#!/usr/bin/env python3
"""
Generate a 24-slide PowerPoint for:
"The Noisy Neighbour Inside Your GPU: Observing Batched LLM Inference"
Speaker: Sagar Utekar · Senior SRE, CrowdStrike · CNCF Ambassador · Kubestronaut
Event: Observability Summit Europe 2026 · 5 Oct · 10:30-10:55 · South Hall 3A
"""

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn
import os

# ── Colors ──────────────────────────────────────────────────────────────
BG       = RGBColor(0x0A, 0x0E, 0x27)
WHITE    = RGBColor(0xE8, 0xE8, 0xE8)
BLUE     = RGBColor(0x00, 0xD4, 0xFF)
GREEN    = RGBColor(0x39, 0xFF, 0x14)
AMBER    = RGBColor(0xFF, 0xB3, 0x47)
RED      = RGBColor(0xFF, 0x44, 0x44)
PURPLE   = RGBColor(0xB8, 0x77, 0xD9)
GRAY     = RGBColor(0x88, 0x88, 0x88)
DARK_GRAY = RGBColor(0x55, 0x55, 0x55)

# Fonts
FONT_BODY = "Calibri"
FONT_CODE = "Consolas"

# Slide dimensions
SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)


def set_slide_bg(slide, color=BG):
    """Set solid background color on a slide."""
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = color


def add_textbox(slide, left, top, width, height):
    """Add a text box and return it."""
    return slide.shapes.add_textbox(left, top, width, height)


def set_text(tf, text, font_name=FONT_BODY, size=Pt(22), color=WHITE,
             bold=False, italic=False, alignment=PP_ALIGN.LEFT):
    """Set text in the first paragraph of a text frame."""
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    p.font.name = font_name
    p.font.size = size
    p.font.color.rgb = color
    p.font.bold = bold
    p.font.italic = italic
    p.alignment = alignment
    return p


def add_para(tf, text, font_name=FONT_BODY, size=Pt(22), color=WHITE,
             bold=False, italic=False, alignment=PP_ALIGN.LEFT,
             space_before=Pt(0), space_after=Pt(0)):
    """Add a new paragraph to a text frame."""
    p = tf.add_paragraph()
    p.text = text
    p.font.name = font_name
    p.font.size = size
    p.font.color.rgb = color
    p.font.bold = bold
    p.font.italic = italic
    p.alignment = alignment
    p.space_before = space_before
    p.space_after = space_after
    return p


def add_run(para, text, font_name=FONT_BODY, size=Pt(22), color=WHITE,
            bold=False, italic=False):
    """Add a run to an existing paragraph."""
    run = para.add_run()
    run.text = text
    run.font.name = font_name
    run.font.size = size
    run.font.color.rgb = color
    run.font.bold = bold
    run.font.italic = italic
    return run


def add_rounded_rect(slide, left, top, width, height, fill_color=None,
                     fill_opacity=None, border_color=None, border_width=Pt(2)):
    """Add a rounded rectangle shape."""
    shape = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height
    )
    shape.shadow.inherit = False
    # Fill
    fill = shape.fill
    if fill_color:
        fill.solid()
        fill.fore_color.rgb = fill_color
        if fill_opacity is not None:
            # Set alpha via direct XML on spPr > solidFill > srgbClr
            from lxml import etree
            spPr = shape._element.find(qn('p:spPr'))
            sf = spPr.find(qn('a:solidFill'))
            if sf is not None:
                clr = sf.find(qn('a:srgbClr'))
                if clr is not None:
                    alpha = clr.find(qn('a:alpha'))
                    if alpha is None:
                        alpha = etree.SubElement(clr, qn('a:alpha'))
                    alpha.set('val', str(int(fill_opacity * 1000)))
    else:
        fill.background()  # No fill

    # Border
    line = shape.line
    if border_color:
        line.color.rgb = border_color
        line.width = border_width
    else:
        line.fill.background()

    return shape


def shape_add_text(shape, text, font_name=FONT_BODY, size=Pt(20), color=WHITE,
                   bold=False, alignment=PP_ALIGN.LEFT):
    """Set text on a shape's text frame."""
    tf = shape.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    p.font.name = font_name
    p.font.size = size
    p.font.color.rgb = color
    p.font.bold = bold
    p.alignment = alignment
    return tf


def shape_add_para(tf, text, font_name=FONT_BODY, size=Pt(20), color=WHITE,
                   bold=False, alignment=PP_ALIGN.LEFT, space_before=Pt(0),
                   space_after=Pt(0)):
    """Add a paragraph to a shape's text frame."""
    return add_para(tf, text, font_name=font_name, size=size, color=color,
                    bold=bold, alignment=alignment, space_before=space_before,
                    space_after=space_after)


def set_notes(slide, notes_text):
    """Set speaker notes on a slide."""
    notes_slide = slide.notes_slide
    tf = notes_slide.notes_text_frame
    tf.text = notes_text


def add_title(slide, text, color=WHITE, size=Pt(36)):
    """Add a standard title at the top."""
    txBox = add_textbox(slide, Inches(0.7), Inches(0.3), Inches(12), Inches(0.8))
    set_text(txBox.text_frame, text, size=size, color=color, bold=True)
    return txBox


# ════════════════════════════════════════════════════════════════════════
# BUILD PRESENTATION
# ════════════════════════════════════════════════════════════════════════

prs = Presentation()
prs.slide_width = SLIDE_W
prs.slide_height = SLIDE_H
blank_layout = prs.slide_layouts[6]  # Blank layout


# ──────────────────────────────────────────────────────────────────────
# SLIDE 1: TITLE
# ──────────────────────────────────────────────────────────────────────
def build_slide_01(prs):
    slide = prs.slides.add_slide(blank_layout)
    set_slide_bg(slide)

    # Centered title block
    txBox = add_textbox(slide, Inches(1.5), Inches(1.0), Inches(10.333), Inches(5.5))
    tf = txBox.text_frame
    tf.word_wrap = True

    p = tf.paragraphs[0]
    p.text = "The Noisy Neighbour"
    p.font.name = FONT_BODY
    p.font.size = Pt(48)
    p.font.color.rgb = BLUE
    p.font.bold = True
    p.alignment = PP_ALIGN.CENTER

    add_para(tf, "Inside Your GPU", size=Pt(48), color=BLUE, bold=True,
             alignment=PP_ALIGN.CENTER)
    add_para(tf, "Observing Batched LLM Inference", size=Pt(24), color=WHITE,
             alignment=PP_ALIGN.CENTER, space_before=Pt(12))
    add_para(tf, "", size=Pt(16), alignment=PP_ALIGN.CENTER)  # spacer
    add_para(tf, "Sagar Utekar  ·  Senior SRE, CrowdStrike", size=Pt(22),
             color=WHITE, alignment=PP_ALIGN.CENTER, space_before=Pt(24))
    add_para(tf, "CNCF Ambassador  ·  Kubestronaut", size=Pt(18), color=WHITE,
             alignment=PP_ALIGN.CENTER, space_before=Pt(4))
    add_para(tf, "Observability Summit Europe 2026", size=Pt(20), color=AMBER,
             alignment=PP_ALIGN.CENTER, space_before=Pt(20))
    add_para(tf, "5 Oct  ·  10:30  ·  South Hall 3A", size=Pt(14), color=GRAY,
             alignment=PP_ALIGN.CENTER, space_before=Pt(8))

    set_notes(slide, "Hi, I'm Sagar. I run GPU infrastructure for AI workloads at CrowdStrike. Today we're hunting a ghost — a latency spike you can see on your dashboard but can't explain with your traces. The victim is Alex. The culprit is Blake. And they both live inside the same GPU.")
    return slide


# ──────────────────────────────────────────────────────────────────────
# SLIDE 2: "The Neighbour You Already Know"
# ──────────────────────────────────────────────────────────────────────
def build_slide_02(prs):
    slide = prs.slides.add_slide(blank_layout)
    set_slide_bg(slide)
    add_title(slide, "The Neighbour You Already Know")

    # Left box — red
    left_box = add_rounded_rect(slide, Inches(0.5), Inches(1.3), Inches(5.9), Inches(4.0),
                                fill_color=RGBColor(0xFF, 0x44, 0x44), fill_opacity=20,
                                border_color=RED, border_width=Pt(2))
    tf = shape_add_text(left_box, "\U0001F525 The CPU Problem", size=Pt(24), color=RED, bold=True)
    shape_add_para(tf, "", size=Pt(6))
    shape_add_para(tf, "Container B is a rogue batch job", size=Pt(20))
    shape_add_para(tf, "Steals CPU from your app", size=Pt(20))
    shape_add_para(tf, "Latency spikes. No errors.", size=Pt(20))
    shape_add_para(tf, "", size=Pt(8))
    shape_add_para(tf, "container_cpu_cfs_throttled_seconds_total", font_name=FONT_CODE,
                   size=Pt(16), color=GREEN)

    # Right box — green
    right_box = add_rounded_rect(slide, Inches(6.9), Inches(1.3), Inches(5.9), Inches(4.0),
                                 fill_color=RGBColor(0x39, 0xFF, 0x14), fill_opacity=20,
                                 border_color=GREEN, border_width=Pt(2))
    tf = shape_add_text(right_box, "✅ How You Fixed It", size=Pt(24), color=GREEN, bold=True)
    shape_add_para(tf, "", size=Pt(6))
    shape_add_para(tf, "cgroups → kernel isolation", size=Pt(20))
    shape_add_para(tf, "Resource limits → cap the bully", size=Pt(20))
    shape_add_para(tf, "Node pools → physical separation", size=Pt(20))
    shape_add_para(tf, "Anti-affinity → scheduling rules", size=Pt(20))

    # Bottom text
    txBox = add_textbox(slide, Inches(0.5), Inches(5.8), Inches(12.333), Inches(1.0))
    set_text(txBox.text_frame, "CPU noisy neighbours? Solved. You had soundproof walls.",
             size=Pt(22), color=GREEN, bold=True, alignment=PP_ALIGN.CENTER)

    set_notes(slide, "You've all debugged this. Container B eats CPU, your app gets throttled. You fixed it with cgroups — soundproof walls between tenants. Resource limits, node pools, anti-affinity. Problem solved. [PAUSE] Now let's talk about a building with no soundproofing.")
    return slide


# ──────────────────────────────────────────────────────────────────────
# SLIDE 3: "Now Forget Everything"
# ──────────────────────────────────────────────────────────────────────
def build_slide_03(prs):
    slide = prs.slides.add_slide(blank_layout)
    set_slide_bg(slide)
    add_title(slide, "Now Forget Everything", color=RED)

    # Left column — CPU World
    txBox = add_textbox(slide, Inches(1.0), Inches(1.4), Inches(5.0), Inches(3.5))
    tf = txBox.text_frame
    tf.word_wrap = True
    set_text(tf, "CPU World \U0001F3E2", size=Pt(28), color=GREEN, bold=True)
    add_para(tf, "✓ cgroups", size=Pt(24), color=GREEN, space_before=Pt(12))
    add_para(tf, "✓ Resource limits", size=Pt(24), color=GREEN, space_before=Pt(8))
    add_para(tf, "✓ 1 process = 1 core", size=Pt(24), color=GREEN, space_before=Pt(8))
    add_para(tf, "✓ Isolation is cheap", size=Pt(24), color=GREEN, space_before=Pt(8))

    # Right column — GPU World
    txBox = add_textbox(slide, Inches(7.333), Inches(1.4), Inches(5.0), Inches(3.5))
    tf = txBox.text_frame
    tf.word_wrap = True
    set_text(tf, "GPU World \U0001F3DA️", size=Pt(28), color=RED, bold=True)
    add_para(tf, "✗ No cgroups", size=Pt(24), color=RED, space_before=Pt(12))
    add_para(tf, "✗ No per-request limits", size=Pt(24), color=RED, space_before=Pt(8))
    add_para(tf, "✗ 32 requests = 1 chip", size=Pt(24), color=RED, space_before=Pt(8))
    add_para(tf, "✗ Isolation kills throughput", size=Pt(24), color=RED, space_before=Pt(8))

    # Bottom box
    bottom_box = add_rounded_rect(slide, Inches(0.5), Inches(5.2), Inches(12.333), Inches(1.8),
                                  fill_color=RED, fill_opacity=15,
                                  border_color=RED, border_width=Pt(2))
    tf = shape_add_text(bottom_box, "On a GPU, requests MUST share the chip. The walls are paper-thin.",
                        size=Pt(24), color=WHITE, bold=True, alignment=PP_ALIGN.CENTER)
    shape_add_para(tf, "The fix isn't soundproofing — it's installing noise monitors.",
                   size=Pt(22), color=AMBER, alignment=PP_ALIGN.CENTER, space_before=Pt(8))

    set_notes(slide, "[PAUSE — let the table sink in] GPUs don't have cgroups. There are no soundproof walls. 32 requests share one chip at the same time. You could isolate — run one request per GPU — but you'd use 10% of a $40,000 card. The fix isn't isolation. It's observability. That's what this talk is about.")
    return slide


# ──────────────────────────────────────────────────────────────────────
# SLIDE 4: "The Apartment Building"
# ──────────────────────────────────────────────────────────────────────
def build_slide_04(prs):
    slide = prs.slides.add_slide(blank_layout)
    set_slide_bg(slide)
    add_title(slide, "The Apartment Building")

    items = [
        ("\U0001F3E2  GPU = The Building", BLUE, "(the whole chip)"),
        ("\U0001F6D7  Batch = The Elevator", PURPLE, "(shared — one trip serves everyone)"),
        ("\U0001F9F3  KV Cache = The Storage Room", AMBER, "(everyone's stuff piles up)"),
        ("\U0001F464  Requests = Tenants", WHITE, "(some quick, some... not)"),
        ("\U0001F4E6  Preemption = Eviction", RED, "(your stuff moved to the basement)"),
    ]

    y = Inches(1.5)
    for emoji_text, color, sub in items:
        txBox = add_textbox(slide, Inches(1.0), y, Inches(11.0), Inches(0.7))
        tf = txBox.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        run1 = p.add_run()
        run1.text = emoji_text
        run1.font.name = FONT_BODY
        run1.font.size = Pt(28)
        run1.font.color.rgb = color
        run1.font.bold = True
        run2 = p.add_run()
        run2.text = "  " + sub
        run2.font.name = FONT_BODY
        run2.font.size = Pt(18)
        run2.font.color.rgb = WHITE
        y += Inches(0.85)

    # Bottom box
    bottom_box = add_rounded_rect(slide, Inches(1.0), Inches(5.9), Inches(11.333), Inches(0.8),
                                  border_color=GREEN, border_width=Pt(2))
    shape_add_text(bottom_box, "Keep this picture. Every slide from here maps back to it.",
                   size=Pt(20), color=GREEN, alignment=PP_ALIGN.CENTER)

    set_notes(slide, "This is the mental model for the whole talk. GPU is an apartment building. The batch is the elevator — everyone shares it. KV cache is the storage room — every tenant's stuff accumulates. When the storage room fills, someone gets evicted. Keep this picture — everything maps back to it.")
    return slide


# ──────────────────────────────────────────────────────────────────────
# SLIDE 5: "Two Phases, Two Numbers"
# ──────────────────────────────────────────────────────────────────────
def build_slide_05(prs):
    slide = prs.slides.add_slide(blank_layout)
    set_slide_bg(slide)
    add_title(slide, "Two Phases, Two Numbers")

    # Top left — PREFILL
    box = add_rounded_rect(slide, Inches(0.5), Inches(1.3), Inches(5.9), Inches(2.0),
                           fill_color=BLUE, fill_opacity=15, border_color=BLUE)
    tf = shape_add_text(box, "PREFILL", size=Pt(32), color=BLUE, bold=True,
                        alignment=PP_ALIGN.CENTER)
    shape_add_para(tf, "Read the request. Once.", size=Pt(20), alignment=PP_ALIGN.CENTER,
                   space_before=Pt(8))
    shape_add_para(tf, "Compute-bound — GPU loves this", size=Pt(18),
                   alignment=PP_ALIGN.CENTER, space_before=Pt(4))

    # Top right — DECODE
    box = add_rounded_rect(slide, Inches(6.9), Inches(1.3), Inches(5.9), Inches(2.0),
                           fill_color=PURPLE, fill_opacity=15, border_color=PURPLE)
    tf = shape_add_text(box, "DECODE", size=Pt(32), color=PURPLE, bold=True,
                        alignment=PP_ALIGN.CENTER)
    shape_add_para(tf, "Write back, one token at a time.", size=Pt(20),
                   alignment=PP_ALIGN.CENTER, space_before=Pt(8))
    shape_add_para(tf, "Memory-bound — GPU waits", size=Pt(18),
                   alignment=PP_ALIGN.CENTER, space_before=Pt(4))

    # Bottom left stat — TTFT
    box = add_rounded_rect(slide, Inches(0.5), Inches(3.9), Inches(5.9), Inches(2.8),
                           border_color=BLUE, border_width=Pt(2))
    tf = shape_add_text(box, "TTFT", size=Pt(48), color=BLUE, bold=True,
                        alignment=PP_ALIGN.CENTER)
    shape_add_para(tf, "Time to First Token", size=Pt(18), alignment=PP_ALIGN.CENTER,
                   space_before=Pt(8))
    shape_add_para(tf, "= elevator wait time", size=Pt(16), color=BLUE,
                   alignment=PP_ALIGN.CENTER, space_before=Pt(8))

    # Bottom right stat — ITL
    box = add_rounded_rect(slide, Inches(6.9), Inches(3.9), Inches(5.9), Inches(2.8),
                           border_color=AMBER, border_width=Pt(2))
    tf = shape_add_text(box, "ITL", size=Pt(48), color=AMBER, bold=True,
                        alignment=PP_ALIGN.CENTER)
    shape_add_para(tf, "Inter-Token Latency", size=Pt(18), alignment=PP_ALIGN.CENTER,
                   space_before=Pt(8))
    shape_add_para(tf, "= elevator speed ← THE SIGNAL", size=Pt(16), color=AMBER,
                   alignment=PP_ALIGN.CENTER, space_before=Pt(8))

    set_notes(slide, "Every LLM reply has two phases. Prefill reads your request — fast, once. Decode writes back one token at a time — slow, hundreds of times. Two numbers to know: TTFT is how long before the first word appears — that's the elevator wait. ITL is the gap between each word — that's how fast the elevator moves. [PAUSE] ITL is THE noisy neighbour signal. When Blake loads furniture in the elevator, ITL is what spikes.")
    return slide


# ──────────────────────────────────────────────────────────────────────
# SLIDE 6: "Meet Your Neighbours"
# ──────────────────────────────────────────────────────────────────────
def build_slide_06(prs):
    slide = prs.slides.add_slide(blank_layout)
    set_slide_bg(slide)
    add_title(slide, "Meet Your Neighbours")

    # Left box — ALEX
    box = add_rounded_rect(slide, Inches(0.5), Inches(1.3), Inches(5.9), Inches(5.5),
                           border_color=BLUE, border_width=Pt(3))
    tf = shape_add_text(box, "ALEX", size=Pt(44), color=BLUE, bold=True,
                        alignment=PP_ALIGN.CENTER)
    shape_add_para(tf, "The Quiet Tenant", size=Pt(20), alignment=PP_ALIGN.CENTER,
                   space_before=Pt(4))
    shape_add_para(tf, "", size=Pt(10))
    shape_add_para(tf, "\U0001F4AC  'Summarise this Jira ticket'", size=Pt(20),
                   space_before=Pt(8))
    shape_add_para(tf, "\U0001F4CF  64 tokens — a quick note", size=Pt(20),
                   space_before=Pt(8))
    shape_add_para(tf, "⚡  In and out in minutes", size=Pt(20),
                   space_before=Pt(8))

    # Sub-box for Alex
    sub = add_rounded_rect(slide, Inches(0.8), Inches(5.5), Inches(5.3), Inches(0.7),
                           fill_color=BLUE, fill_opacity=20)
    shape_add_text(sub, "Alex will file the noise complaint.", size=Pt(18),
                   color=WHITE, bold=True, alignment=PP_ALIGN.CENTER)

    # Right box — BLAKE
    box = add_rounded_rect(slide, Inches(6.9), Inches(1.3), Inches(5.9), Inches(5.5),
                           border_color=RED, border_width=Pt(3))
    tf = shape_add_text(box, "BLAKE", size=Pt(44), color=RED, bold=True,
                        alignment=PP_ALIGN.CENTER)
    shape_add_para(tf, "The Renovator", size=Pt(20), alignment=PP_ALIGN.CENTER,
                   space_before=Pt(4))
    shape_add_para(tf, "", size=Pt(10))
    shape_add_para(tf, "\U0001F4CA  'Write a capacity report'", size=Pt(20),
                   space_before=Pt(8))
    shape_add_para(tf, "\U0001F4CF  4,000 tokens — a 5-page plan", size=Pt(20),
                   space_before=Pt(8))
    shape_add_para(tf, "\U0001F528  Same building, same elevator", size=Pt(20),
                   space_before=Pt(8))

    # Sub-box for Blake
    sub = add_rounded_rect(slide, Inches(7.2), Inches(5.5), Inches(5.3), Inches(0.7),
                           fill_color=RED, fill_opacity=20)
    shape_add_text(sub, "Blake is about to ruin Alex's morning.", size=Pt(18),
                   color=WHITE, bold=True, alignment=PP_ALIGN.CENTER)

    set_notes(slide, "Meet your neighbours. Alex sends a quick question — 64 tokens, like a note under the door. Blake wants a 5-page capacity report — 4,000 tokens. They're in the same building, sharing the same elevator, sharing every single trip. Alex is about to have a bad morning.")
    return slide


# ──────────────────────────────────────────────────────────────────────
# SLIDE 7: "Why Everyone Shares the Elevator"
# ──────────────────────────────────────────────────────────────────────
def build_slide_07(prs):
    slide = prs.slides.add_slide(blank_layout)
    set_slide_bg(slide)
    add_title(slide, "Why Everyone Shares the Elevator")

    # Left stat
    txBox = add_textbox(slide, Inches(0.5), Inches(1.5), Inches(5.9), Inches(3.5))
    tf = txBox.text_frame
    tf.word_wrap = True
    set_text(tf, "1 tenant", size=Pt(22), color=RED, alignment=PP_ALIGN.CENTER)
    add_para(tf, "10%", size=Pt(60), color=RED, bold=True, alignment=PP_ALIGN.CENTER,
             space_before=Pt(8))
    add_para(tf, "GPU utilization", size=Pt(18), alignment=PP_ALIGN.CENTER)
    add_para(tf, "You pay for 100% of the building.", size=Pt(18), color=RED,
             alignment=PP_ALIGN.CENTER, space_before=Pt(8))

    # Right stat
    txBox = add_textbox(slide, Inches(6.9), Inches(1.5), Inches(5.9), Inches(3.5))
    tf = txBox.text_frame
    tf.word_wrap = True
    set_text(tf, "8 tenants", size=Pt(22), color=GREEN, alignment=PP_ALIGN.CENTER)
    add_para(tf, "65%", size=Pt(60), color=GREEN, bold=True, alignment=PP_ALIGN.CENTER,
             space_before=Pt(8))
    add_para(tf, "GPU utilization", size=Pt(18), alignment=PP_ALIGN.CENTER)
    add_para(tf, "Same building, 8× the revenue.", size=Pt(18), color=GREEN,
             alignment=PP_ALIGN.CENTER, space_before=Pt(8))

    # Bottom box
    box = add_rounded_rect(slide, Inches(0.5), Inches(5.2), Inches(12.333), Inches(1.2),
                           border_color=GREEN, border_width=Pt(2))
    tf = shape_add_text(box, "Continuous batching: check after every trip. Slot opens → fill it.",
                        size=Pt(20), alignment=PP_ALIGN.CENTER)
    shape_add_para(tf, "36× more tenants served vs. static batching (Orca, 2022)",
                   size=Pt(18), color=GREEN, alignment=PP_ALIGN.CENTER, space_before=Pt(4))

    # Small red text at bottom
    txBox = add_textbox(slide, Inches(0.5), Inches(6.6), Inches(12.333), Inches(0.6))
    set_text(txBox.text_frame,
             "But now everyone shares the elevator. Blake's furniture slows it for everyone.",
             size=Pt(18), color=RED, alignment=PP_ALIGN.CENTER)

    set_notes(slide, "One tenant on a GPU — 10% utilized. You're paying for a building that's 90% empty. Batch 8 tenants — 65% utilized. Continuous batching checks after every elevator trip: someone got off? Fill the spot immediately. 36× more tenants served. [PAUSE] But now they all share every trip. Blake's renovation materials slow the elevator for everyone.")
    return slide


# ──────────────────────────────────────────────────────────────────────
# SLIDE 8: "The Storage Room Crisis"
# ──────────────────────────────────────────────────────────────────────
def build_slide_08(prs):
    slide = prs.slides.add_slide(blank_layout)
    set_slide_bg(slide)
    add_title(slide, "The Storage Room Crisis")

    # Subtitle
    txBox = add_textbox(slide, Inches(0.7), Inches(1.1), Inches(12), Inches(0.5))
    set_text(txBox.text_frame, "KV Cache — every token adds to the pile",
             size=Pt(18), color=WHITE)

    # Visual: Alex boxes (small blue)
    y_row = Inches(1.9)
    box_h = Inches(1.2)
    for i in range(3):
        b = add_rounded_rect(slide, Inches(0.5 + i * 1.1), y_row, Inches(1.0), box_h,
                             fill_color=BLUE, fill_opacity=40, border_color=BLUE)
        shape_add_text(b, "Alex", size=Pt(14), color=WHITE, alignment=PP_ALIGN.CENTER)

    # Label
    txBox = add_textbox(slide, Inches(3.8), y_row, Inches(2.0), box_h)
    tf = txBox.text_frame
    tf.word_wrap = True
    set_text(tf, "8%", size=Pt(28), color=BLUE, bold=True)
    add_para(tf, "of room", size=Pt(16), color=BLUE)

    # Blake boxes (large red)
    for i in range(6):
        b = add_rounded_rect(slide, Inches(5.5 + i * 1.1), y_row, Inches(1.0), box_h,
                             fill_color=RED, fill_opacity=40, border_color=RED)
        shape_add_text(b, "Blake", size=Pt(14), color=WHITE, alignment=PP_ALIGN.CENTER)

    # Label
    txBox = add_textbox(slide, Inches(12.2), y_row, Inches(1.0), box_h)
    tf = txBox.text_frame
    tf.word_wrap = True
    set_text(tf, "79%", size=Pt(28), color=RED, bold=True)
    add_para(tf, "of room", size=Pt(16), color=RED)

    # Blake memory note
    txBox = add_textbox(slide, Inches(0.5), Inches(3.3), Inches(12.333), Inches(0.4))
    set_text(txBox.text_frame, "Blake's 4,000 tokens = ~4 GB of GPU memory",
             size=Pt(18), color=WHITE, alignment=PP_ALIGN.CENTER)

    # Red alert box
    alert = add_rounded_rect(slide, Inches(0.5), Inches(3.9), Inches(12.333), Inches(2.2),
                             fill_color=RED, fill_opacity=12, border_color=RED, border_width=Pt(2))
    tf = shape_add_text(alert, "⚠️ STORAGE FULL → EVICTION", size=Pt(28),
                        color=RED, bold=True, alignment=PP_ALIGN.CENTER)
    shape_add_para(tf, "Alex's stuff moved to basement. Must re-register when rescheduled.",
                   size=Pt(20), alignment=PP_ALIGN.CENTER, space_before=Pt(10))
    shape_add_para(tf, "That's your mystery TTFT spike.", size=Pt(20), color=AMBER,
                   alignment=PP_ALIGN.CENTER, space_before=Pt(8))

    # Code box
    txBox = add_textbox(slide, Inches(0.5), Inches(6.4), Inches(12.333), Inches(0.5))
    set_text(txBox.text_frame, "vllm:kv_cache_usage_perc  >85% = danger zone",
             font_name=FONT_CODE, size=Pt(18), color=GREEN, alignment=PP_ALIGN.CENTER)

    set_notes(slide, "KV cache is the storage room. Every token generated adds to the pile. Alex's 64 tokens — three small boxes, 8% of the room. Blake's 4,000 tokens — fills 79% of the room, about 4 gigabytes. When storage hits capacity, someone gets evicted. Their stuff goes to the basement — CPU memory or disk. When they get rescheduled, they must re-prefill from scratch. That's your mystery TTFT spike — it's not a new request, it's a re-registering tenant.")
    return slide


# ──────────────────────────────────────────────────────────────────────
# SLIDE 9: "What Alex Experiences"
# ──────────────────────────────────────────────────────────────────────
def build_slide_09(prs):
    slide = prs.slides.add_slide(blank_layout)
    set_slide_bg(slide)
    add_title(slide, "What Alex Experiences")

    # Top green box
    box = add_rounded_rect(slide, Inches(0.5), Inches(1.3), Inches(12.333), Inches(1.6),
                           border_color=GREEN, border_width=Pt(2))
    tf = shape_add_text(box, "\U0001F7E2 Alex alone:", size=Pt(24), color=GREEN)
    shape_add_para(tf, "TTFT 82ms → ITL 14ms × 64 tokens → Done in 210ms",
                   size=Pt(22), space_before=Pt(8))
    shape_add_para(tf, "Express elevator. Smooth.", size=Pt(18), color=GREEN,
                   space_before=Pt(4))

    # Bottom red box
    box = add_rounded_rect(slide, Inches(0.5), Inches(3.2), Inches(12.333), Inches(1.6),
                           border_color=RED, border_width=Pt(2))
    tf = shape_add_text(box, "\U0001F534 Alex + Blake in batch:", size=Pt(24), color=RED)
    shape_add_para(tf, "TTFT 120ms → ITL 45ms × 64 tokens → Done in 482ms",
                   size=Pt(22), space_before=Pt(8))
    shape_add_para(tf, "Same 64 tokens. 2.3× slower. Zero errors.", size=Pt(18),
                   color=RED, space_before=Pt(4))

    # Large amber text box
    box = add_rounded_rect(slide, Inches(1.5), Inches(5.2), Inches(10.333), Inches(1.8),
                           fill_color=AMBER, fill_opacity=15, border_color=AMBER, border_width=Pt(2))
    tf = shape_add_text(box, "ITL × tokens = phantom latency", size=Pt(28),
                        color=AMBER, bold=True, alignment=PP_ALIGN.CENTER)
    shape_add_para(tf, "The elevator slowed. Alex didn't change. The building did.",
                   size=Pt(22), alignment=PP_ALIGN.CENTER, space_before=Pt(10))

    set_notes(slide, "Here's what Alex feels. Alone: elevator wait 82ms, each floor 14ms, done in 210ms. With Blake: elevator wait 120ms, each floor 45ms — same 64 tokens, 2.3× slower, zero errors, zero timeouts. [PAUSE] ITL times tokens equals phantom latency. The elevator slowed down. Alex didn't change. The building did.")
    return slide


# ──────────────────────────────────────────────────────────────────────
# SLIDE 10: "Your Dashboard Lies"
# ──────────────────────────────────────────────────────────────────────
def build_slide_10(prs):
    slide = prs.slides.add_slide(blank_layout)
    set_slide_bg(slide)
    add_title(slide, "Your Dashboard Lies", color=RED)

    # Left column
    txBox = add_textbox(slide, Inches(0.5), Inches(1.3), Inches(5.9), Inches(0.5))
    set_text(txBox.text_frame, "What RED Shows", size=Pt(24), color=RED, bold=True,
             alignment=PP_ALIGN.CENTER)

    # RATE box
    box = add_rounded_rect(slide, Inches(0.5), Inches(2.0), Inches(5.9), Inches(1.0),
                           border_color=GREEN)
    tf = shape_add_text(box, "RATE                                   ✓", size=Pt(22),
                        color=GREEN, bold=True, alignment=PP_ALIGN.CENTER)

    # ERRORS box
    box = add_rounded_rect(slide, Inches(0.5), Inches(3.2), Inches(5.9), Inches(1.0),
                           border_color=GREEN)
    tf = shape_add_text(box, "ERRORS                                 0", size=Pt(22),
                        color=GREEN, bold=True, alignment=PP_ALIGN.CENTER)

    # P99 box
    box = add_rounded_rect(slide, Inches(0.5), Inches(4.4), Inches(5.9), Inches(1.0),
                           border_color=RED)
    tf = shape_add_text(box, "P99                              1.8s ✗", size=Pt(22),
                        color=RED, bold=True, alignment=PP_ALIGN.CENTER)

    # Conclusion
    box = add_rounded_rect(slide, Inches(0.5), Inches(5.6), Inches(5.9), Inches(0.8),
                           fill_color=RED, fill_opacity=15)
    shape_add_text(box, "Conclusion: slow tenants. Build more buildings.", size=Pt(18),
                   color=RED, alignment=PP_ALIGN.CENTER)

    # Right column
    txBox = add_textbox(slide, Inches(6.9), Inches(1.3), Inches(5.9), Inches(0.5))
    set_text(txBox.text_frame, "What Actually Happened", size=Pt(24), color=GREEN, bold=True,
             alignment=PP_ALIGN.CENTER)

    # Green bar (compute)
    box = add_rounded_rect(slide, Inches(6.9), Inches(2.0), Inches(1.5), Inches(0.7),
                           fill_color=GREEN, fill_opacity=60)
    shape_add_text(box, "190ms", size=Pt(14), color=WHITE, alignment=PP_ALIGN.CENTER)

    # Red bar (waiting)
    box = add_rounded_rect(slide, Inches(8.5), Inches(2.0), Inches(4.3), Inches(0.7),
                           fill_color=RED, fill_opacity=60)
    shape_add_text(box, "1,610ms WAITING", size=Pt(14), color=WHITE, alignment=PP_ALIGN.CENTER)

    # Bullets
    txBox = add_textbox(slide, Inches(7.0), Inches(3.0), Inches(5.8), Inches(2.8))
    tf = txBox.text_frame
    tf.word_wrap = True
    set_text(tf, "• Storage: 94% full", size=Pt(20), color=RED)
    add_para(tf, "• Occupancy: 28 tenants", size=Pt(20), color=AMBER, space_before=Pt(8))
    add_para(tf, "• Blake: generating 3,000+ tokens", size=Pt(20), color=RED,
             space_before=Pt(8))
    add_para(tf, "• Alex: evicted twice", size=Pt(20), color=RED, space_before=Pt(8))

    # Green conclusion box
    box = add_rounded_rect(slide, Inches(6.9), Inches(5.6), Inches(5.9), Inches(0.8),
                           fill_color=GREEN, fill_opacity=15)
    shape_add_text(box, "The tenant was fine. The building was noisy.", size=Pt(18),
                   color=GREEN, bold=True, alignment=PP_ALIGN.CENTER)

    set_notes(slide, "Your RED dashboard says: rate fine, errors zero, p99 is 1.8 seconds. Conclusion: slow tenants, build more buildings. [PAUSE] Wrong. That 1,800ms was 190 milliseconds of actual compute and 1,610 milliseconds of waiting. KV cache 94% full. 28 tenants in the batch. Blake generating 3,000 tokens. Alex got evicted twice. The tenant was fine. The building was noisy.")
    return slide


# ──────────────────────────────────────────────────────────────────────
# SLIDE 11: "Three Causes of Latency"
# ──────────────────────────────────────────────────────────────────────
def build_slide_11(prs):
    slide = prs.slides.add_slide(blank_layout)
    set_slide_bg(slide)
    add_title(slide, "Three Causes of Latency")

    box_w = Inches(3.8)
    box_h = Inches(4.2)
    gap = Inches(0.5)
    start_x = Inches(0.5)

    # Box 1 — SCHEDULING
    box = add_rounded_rect(slide, start_x, Inches(1.3), box_w, box_h,
                           border_color=BLUE, border_width=Pt(2))
    tf = shape_add_text(box, "\U0001F550", size=Pt(36), alignment=PP_ALIGN.CENTER)
    shape_add_para(tf, "SCHEDULING", size=Pt(24), color=BLUE, bold=True,
                   alignment=PP_ALIGN.CENTER, space_before=Pt(8))
    shape_add_para(tf, "Waiting in the lobby", size=Pt(18), alignment=PP_ALIGN.CENTER,
                   space_before=Pt(8))
    shape_add_para(tf, "vllm:num_requests_waiting", font_name=FONT_CODE, size=Pt(14),
                   color=GREEN, alignment=PP_ALIGN.CENTER, space_before=Pt(12))
    shape_add_para(tf, "Fix: Build more buildings", size=Pt(16), color=GREEN,
                   alignment=PP_ALIGN.CENTER, space_before=Pt(12))

    # Box 2 — MEMORY
    box = add_rounded_rect(slide, start_x + box_w + gap, Inches(1.3), box_w, box_h,
                           border_color=AMBER, border_width=Pt(2))
    tf = shape_add_text(box, "\U0001F9E0", size=Pt(36), alignment=PP_ALIGN.CENTER)
    shape_add_para(tf, "MEMORY", size=Pt(24), color=AMBER, bold=True,
                   alignment=PP_ALIGN.CENTER, space_before=Pt(8))
    shape_add_para(tf, "Storage full → evictions", size=Pt(18), alignment=PP_ALIGN.CENTER,
                   space_before=Pt(8))
    shape_add_para(tf, "vllm:kv_cache_usage_perc", font_name=FONT_CODE, size=Pt(14),
                   color=GREEN, alignment=PP_ALIGN.CENTER, space_before=Pt(12))
    shape_add_para(tf, "Fix: Occupancy cap + shared storage", size=Pt(16), color=GREEN,
                   alignment=PP_ALIGN.CENTER, space_before=Pt(12))

    # Box 3 — NEIGHBOUR
    box = add_rounded_rect(slide, start_x + 2 * (box_w + gap), Inches(1.3), box_w, box_h,
                           border_color=RED, border_width=Pt(2))
    tf = shape_add_text(box, "\U0001F465", size=Pt(36), alignment=PP_ALIGN.CENTER)
    shape_add_para(tf, "NEIGHBOUR", size=Pt(24), color=RED, bold=True,
                   alignment=PP_ALIGN.CENTER, space_before=Pt(8))
    shape_add_para(tf, "Elevator slowed by renovators", size=Pt(18), alignment=PP_ALIGN.CENTER,
                   space_before=Pt(8))
    shape_add_para(tf, "vllm:inter_token_latency_seconds", font_name=FONT_CODE, size=Pt(14),
                   color=GREEN, alignment=PP_ALIGN.CENTER, space_before=Pt(12))
    shape_add_para(tf, "Fix: Renovators → different building", size=Pt(16), color=GREEN,
                   alignment=PP_ALIGN.CENTER, space_before=Pt(12))

    # Bottom text
    txBox = add_textbox(slide, Inches(0.5), Inches(5.9), Inches(12.333), Inches(0.6))
    set_text(txBox.text_frame,
             "Your dashboard shows the complaint. These three tell you the cause.",
             size=Pt(20), color=AMBER, alignment=PP_ALIGN.CENTER)

    set_notes(slide, "Three causes. Scheduling — people waiting in the lobby, real capacity limit, build more buildings. Memory — storage room full, evictions, cap the occupancy and enable shared storage. Neighbour — Blake's furniture in the elevator, route renovators to a different building. Your dashboard shows the complaint. These three tell you the actual cause.")
    return slide


# ──────────────────────────────────────────────────────────────────────
# SLIDE 12: "The Monitoring System"
# ──────────────────────────────────────────────────────────────────────
def build_slide_12(prs):
    slide = prs.slides.add_slide(blank_layout)
    set_slide_bg(slide)
    add_title(slide, "The Monitoring System")

    cx = Inches(4.667)
    bw = Inches(4.0)

    # GRAFANA box
    box = add_rounded_rect(slide, cx, Inches(1.3), bw, Inches(1.0),
                           fill_color=BLUE, fill_opacity=25, border_color=BLUE)
    tf = shape_add_text(box, "GRAFANA", size=Pt(28), color=BLUE, bold=True,
                        alignment=PP_ALIGN.CENTER)
    shape_add_para(tf, "Security cameras", size=Pt(16), alignment=PP_ALIGN.CENTER)

    # Arrow
    txBox = add_textbox(slide, cx, Inches(2.3), bw, Inches(0.5))
    set_text(txBox.text_frame, "↓ queries", size=Pt(18), alignment=PP_ALIGN.CENTER)

    # PROMETHEUS box
    box = add_rounded_rect(slide, cx, Inches(2.8), bw, Inches(1.0),
                           fill_color=GREEN, fill_opacity=25, border_color=GREEN)
    tf = shape_add_text(box, "PROMETHEUS", size=Pt(28), color=GREEN, bold=True,
                        alignment=PP_ALIGN.CENTER)
    shape_add_para(tf, "Sensor network (every 15s)", size=Pt(16), alignment=PP_ALIGN.CENTER)

    # Arrows down
    txBox = add_textbox(slide, Inches(2.5), Inches(3.85), Inches(4.0), Inches(0.4))
    set_text(txBox.text_frame, "↙", size=Pt(24), alignment=PP_ALIGN.CENTER)
    txBox = add_textbox(slide, Inches(6.833), Inches(3.85), Inches(4.0), Inches(0.4))
    set_text(txBox.text_frame, "↘", size=Pt(24), alignment=PP_ALIGN.CENTER)

    # vLLM /metrics box
    box = add_rounded_rect(slide, Inches(1.5), Inches(4.3), Inches(4.5), Inches(1.2),
                           fill_color=BLUE, fill_opacity=20, border_color=BLUE)
    tf = shape_add_text(box, "vLLM /metrics", size=Pt(22), color=BLUE, bold=True,
                        alignment=PP_ALIGN.CENTER)
    shape_add_para(tf, "Elevator, storage, lobby", size=Pt(14), alignment=PP_ALIGN.CENTER,
                   space_before=Pt(4))

    # DCGM Exporter box
    box = add_rounded_rect(slide, Inches(7.333), Inches(4.3), Inches(4.5), Inches(1.2),
                           fill_color=RED, fill_opacity=20, border_color=RED)
    tf = shape_add_text(box, "DCGM Exporter", size=Pt(22), color=RED, bold=True,
                        alignment=PP_ALIGN.CENTER)
    shape_add_para(tf, "Power, temperature, structure", size=Pt(14), alignment=PP_ALIGN.CENTER,
                   space_before=Pt(4))

    # Bottom text
    txBox = add_textbox(slide, Inches(0.5), Inches(6.0), Inches(12.333), Inches(0.6))
    set_text(txBox.text_frame, "Four components. All open-source. No vendor lock-in.",
             size=Pt(18), color=BLUE, alignment=PP_ALIGN.CENTER)

    set_notes(slide, "Quick architecture slide. Grafana is the security camera. Prometheus is the sensor network scraping every 15 seconds. Two sources: vLLM metrics for elevator speed, storage, lobby — that's the application layer. DCGM Exporter for power, temperature, structural load — that's the GPU hardware layer. Four components, all open-source. Moving on.")
    return slide


# ──────────────────────────────────────────────────────────────────────
# SLIDE 13: "[DEMO] Quiet Morning"
# ──────────────────────────────────────────────────────────────────────
def build_slide_13(prs):
    slide = prs.slides.add_slide(blank_layout)
    set_slide_bg(slide)
    add_title(slide, "[PRE-RECORDED] Quiet Sunday Morning")

    txBox = add_textbox(slide, Inches(0.7), Inches(1.1), Inches(12), Inches(0.4))
    set_text(txBox.text_frame, "5 Alexes. All quiet. Replace with Grafana screenshot.",
             size=Pt(18), color=GRAY)

    metrics = [
        ("TTFT p99", "82ms", GREEN),
        ("ITL p99", "14ms", GREEN),
        ("Storage", "18%", GREEN),
        ("Occupancy", "5", BLUE),
        ("Power", "38%", BLUE),
        ("Lobby", "0", GREEN),
    ]

    box_w = Inches(3.8)
    box_h = Inches(1.8)
    gap_x = Inches(0.5)
    gap_y = Inches(0.3)
    start_x = Inches(0.5)
    start_y = Inches(1.8)

    for i, (label, value, color) in enumerate(metrics):
        col = i % 3
        row = i // 3
        x = start_x + col * (box_w + gap_x)
        y = start_y + row * (box_h + gap_y)

        box = add_rounded_rect(slide, x, y, box_w, box_h,
                               border_color=color, border_width=Pt(2))
        tf = shape_add_text(box, label, size=Pt(18), color=GRAY, alignment=PP_ALIGN.CENTER)
        shape_add_para(tf, value, size=Pt(36), color=color, bold=True,
                       alignment=PP_ALIGN.CENTER, space_before=Pt(8))

    # Bottom text
    txBox = add_textbox(slide, Inches(0.5), Inches(6.3), Inches(12.333), Inches(0.6))
    set_text(txBox.text_frame, "Everything flat. Everything green. Remember these numbers.",
             size=Pt(22), color=GREEN, bold=True, alignment=PP_ALIGN.CENTER)

    set_notes(slide, "This is the pre-recorded baseline. Five Alexes, quiet Sunday morning. [Read each metric] TTFT 82 milliseconds. ITL 14 milliseconds. Storage 18%. Occupancy 5. Power 38%. Lobby zero. [PAUSE] Everything flat. Everything green. Remember these six numbers. I'm about to change three of them dramatically.")
    return slide


# ──────────────────────────────────────────────────────────────────────
# SLIDE 14: "[DEMO] Blake Arrives"
# ──────────────────────────────────────────────────────────────────────
def build_slide_14(prs):
    slide = prs.slides.add_slide(blank_layout)
    set_slide_bg(slide)
    add_title(slide, "[DEMO] The Renovators Arrive")

    txBox = add_textbox(slide, Inches(0.7), Inches(1.1), Inches(12), Inches(0.4))
    set_text(txBox.text_frame,
             "+3 Blakes. Same building. Alex didn't change — the building did.",
             size=Pt(18), color=WHITE)

    metrics = [
        ("TTFT", "82 → 420ms", "▲ 5×", RED),
        ("ITL", "14 → 43ms", "▲ 3×", RED),
        ("Storage", "18 → 87%", "▲ DANGER", RED),
        ("Occupancy", "5 → 8", "▲ +3", AMBER),
        ("Power", "38 → 74%", "▲ 2×", AMBER),
        ("Lobby", "0", "✓ STILL ZERO", GREEN),
    ]

    box_w = Inches(3.8)
    box_h = Inches(1.8)
    gap_x = Inches(0.5)
    gap_y = Inches(0.3)
    start_x = Inches(0.5)
    start_y = Inches(1.8)

    for i, (label, value, delta, color) in enumerate(metrics):
        col = i % 3
        row = i // 3
        x = start_x + col * (box_w + gap_x)
        y = start_y + row * (box_h + gap_y)

        box = add_rounded_rect(slide, x, y, box_w, box_h,
                               border_color=color, border_width=Pt(2))
        tf = shape_add_text(box, label, size=Pt(18), color=GRAY, alignment=PP_ALIGN.CENTER)
        shape_add_para(tf, value, size=Pt(28), color=color, bold=True,
                       alignment=PP_ALIGN.CENTER, space_before=Pt(4))
        shape_add_para(tf, delta, size=Pt(18), color=color, bold=True,
                       alignment=PP_ALIGN.CENTER, space_before=Pt(4))

    # Bottom text
    txBox = add_textbox(slide, Inches(0.5), Inches(6.3), Inches(12.333), Inches(0.6))
    set_text(txBox.text_frame,
             "Lobby is EMPTY. It's not a building shortage. It's a neighbour problem.",
             size=Pt(24), color=RED, bold=True, alignment=PP_ALIGN.CENTER)

    set_notes(slide, "[Dramatic pause before revealing each metric] Three Blakes move in. TTFT — 5× slower. ITL — 3× slower. Storage jumps to 87 percent. Occupancy goes to 8. Power doubles to 74. [LONG PAUSE] And the lobby? Still zero. Nobody is waiting to get in. [PAUSE] This is not a building shortage. This is a noisy neighbour problem. The GPU isn't overloaded — it's sharing badly.")
    return slide


# ──────────────────────────────────────────────────────────────────────
# SLIDE 15: "The Chain Reaction"
# ──────────────────────────────────────────────────────────────────────
def build_slide_15(prs):
    slide = prs.slides.add_slide(blank_layout)
    set_slide_bg(slide)
    add_title(slide, "The Chain Reaction")

    chain = [
        ("Blake\nmoves in", RED),
        ("Occupancy\n5→8", AMBER),
        ("Storage\n18→87%", RED),
        ("Evictions\nstart", RED),
        ("ITL\n14→43ms", AMBER),
        ("Alex:\n210→482ms", RED),
    ]

    box_w = Inches(1.7)
    box_h = Inches(1.5)
    gap = Inches(0.35)
    start_x = Inches(0.5)
    y = Inches(1.5)

    for i, (text, color) in enumerate(chain):
        x = start_x + i * (box_w + gap)
        box = add_rounded_rect(slide, x, y, box_w, box_h,
                               fill_color=color, fill_opacity=25, border_color=color)
        shape_add_text(box, text, size=Pt(16), color=WHITE, bold=True,
                       alignment=PP_ALIGN.CENTER)
        # Arrow between boxes
        if i < len(chain) - 1:
            arr_x = x + box_w
            txBox = add_textbox(slide, arr_x, y + Inches(0.5), gap, Inches(0.5))
            set_text(txBox.text_frame, "→", size=Pt(24), color=WHITE,
                     alignment=PP_ALIGN.CENTER)

    # Big text
    txBox = add_textbox(slide, Inches(0.5), Inches(3.5), Inches(12.333), Inches(0.8))
    set_text(txBox.text_frame,
             "More renovators × more stuff = slower elevator for everyone",
             size=Pt(24), color=WHITE, bold=True, alignment=PP_ALIGN.CENTER)

    # Red box
    box = add_rounded_rect(slide, Inches(0.5), Inches(4.6), Inches(12.333), Inches(1.0),
                           fill_color=RED, fill_opacity=15, border_color=RED)
    shape_add_text(box, "❌ Dashboard: GPU 74%, p99 up → BUILD MORE BUILDINGS",
                   size=Pt(20), color=RED, alignment=PP_ALIGN.CENTER)

    # Green box
    box = add_rounded_rect(slide, Inches(0.5), Inches(5.8), Inches(12.333), Inches(1.0),
                           fill_color=GREEN, fill_opacity=15, border_color=GREEN)
    shape_add_text(box, "✓ Reality: Cap occupancy. Rehouse renovators. → FEWER NEIGHBOURS",
                   size=Pt(20), color=GREEN, alignment=PP_ALIGN.CENTER)

    set_notes(slide, "The chain reaction in one picture. Blake moves in. Occupancy grows. Storage fills. Evictions start. ITL spikes. Alex goes from 210 to 482 milliseconds. [PAUSE] Your dashboard says: GPU at 74%, latency doubled, build more buildings. The real answer: cap the occupancy, send renovators to their own building. You don't need more buildings. You need fewer neighbours.")
    return slide


# ──────────────────────────────────────────────────────────────────────
# SLIDE 16: "Six Sensors for Your Building"
# ──────────────────────────────────────────────────────────────────────
def build_slide_16(prs):
    slide = prs.slides.add_slide(blank_layout)
    set_slide_bg(slide)
    add_title(slide, "Six Sensors for Your Building")

    txBox = add_textbox(slide, Inches(0.7), Inches(1.1), Inches(12), Inches(0.4))
    set_text(txBox.text_frame, "\U0001F4F8 Take a photo of this slide.", size=Pt(18),
             color=AMBER)

    sensors = [
        ("\U0001F535 Elevator Wait (TTFT p99)",
         "histogram_quantile(0.99,\n  rate(vllm:time_to_first_token_seconds_bucket[5m]))",
         "How long to get in?", BLUE, False),
        ("\U0001F7E1 Elevator Speed (ITL p99) — THE SIGNAL",
         "histogram_quantile(0.99,\n  rate(vllm:inter_token_latency_seconds_bucket[5m]))",
         "How fast does it move?", AMBER, True),
        ("\U0001F7E0 Storage (KV Cache)",
         "vllm:kv_cache_usage_perc",
         ">85% = danger zone", AMBER, False),
        ("\U0001F7E3 Shared Storage Hits",
         "rate(vllm:prefix_cache_hits[5m]) /\n  rate(vllm:prefix_cache_queries[5m])",
         "Re-reading the same mail?", PURPLE, False),
        ("\U0001F7E3 Occupancy (Batch)",
         "vllm:num_requests_running",
         "How crowded is the building?", PURPLE, False),
        ("\U0001F534 Power Load (Tensor)",
         "DCGM_FI_PROF_PIPE_TENSOR_ACTIVE",
         "Computing or idling?", RED, False),
    ]

    box_w = Inches(3.9)
    box_h = Inches(1.8)
    gap_x = Inches(0.4)
    gap_y = Inches(0.2)
    start_x = Inches(0.4)
    start_y = Inches(1.6)

    for i, (label, code, desc, color, highlight) in enumerate(sensors):
        col = i % 3
        row = i // 3
        x = start_x + col * (box_w + gap_x)
        y = start_y + row * (box_h + gap_y)

        border_w = Pt(3) if highlight else Pt(2)
        fill_c = color if highlight else None
        fill_o = 15 if highlight else None
        box = add_rounded_rect(slide, x, y, box_w, box_h,
                               fill_color=fill_c, fill_opacity=fill_o,
                               border_color=color, border_width=border_w)
        tf = shape_add_text(box, label, size=Pt(13), color=color, bold=True)
        shape_add_para(tf, code, font_name=FONT_CODE, size=Pt(11), color=GREEN,
                       space_before=Pt(4))
        shape_add_para(tf, desc, size=Pt(12), color=WHITE, space_before=Pt(4))

    set_notes(slide, "Six sensors. Take a photo — this is what you'll build Monday. [Point to each] TTFT: elevator wait. ITL — THE signal — elevator speed. KV cache: storage fullness, over 85% is danger. Prefix cache hit rate: are we re-reading mail we already read? Batch size: building occupancy. Tensor core: is the GPU actually working or just heating the room? ITL is number two and it's the one that changes everything.")
    return slide


# ──────────────────────────────────────────────────────────────────────
# SLIDE 17: "Three Alarms"
# ──────────────────────────────────────────────────────────────────────
def build_slide_17(prs):
    slide = prs.slides.add_slide(blank_layout)
    set_slide_bg(slide)
    add_title(slide, "Three Alarms. Not Thirty.")

    # Box 1
    box = add_rounded_rect(slide, Inches(0.5), Inches(1.5), Inches(12.333), Inches(1.4),
                           fill_color=AMBER, fill_opacity=15, border_color=AMBER)
    tf = shape_add_text(box, "⚠️  Storage > 90% for 2 minutes", size=Pt(24),
                        color=AMBER, bold=True)
    shape_add_para(tf, "Evictions imminent. Cap occupancy immediately.", size=Pt(20),
                   space_before=Pt(8))

    # Box 2
    box = add_rounded_rect(slide, Inches(0.5), Inches(3.2), Inches(12.333), Inches(1.4),
                           fill_color=RED, fill_opacity=15, border_color=RED)
    tf = shape_add_text(box, "\U0001F6A8  Elevator wait > 2s for 5 minutes", size=Pt(24),
                        color=RED, bold=True)
    shape_add_para(tf, "Tenants banging on doors. Scale or shed load.", size=Pt(20),
                   space_before=Pt(8))

    # Box 3
    box = add_rounded_rect(slide, Inches(0.5), Inches(4.9), Inches(12.333), Inches(1.4),
                           fill_color=BLUE, fill_opacity=15, border_color=BLUE)
    tf = shape_add_text(box, "\U0001F4CA  Lobby > 0 for 3 minutes", size=Pt(24),
                        color=BLUE, bold=True)
    shape_add_para(tf, "Real building shortage. Build more.", size=Pt(20),
                   space_before=Pt(8))

    # Bottom text
    txBox = add_textbox(slide, Inches(0.5), Inches(6.5), Inches(12.333), Inches(0.6))
    set_text(txBox.text_frame, "Three alarms. Not thirty.", size=Pt(24), color=GREEN,
             bold=True, alignment=PP_ALIGN.CENTER)

    set_notes(slide, "Three alarms. Storage over 90% for 2 minutes — evictions are imminent, cap occupancy now. TTFT over 2 seconds for 5 minutes — tenants are banging on the door, scale up or shed load. Lobby greater than zero for 3 minutes — this is a real capacity limit, time to build more. Three alarms. Not thirty. You can set these up in 20 minutes.")
    return slide


# ──────────────────────────────────────────────────────────────────────
# SLIDE 18: "Taming the Renovators"
# ──────────────────────────────────────────────────────────────────────
def build_slide_18(prs):
    slide = prs.slides.add_slide(blank_layout)
    set_slide_bg(slide)
    add_title(slide, "Taming the Renovators")

    box_w = Inches(5.9)
    box_h = Inches(2.6)
    gap_x = Inches(0.5)
    gap_y = Inches(0.3)

    # Box 1 — Occupancy Cap
    box = add_rounded_rect(slide, Inches(0.5), Inches(1.3), box_w, box_h,
                           border_color=BLUE, border_width=Pt(2))
    tf = shape_add_text(box, "1. Occupancy Cap", size=Pt(24), color=BLUE, bold=True)
    shape_add_para(tf, "--max-num-seqs 16", font_name=FONT_CODE, size=Pt(18), color=GREEN,
                   space_before=Pt(8))
    shape_add_para(tf, "Default is 256. Start at 16.", size=Pt(18), space_before=Pt(8))
    shape_add_para(tf, "Watch ITL as you tune up.", size=Pt(16), color=AMBER,
                   space_before=Pt(4))

    # Box 2 — Separate Building
    box = add_rounded_rect(slide, Inches(6.9), Inches(1.3), box_w, box_h,
                           border_color=PURPLE, border_width=Pt(2))
    tf = shape_add_text(box, "2. Separate Building", size=Pt(24), color=PURPLE, bold=True)
    shape_add_para(tf, "Route by estimated output length", size=Pt(18), space_before=Pt(8))
    shape_add_para(tf, "Short requests (<256 tok) → Pool A", size=Pt(16), color=BLUE,
                   space_before=Pt(6))
    shape_add_para(tf, "Long requests (>256 tok) → Pool B", size=Pt(16), color=RED,
                   space_before=Pt(4))

    # Box 3 — Shared Storage
    box = add_rounded_rect(slide, Inches(0.5), Inches(1.3 + box_h + gap_y), box_w, box_h,
                           border_color=GREEN, border_width=Pt(2))
    tf = shape_add_text(box, "3. Shared Storage", size=Pt(24), color=GREEN, bold=True)
    shape_add_para(tf, "--enable-prefix-caching", font_name=FONT_CODE, size=Pt(18),
                   color=GREEN, space_before=Pt(8))
    shape_add_para(tf, "Same system prompt → share the cache", size=Pt(18),
                   space_before=Pt(8))
    shape_add_para(tf, "30-50% memory savings", size=Pt(16), color=GREEN,
                   space_before=Pt(4))

    # Box 4 — Scale on Lobby
    box = add_rounded_rect(slide, Inches(6.9), Inches(1.3 + box_h + gap_y), box_w, box_h,
                           border_color=AMBER, border_width=Pt(2))
    tf = shape_add_text(box, "4. Scale on Lobby", size=Pt(24), color=AMBER, bold=True)
    shape_add_para(tf, "Lobby count = leading indicator", size=Pt(18), space_before=Pt(8))
    shape_add_para(tf, "Power usage = lagging indicator", size=Pt(18), space_before=Pt(6))
    shape_add_para(tf, "Scale when lobby > 0, not power > 80%", size=Pt(16), color=AMBER,
                   space_before=Pt(4))

    set_notes(slide, "Four ways to tame Blake. [One] Cap occupancy at 16 — the default is 256, that's 256 tenants sharing one elevator, madness. Start at 16, watch ITL as you tune up. [Two] Separate building — route short and long requests to different GPU pools. [Three] Enable shared storage — prefix caching reuses KV cache for common system prompts, saves 30-50% memory. [Four] Scale on lobby count, not power usage. Lobby is a leading indicator. Power is lagging.")
    return slide


# ──────────────────────────────────────────────────────────────────────
# SLIDE 19: "PagedAttention: Why This Works"
# ──────────────────────────────────────────────────────────────────────
def build_slide_19(prs):
    slide = prs.slides.add_slide(blank_layout)
    set_slide_bg(slide)
    add_title(slide, "PagedAttention: Why This Works")

    # Left column — Before
    box = add_rounded_rect(slide, Inches(0.5), Inches(1.3), Inches(5.9), Inches(4.0),
                           border_color=RED, border_width=Pt(2))
    tf = shape_add_text(box, "Before", size=Pt(28), color=RED, bold=True,
                        alignment=PP_ALIGN.CENTER)
    shape_add_para(tf, "", size=Pt(6))
    shape_add_para(tf, "Contiguous memory allocation", size=Pt(20), space_before=Pt(8))
    shape_add_para(tf, "Pre-reserve max context per request", size=Pt(20), space_before=Pt(8))
    shape_add_para(tf, "60-80% of allocated memory WASTED", size=Pt(22), color=RED,
                   bold=True, space_before=Pt(12))
    shape_add_para(tf, "Can't do continuous batching efficiently", size=Pt(18),
                   space_before=Pt(8))

    # Right column — After
    box = add_rounded_rect(slide, Inches(6.9), Inches(1.3), Inches(5.9), Inches(4.0),
                           border_color=GREEN, border_width=Pt(2))
    tf = shape_add_text(box, "After (vLLM)", size=Pt(28), color=GREEN, bold=True,
                        alignment=PP_ALIGN.CENTER)
    shape_add_para(tf, "", size=Pt(6))
    shape_add_para(tf, "Virtual memory-style paging", size=Pt(20), space_before=Pt(8))
    shape_add_para(tf, "Fixed-size blocks allocated on demand", size=Pt(20), space_before=Pt(8))
    shape_add_para(tf, "Near-zero waste", size=Pt(22), color=GREEN, bold=True,
                   space_before=Pt(12))
    shape_add_para(tf, "Enables dynamic slot-filling", size=Pt(18), space_before=Pt(8))

    # Bottom links
    txBox = add_textbox(slide, Inches(0.5), Inches(5.8), Inches(12.333), Inches(0.5))
    set_text(txBox.text_frame,
             "\U0001F517 Interactive visualization: understandingdata.com/ai-engineering-visualised/kv-cache/",
             size=Pt(16), color=BLUE, alignment=PP_ALIGN.CENTER)

    txBox = add_textbox(slide, Inches(0.5), Inches(6.3), Inches(12.333), Inches(0.4))
    set_text(txBox.text_frame, "Credit: James Phoenix", size=Pt(14), color=GRAY,
             alignment=PP_ALIGN.CENTER)

    set_notes(slide, "Why does continuous batching actually work? PagedAttention. Before: you pre-reserved the full context length for every request — like reserving an entire storage unit for each tenant even if they only bring one box. 60 to 80 percent waste. After: vLLM allocates fixed-size blocks on demand, like virtual memory. Near-zero waste. This is what enables dynamic slot-filling. James Phoenix has an amazing interactive visualization of this at understandingdata.com — link is on the slide.")
    return slide


# ──────────────────────────────────────────────────────────────────────
# SLIDE 20: "Disaggregate Prefill & Decode"
# ──────────────────────────────────────────────────────────────────────
def build_slide_20(prs):
    slide = prs.slides.add_slide(blank_layout)
    set_slide_bg(slide)
    add_title(slide, "Advanced: Disaggregate Prefill & Decode")

    # Left box — The Conflict
    box = add_rounded_rect(slide, Inches(0.5), Inches(1.3), Inches(5.9), Inches(4.5),
                           border_color=RED, border_width=Pt(2))
    tf = shape_add_text(box, "The Conflict", size=Pt(24), color=RED, bold=True)
    shape_add_para(tf, "", size=Pt(6))
    shape_add_para(tf, "Prefill = compute-heavy (GPU goes brrrr)", size=Pt(20),
                   space_before=Pt(10))
    shape_add_para(tf, "Decode = memory-heavy (GPU waits)", size=Pt(20), space_before=Pt(10))
    shape_add_para(tf, "Running both on same GPU → head-of-line blocking", size=Pt(18),
                   color=RED, space_before=Pt(12))
    shape_add_para(tf, "Blake's prefill starves Alex's decode", size=Pt(18), color=RED,
                   space_before=Pt(8))

    # Right box — The Fix
    box = add_rounded_rect(slide, Inches(6.9), Inches(1.3), Inches(5.9), Inches(4.5),
                           border_color=GREEN, border_width=Pt(2))
    tf = shape_add_text(box, "The Fix", size=Pt(24), color=GREEN, bold=True)
    shape_add_para(tf, "", size=Pt(6))
    shape_add_para(tf, "Prefill workers ← dedicated pool", size=Pt(20), space_before=Pt(10))
    shape_add_para(tf, "Decode workers ← dedicated pool", size=Pt(20), space_before=Pt(10))
    shape_add_para(tf, "TTFT stays fast (prefill not blocked)", size=Pt(18), color=GREEN,
                   space_before=Pt(12))
    shape_add_para(tf, "ITL stays stable (decode not starved)", size=Pt(18), color=GREEN,
                   space_before=Pt(8))

    # Bottom text
    txBox = add_textbox(slide, Inches(0.5), Inches(6.2), Inches(12.333), Inches(0.6))
    set_text(txBox.text_frame,
             "Emerging pattern in TensorRT-LLM, Sarathi-Serve, Splitwise. Watch this space.",
             size=Pt(18), color=GRAY, alignment=PP_ALIGN.CENTER)

    set_notes(slide, "For the advanced folks. The prefill phase is compute-bound — GPU loves it. The decode phase is memory-bound — GPU waits. Running both on the same device causes head-of-line blocking. Blake's massive prefill starves Alex's decode. The cutting-edge fix: separate worker pools. Prefill goes to dedicated GPUs. Decode goes to dedicated GPUs. TTFT stays fast. ITL stays stable. This is emerging in TensorRT-LLM and Sarathi-Serve. Watch this space.")
    return slide


# ──────────────────────────────────────────────────────────────────────
# SLIDE 21: "Monday Morning"
# ──────────────────────────────────────────────────────────────────────
def build_slide_21(prs):
    slide = prs.slides.add_slide(blank_layout)
    set_slide_bg(slide)
    add_title(slide, "Monday Morning")

    items = [
        "□  Install elevator sensors → vLLM /metrics to Prometheus",
        "□  Install power monitors → DCGM Exporter on GPU nodes",
        "□  Build the 6-sensor dashboard (slide 16)",
        "□  Set the 3 alarms (slide 17)",
        "□  Set occupancy cap → --max-num-seqs 16, watch ITL",
        "□  Enable shared storage → --enable-prefix-caching",
    ]

    txBox = add_textbox(slide, Inches(1.0), Inches(1.4), Inches(11.333), Inches(4.8))
    tf = txBox.text_frame
    tf.word_wrap = True
    set_text(tf, items[0], size=Pt(22))
    for item in items[1:]:
        add_para(tf, item, size=Pt(22), space_before=Pt(18))

    # Bottom box
    box = add_rounded_rect(slide, Inches(0.5), Inches(5.8), Inches(12.333), Inches(1.0),
                           fill_color=GREEN, fill_opacity=15, border_color=GREEN)
    shape_add_text(box, "2-4 hours to install. 50-70% fewer complaints on mixed-tenant buildings.",
                   size=Pt(24), color=GREEN, bold=True, alignment=PP_ALIGN.CENTER)

    set_notes(slide, "Monday morning, six items. Install elevator sensors — expose vLLM metrics to Prometheus. Install power monitors — DCGM Exporter on your GPU nodes. Build the six-sensor dashboard from slide 16. Set the three alarms from slide 17. Cap occupancy at 16, watch ITL as you tune. Enable shared storage with prefix caching. Two to four hours of work. 50 to 70 percent p99 reduction on mixed workloads. That's the ROI of observing your neighbours.")
    return slide


# ──────────────────────────────────────────────────────────────────────
# SLIDE 22: "The Closing Line"
# ──────────────────────────────────────────────────────────────────────
def build_slide_22(prs):
    slide = prs.slides.add_slide(blank_layout)
    set_slide_bg(slide)

    txBox = add_textbox(slide, Inches(1.5), Inches(2.0), Inches(10.333), Inches(4.0))
    tf = txBox.text_frame
    tf.word_wrap = True

    set_text(tf, "Next time your LLM p99 spikes...", size=Pt(28), alignment=PP_ALIGN.CENTER)
    add_para(tf, "", size=Pt(20))  # spacer
    add_para(tf, "don't ask 'which tenant is slow?'", size=Pt(28), color=RED, bold=True,
             alignment=PP_ALIGN.CENTER, space_before=Pt(12))
    add_para(tf, "", size=Pt(20))  # spacer
    add_para(tf, "Ask: 'who else is in the building?'", size=Pt(32), color=GREEN, bold=True,
             alignment=PP_ALIGN.CENTER, space_before=Pt(12))

    set_notes(slide, "[Slow, deliberate delivery] Next time your LLM p99 spikes... don't ask which tenant is slow. [PAUSE] Ask: who else is in the building. [PAUSE] Thank you.")
    return slide


# ──────────────────────────────────────────────────────────────────────
# SLIDE 23: "Resources"
# ──────────────────────────────────────────────────────────────────────
def build_slide_23(prs):
    slide = prs.slides.add_slide(blank_layout)
    set_slide_bg(slide)
    add_title(slide, "Resources")

    resources = [
        ("\U0001F4CA  Dashboard & Demo", "github.com/Sagar2366/gpu-noisy-neighbour", BLUE),
        ("\U0001F3A5  KV Cache Visual", "understandingdata.com/ai-engineering-visualised/kv-cache/", BLUE),
        ("\U0001F3A5  Prefill/Decode Visual", "understandingdata.com/ai-engineering-visualised/prefill-decode/", BLUE),
        ("\U0001F4C4  PagedAttention Paper", "arxiv.org/abs/2309.06180", WHITE),
        ("\U0001F4C4  Orca Paper", "arxiv.org/abs/2206.00364", WHITE),
        ("\U0001F4C4  Continuous Batching Explainer", "pub.towardsai.net — Vedanti", WHITE),
    ]

    txBox = add_textbox(slide, Inches(0.7), Inches(1.3), Inches(12.0), Inches(5.0))
    tf = txBox.text_frame
    tf.word_wrap = True

    first = True
    for label, url, color in resources:
        if first:
            p = tf.paragraphs[0]
            first = False
        else:
            p = tf.add_paragraph()
            p.space_before = Pt(10)

        run1 = p.add_run()
        run1.text = label + "  "
        run1.font.name = FONT_BODY
        run1.font.size = Pt(22)
        run1.font.color.rgb = color

        run2 = p.add_run()
        run2.text = url
        run2.font.name = FONT_BODY
        run2.font.size = Pt(18)
        run2.font.color.rgb = BLUE

    # Twitter
    p = tf.add_paragraph()
    p.space_before = Pt(24)
    run = p.add_run()
    run.text = "\U0001F426  @SaijUtekar"
    run.font.name = FONT_BODY
    run.font.size = Pt(22)
    run.font.color.rgb = BLUE

    # Credit
    p = tf.add_paragraph()
    p.space_before = Pt(16)
    run = p.add_run()
    run.text = "Animations credit: James Phoenix / understandingdata.com"
    run.font.name = FONT_BODY
    run.font.size = Pt(16)
    run.font.color.rgb = GRAY

    set_notes(slide, "Everything's on GitHub — the slides, the demo infrastructure, the Grafana dashboard, the load generator. The links to James Phoenix's visualizations are there too — amazing interactive explainers for KV cache and prefill/decode. Find me on Twitter at @SaijUtekar. Questions?")
    return slide


# ──────────────────────────────────────────────────────────────────────
# SLIDE 24: "Q&A"
# ──────────────────────────────────────────────────────────────────────
def build_slide_24(prs):
    slide = prs.slides.add_slide(blank_layout)
    set_slide_bg(slide)

    txBox = add_textbox(slide, Inches(1.5), Inches(2.0), Inches(10.333), Inches(3.5))
    tf = txBox.text_frame
    tf.word_wrap = True

    set_text(tf, "Q & A", size=Pt(60), color=BLUE, bold=True, alignment=PP_ALIGN.CENTER)
    add_para(tf, "", size=Pt(16))
    add_para(tf, "github.com/Sagar2366/gpu-noisy-neighbour", size=Pt(20),
             alignment=PP_ALIGN.CENTER, space_before=Pt(16))
    add_para(tf, "@SaijUtekar", size=Pt(18), color=BLUE, alignment=PP_ALIGN.CENTER,
             space_before=Pt(12))

    set_notes(slide, "Prepared answers — [1] TGI: yes, same dynamics, different metric names. [2] Multi-GPU / tensor parallelism: same problem, batch shared across all GPUs in the TP group. [3] How to route by length without knowing output in advance: estimate from prompt structure + historical data, 'write a detailed report' → long pool. [4] Can you just set max_num_seqs to 1: yes but throughput drops 10-20×, the goal is managing not disabling. [5] What model size matters: any model using continuous batching, more visible with larger models because KV per token is bigger.")
    return slide


# ════════════════════════════════════════════════════════════════════════
# BUILD ALL SLIDES
# ════════════════════════════════════════════════════════════════════════

build_slide_01(prs)
build_slide_02(prs)
build_slide_03(prs)
build_slide_04(prs)
build_slide_05(prs)
build_slide_06(prs)
build_slide_07(prs)
build_slide_08(prs)
build_slide_09(prs)
build_slide_10(prs)
build_slide_11(prs)
build_slide_12(prs)
build_slide_13(prs)
build_slide_14(prs)
build_slide_15(prs)
build_slide_16(prs)
build_slide_17(prs)
build_slide_18(prs)
build_slide_19(prs)
build_slide_20(prs)
build_slide_21(prs)
build_slide_22(prs)
build_slide_23(prs)
build_slide_24(prs)


# ════════════════════════════════════════════════════════════════════════
# SAVE
# ════════════════════════════════════════════════════════════════════════

output_dir = "/tmp/gpu-noisy-neighbour"
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, "slides-v2.pptx")
prs.save(output_path)

file_size = os.path.getsize(output_path)
print(f"Saved: {output_path}")
print(f"Size:  {file_size:,} bytes ({file_size / 1024:.1f} KB)")
print(f"Slides: {len(prs.slides)}")

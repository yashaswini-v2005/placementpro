import json, os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, HRFlowable,
    Table, TableStyle, KeepTogether)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY

# ── Palette matching sample resume (clean minimal, black/gray) ────────
BLACK  = colors.HexColor('#0d0d0d')
DARK   = colors.HexColor('#1a1a1a')
TEXT   = colors.HexColor('#2c2c2c')
MUTED  = colors.HexColor('#555555')
LINE   = colors.HexColor('#cccccc')
WHITE  = colors.white

W, H = A4  # 595 x 842 pt

def ps(name, **kw):
    base = dict(fontName='Helvetica', fontSize=10, textColor=TEXT, leading=14, spaceAfter=0)
    base.update(kw)
    return ParagraphStyle(name, **base)

def safe(row, key, default=''):
    try:
        val = row[key]
        return val if val is not None else default
    except: return default

def generate_resume_pdf(user, profile):
    os.makedirs('static/resumes', exist_ok=True)
    uid = user['id'] if user else 'unknown'
    filepath = f"static/resumes/resume_{uid}.pdf"

    def load_json(key):
        try:
            raw = profile[key] if profile else None
            if raw: return json.loads(raw)
        except: pass
        return []

    skills   = load_json('skills')
    projects = load_json('projects')
    certs    = load_json('certificates')

    name     = safe(user,    'name',    'Student Name')
    email    = safe(user,    'email',   '')
    phone    = safe(profile, 'phone',   '')
    linkedin = safe(profile, 'linkedin','')
    branch   = safe(profile, 'branch',  '')
    cgpa     = safe(profile, 'cgpa',    '')
    dob      = safe(profile, 'dob',     '')

    LM = 18*mm; RM = 18*mm; TM = 18*mm; BM = 18*mm
    doc = SimpleDocTemplate(filepath, pagesize=A4,
        leftMargin=LM, rightMargin=RM, topMargin=TM, bottomMargin=BM)
    TW = W - LM - RM   # total usable width  ≈ 159 mm

    story = []

    # ══════════════════════════════════════════════════════════════════
    # HEADER — Name large, then contact line below (matches sample)
    # ══════════════════════════════════════════════════════════════════
    story.append(Paragraph(name,
        ps('hname', fontName='Helvetica-Bold', fontSize=22,
           textColor=BLACK, leading=26, alignment=TA_LEFT)))
    story.append(Spacer(1, 1.5*mm))

    # Contact line: email   phone   linkedin
    contact_parts = []
    if email:    contact_parts.append(email)
    if phone:    contact_parts.append(phone)
    if linkedin: contact_parts.append(linkedin)
    contact_str = '   '.join(contact_parts)
    if contact_str:
        story.append(Paragraph(contact_str,
            ps('hcontact', fontSize=9.5, textColor=MUTED, leading=13)))
    story.append(Spacer(1, 2*mm))
    story.append(HRFlowable(width='100%', thickness=0.8, color=LINE))
    story.append(Spacer(1, 3*mm))

    # ── helper: section heading ────────────────────────────────────
    def sec(title):
        return [
            Paragraph(title.upper(),
                ps('sh', fontName='Helvetica-Bold', fontSize=9,
                   textColor=BLACK, leading=12, letterSpacing=1.5)),
            HRFlowable(width='100%', thickness=0.7, color=LINE, spaceAfter=3),
            Spacer(1, 1*mm),
        ]

    # ══════════════════════════════════════════════════════════════════
    # SUMMARY
    # ══════════════════════════════════════════════════════════════════
    about = ''
    if branch:
        about = (f"{branch} undergraduate with strong foundations in programming, "
                 f"data analysis, and software development. Experienced in building "
                 f"projects and applying analytical skills to solve real-world problems.")
    else:
        about = ("Computer Science undergraduate with strong programming and analytical skills. "
                 "Experienced in building academic and personal projects using modern tools and technologies.")

    story += sec('Summary')
    story.append(Paragraph(about,
        ps('ab', fontSize=9.5, textColor=TEXT, leading=14.5, alignment=TA_JUSTIFY)))
    story.append(Spacer(1, 5*mm))

    # ══════════════════════════════════════════════════════════════════
    # PROJECTS
    # ══════════════════════════════════════════════════════════════════
    if projects:
        story += sec('Project')
        for p in projects:
            if not isinstance(p, dict): continue
            pname = p.get('name', '').strip()
            pdesc = p.get('desc', '').strip()
            purl  = p.get('url',  '').strip()
            if not pname: continue

            # Project title row
            title_row = Table([[
                Paragraph(f'<b>{pname}</b>',
                    ps('pname', fontName='Helvetica-Bold', fontSize=10,
                       textColor=DARK, leading=13)),
                Paragraph('Academic Project',
                    ps('ptype', fontSize=9, textColor=MUTED, leading=13,
                       alignment=TA_RIGHT)),
            ]], colWidths=[TW*0.70, TW*0.30])
            title_row.setStyle(TableStyle([
                ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
                ('LEFTPADDING',(0,0),(-1,-1),0),
                ('RIGHTPADDING',(0,0),(-1,-1),0),
                ('TOPPADDING',(0,0),(-1,-1),0),
                ('BOTTOMPADDING',(0,0),(-1,-1),0),
            ]))
            story.append(title_row)

            # Tech / URL sub-line
            sub_parts = []
            if purl: sub_parts.append(purl)
            if sub_parts:
                story.append(Paragraph(' • '.join(sub_parts),
                    ps('purl', fontSize=8.5, textColor=MUTED, leading=11)))

            # Description as bullet
            if pdesc:
                story.append(Paragraph(f'• {pdesc}',
                    ps('pdesc', fontSize=9.5, textColor=TEXT,
                       leading=14, leftIndent=4*mm)))
            story.append(Spacer(1, 3.5*mm))
        story.append(Spacer(1, 2*mm))

    # ══════════════════════════════════════════════════════════════════
    # EDUCATION
    # ══════════════════════════════════════════════════════════════════
    story += sec('Education')
    deg_label = f'Bachelor of Technology (B.Tech) – {branch}' if branch else "Bachelor's Programme"
    edu_block = KeepTogether([
        Table([[
            Paragraph(f'<b>{deg_label}</b>',
                ps('edeg', fontName='Helvetica-Bold', fontSize=10, textColor=DARK, leading=13)),
            Paragraph('2020 – 2024',
                ps('eyear', fontSize=9.5, textColor=MUTED, leading=13, alignment=TA_RIGHT)),
        ]], colWidths=[TW*0.72, TW*0.28],
        style=TableStyle([
            ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
            ('LEFTPADDING',(0,0),(-1,-1),0),
            ('RIGHTPADDING',(0,0),(-1,-1),0),
            ('TOPPADDING',(0,0),(-1,-1),0),
            ('BOTTOMPADDING',(0,0),(-1,-1),0),
        ])),
        Paragraph('University / College Name, India',
            ps('euni', fontSize=9.5, textColor=MUTED, leading=13)),
    ])
    story.append(edu_block)
    if cgpa:
        story.append(Paragraph(f'CGPA: {cgpa} / 10',
            ps('ecgpa', fontSize=9.5, textColor=TEXT, leading=13)))
    story.append(Spacer(1, 5*mm))

    # ══════════════════════════════════════════════════════════════════
    # CERTIFICATIONS
    # ══════════════════════════════════════════════════════════════════
    if certs:
        story += sec('Certifications')
        for c in certs:
            if not isinstance(c, dict): continue
            title  = c.get('title',  '').strip()
            issuer = c.get('issuer', '').strip()
            year   = c.get('year',   '').strip()
            if not title: continue
            cert_block = KeepTogether([
                Table([[
                    Paragraph(f'<b>{title}</b>',
                        ps('ctitle', fontName='Helvetica-Bold', fontSize=10,
                           textColor=DARK, leading=13)),
                    Paragraph(year,
                        ps('cyear', fontSize=9, textColor=MUTED, leading=13,
                           alignment=TA_RIGHT)),
                ]], colWidths=[TW*0.80, TW*0.20],
                style=TableStyle([
                    ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
                    ('LEFTPADDING',(0,0),(-1,-1),0),
                    ('RIGHTPADDING',(0,0),(-1,-1),0),
                    ('TOPPADDING',(0,0),(-1,-1),0),
                    ('BOTTOMPADDING',(0,0),(-1,-1),0),
                ])),
                Paragraph(issuer,
                    ps('ciss', fontSize=9.5, textColor=MUTED, leading=12)),
            ])
            story.append(cert_block)
            story.append(Spacer(1, 3*mm))
        story.append(Spacer(1, 2*mm))

    # ══════════════════════════════════════════════════════════════════
    # SKILLS
    # ══════════════════════════════════════════════════════════════════
    if skills:
        story += sec('Skills')
        # Group into categories if they follow "Category: skill1, skill2" pattern
        # Otherwise just output as single line like sample resume
        skill_line = ' | '.join(str(s) for s in skills)
        story.append(Paragraph(skill_line,
            ps('skline', fontSize=9.5, textColor=TEXT, leading=14.5)))
        story.append(Spacer(1, 3*mm))

    # ══════════════════════════════════════════════════════════════════
    # DECLARATION
    # ══════════════════════════════════════════════════════════════════
    story.append(Spacer(1, 4*mm))
    story.append(HRFlowable(width='100%', thickness=0.5, color=LINE))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(
        'I hereby declare that all information furnished above is true and correct to the best of my knowledge.',
        ps('decl', fontSize=8, textColor=MUTED, leading=11)))
    story.append(Spacer(1, 3*mm))
    story.append(Table([[
        Paragraph('Place: _______________', ps('s1', fontSize=8.5, textColor=MUTED)),
        Paragraph('Date: _______________',  ps('s2', fontSize=8.5, textColor=MUTED, alignment=TA_CENTER)),
        Paragraph(f'({name})', ps('s3', fontSize=8.5, textColor=DARK, alignment=TA_RIGHT)),
    ]], colWidths=[TW/3]*3,
    style=TableStyle([
        ('LEFTPADDING',(0,0),(-1,-1),0),
        ('RIGHTPADDING',(0,0),(-1,-1),0),
    ])))

    doc.build(story)
    return filepath

from io import BytesIO
from xml.sax.saxutils import escape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT

def build_pack(case, run, actions, supplier_context):
    result=run['result']; out=BytesIO(); styles=getSampleStyleSheet(); styles['BodyText'].fontSize=9; styles['BodyText'].leading=13; styles.add(ParagraphStyle('Evidence',parent=styles['BodyText'],fontSize=8,leading=11))
    story=[]
    def p(text,style='BodyText'):
        paragraph=Paragraph(escape(str(text)),styles[style])
        if style.startswith('Heading') or style=='Title': story.append(paragraph);story.append(Spacer(1,7))
        else: story.append(KeepTogether([paragraph,Spacer(1,2 if style=='Evidence' else 7)]))
    p('BSES x AIONOS','Title'); p('Procurement Negotiation Intelligence','Heading2'); p('DEMO / SYNTHETIC - Advisory internal negotiation pack','Heading3')
    p('Management summary','Heading1'); p(case['title']); p(f"Case {case['id']} | Run / Evidence Card {run['id']} | Review: {case['status']}")
    p(result.get('narrative',{}).get('explanation',result['explanation'])); p('Potential opportunity is a negotiation estimate, never realized savings.')
    metrics=[['Measure',result['quote']['currency']+' / quoted unit'],['Supplier quotation',result['quote']['unit_price']],['Historical best',result.get('best','Abstained')],['Historical median',result.get('median','Abstained')],['Fair-value band',f"{result.get('lower','N/A')} to {result.get('upper','N/A')}"],['Proposed target',result.get('target','Not recommended')],['Potential opportunity ('+result['quote']['currency']+')',result.get('opportunity','Not recommended')]]
    t=Table(metrics,colWidths=[270,200]); t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#142c4c')),('TEXTCOLOR',(0,0),(-1,0),colors.white),('GRID',(0,0),(-1,-1),.3,colors.HexColor('#dce3ed')),('PADDING',(0,0),(-1,-1),8)])); story.append(t)
    p(result['walk_away']); p('Challenge price: use the provisional target only after human comparator review; no separate approved challenge-price policy.')
    p('Evidence quality and limitations','Heading2'); p(result['evidence_quality'])
    for x in result['limitations']: p(x)
    story.append(PageBreak()); p('Case, supplier and negotiation strategy','Heading1')
    q=result['quote']
    fields=[('Quote / supplier',f"{q['id']} / {q['supplier']}"),('Material',q['material']),('Technical specification',q['specification']),('Date / quantity',f"{q['date']} / {q['quantity']} {q['uom']}"),('Commercial treatment',f"{q['currency']} / {q['tax']} / {q['payment_days']} days"),('Location / delivery',f"{q['location']} / {q['delivery']}"),('Source reference',q['source_ref'])]
    qt=Table([[Paragraph(escape(str(k)),styles['BodyText']),Paragraph(escape(str(v)),styles['BodyText'])] for k,v in fields],colWidths=[145,370]);qt.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('BOTTOMPADDING',(0,0),(-1,-1),7),('LINEBELOW',(0,0),(-1,-1),.2,colors.HexColor('#dce3ed'))]));story.append(qt);story.append(Spacer(1,12))
    p('Supplier performance and permitted risk evidence','Heading2')
    for item in supplier_context: p(item)
    if not supplier_context: p('Supplier performance or official risk evidence unavailable. No adverse finding is inferred.')
    for label,key in [('Negotiation questions','questions'),('Challenge points','challenge_points'),('Possible concessions','concessions')]:
        p(label,'Heading2')
        for value in (result.get('narrative',{}).get(key) or result[key]): p(value)
    p('Key price drivers','Heading2'); p('Specification, unit, quantity eligibility, date, tax, payment, delivery and location are screened explicitly. Only registered UoM conversions are applied.')
    p('Reviewer history','Heading2')
    for action in actions: p(f"{action['created']} | {action['actor']} | {action['action']} | {action['comment']}")
    if not actions: p('No reviewer actions. Recommendation is unapproved.')
    story.append(PageBreak()); p('Source and transformation evidence','Heading1'); p(f"Evidence observation captured by run at {run['created']} | Engine {result.get('engine_version','legacy v1')}"); p(f"Dataset snapshot: {case['snapshot_id']} | Rule: {run['rule_id']} | Result SHA256: {run['sha256']}")
    p('Included comparator set','Heading2')
    for row in result['included']: p(f"{row['id']} | source {row['source_ref']} | {row['transformation']} | original: {row['original']}",'Evidence')
    p('Excluded observations','Heading2')
    for row in result['excluded']: p(f"{row['id']}: {'; '.join(row['reasons'])}",'Evidence')
    p('Methodology and provenance','Heading2'); p({k:result.get('narrative',{}).get(k) for k in ['provider_status','prompt_version','model','evidence_hash']},'Evidence'); p(result['rule'],'Evidence'); p('Source hashes establish retained-file integrity, not independent source authenticity. Demo sources are synthetic, internally generated and unauthenticated as business evidence.','Evidence')
    def footer(canvas,doc):
        canvas.setFont('Helvetica',8); canvas.setFillColor(colors.HexColor('#52657b')); canvas.drawString(40,25,'DEMO / SYNTHETIC | Confidential internal review | No automatic procurement action'); canvas.drawRightString(555,25,str(doc.page))
    SimpleDocTemplate(out,pagesize=(595,842),rightMargin=40,leftMargin=40,topMargin=36,bottomMargin=44).build(story,onFirstPage=footer,onLaterPages=footer)
    return out.getvalue()

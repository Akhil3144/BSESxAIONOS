"""Chrome end-to-end regression of read-only procurement intelligence and existing UI."""
import argparse,json,os
from datetime import date,timedelta
from decimal import Decimal
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--base-url',default='http://127.0.0.1:8002');args=parser.parse_args()
password=dict(l.split('=',1) for l in (ROOT/'.env').read_text().splitlines() if '=' in l)['DEMO_PASSWORD']
out=ROOT/'output/procurement-intelligence';out.mkdir(parents=True,exist_ok=True)
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless=True)
    page=browser.new_page(viewport={'width':1512,'height':1100});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto(args.base_url);page.locator('[name=username]').fill('admin');page.locator('[name=password]').fill(password)
    page.get_by_role('button',name='Sign in',exact=True).click();page.get_by_role('heading',name='Negotiation intelligence',exact=True).wait_for()
    nav=page.locator('nav');assert nav.get_by_role('button').nth(1).inner_text().endswith('Procurement Intelligence')
    nav.get_by_role('button',name='Procurement Intelligence',exact=False).click();page.get_by_role('heading',name='Three-month cable price trend',exact=True).wait_for()
    assert page.get_by_text('SYNTHETIC DEMONSTRATION — NOT LIVE MARKET PRICES',exact=True).count()==1
    assert page.locator('.trend-months button').count()==3
    assert page.get_by_role('heading',name='INSUFFICIENT EVIDENCE',exact=True).count()==1
    page.locator('.trend-point').first.focus();assert 'original observations' in page.locator('#trend-tooltip').inner_text()
    page.locator('.trend-months button').first.click();assert page.locator('#trend-evidence tbody tr').count()==2
    # Read the same authenticated API for numerical consistency and immutable case checks.
    data=page.evaluate("""async()=>{const headers={Authorization:'Bearer '+sessionStorage.getItem('token')};const cases=await (await fetch('/api/cases',{headers})).json();const c=cases.find(c=>c.title==='DEMO / SYNTHETIC - 11 kV XLPE cable lot 1');const before=await (await fetch('/api/cases/'+c.id,{headers})).json();const intelligence=await (await fetch('/api/procurement-intelligence?case_id='+c.id,{headers})).json();return {id:c.id,before,intelligence};}""")
    i=data['intelligence'];today=date.fromisoformat(i['trend']['as_of']);f=page.locator('#timing-form')
    f.locator('[name=quantity_m]').fill('5000');f.locator('[name=current_quote_per_metre]').fill('600')
    page.get_by_role('button',name='Evaluate purchase scenario').click();page.locator('#timing-result').filter(has_text='30,00,000').wait_for()
    # Review explicit scenario assumptions and exercise an urgent within-band order.
    f.locator('[name=quantity_m]').fill('1000');f.locator('[name=current_quote_per_metre]').fill(i['benchmark']['median'])
    f.locator('[name=planned_purchase_date]').fill(today.isoformat());f.locator('[name=required_delivery_date]').fill((today+timedelta(days=7)).isoformat());f.locator('[name=supplier_lead_time_days]').fill('5')
    page.get_by_text('Review scenario assumptions before interpreting a recommendation',exact=True).click()
    for key in ['requirement_confirmed','current_quote_confirmed','commercial_terms_confirmed','benchmark_applicability_reviewed']:f.locator('[name='+key+']').check()
    page.get_by_role('button',name='Evaluate purchase scenario').click();page.get_by_role('heading',name='BUY NOW',exact=True).wait_for()
    page.screenshot(path=str(out/'intelligence-desktop.png'),full_page=True)
    # Proposed future price remains explicitly assumed and delivery feasibility remains independent.
    f.locator('[name=assumed_future_price_per_metre]').fill('610');f.locator('[name=supplier_lead_time_days]').fill('10')
    page.get_by_role('button',name='Evaluate purchase scenario').click();page.get_by_role('heading',name='INSUFFICIENT EVIDENCE',exact=True).wait_for()
    assert 'User-entered assumed price' in page.locator('#timing-result').inner_text()
    page.get_by_role('button',name='Ask about purchase timing',exact=False).click()
    page.get_by_role('button',name='Should procurement wait until next month?',exact=True).click()
    page.locator('.chat-message.assistant').filter(has_text='Future prices are uncertain').wait_for()
    assert 'INSUFFICIENT EVIDENCE' in page.locator('.chat-message.assistant').last.inner_text()
    assert page.locator('[data-evidence-kind="trend"]').count()>=6
    page.locator('[data-evidence-kind="trend"]').first.click();page.get_by_role('heading',name='Three-month cable price trend',exact=True).wait_for()
    page.get_by_role('button',name='Reset assumptions',exact=True).click();page.get_by_role('heading',name='INSUFFICIENT EVIDENCE',exact=True).wait_for()
    page.set_viewport_size({'width':390,'height':844});assert page.evaluate('document.documentElement.scrollWidth<=window.innerWidth+1')
    page.screenshot(path=str(out/'intelligence-mobile.png'),full_page=True);page.set_viewport_size({'width':1512,'height':1100})
    # Existing feature regressions: benchmark, Evidence Card, source directory, pack and tour controls.
    nav.get_by_role('button',name='Price Benchmarking',exact=False).click();page.get_by_text('External Market References',exact=True).wait_for()
    nav.get_by_role('button',name='Supplier & Evidence',exact=False).click();page.get_by_role('heading',name='Evidence Card',exact=True).wait_for()
    nav.get_by_role('button',name='Data Sources',exact=False).click();page.get_by_role('heading',name='Public Source Directory',exact=True).wait_for()
    page.get_by_role('button',name='Inspect trend observations',exact=False).click();page.get_by_role('heading',name='Three-month cable price trend',exact=True).wait_for()
    nav.get_by_role('button',name='Reports & Validation',exact=False).click()
    with page.expect_download() as download:page.get_by_role('button',name='Download Negotiation Pack',exact=False).click()
    download.value.save_as(str(out/'existing-negotiation-pack.pdf'))
    page.locator('#side-guide').click();page.locator('.tour-panel').wait_for()
    headings=[]
    while True:
        page.locator('.tour-panel h2').wait_for()
        heading=page.locator('.tour-panel h2').inner_text();headings.append(heading)
        if len(headings)==3:
            page.locator('#tour-back').click();page.locator('.tour-panel h2').filter(has_text='Inspect cable price movement').wait_for()
            page.locator('#tour-next').click();page.locator('.tour-panel h2').filter(has_text=heading).wait_for()
        final=page.locator('#tour-next').inner_text()=='Finish demo'
        if final:
            page.locator('#tour-next').click();page.wait_for_function("!document.querySelector('.tour-panel')");break
        page.locator('#tour-skip' if 'Try a timing scenario' in heading else '#tour-next').click()
        page.locator('.tour-panel h2').wait_for()
        page.wait_for_function("old=>document.querySelector('.tour-panel h2')?.textContent!==old",arg=heading)
    assert any('buying decision' in h for h in headings) and any('purchase timing' in h for h in headings)
    page.locator('#side-guide').click();page.locator('#tour-exit').click();assert page.locator('.tour-panel').count()==0
    after=page.evaluate("""async(id)=>{const headers={Authorization:'Bearer '+sessionStorage.getItem('token')};return (await fetch('/api/cases/'+id,{headers})).json();}""",data['id'])
    assert after==data['before'],'Simulator or tour changed the saved case'
    assert not errors,errors
    report={'browser':'Google Chrome','base_url':args.base_url,'trend_and_chart':'passed','simulator_states':'passed','assumed_future_price':'passed','chat_numerical_context':'passed','mobile':'passed','benchmark_evidence_sources_pack':'passed','tour_steps':len(headings),'case_unchanged':True,'javascript_errors':errors}
    (out/'verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
    browser.close()

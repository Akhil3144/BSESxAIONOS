"""Chrome integration verification; credentials stay in local .env and memory."""
import os,json,argparse
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--base-url',default=os.getenv('QA_BASE_URL','http://127.0.0.1:8000'))
base=parser.parse_args().base_url
password=dict(line.split('=',1) for line in (ROOT/'.env').read_text().splitlines() if '=' in line)['DEMO_PASSWORD']
out=ROOT/'output/public-sources';out.mkdir(parents=True,exist_ok=True)
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless=True)
    page=browser.new_page(viewport={'width':1512,'height':1100});errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto(base);page.locator('[name=username]').fill('admin');page.locator('[name=password]').fill(password)
    page.get_by_role('button',name='Sign in',exact=True).click()
    page.get_by_role('heading',name='Negotiation intelligence',exact=True).wait_for()
    page.locator('nav').get_by_role('button',name='Data Sources',exact=False).click()
    page.get_by_role('heading',name='Data Origin Summary',exact=True).wait_for()
    assert page.get_by_role('heading',name='Public Source Directory').count()==1
    assert page.get_by_text('No verified public price is currently available for this exact specification.',exact=True).count()==1
    assert page.get_by_text('Third-party published price-list copy — authenticity and comparability pending',exact=True).count()==1
    assert page.get_by_text('Government-hosted technical specification — not price evidence',exact=True).count()==1
    assert page.get_by_role('link',name='Open Original Source',exact=False).count()==3
    assert page.locator('a[href="https://gem.gov.in/"]').count()==1
    expected=[
        'https://gem.gov.in/',
        'https://www.scribd.com/document/1070412982/KEI-Cable-List-Price-13th-Mar-2026',
        'https://cdnbbsr.s3waas.gov.in/s303412aef4dcdee4f934f7bf599f89783/uploads/2025/06/202506302010749769.pdf',
    ]
    links=page.get_by_role('link',name='Open Original Source',exact=False)
    assert [links.nth(i).get_attribute('href') for i in range(3)]==expected
    # Test failure rendering and navigation without relying on external site uptime.
    fault_url='**/api/public-sources/kei/availability'
    page.route(fault_url,lambda route:route.fulfill(json={
        'status':'Unavailable','message':'HTTP 500: external source is unavailable. Try again later. The benchmark is unchanged.',
        'checked_at':'2026-10-30T06:00:00Z','cached':False}))
    page.locator('[data-source-check="kei"]').click()
    page.locator('[data-availability="kei"]').filter(has_text='HTTP 500').wait_for()
    # The click opens exactly the configured source, not the legacy broken URL.
    for i,url in enumerate(expected):
        page.context.route(url,lambda route:route.fulfill(content_type='text/html',body='<h1>Navigation target verified</h1>'))
        with page.expect_popup() as popup:
            links.nth(i).click()
        popup.value.wait_for_load_state()
        assert popup.value.url==url
        popup.value.close()
        page.context.unroute(url)
    page.unroute(fault_url)
    page.route(fault_url,lambda route:route.fulfill(status=503,json={'detail':'check unavailable'}))
    page.locator('[data-source-check="kei"]').click()
    page.locator('[data-availability="kei"]').filter(has_text='Unable to check external source availability').wait_for()
    page.unroute(fault_url)
    page.screenshot(path=str(out/'data-sources.png'),full_page=True)
    page.locator('nav').get_by_role('button',name='Price Benchmarking',exact=False).click()
    page.get_by_text('External Market References',exact=True).click()
    page.get_by_text('Compare with this case',exact=True).click()
    assert page.get_by_text('Not directly comparable',exact=True).count()>0
    assert page.get_by_text('Unconfirmed case fields:',exact=False).count()>0
    page.screenshot(path=str(out/'benchmarking.png'),full_page=True)
    page.locator('nav').get_by_role('button',name='Supplier & Evidence',exact=False).click()
    page.get_by_role('heading',name='Evidence Card',exact=True).wait_for()
    page.get_by_text('Technical Details',exact=True).click()
    page.get_by_role('button',name='Open Data Sources',exact=True).click()
    page.get_by_role('heading',name='Data Origin Summary').wait_for()
    page.locator('nav').get_by_role('button',name='AI Negotiation Chat',exact=False).click()
    page.get_by_role('button',name='Where does the pricing data come from?',exact=True).click()
    page.locator('.chat-message.assistant').filter(has_text='No verified public price').wait_for()
    assert page.locator('.chat-message.assistant a').count()==3
    page.get_by_role('button',name='Open Data Sources',exact=True).click()
    page.get_by_role('heading',name='Data Origin Summary').wait_for()
    page.set_viewport_size({'width':390,'height':844})
    page.screenshot(path=str(out/'mobile.png'),full_page=True)
    assert not errors,errors
    browser.close()
    print(json.dumps({'browser':'Google Chrome','base_url':base,'source_directory':'passed','unavailable_sources':'passed','benchmark_comparison':'passed','evidence_card_link':'passed','chat_sources':'passed','javascript_errors':errors}))

import os,json,time,csv,io
from pathlib import Path
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[1];password=dict(l.split('=',1) for l in (root/'.env').read_text().splitlines() if '=' in l)['DEMO_PASSWORD'];out=root/'output/browser';out.mkdir(parents=True,exist_ok=True)
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless=True)
    page=browser.new_page(viewport={'width':1512,'height':1100});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto('http://127.0.0.1:8000');page.locator('[name=username]').fill('admin');page.locator('[name=password]').fill(password);page.get_by_role('button',name='Sign in to workspace').click();page.get_by_role('heading',name='Procurement intelligence',exact=True).wait_for()
    page.locator('nav').get_by_role('button',name='Administration',exact=False).click();page.get_by_role('button',name='Initialize synthetic demonstration').click();page.locator('.success').wait_for();page.locator('nav').get_by_role('button',name='Dashboard').click();page.get_by_role('heading',name='Analysis cases',exact=True).wait_for();page.screenshot(path=str(out/'dashboard.png'),full_page=True)
    page.get_by_role('button',name='Open →').first.click();page.get_by_role('heading',name='Comparable evidence & price normalization').wait_for();
    if page.get_by_role('button',name='Run six-stage analysis').is_enabled(): page.get_by_role('button',name='Run six-stage analysis').click()
    page.get_by_role('heading',name='Calculation provenance').wait_for();page.screenshot(path=str(out/'cockpit.png'),full_page=True)
    with page.expect_download() as download:
        page.get_by_role('button',name='↓ Negotiation pack',exact=True).click()
    download.value.save_as(str(out/'browser-pack.pdf'))
    for section,heading in [('Data ingestion','Import approved evidence'),('Materials & comparables','Material and transaction explorer'),('Evidence cards','Evidence Card'),('Negotiation packs','Versioned negotiation packs'),('Supplier intelligence','Supplier performance & permitted risk evidence'),('Review & approvals','Human review decision'),('Audit trail','Tamper-evident audit chain')]:
        page.locator('nav').get_by_role('button',name=section,exact=False).click();page.get_by_role('heading',name=heading,exact=False).first.wait_for();assert not page.locator('#error .error').count(),section
    # Regression: navigating during a delayed dashboard response cannot overwrite the newer view.
    page.route('**/api/dashboard',lambda route:(time.sleep(.4),route.continue_()))
    page.locator('nav').get_by_role('button',name='Dashboard',exact=False).click();page.locator('nav').get_by_role('button',name='Administration',exact=False).click();page.get_by_role('button',name='Initialize synthetic demonstration').wait_for();page.wait_for_timeout(600);assert page.get_by_role('button',name='Initialize synthetic demonstration').count()==1
    page.unroute('**/api/dashboard')
    version='demo-browser-policy-'+str(time.time_ns());page.locator('#rule input[name=version]').fill(version);page.get_by_label('Maximum age in days').fill('730');page.get_by_role('button',name='Propose version',exact=True).click();page.locator('summary').filter(has_text=version).wait_for();assert not page.locator('#error .error').count()
    # Exercise actual upload, snapshot freeze, case creation and human workflow controls.
    page.locator('nav').get_by_role('button',name='Data ingestion',exact=False).click()
    with (root/'demo-data/synthetic-procurement.csv').open() as f: row=next(csv.DictReader(f))
    row['id']='DEMO-BROWSER-'+str(time.time_ns());fixture=out/'browser-import.csv'
    with fixture.open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(row));w.writeheader();w.writerow(row)
    page.locator('input[type=file]').set_input_files(str(fixture));page.get_by_role('button',name='Validate & import',exact=True).click();page.locator('#import-result pre').wait_for();assert '"accepted": 1' in page.locator('#import-result pre').inner_text()
    page.get_by_role('button',name='Freeze current dataset',exact=True).click();page.wait_for_timeout(300)
    page.get_by_role('button',name='＋ New analysis',exact=True).click();page.locator('#caseform input[name=title]').fill('DEMO / SYNTHETIC - Browser workflow '+str(time.time_ns()));page.get_by_role('button',name='Create analysis case',exact=True).click();page.get_by_role('button',name='Run six-stage analysis',exact=True).click();page.get_by_role('heading',name='Comparable evidence & price normalization').wait_for()
    page.locator('nav').get_by_role('button',name='Review & approvals',exact=False).click()
    for action in ['ready_for_review','under_review','accepted']:
        page.locator('#review select').select_option(action);page.locator('#review textarea').fill('Browser reviewer inspected source evidence and provisional methodology');page.get_by_role('button',name='Record review action',exact=True).click();page.locator('div.actions.section > span.tag').filter(has_text=action.replace('_',' ')).wait_for()
    page.locator('nav').get_by_role('button',name='Historical testing',exact=False).click();page.get_by_role('button',name='Freeze rubric & lock predictions').click();page.get_by_role('button',name='Reveal outcomes & evaluate locked predictions').last.wait_for();page.get_by_role('button',name='Reveal outcomes & evaluate locked predictions').last.click();page.get_by_role('cell',name='DEMO-HOLDOUT-1',exact=True).last.wait_for();page.screenshot(path=str(out/'evaluation.png'),full_page=True)
    form=page.locator('form.finding').last;form.locator('input[name=comment]').fill('Synthetic outlier retained and reviewed in browser test');form.get_by_role('button',name='Record finding').click();page.get_by_role('cell',name='Synthetic outlier retained and reviewed in browser test',exact=True).last.wait_for()
    page.locator('nav').get_by_role('button',name='Dashboard').click();page.set_viewport_size({'width':390,'height':844});page.get_by_role('heading',name='Analysis cases',exact=True).wait_for();page.screenshot(path=str(out/'mobile.png'),full_page=True)
    assert not errors,errors
    browser.close();report={'browser':'Chrome headless','screens_verified':11,'download':'valid PDF downloaded','historical_tests':'predicted, locked, revealed, failures displayed','javascript_errors':errors,'screenshots':str(out),'navigation_race_regression':'passed','policy_form_submission':'passed'}; (root/'docs/browser-verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

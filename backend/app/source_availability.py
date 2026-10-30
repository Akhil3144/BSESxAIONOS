"""Bounded availability checks for configured public URLs, never price verification."""
from datetime import datetime, timezone
import time
from threading import Lock
import httpx
from .public_sources import directory

_cache={}
_lock=Lock()
CACHE_SECONDS=300

def check_availability(source_id, transport=None):
    source=next((s for s in directory() if s['source_id']==source_id),None)
    if source is None: raise KeyError(source_id)
    # Only configured URLs are accepted. Do not follow redirects into arbitrary hosts.
    url=source['current_url']
    with _lock:
        cached=_cache.get(source_id)
        if transport is None and cached and time.monotonic()-cached[0]<CACHE_SECONDS:
            return {**cached[1],'cached':True}
    result={'source_id':source_id,'url':url,'checked_at':datetime.now(timezone.utc).isoformat(),
            'http_status':None,'status':'Unable to check','cached':False,
            'notice':'Availability does not verify authenticity, product comparability or a published price.'}
    try:
        with httpx.Client(transport=transport,timeout=8,follow_redirects=False,trust_env=False) as client:
            with client.stream('GET',url,headers={'User-Agent':'BSES-Demo-Source-Availability/1.0'}) as response:
                code=response.status_code;result['http_status']=code
                if code==200:
                    prefix=next(response.iter_bytes(chunk_size=1024),b'')
                    if url.endswith('.pdf') and not prefix.lstrip().startswith(b'%PDF-'):
                        result.update(status='Unable to verify availability',message='The website returned a page instead of the expected PDF. It may require sign-in or be temporarily unavailable.')
                    else:
                        result.update(status='Available',message='Website responded HTTP 200. Browser access may still require sign-in, subscription or regional access; no price is verified.')
                elif 300<=code<400:
                    result.update(status='Access restricted or redirected',message=f'HTTP {code}: website redirected the request. Open Original Source to check access in your browser.')
                elif code in (401,403,429):
                    result.update(status='Access restricted',message=f'HTTP {code}: website blocked or limited the check. Try Open Original Source; browser access may differ.')
                else:
                    result.update(status='Unavailable',message=f'HTTP {code}: external source is unavailable. Try again later. Historical verification records are preserved; this does not affect the benchmark.')
    except httpx.TimeoutException:
        result['message']='The external website timed out. Try again later or use Open Original Source. The benchmark is unchanged.'
    except httpx.HTTPError:
        result['message']='Could not connect securely to the external website. Try again later or use Open Original Source. The benchmark is unchanged.'
    if transport is None:
        with _lock:_cache[source_id]=(time.monotonic(),dict(result))
    return result

import os, hashlib, hmac, secrets, time
from fastapi import Header, HTTPException
from sqlalchemy import select
from .db import engine, users, sessions

def hash_password(p):
    salt=secrets.token_hex(16); return salt+':'+hashlib.scrypt(p.encode(),salt=salt.encode(),n=16384,r=8,p=1).hex()
def check(p,stored):
    salt,expected=stored.split(':'); return hmac.compare_digest(expected,hashlib.scrypt(p.encode(),salt=salt.encode(),n=16384,r=8,p=1).hex())
def current(authorization: str=Header(default='')):
    if not authorization.startswith('Bearer '): raise HTTPException(401,'Authentication required')
    token=hashlib.sha256(authorization[7:].encode()).hexdigest()
    with engine.connect() as c:
        row=c.execute(select(users).join(sessions).where(sessions.c.id==token,sessions.c.expires>int(time.time()))).mappings().first()
    if not row: raise HTTPException(401,'Session expired or invalid')
    return dict(row)
def permit(user,*roles):
    if user['role'] not in roles: raise HTTPException(403,'Role does not permit this action')

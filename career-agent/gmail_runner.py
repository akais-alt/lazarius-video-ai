import os, sqlite3, requests
from datetime import datetime, timezone
from gmail_backend import send_gmail, read_inbox

DB='career_agent.db'
DAILY_LIMIT=int(os.getenv('DAILY_LIMIT','20'))
AUTO_SEND=os.getenv('AUTO_SEND','false').lower()=='true'
PROFILE={
 'name':'Siaka Kamagate','country':"Côte d'Ivoire",
 'education':'BTS Génie Civil, option Travaux Publics, obtenu en 2026',
 'skills':'AutoCAD, Excel, génie civil, travaux publics','target':'stage ou premier emploi',
 'keywords':['travaux publics','génie civil','routes','VRD','assainissement','drainage','hydraulique','barrages','géotechnique','topographie','bureau d’études','BTP']
}

def db():
 c=sqlite3.connect(DB)
 c.execute('CREATE TABLE IF NOT EXISTS companies(id INTEGER PRIMARY KEY,name TEXT,email TEXT,website TEXT,city TEXT,sector TEXT,score INTEGER,source TEXT,created_at TEXT,UNIQUE(name,email))')
 c.execute('CREATE TABLE IF NOT EXISTS applications(id INTEGER PRIMARY KEY,company_id INTEGER,sent_at TEXT,status TEXT,UNIQUE(company_id))')
 c.execute('CREATE TABLE IF NOT EXISTS emails(id TEXT PRIMARY KEY,sender TEXT,subject TEXT,received_at TEXT,category TEXT,summary TEXT,action TEXT)')
 c.commit(); return c

def search_web():
 key=os.getenv('SEARCH_API_KEY'); cx=os.getenv('SEARCH_ENGINE_ID')
 if not key or not cx: return []
 queries=[
  'entreprise travaux publics génie civil Côte d’Ivoire recrutement stage',
  'BTP routes VRD assainissement Côte d’Ivoire recrutement',
  'bureau étude génie civil Côte d’Ivoire stage',
  'entreprise hydraulique barrage Côte d’Ivoire recrutement'
 ]
 out=[]; seen=set()
 for q in queries:
  r=requests.get('https://www.googleapis.com/customsearch/v1',params={'key':key,'cx':cx,'q':q,'num':10},timeout=30)
  if not r.ok: continue
  for x in r.json().get('items',[]):
   link=x.get('link','')
   if link and link not in seen:
    seen.add(link); out.append({'name':x.get('title','')[:180],'website':link,'snippet':x.get('snippet',''),'source':'Google Custom Search'})
 return out

def enrich_email(item):
 api=os.getenv('HUNTER_API_KEY'); url=item.get('website','')
 if not api or not url: return item
 domain=url.split('//')[-1].split('/')[0].replace('www.','')
 try:
  r=requests.get('https://api.hunter.io/v2/domain-search',params={'domain':domain,'api_key':api,'limit':10},timeout=20)
  if not r.ok: return item
  data=r.json().get('data',{}).get('emails',[])
  preferred=[e for e in data if e.get('type')=='generic'] or data
  if preferred: item['email']=preferred[0].get('value','')
 except requests.RequestException: pass
 return item

def score(x):
 t=(x.get('name','')+' '+x.get('snippet','')).lower()
 return min(100,sum(10 for k in PROFILE['keywords'] if k in t))

def save_companies(items):
 c=db(); n=0
 for x in items:
  x=enrich_email(x); x['score']=score(x)
  if x['score']<20: continue
  try:
   c.execute('INSERT INTO companies(name,email,website,city,sector,score,source,created_at) VALUES(?,?,?,?,?,?,?,?)',(
    x['name'],x.get('email',''),x['website'],'Côte d’Ivoire','Génie civil / Travaux publics',x['score'],x['source'],datetime.now(timezone.utc).isoformat()))
   n+=1
  except sqlite3.IntegrityError: pass
 c.commit(); return n

def compose(company):
 return f'''Madame, Monsieur,\n\nJe suis {PROFILE['name']}, titulaire du {PROFILE['education']}. Je recherche actuellement un {PROFILE['target']} dans le domaine du génie civil et des travaux publics.\n\nL’activité de votre entreprise dans le secteur des infrastructures m’intéresse particulièrement. Je souhaite mettre en pratique mes connaissances et développer mes compétences sur le terrain.\n\nJe joins à ce message mon CV et ma lettre de motivation.\n\nCordialement,\n{PROFILE['name']}'''

def classify(text):
 t=text.lower()
 if any(k in t for k in ['entretien','interview','convocation']): return 'ENTRETIEN'
 if any(k in t for k in ['félicit','retenu','recrut','stage accepté','candidature retenue','vous êtes sélectionné']): return 'REPONSE_POSITIVE'
 if any(k in t for k in ['refus','regret','malheureusement','candidature non retenue']): return 'REFUS'
 if any(k in t for k in ['stage','stagiaire']): return 'OFFRE_STAGE'
 if any(k in t for k in ['emploi','poste','recrutement']): return 'OFFRE_EMPLOI'
 return 'AUTRE'

def whatsapp(text):
 pid=os.getenv('WHATSAPP_PHONE_NUMBER_ID'); token=os.getenv('WHATSAPP_ACCESS_TOKEN'); to=os.getenv('WHATSAPP_RECIPIENT')
 if not all([pid,token,to]): return False
 r=requests.post(f'https://graph.facebook.com/v23.0/{pid}/messages',headers={'Authorization':f'Bearer {token}','Content-Type':'application/json'},json={'messaging_product':'whatsapp','to':to,'type':'text','text':{'preview_url':False,'body':text}},timeout=30)
 return r.status_code in (200,201)

def run():
 c=db(); added=save_companies(search_web()); rows=c.execute('SELECT id,name,email,score FROM companies ORDER BY score DESC,id DESC').fetchall(); sent=0
 for cid,name,email,s in rows:
  if sent>=DAILY_LIMIT: break
  if not email or c.execute('SELECT 1 FROM applications WHERE company_id=?',(cid,)).fetchone(): continue
  ok=False
  if AUTO_SEND:
   ok=send_gmail(email,f'Candidature – Génie Civil / Travaux Publics – {PROFILE["name"]}',compose(name))
  status='sent' if ok else ('prepared' if not AUTO_SEND else 'error')
  if status!='error': sent+=1
  c.execute('INSERT OR IGNORE INTO applications(company_id,sent_at,status) VALUES(?,?,?)',(cid,datetime.now(timezone.utc).isoformat(),status))
 c.commit()
 inbox=read_inbox(20); counts={k:0 for k in ['OFFRE_STAGE','OFFRE_EMPLOI','ENTRETIEN','REPONSE_POSITIVE','REFUS','AUTRE']}
 for m in inbox:
  cat=classify(m['subject']+' '+m.get('snippet','')); counts[cat]+=1
  c.execute('INSERT OR REPLACE INTO emails(id,sender,subject,received_at,category,summary,action) VALUES(?,?,?,?,?,?,?)',(m['id'],m['sender'],m['subject'],m['received_at'],cat,m.get('snippet','')[:350],'Lire et répondre si nécessaire'))
 c.commit()
 report=f'''🤖 LAZARIUS CAREER AGENT\n📅 {datetime.now().strftime('%d/%m/%Y')}\n\n🔎 Nouvelles entreprises : {added}\n📩 Candidatures {"envoyées" if AUTO_SEND else "préparées"} : {sent}/{DAILY_LIMIT}\n\n📬 ACTIVITÉ GMAIL\n🟢 Réponses positives : {counts["REPONSE_POSITIVE"]}\n🎤 Entretiens : {counts["ENTRETIEN"]}\n🔵 Offres de stage : {counts["OFFRE_STAGE"]}\n💼 Offres d’emploi : {counts["OFFRE_EMPLOI"]}\n🔴 Refus : {counts["REFUS"]}\n\nMode candidature automatique : {"ACTIVÉ" if AUTO_SEND else "DÉSACTIVÉ"}'''
 for m in inbox[:5]: report += f'\n\n• {classify(m["subject"]+" "+m.get("snippet",""))} — {m["subject"]}\n  {m["sender"]}'
 print(report); whatsapp(report)

if __name__=='__main__': run()

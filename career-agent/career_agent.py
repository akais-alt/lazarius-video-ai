import os, sqlite3, base64
from datetime import datetime, timezone
import requests

DB='career_agent.db'
DAILY_LIMIT=int(os.getenv('DAILY_LIMIT','20'))
AUTO_SEND=os.getenv('AUTO_SEND','false').lower()=='true'
PROFILE={
 'name':'Siaka Kamagate','country':'Côte d’Ivoire','education':'BTS Génie Civil, option Travaux Publics, obtenu en 2026',
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
 q='entreprise BTP travaux publics génie civil Côte d Ivoire recrutement stage'
 r=requests.get('https://www.googleapis.com/customsearch/v1',params={'key':key,'cx':cx,'q':q,'num':10},timeout=30); r.raise_for_status()
 return [{'name':x.get('title','')[:180],'website':x.get('link',''),'snippet':x.get('snippet',''),'source':'Google Custom Search'} for x in r.json().get('items',[])]

def enrich_email(item):
 api=os.getenv('HUNTER_API_KEY'); url=item.get('website','')
 if not api or not url: return item
 domain=url.split('//')[-1].split('/')[0].replace('www.','')
 try:
  r=requests.get('https://api.hunter.io/v2/domain-search',params={'domain':domain,'api_key':api,'limit':5},timeout=20); r.raise_for_status()
  data=r.json().get('data',{}).get('emails',[])
  preferred=[e for e in data if e.get('type')=='generic'] or data
  if preferred: item['email']=preferred[0].get('value','')
 except requests.RequestException: pass
 return item

def score(x):
 t=(x.get('name','')+' '+x.get('snippet','')).lower(); return min(100,sum(12 for k in PROFILE['keywords'] if k in t))

def save_companies(items):
 c=db(); n=0
 for x in items:
  x=enrich_email(x); x['score']=score(x)
  if x['score']<24: continue
  try:
   c.execute('INSERT INTO companies(name,email,website,city,sector,score,source,created_at) VALUES(?,?,?,?,?,?,?,?)',(x['name'],x.get('email',''),x['website'],'Côte d’Ivoire','Génie civil / TP',x['score'],x['source'],datetime.now(timezone.utc).isoformat())); n+=1
  except sqlite3.IntegrityError: pass
 c.commit(); return n

def compose(company):
 return f"Madame, Monsieur,\n\nJe suis {PROFILE['education']}. Je souhaite intégrer votre structure dans le cadre d’un {PROFILE['target']}. Votre activité dans le domaine du génie civil et des travaux publics correspond à mon projet professionnel.\n\nJe maîtrise notamment {PROFILE['skills']}. Vous trouverez mon dossier de candidature en pièces jointes.\n\nCordialement,\n{PROFILE['name']}"

def outlook_token():
 refresh=os.getenv('OUTLOOK_REFRESH_TOKEN'); client=os.getenv('OUTLOOK_CLIENT_ID'); secret=os.getenv('OUTLOOK_CLIENT_SECRET'); tenant=os.getenv('OUTLOOK_TENANT_ID')
 if not all([refresh,client,secret,tenant]): return None
 r=requests.post(f'https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token',data={'client_id':client,'client_secret':secret,'refresh_token':refresh,'grant_type':'refresh_token','scope':'https://graph.microsoft.com/.default'},timeout=30); r.raise_for_status(); return r.json()['access_token']

def attachments():
 out=[]
 for env_name, filename in [('CV_BASE64','CV_Siaka_Kamagate.pdf'),('LETTER_BASE64','Lettre_Motivation_Siaka_Kamagate.pdf')]:
  raw=os.getenv(env_name)
  if raw: out.append({'@odata.type':'#microsoft.graph.fileAttachment','name':filename,'contentBytes':raw})
 return out

def send_outlook(to, subject, body):
 tok=outlook_token(); sender=os.getenv('OUTLOOK_SENDER_EMAIL')
 if not tok or not sender or not to: return False
 msg={'subject':subject,'body':{'contentType':'Text','content':body},'toRecipients':[{'emailAddress':{'address':to}}]}
 ats=attachments()
 if ats: msg['attachments']=ats
 payload={'message':msg,'saveToSentItems':True}
 r=requests.post(f'https://graph.microsoft.com/v1.0/users/{sender}/sendMail',headers={'Authorization':f'Bearer {tok}','Content-Type':'application/json'},json=payload,timeout=30); return r.status_code in (200,202)

def whatsapp(text):
 pid=os.getenv('WHATSAPP_PHONE_NUMBER_ID'); token=os.getenv('WHATSAPP_ACCESS_TOKEN'); to=os.getenv('WHATSAPP_RECIPIENT')
 if not all([pid,token,to]): return False
 r=requests.post(f'https://graph.facebook.com/v23.0/{pid}/messages',headers={'Authorization':f'Bearer {token}','Content-Type':'application/json'},json={'messaging_product':'whatsapp','to':to,'type':'text','text':{'preview_url':False,'body':text}},timeout=30); return r.status_code in (200,201)

def classify(text):
 t=text.lower()
 if any(k in t for k in ['entretien','interview','convocation']): return 'ENTRETIEN'
 if any(k in t for k in ['félicit','retenu','recrut','stage accepté','candidature retenue']): return 'REPONSE_POSITIVE'
 if any(k in t for k in ['refus','regret','malheureusement']): return 'REFUS'
 if any(k in t for k in ['stage','stagiaire']): return 'OFFRE_STAGE'
 if any(k in t for k in ['emploi','poste','recrutement']): return 'OFFRE_EMPLOI'
 return 'AUTRE'

def get_mail_summary():
 tok=outlook_token(); sender=os.getenv('OUTLOOK_SENDER_EMAIL')
 if not tok or not sender: return []
 r=requests.get(f'https://graph.microsoft.com/v1.0/users/{sender}/mailFolders/inbox/messages?$top=20&$orderby=receivedDateTime%20desc',headers={'Authorization':f'Bearer {tok}'},timeout=30); r.raise_for_status(); arr=[]
 for m in r.json().get('value',[]):
  arr.append({'sender':m.get('from',{}).get('emailAddress',{}).get('address',''),'subject':m.get('subject',''),'received_at':m.get('receivedDateTime',''),'category':classify((m.get('subject','')+' '+m.get('bodyPreview',''))),'summary':m.get('bodyPreview','')[:350]})
 return arr

def run():
 c=db(); found=search_web(); added=save_companies(found)
 rows=c.execute('SELECT id,name,email,score FROM companies ORDER BY score DESC, id DESC').fetchall(); sent=0
 for cid,name,email,s in rows:
  if sent>=DAILY_LIMIT: break
  if c.execute('SELECT 1 FROM applications WHERE company_id=?',(cid,)).fetchone() or not email: continue
  body=compose({'name':name}); ok=False
  if AUTO_SEND: ok=send_outlook(email, f'Candidature – Génie Civil / Travaux Publics – {PROFILE["name"]}', body)
  status='sent' if ok else ('prepared' if not AUTO_SEND else 'error')
  if status!='error': sent+=1
  c.execute('INSERT OR IGNORE INTO applications(company_id,sent_at,status) VALUES(?,?,?)',(cid,datetime.now(timezone.utc).isoformat(),status))
 c.commit(); emails=get_mail_summary(); positives=sum(1 for e in emails if e['category'] in ('REPONSE_POSITIVE','ENTRETIEN'))
 report=f"🤖 LAZARIUS CAREER AGENT\n📅 {datetime.now(timezone.utc).date().isoformat()}\n\n🔎 Nouvelles entreprises: {added}\n📩 Candidatures {'envoyées' if AUTO_SEND else 'préparées'}: {sent}/{DAILY_LIMIT}\n📬 Mails récents analysés: {len(emails)}\n🟢 Réponses positives/entretiens: {positives}\n\nMode automatique: {'ACTIVÉ' if AUTO_SEND else 'DÉSACTIVÉ'}"
 for e in emails[:5]: report+=f"\n\n• {e['category']} — {e['subject']}\n  {e['sender']}"
 print(report); whatsapp(report)

if __name__=='__main__': run()

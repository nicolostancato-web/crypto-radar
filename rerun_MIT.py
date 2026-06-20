"""
PROMPT MIT — il re-lancio del "piu grande script di analisi dati" del progetto.
PARCHEGGIATO. Trigger: lanciarlo a 200 token e di nuovo a 300 token accumulati.

Cosa fa: ricostruisce il dataset compatto AGGIORNATO (tutti i token a oggi), lo inietta
nel Prompt MIT (PROMPT_MIT.txt) e lo manda a piu' AI di famiglie diverse (Grok, DeepSeek,
GPT, Gemini) + l'analisi calcolata in locale. Raccoglie e confronta. A 200/300 token il
campione e' grande abbastanza per un verdetto VERO (non una sbirciata come a 97).

Uso:   python rerun_MIT.py        (controlla se siamo a >=200 e in caso lancia)
       python rerun_MIT.py force  (lancia comunque, anche sotto i 200)
"""
import sys, os, json, statistics as st
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def build_dataset():
    obs={}
    for l in open('data/track.jsonl'):
        o=json.loads(l); obs.setdefault(o['ca'],[]).append(o)
    ret={}
    for ca,s in obs.items():
        s=sorted(s,key=lambda x:x['obs_ts']); pr=[x['price'] for x in s if x.get('price')]
        if len(pr)>=2 and pr[0]: ret[ca]=max(pr)/pr[0]-1
    sig={}
    for l in open('data/candidates.jsonl'):
        c=json.loads(l); ca=c.get('ca')
        if ca and ca not in sig:
            m=c.get('metrics',{}); sig[ca]={'liq':m.get('liq'),'vol1h':m.get('vol_1h'),'vol24h':m.get('vol_24h'),
            'voliq':m.get('voliq'),'age_h':m.get('age_h'),'top10':m.get('top10_pct'),'bs':m.get('bs_ratio_1h'),
            'heat':c.get('grok_heat'),'arena':c.get('arena')}
    wf={}
    for l in open('data/whale_flow.jsonl'):
        r=json.loads(l); wf.setdefault(r['ca'],[]).append(r.get('whale_pressure'))
    wp={ca:round(st.mean([x for x in v[:3] if x is not None]),2) for ca,v in wf.items() if any(x is not None for x in v[:3])}
    rc={}
    for l in open('data/rugcheck.jsonl'):
        r=json.loads(l); rc[r['ca']]=r
    cols=['ret','run','age_h','liq','vol1h','voliq','bs','top10','heat','arena','whale_early','risk','insider','lp']
    lines=['\t'.join(cols)]
    n=0
    for ca in ret:
        if ca not in sig: continue
        s=sig[ca]; r=rc.get(ca,{}); n+=1
        vals=[round(ret[ca],2),int(ret[ca]>=0.5),s['age_h'],s['liq'],s['vol1h'],s['voliq'],s['bs'],
              s['top10'],s['heat'],s['arena'],wp.get(ca),r.get('risk_score'),r.get('insider_accounts'),r.get('lp_locked_pct')]
        lines.append('\t'.join(str(x) for x in vals))
    return '\n'.join(lines), n

def run(force=False):
    table, n = build_dataset()
    print(f"[MIT] token nel dataset: {n}")
    if n < 200 and not force:
        print(f"[MIT] PARCHEGGIATO: servono >=200 token (ora {n}). Usa 'force' per lanciare comunque."); return
    import double_agent as da
    base = open('PROMPT_MIT.txt').read()
    # sostituisci la vecchia tabella con quella aggiornata (tra i marcatori del prompt)
    prompt = base.split('# CRITICAL CAVEATS')[0].rsplit('Columns:',1)[0] + \
        "Columns: ret,run,age_h,liq,vol1h,voliq,bs,top10,heat,arena,whale_early,risk,insider,lp\n\n" + table + \
        "\n\n# CRITICAL CAVEATS" + base.split('# CRITICAL CAVEATS',1)[1]
    open('PROMPT_MIT_filled.txt','w').write(prompt)
    for name,fn,kw in [("grok",da.ask_grok,{"max_tokens":5000,"timeout":300,"live_x":False}),
                       ("deepseek",da.ask_deepseek,{"max_tokens":5000,"timeout":480}),
                       ("gpt5",da.ask_gpt5,{"max_tokens":5000,"timeout":300}),
                       ("gemini",da.ask_gemini,{})]:
        print(f"\n=== {name.upper()} ===")
        try: txt=fn(prompt,**kw) if kw else fn(prompt)
        except Exception as e: print("errore:",str(e)[:120]); txt=None
        if txt:
            open(f"CONSULENZA_MIT_{name}.md","w").write(f"# {name} (re-run MIT, n={n})\n\n"+txt)
            print(txt[:1500])
        else: print("nessuna risposta")

if __name__=="__main__":
    run(force=(len(sys.argv)>1 and sys.argv[1]=="force"))

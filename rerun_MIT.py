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
    ret={}; nobs={}
    for ca,s in obs.items():
        s=sorted(s,key=lambda x:x['obs_ts']); pr=[x['price'] for x in s if x.get('price')]
        nobs[ca]=len(pr)
        if len(pr)>=2 and pr[0]: ret[ca]=max(pr)/pr[0]-1
    sig={}
    for l in open('data/candidates.jsonl'):
        c=json.loads(l); ca=c.get('ca')
        if ca and ca not in sig:
            m=c.get('metrics',{}); sig[ca]={'liq':m.get('liq'),'vol1h':m.get('vol_1h'),'vol24h':m.get('vol_24h'),
            'voliq':m.get('voliq'),'age_h':m.get('age_h'),'top10':m.get('top10_pct'),'bs':m.get('bs_ratio_1h'),
            'np1':m.get('np_1h'),'np6':m.get('np_6h'),'accel':m.get('bs_accel'),'bsm5':m.get('bs_ratio_m5'),
            'heat':c.get('grok_heat'),'arena':c.get('arena')}
    wf={}
    for l in open('data/whale_flow.jsonl'):
        r=json.loads(l); wf.setdefault(r['ca'],[]).append(r.get('whale_pressure'))
    wp={ca:round(st.mean([x for x in v[:3] if x is not None]),2) for ca,v in wf.items() if any(x is not None for x in v[:3])}
    rc={}
    for l in open('data/rugcheck.jsonl'):
        r=json.loads(l); rc[r['ca']]=r
    cols=['ret','run','nobs','age_h','liq','vol1h','voliq','bs','np1h','np6h','accel','bsm5','top10','heat','arena','whale_early','risk','insider','lp']
    lines=['\t'.join(cols)]
    n=0
    for ca in ret:
        if ca not in sig: continue
        s=sig[ca]; r=rc.get(ca,{}); n+=1
        vals=[round(ret[ca],2),int(ret[ca]>=0.5),nobs.get(ca),s['age_h'],s['liq'],s['vol1h'],s['voliq'],s['bs'],
              s.get('np1'),s.get('np6'),s.get('accel'),s.get('bsm5'),
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
        "Columns: ret(max return),run(1=runner>=+50%),nobs(n osservazioni=MATURITA: <6 = immaturo,ignora),age_h,liq,vol1h,voliq,bs(buy/sell 1h),np1h(pressione netta 1h -1..+1),np6h,accel(bs 5min/1h: >1=onda parte),bsm5,top10,heat,arena,whale_early,risk,insider,lp\n\n" + table + \
        "\n\n# CRITICAL CAVEATS" + base.split('# CRITICAL CAVEATS',1)[1]
    # inietta i numeri VERI (il testo del prompt aveva hardcoded "97 tokens / 22 runners" dal primo run)
    nr = sum(1 for ln in table.splitlines()[1:] if ln.split('\t')[1] == '1')
    nm = sum(1 for ln in table.splitlines()[1:] if (ln.split('\t')[2] not in ('None','')) and int(float(ln.split('\t')[2] or 0)) >= 6)
    prompt = prompt.replace("97 tokens", f"{n} tokens").replace("only 22 runners", f"only {nr} runners") \
                   .replace("(97 tokens, one row each", f"({n} tokens, one row each") \
                   .replace("22 runners in 97", f"{nr} runners in {n}")
    prompt += f"\n\n# NOTA CAMPIONE (REALE, conta le righe): {n} token totali, {nr} runner (+50%), ~{nm} con nobs>=6 (maturi). NON e' piu' il vecchio campione da 97: ora e' >2x piu' grande. Conta TU le righe, non fidarti di numeri citati altrove."
    open('PROMPT_MIT_filled.txt','w').write(prompt)
    print(f"[MIT] campione reale iniettato: {n} token, {nr} runner, ~{nm} maturi")
    for name,fn,kw in [("grok",da.ask_grok,{"max_tokens":5000,"timeout":300,"live_x":False}),
                       ("deepseek",da.ask_deepseek,{"max_tokens":5000,"timeout":480}),
                       ("glm",da.ask_glm,{"max_tokens":5000,"timeout":300}),
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

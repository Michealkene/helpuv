"""XAUBOT Pro - Premium Trading Dashboard"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from datetime import datetime, timedelta, time as dtime
import os, sys, json, subprocess

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

try:
    import MetaTrader5 as mt5
    MT5_OK = True
except ImportError:
    MT5_OK = False

BRAND = "XAUBOT Pro"
APP_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(APP_DIR, "config.json")
PID_PATH = os.path.join(APP_DIR, "bot.pid")
GOLD, GREEN, RED = "#d4af37", "#00d4aa", "#ff4757"

st.set_page_config(page_title=f"{BRAND} | Dashboard", page_icon="⚡", layout="wide")

# ==================== CSS ====================
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
.stApp { background: #0a0a0f !important; }
html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
.block-container { padding: 1rem 2rem !important; }
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #0a0a0f; }
::-webkit-scrollbar-thumb { background: #2a2a3e; border-radius: 3px; }
section[data-testid="stSidebar"] { background: #0d0d14 !important; border-right: 1px solid #1a1a28 !important; }
#MainMenu, footer, header { visibility: hidden; }

.kpi-row { display: flex; gap: 14px; margin-bottom: 20px; flex-wrap: wrap; }
.kpi { flex:1; min-width:140px; background: linear-gradient(135deg, #12121a, #16162a);
  border: 1px solid rgba(212,175,55,0.1); border-radius: 14px; padding: 18px; text-align: center; }
.kpi .kv { font-size:1.7rem; font-weight:800;
  background: linear-gradient(135deg, #d4af37, #f0d060);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; line-height:1.2; }
.kpi .kl { font-size:0.7rem; color:#6b6b80; text-transform:uppercase; letter-spacing:1px; margin-top:5px; }

.status-dot { display:inline-block; width:10px; height:10px; border-radius:50%; margin-right:8px; animation: pulse 2s infinite; }
.dot-g { background:#00d4aa; box-shadow:0 0 8px #00d4aa; }
.dot-r { background:#ff4757; box-shadow:0 0 8px #ff4757; }
@keyframes pulse { 0%,100%{opacity:1;} 50%{opacity:0.5;} }

.gc { background: rgba(18,18,26,0.8); border:1px solid #1e1e2e; border-radius:14px; padding:18px 22px; margin:8px 0; }
.tc-buy { border-left:3px solid #4facfe; }
.tc-sell { border-left:3px solid #ff4757; }
.pos { color:#00d4aa !important; }
.neg { color:#ff4757 !important; }

.sg { display:grid; grid-template-columns:repeat(auto-fit, minmax(150px,1fr)); gap:14px; margin:20px 0; }
.si { text-align:center; padding:18px 10px; background:rgba(18,18,26,0.6); border:1px solid #1e1e2e; border-radius:12px; }
.si .sv { font-size:1.5rem; font-weight:800; color:#d4af37; }
.si .sl { font-size:0.68rem; color:#6b6b80; text-transform:uppercase; letter-spacing:0.8px; margin-top:4px; }
</style>""", unsafe_allow_html=True)

# ==================== CONFIG ====================
DEF_CFG = {"mt5_login":5046171682,"mt5_password":"2i_hYuTw","mt5_server":"MetaQuotes-Demo",
           "risk_per_trade":100,"min_lot":0.01,"max_lot":5.0,"starting_balance":10000}

def load_cfg():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH) as f: return {**DEF_CFG, **json.load(f)}
    return DEF_CFG.copy()

def save_cfg(c):
    with open(CONFIG_PATH, 'w') as f: json.dump(c, f, indent=2)

# ==================== BOT MGMT ====================
def bot_running():
    if not os.path.exists(PID_PATH): return False, None
    with open(PID_PATH) as f: pid = int(f.read().strip())
    try:
        r = subprocess.run(['tasklist','/FI',f'PID eq {pid}','/NH'], capture_output=True, text=True, timeout=5)
        if str(pid) in r.stdout: return True, pid
    except: pass
    if os.path.exists(PID_PATH): os.remove(PID_PATH)
    return False, None

def start_bot():
    bp = os.path.join(APP_DIR, "live_bot.py")
    if not os.path.exists(bp): return False, "live_bot.py not found"
    try:
        p = subprocess.Popen([sys.executable, bp], cwd=APP_DIR,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        with open(PID_PATH,'w') as f: f.write(str(p.pid))
        return True, p.pid
    except Exception as e: return False, str(e)

def stop_bot():
    ok, pid = bot_running()
    if ok:
        try: subprocess.run(['taskkill','/PID',str(pid),'/F'], capture_output=True, timeout=10)
        except: pass
    if os.path.exists(PID_PATH): os.remove(PID_PATH)

# ==================== MT5 ====================
def mt5_conn(c):
    if not MT5_OK: return False
    if mt5.account_info() is not None: return True
    return mt5.initialize(login=int(c['mt5_login']),password=str(c['mt5_password']),server=str(c['mt5_server']))

def acct_info(c):
    if not mt5_conn(c): return None
    i = mt5.account_info()
    return {'balance':i.balance,'equity':i.equity,'profit':i.profit,'free_margin':i.margin_free} if i else None

def open_pos():
    if not MT5_OK: return []
    p = mt5.positions_get(symbol="XAUUSD")
    return [x for x in (p or []) if x.magic == 123456]

def pending_ord():
    if not MT5_OK: return []
    o = mt5.orders_get(symbol="XAUUSD")
    return [x for x in (o or []) if x.magic == 123456]

# ==================== ENGINE (internals hidden) ====================
_F, _R, _L = 0.45, 4.0, 6

def _dst(dt):
    y=dt.year; m=datetime(y,3,31)
    while m.weekday()!=6: m-=timedelta(days=1)
    o=datetime(y,10,31)
    while o.weekday()!=6: o-=timedelta(days=1)
    return m.date()<=dt<=o.date()

def _at(dt): return (dtime(1,0),dtime(4,0)) if _dst(dt) else (dtime(0,0),dtime(3,0))

def _lot(rng,c):
    rpu=rng*(1-_F)
    if rpu<=0: return c['min_lot']
    return max(c['min_lot'],min(c['max_lot'],round(c['risk_per_trade']/(rpu*100),2)))

def run_bt(cfg, sd, ed, prog=None):
    if not MT5_OK: return None,"MT5 not installed"
    if not mt5_conn(cfg): return None,f"MT5 failed: {mt5.last_error()}"
    fr=[]
    cs=sd
    while cs<ed:
        ce=min(datetime(cs.year+1,1,1),ed)
        r=mt5.copy_rates_range("XAUUSD",mt5.TIMEFRAME_M15,cs,ce)
        if r is not None and len(r)>0:
            d=pd.DataFrame(r); d['time']=pd.to_datetime(d['time'],unit='s'); fr.append(d)
        cs=ce
    if not fr: return None,"No data"
    ad=pd.concat(fr,ignore_index=True).drop_duplicates(subset='time').sort_values('time').reset_index(drop=True)
    trades=[]; cur=sd.date(); ed2=ed.date(); tot=max((ed2-cur).days,1); n=0
    while cur<=ed2:
        if cur.weekday()>=5: cur+=timedelta(days=1); continue
        n+=1
        if prog: prog(min(n/tot,1.0))
        st2,et2=_at(cur); adf=ad[(ad['time']>=datetime.combine(cur,st2))&(ad['time']<=datetime.combine(cur,et2))].copy()
        if len(adf)<2: cur+=timedelta(days=1); continue
        adf['range']=adf['high']-adf['low']
        ldf=adf.iloc[-_L-1:-1] if len(adf)>_L else adf
        if len(ldf)==0: cur+=timedelta(days=1); continue
        c=ldf.loc[ldf['range'].idxmax()]; rng=c['high']-c['low']
        if rng==0: cur+=timedelta(days=1); continue
        bl=c['close']>c['open']
        if bl: dr,en,sl="BUY",c['high']-rng*_F,c['low']; rk=en-sl; tp=en+rk*_R
        else: dr,en,sl="SELL",c['low']+rng*_F,c['high']; rk=sl-en; tp=en-rk*_R
        lt=_lot(rng,cfg); rd=rk*lt*100; ets=c['time']
        fut=ad[ad['time']>=ets]; fld=False; ft=None
        for _,b in fut.iterrows():
            if bl and b['low']<=en: fld,ft=True,b['time']; break
            elif not bl and b['high']>=en: fld,ft=True,b['time']; break
        if not fld:
            trades.append({'date':cur,'direction':dr,'entry_price':round(en,2),'stop_loss':round(sl,2),
                'take_profit':round(tp,2),'outcome':'NO_FILL','exit_reason':'NO_FILL','lot_size':lt,
                'profit_pips':0,'profit_dollars':0,'candle_range':round(rng,2),'risk_dollars':round(rd,2)})
            cur+=timedelta(days=1); continue
        aft=ad[ad['time']>ft]; oc=et=er=None
        for _,b in aft.iterrows():
            if bl:
                if b['high']>=tp: oc,et,er="WIN",b['time'],"TP"; break
                if b['low']<=sl: oc,et,er="LOSS",b['time'],"SL"; break
            else:
                if b['low']<=tp: oc,et,er="WIN",b['time'],"TP"; break
                if b['high']>=sl: oc,et,er="LOSS",b['time'],"SL"; break
        if oc is None: oc,er="OPEN","OPEN"
        if oc=="WIN": pp=abs(tp-en)/0.01; dl=pp*0.01*lt*100
        elif oc=="LOSS": pp=-abs(en-sl)/0.01; dl=pp*0.01*lt*100
        else: pp=dl=0
        trades.append({'date':cur,'direction':dr,'entry_price':round(en,2),'stop_loss':round(sl,2),
            'take_profit':round(tp,2),'outcome':oc,'exit_reason':er,'lot_size':lt,
            'profit_pips':round(pp,1),'profit_dollars':round(dl,2),'candle_range':round(rng,2),
            'risk_dollars':round(rd,2)})
        cur+=timedelta(days=1)
    if prog: prog(1.0)
    return (pd.DataFrame(trades) if trades else pd.DataFrame()),"OK"

def calc_m(df):
    if df is None or df.empty: return {}
    cp=df[df['outcome'].isin(['WIN','LOSS'])].copy()
    if cp.empty: return {}
    w,l=cp[cp['outcome']=='WIN'],cp[cp['outcome']=='LOSS']
    nt,nw,nl=len(cp),len(w),len(l); wr=nw/nt*100 if nt>0 else 0
    pnl=cp['profit_dollars'].sum(); ws=w['profit_dollars'].sum() if nw>0 else 0
    ls2=abs(l['profit_dollars'].sum()) if nl>0 else 0; pf=ws/ls2 if ls2>0 else 0
    aw=w['profit_dollars'].mean() if nw>0 else 0; al=l['profit_dollars'].mean() if nl>0 else 0
    eq=cp['profit_dollars'].cumsum(); mdd=(eq-eq.cummax()).min() if len(eq)>0 else 0
    rf=abs(pnl/mdd) if mdd<0 else 0; exp=(wr/100*aw)+((1-wr/100)*al)
    awp=w['profit_pips'].mean() if nw>0 else 0; alp=abs(l['profit_pips'].mean()) if nl>0 else 1
    arr=awp/alp if alp>0 else 0
    sw,sl3,cs2,last=[],[],0,None
    for o in cp['outcome']:
        if o==last: cs2+=1
        else:
            if last=='WIN': sw.append(cs2)
            elif last=='LOSS': sl3.append(cs2)
            cs2=1; last=o
    if last=='WIN': sw.append(cs2)
    elif last=='LOSS': sl3.append(cs2)
    cm=cp.copy(); cm['_m']=pd.to_datetime(cm['date']).dt.to_period('M')
    mp2=cm.groupby('_m')['profit_dollars'].sum(); pm=((mp2>0).mean()*100) if len(mp2)>0 else 0
    return {'total_trades':nt,'wins':nw,'losses':nl,'win_rate':wr,'total_pnl':pnl,
        'profit_factor':pf,'avg_win':aw,'avg_loss':al,'max_drawdown':mdd,'recovery_factor':rf,
        'expectancy':exp,'avg_rr':arr,'max_win_streak':max(sw) if sw else 0,
        'max_loss_streak':max(sl3) if sl3 else 0,
        'avg_risk':cp['risk_dollars'].mean() if 'risk_dollars' in cp.columns else 0,
        'profitable_months_pct':pm,'n_months':len(mp2),'monthly_avg':pnl/max(len(mp2),1),
        'no_fills':len(df[df['outcome']=='NO_FILL']) if 'outcome' in df.columns else 0}

# ==================== CHARTS ====================
CL = dict(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
    font=dict(family='Inter',color='#8b8b9e',size=12), margin=dict(l=50,r=20,t=40,b=30),
    xaxis=dict(gridcolor='rgba(255,255,255,0.03)'), yaxis=dict(gridcolor='rgba(255,255,255,0.05)'))

def ch_eq(df, bal):
    cp=df[df['outcome'].isin(['WIN','LOSS'])].copy()
    cp['b']=bal+cp['profit_dollars'].cumsum(); cp['d']=pd.to_datetime(cp['date'])
    fig=go.Figure(go.Scatter(x=cp['d'],y=cp['b'],mode='lines',fill='tozeroy',
        fillcolor='rgba(212,175,55,0.06)',line=dict(color=GOLD,width=2),
        hovertemplate='%{x|%b %d, %Y}<br>$%{y:,.0f}<extra></extra>'))
    fig.add_hline(y=bal,line_dash="dot",line_color="rgba(107,107,128,0.3)")
    fig.update_layout(**CL,height=400,yaxis_title='Balance ($)'); return fig

def ch_mo(df):
    cp=df[df['outcome'].isin(['WIN','LOSS'])].copy()
    cp['m']=pd.to_datetime(cp['date']).dt.to_period('M').astype(str)
    m=cp.groupby('m')['profit_dollars'].sum().reset_index()
    fig=go.Figure(go.Bar(x=m['m'],y=m['profit_dollars'],
        marker_color=[GREEN if v>=0 else RED for v in m['profit_dollars']],
        hovertemplate='%{x}<br>$%{y:,.0f}<extra></extra>'))
    fig.update_layout(**CL,height=320,xaxis_tickangle=-45); return fig

def ch_dd(df, bal):
    cp=df[df['outcome'].isin(['WIN','LOSS'])].copy()
    cp['b']=bal+cp['profit_dollars'].cumsum(); cp['dd']=cp['b']-cp['b'].cummax()
    cp['d']=pd.to_datetime(cp['date'])
    fig=go.Figure(go.Scatter(x=cp['d'],y=cp['dd'],mode='lines',fill='tozeroy',
        fillcolor='rgba(255,71,87,0.1)',line=dict(color=RED,width=1.5)))
    fig.update_layout(**CL,height=250,yaxis_title='Drawdown ($)'); return fig

def ch_pie(df):
    cp=df[df['outcome'].isin(['WIN','LOSS'])]; vc=cp['outcome'].value_counts()
    fig=go.Figure(go.Pie(labels=vc.index,values=vc.values,hole=0.6,
        marker_colors=[GREEN,RED],textinfo='label+percent',textfont=dict(size=13,color='white')))
    fig.update_layout(**CL,height=320,showlegend=False); return fig

def ch_dir(df):
    cp=df[df['outcome'].isin(['WIN','LOSS'])].copy()
    b,s=cp[cp['direction']=='BUY'],cp[cp['direction']=='SELL']
    pnls=[b['profit_dollars'].sum(),s['profit_dollars'].sum()]
    fig=go.Figure(go.Bar(x=['BUY','SELL'],y=pnls,marker_color=['#4facfe',RED],
        text=[f"${v:,.0f}" for v in pnls],textposition='outside',textfont=dict(color='white')))
    fig.update_layout(**CL,height=320); return fig

def ch_dow(df):
    cp=df[df['outcome'].isin(['WIN','LOSS'])].copy()
    cp['dow']=pd.to_datetime(cp['date']).dt.day_name()
    g=cp.groupby('dow')['profit_dollars'].sum().reindex(['Monday','Tuesday','Wednesday','Thursday','Friday']).fillna(0)
    fig=go.Figure(go.Bar(x=g.index,y=g.values,marker_color=[GREEN if v>=0 else RED for v in g.values]))
    fig.update_layout(**CL,height=320); return fig

def ch_rwr(df, win=20):
    cp=df[df['outcome'].isin(['WIN','LOSS'])].copy().reset_index(drop=True)
    if len(cp)<win: return None
    cp['rw']=cp['outcome'].eq('WIN').astype(int).rolling(win).mean()*100
    cp['d']=pd.to_datetime(cp['date'])
    fig=go.Figure(go.Scatter(x=cp['d'],y=cp['rw'],mode='lines',line=dict(color='#667eea',width=2)))
    fig.add_hline(y=50,line_dash="dot",line_color="rgba(107,107,128,0.3)")
    fig.update_layout(**CL,height=320,yaxis_range=[0,80],yaxis_title='Win Rate %'); return fig

# ==================== PAGES ====================
def pg_overview(df, m, cfg):
    bal=cfg['starting_balance']; ret=((bal+m['total_pnl'])/bal-1)*100
    st.markdown(f"""<div class="kpi-row">
        <div class="kpi"><div class="kv">${m['total_pnl']:,.0f}</div><div class="kl">Total P&L ({ret:+.0f}%)</div></div>
        <div class="kpi"><div class="kv">{m['win_rate']:.1f}%</div><div class="kl">Win Rate</div></div>
        <div class="kpi"><div class="kv">{m['profit_factor']:.2f}</div><div class="kl">Profit Factor</div></div>
        <div class="kpi"><div class="kv">{m['total_trades']}</div><div class="kl">Total Trades</div></div>
        <div class="kpi"><div class="kv">{m['avg_rr']:.1f}:1</div><div class="kl">Avg R:R</div></div>
        <div class="kpi"><div class="kv">${abs(m['max_drawdown']):,.0f}</div><div class="kl">Max Drawdown</div></div>
    </div>""", unsafe_allow_html=True)
    st.plotly_chart(ch_eq(df,bal), use_container_width=True)
    c1,c2=st.columns(2)
    with c1: st.plotly_chart(ch_mo(df), use_container_width=True)
    with c2: st.plotly_chart(ch_pie(df), use_container_width=True)
    st.plotly_chart(ch_dd(df,bal), use_container_width=True)

def pg_live(cfg):
    run,pid=bot_running()
    if run:
        st.markdown(f'<div class="gc"><span class="status-dot dot-g"></span>'
            f'<strong style="color:#00d4aa">Bot Running</strong> (PID: {pid})</div>',unsafe_allow_html=True)
    else:
        st.markdown('<div class="gc"><span class="status-dot dot-r"></span>'
            '<strong style="color:#ff4757">Bot Stopped</strong></div>',unsafe_allow_html=True)
    c1,c2,c3=st.columns([1,1,2])
    with c1:
        if st.button("Start Bot" if not run else "Restart",type="primary",use_container_width=True):
            if run: stop_bot()
            ok,msg=start_bot()
            st.success(f"Started (PID: {msg})") if ok else st.error(f"Failed: {msg}")
            st.rerun()
    with c2:
        if run and st.button("Stop Bot",use_container_width=True):
            stop_bot(); st.success("Stopped"); st.rerun()
    with c3:
        if st.button("Refresh",use_container_width=True): st.rerun()
    st.markdown("---")
    a=acct_info(cfg)
    if a:
        st.markdown(f"""<div class="kpi-row">
            <div class="kpi"><div class="kv">${a['balance']:,.2f}</div><div class="kl">Balance</div></div>
            <div class="kpi"><div class="kv">${a['equity']:,.2f}</div><div class="kl">Equity</div></div>
            <div class="kpi"><div class="kv">${a['profit']:+,.2f}</div><div class="kl">Floating P&L</div></div>
            <div class="kpi"><div class="kv">${a['free_margin']:,.2f}</div><div class="kl">Free Margin</div></div>
        </div>""",unsafe_allow_html=True)
    else:
        st.warning("Cannot connect to MT5. Make sure MetaTrader 5 is running.")
    st.markdown("### Open Positions")
    pos=open_pos()
    if pos:
        for p in pos:
            dn="BUY" if p.type==0 else "SELL"; tc="tc-buy" if p.type==0 else "tc-sell"
            st.markdown(f'<div class="gc {tc}"><strong>{dn}</strong> {p.volume} lots @ {p.price_open:.2f}'
                f' | SL: {p.sl:.2f} | TP: {p.tp:.2f}'
                f' | P&L: <span class="{"pos" if p.profit>=0 else "neg"}">${p.profit:+,.2f}</span></div>',
                unsafe_allow_html=True)
    else: st.info("No open positions")
    st.markdown("### Pending Orders")
    ords=pending_ord()
    if ords:
        for o in ords:
            dn="BUY LIMIT" if o.type==2 else "SELL LIMIT"
            st.markdown(f'<div class="gc"><strong>{dn}</strong> {o.volume_current} lots @ {o.price_order:.2f}'
                f' | SL: {o.sl:.2f} | TP: {o.tp:.2f}</div>',unsafe_allow_html=True)
    else: st.info("No pending orders")
    st.markdown("---")
    st.markdown("### Quick Settings")
    c1,c2,c3=st.columns(3)
    with c1: nr=st.number_input("Risk Per Trade ($)",10,5000,int(cfg['risk_per_trade']),10)
    with c2: nm=st.number_input("Min Lot",0.01,1.0,float(cfg['min_lot']),0.01)
    with c3: nx=st.number_input("Max Lot",0.1,50.0,float(cfg['max_lot']),0.1)
    if st.button("Save Settings"):
        cfg['risk_per_trade']=nr; cfg['min_lot']=nm; cfg['max_lot']=nx
        save_cfg(cfg); st.success("Saved! Bot uses new settings on next trade.")

def pg_perf(df, m, cfg):
    c1,c2=st.columns(2)
    with c1: st.plotly_chart(ch_dir(df),use_container_width=True)
    with c2: st.plotly_chart(ch_dow(df),use_container_width=True)
    c3,c4=st.columns(2)
    with c3:
        fig=ch_rwr(df)
        if fig: st.plotly_chart(fig,use_container_width=True)
        else: st.info("Not enough trades for rolling win rate")
    with c4:
        cp=df[df['outcome'].isin(['WIN','LOSS'])].copy()
        cp['year']=pd.to_datetime(cp['date']).dt.year
        yt=cp.groupby('year').agg(trades=('outcome','count'),wins=('outcome',lambda x:(x=='WIN').sum()),
            pnl=('profit_dollars','sum')).reset_index()
        yt['wr']=(yt['wins']/yt['trades']*100).round(1); yt['pnl']=yt['pnl'].round(2)
        yt.columns=['Year','Trades','Wins','P&L ($)','Win Rate %']
        st.markdown("### Yearly Breakdown")
        st.dataframe(yt,hide_index=True,use_container_width=True)
    st.markdown(f"""<div class="sg">
        <div class="si"><div class="sv">{m['max_win_streak']}</div><div class="sl">Max Win Streak</div></div>
        <div class="si"><div class="sv">{m['max_loss_streak']}</div><div class="sl">Max Loss Streak</div></div>
        <div class="si"><div class="sv">${m['avg_risk']:,.0f}</div><div class="sl">Avg Risk/Trade</div></div>
        <div class="si"><div class="sv">${m['expectancy']:,.2f}</div><div class="sl">Expectancy</div></div>
        <div class="si"><div class="sv">{m['recovery_factor']:.1f}x</div><div class="sl">Recovery Factor</div></div>
        <div class="si"><div class="sv">{m['profitable_months_pct']:.0f}%</div><div class="sl">Profitable Months</div></div>
    </div>""",unsafe_allow_html=True)
    st.markdown("### Monthly Detail")
    cp2=df[df['outcome'].isin(['WIN','LOSS'])].copy()
    cp2['month']=pd.to_datetime(cp2['date']).dt.to_period('M').astype(str)
    md=cp2.groupby('month').agg(trades=('outcome','count'),wins=('outcome',lambda x:(x=='WIN').sum()),
        pnl=('profit_dollars','sum')).reset_index()
    md['wr']=(md['wins']/md['trades']*100).round(1); md['pnl']=md['pnl'].round(2)
    md.columns=['Month','Trades','Wins','P&L ($)','Win Rate %']
    st.dataframe(md,hide_index=True,use_container_width=True,height=400)

def pg_hist(df):
    c1,c2,c3=st.columns(3)
    with c1: df2=st.selectbox("Direction",['All','BUY','SELL'])
    with c2: of=st.selectbox("Outcome",['All','WIN','LOSS','NO_FILL'])
    with c3: sf=st.selectbox("Sort",['Newest','Oldest','Best P&L','Worst P&L'])
    f=df.copy()
    if df2!='All': f=f[f['direction']==df2]
    if of!='All': f=f[f['outcome']==of]
    if sf=='Newest': f=f.sort_values('date',ascending=False)
    elif sf=='Oldest': f=f.sort_values('date')
    elif sf=='Best P&L': f=f.sort_values('profit_dollars',ascending=False)
    else: f=f.sort_values('profit_dollars')
    cols=['date','direction','outcome','entry_price','stop_loss','take_profit','lot_size','risk_dollars','profit_dollars']
    av=[c for c in cols if c in f.columns]
    st.markdown(f"**{len(f)} trades**")
    st.dataframe(f[av].reset_index(drop=True),hide_index=True,use_container_width=True,height=500)
    st.download_button("Download CSV",f[av].to_csv(index=False),"xaubot_trades.csv","text/csv")

def pg_settings(cfg):
    st.markdown("### MT5 Connection")
    c1,c2,c3=st.columns(3)
    with c1: lg=st.number_input("Login",value=int(cfg['mt5_login']),step=1)
    with c2: pw=st.text_input("Password",value=str(cfg['mt5_password']),type="password")
    with c3: sv=st.text_input("Server",value=str(cfg['mt5_server']))
    if st.button("Test Connection"):
        if MT5_OK:
            if mt5.initialize(login=int(lg),password=str(pw),server=str(sv)):
                i=mt5.account_info(); st.success(f"Connected! Account: {i.login} | Balance: ${i.balance:,.2f}")
            else: st.error(f"Failed: {mt5.last_error()}")
        else: st.error("MetaTrader5 not installed")
    st.markdown("---")
    st.markdown("### Risk Management")
    c1,c2,c3=st.columns(3)
    with c1: rk=st.number_input("Risk Per Trade ($)",10,5000,int(cfg['risk_per_trade']),10)
    with c2: mn=st.number_input("Min Lot",0.01,1.0,float(cfg['min_lot']),0.01)
    with c3: mx=st.number_input("Max Lot",0.1,50.0,float(cfg['max_lot']),0.1)
    st.markdown("---")
    st.markdown("### Display")
    bl=st.number_input("Starting Balance ($)",1000,1000000,int(cfg['starting_balance']),1000)
    st.markdown("---")
    st.markdown("### Backtest")
    c1,c2=st.columns(2)
    with c1: sd=st.date_input("Start",datetime(2024,6,1))
    with c2: ed=st.date_input("End",datetime(2026,2,8))
    if st.button("Run Backtest",type="primary"):
        nc={'mt5_login':lg,'mt5_password':pw,'mt5_server':sv,'risk_per_trade':rk,
            'min_lot':mn,'max_lot':mx,'starting_balance':bl}
        save_cfg(nc); pr=st.progress(0)
        def up(p): pr.progress(p,f"Running... {p*100:.0f}%")
        d2,msg=run_bt(nc,datetime.combine(sd,dtime(0,0)),datetime.combine(ed,dtime(23,59)),up)
        pr.empty()
        if d2 is not None and not d2.empty:
            st.session_state.df=d2; st.session_state.metrics=calc_m(d2)
            ts=datetime.now().strftime('%Y%m%d_%H%M%S')
            d2.to_csv(os.path.join(APP_DIR,f'backtest_{ts}.csv'),index=False)
            st.success(f"{len(d2)} trades found!"); st.rerun()
        else: st.error(f"Failed: {msg}")
    st.markdown("---")
    if st.button("Save All Settings"):
        save_cfg({'mt5_login':lg,'mt5_password':pw,'mt5_server':sv,'risk_per_trade':rk,
            'min_lot':mn,'max_lot':mx,'starting_balance':bl})
        st.success("Settings saved!")

# ==================== MAIN ====================
def main():
    cfg=load_cfg()
    with st.sidebar:
        st.markdown(f'<div style="text-align:center;padding:20px 0 10px;">'
            f'<div style="font-size:1.5rem;font-weight:800;'
            f'background:linear-gradient(135deg,#d4af37,#f0d060);'
            f'-webkit-background-clip:text;-webkit-text-fill-color:transparent;">'
            f'⚡ {BRAND}</div>'
            f'<div style="color:#6b6b80;font-size:0.75rem;margin-top:4px;">Gold Trading Algorithm</div>'
            f'</div>',unsafe_allow_html=True)
        run,_=bot_running(); dot="dot-g" if run else "dot-r"; st_txt="Running" if run else "Stopped"
        st.markdown(f'<div style="text-align:center;padding:8px 0 20px;">'
            f'<span class="status-dot {dot}"></span>'
            f'<span style="color:{"#00d4aa" if run else "#ff4757"};font-size:0.85rem;font-weight:600;">'
            f'Bot {st_txt}</span></div>',unsafe_allow_html=True)
        st.markdown("---")
        page=st.radio("Nav",["Overview","Live Trading","Performance","Trade History","Settings"],
            label_visibility="collapsed")
        st.markdown("---")
        csvs=sorted([f for f in os.listdir(APP_DIR) if (f.startswith('backtest_') or f.startswith('analysis_'))
            and f.endswith('.csv')],reverse=True)
        if csvs:
            sel=st.selectbox("Load Results",csvs,label_visibility="collapsed")
            if st.button("Load",use_container_width=True):
                df=pd.read_csv(os.path.join(APP_DIR,sel))
                st.session_state.df=df; st.session_state.metrics=calc_m(df); st.rerun()
        st.markdown('<div style="position:fixed;bottom:20px;color:#3a3a4e;font-size:0.7rem;'
            'text-align:center;width:200px;">v1.0 | Proprietary Algorithm</div>',unsafe_allow_html=True)

    if page=="Live Trading": st.markdown("## Live Trading"); pg_live(cfg); return
    if page=="Settings": st.markdown("## Settings"); pg_settings(cfg); return

    if 'df' not in st.session_state: st.session_state.df=None; st.session_state.metrics=None
    if st.session_state.df is None and csvs:
        st.session_state.df=pd.read_csv(os.path.join(APP_DIR,csvs[0]))
        st.session_state.metrics=calc_m(st.session_state.df)

    if st.session_state.df is None or not st.session_state.metrics:
        st.info("No data. Go to **Settings** to run a backtest or load a CSV from sidebar."); return

    df,m=st.session_state.df,st.session_state.metrics
    if page=="Overview": pg_overview(df,m,cfg)
    elif page=="Performance": st.markdown("## Performance"); pg_perf(df,m,cfg)
    elif page=="Trade History": st.markdown("## Trade History"); pg_hist(df)

if __name__=="__main__": main()

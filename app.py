import io
import os
import secrets
import threading
import time
from collections import Counter
from functools import wraps

import qrcode
from flask import Flask, abort, jsonify, redirect, render_template, request, send_file, session, url_for

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(32))
TEACHER_PASSWORD = os.environ.get("TEACHER_PASSWORD")
if not TEACHER_PASSWORD:
    print("ATTENZIONE: configura TEACHER_PASSWORD su Render prima di usare il pannello docente.")

QUESTIONS = [
    {"id":"q1","prompt":"Se il limite di f(x) per x→2 è 3, quale affermazione è necessaria?","options":["f(2)=3","I valori f(x) sono vicini a 3 quando x è sufficientemente vicino a 2, con x≠2","f(x)=3 per ogni x","f è continua ovunque"],"correct":1,"explanation":"Il limite riguarda il comportamento vicino al punto, non necessariamente il valore nel punto."},
    {"id":"q2","prompt":"Per f(x)=2x−1, quanto vale il limite per x→2?","options":["1","2","3","4"],"correct":2,"explanation":"Quando x si avvicina a 2, 2x−1 si avvicina a 3."},
    {"id":"q3","prompt":"Nella definizione di limite finito, che cosa rappresenta ε?","options":["La distanza richiesta tra f(x) e L","Il valore f(x₀)","Il numero di punti del grafico","Il limite laterale"],"correct":0,"explanation":"ε indica una tolleranza positiva, arbitrariamente piccola, sui valori della funzione."},
    {"id":"q4","prompt":"Se il limite sinistro è 4 e il limite destro è 4, mentre f(a)=9, qual è il limite per x→a?","options":["9","4","Non esiste","13"],"correct":1,"explanation":"I limiti laterali coincidono: il limite è 4, indipendentemente dal valore in a."},
    {"id":"q5","prompt":"Se il limite sinistro è 3 e quello destro è 5, quale conclusione è corretta?","options":["Il limite è 4","Il limite è 8","Il limite bilatero non esiste","Il limite è 5"],"correct":2,"explanation":"Limiti laterali diversi impediscono l'esistenza del limite bilatero."},
    {"id":"q6","prompt":"Per f(x)=1/x², che cosa succede quando x→0?","options":["Il limite è 0","Il limite è +∞","Il limite è −∞","Il limite è 1"],"correct":1,"explanation":"Il denominatore è positivo e tende a zero: i valori crescono senza limite."},
    {"id":"q7","prompt":"Che cosa significa lim f(x)=+∞ per x→a?","options":["f(a) è un numero molto grande","f(x) supera ogni soglia M>0 per x sufficientemente vicino ad a","f(x) è sempre positiva su tutto il dominio","Il grafico incontra il punto (+∞,+∞)"],"correct":1,"explanation":"Ogni soglia positiva può essere superata stabilmente in un intorno puntato di a."},
    {"id":"q8","prompt":"Per f(x)=1/x, quando x→0 da sinistra e da destra, rispettivamente, si ottiene:","options":["+∞ e +∞","−∞ e −∞","−∞ e +∞","0 e 0"],"correct":2,"explanation":"Da sinistra il reciproco è negativo e illimitato; da destra è positivo e illimitato."},
    {"id":"q9","prompt":"Per f(x)=−1/x², quale limite si ottiene quando x→0?","options":["+∞","−∞","0","Il limite destro è +∞"],"correct":1,"explanation":"Il reciproco di x² cresce senza limite, ma il segno meno rende tutti i valori negativi."},
    {"id":"q10","prompt":"Quale frase descrive correttamente δ nella definizione di limite?","options":["La precisione richiesta sui valori di f(x)","La vicinanza sufficiente di x a x₀","Il valore del limite","Il valore della funzione nel punto"],"correct":1,"explanation":"δ esprime quanto vicino a x₀ bisogna considerare x, senza richiedere agli studenti di calcolarlo."},
]
QMAP = {q["id"]:q for q in QUESTIONS}
lock = threading.RLock()
state = {"id":None, "open":False, "reveal":False, "answers":{}, "seen":{}, "generation":secrets.token_hex(8)}

def teacher_only(f):
    @wraps(f)
    def inner(*a,**kw):
        if not session.get("teacher"): return jsonify(error="Accesso docente richiesto"),403
        return f(*a,**kw)
    return inner

@app.get("/")
def home(): return redirect(url_for("lesson"))

@app.route("/teacher/login",methods=["GET","POST"])
def login():
    error=""
    if request.method=="POST":
        if TEACHER_PASSWORD and secrets.compare_digest(request.form.get("password",""),TEACHER_PASSWORD):
            session.clear();session["teacher"]=True
            return redirect(url_for("teacher"))
        error="Password non corretta o non configurata."
    return render_template("login.html",error=error)

@app.get("/teacher")
def teacher():
    if not session.get("teacher"):return redirect(url_for("login"))
    return render_template("teacher.html")

@app.get("/lezione")
def lesson():
    if "student_id" not in session:session["student_id"]=secrets.token_urlsafe(24)
    return render_template("lesson.html")

@app.get("/qr")
def qr():
    url=request.url_root.rstrip("/") + url_for("lesson")
    qr_img=qrcode.make(url)
    out=io.BytesIO();qr_img.save(out,format="PNG");out.seek(0)
    return send_file(out,mimetype="image/png",max_age=30)

@app.get("/api/questions")
@teacher_only
def questions():return jsonify([{"id":q["id"],"prompt":q["prompt"]} for q in QUESTIONS])

@app.get("/api/state")
def student_state():
    sid=session.get("student_id")
    if not sid:
        sid=secrets.token_urlsafe(24);session["student_id"]=sid
    with lock:
        state["seen"][sid]=time.time()
        q=QMAP.get(state["id"])
        ans=state["answers"].get(sid)
        return jsonify(question={"id":q["id"],"prompt":q["prompt"],"options":q["options"]} if q else None,
                       open=state["open"],reveal=state["reveal"],answered=ans is not None,
                       selected=ans,correct=q["correct"] if q and state["reveal"] else None,
                       explanation=q["explanation"] if q and state["reveal"] else None)

@app.post("/api/answer")
def answer():
    sid=session.get("student_id")
    if not sid:return jsonify(error="Apri prima la pagina della lezione."),400
    d=request.get_json(silent=True) or {}
    with lock:
        q=QMAP.get(state["id"])
        if not q or not state["open"] or d.get("id")!=q["id"]:return jsonify(error="Domanda chiusa o non attiva."),409
        if sid in state["answers"]:return jsonify(error="Hai già risposto a questa domanda."),409
        i=d.get("index")
        if type(i) is not int or i<0 or i>=len(q["options"]):return jsonify(error="Risposta non valida."),400
        state["answers"][sid]=i
    return jsonify(ok=True)

@app.get("/api/teacher/state")
@teacher_only
def teacher_state():
    with lock:
        q=QMAP.get(state["id"])
        counts=Counter(state["answers"].values())
        return jsonify(question=q,open=state["open"],reveal=state["reveal"],
                       counts=[counts[i] for i in range(len(q["options"]))] if q else [],
                       total=len(state["answers"]),
                       online=sum(time.time()-t<45 for t in state["seen"].values()))

@app.post("/api/teacher/action")
@teacher_only
def teacher_action():
    d=request.get_json(silent=True) or {}
    a=d.get("action")
    with lock:
        if a=="open":
            if d.get("id") not in QMAP:return jsonify(error="Domanda sconosciuta."),400
            state.update(id=d["id"],open=True,reveal=False,answers={})
        elif a=="close":state["open"]=False
        elif a=="reveal":state["open"]=False;state["reveal"]=True
        elif a=="clear":state.update(id=None,open=False,reveal=False,answers={})
        elif a=="reset":state["answers"]={}
        elif a=="new":state.update(id=None,open=False,reveal=False,answers={},seen={},generation=secrets.token_hex(8))
        else:return jsonify(error="Azione non valida."),400
    return jsonify(ok=True)

@app.get("/health")
def health():return "ok",200

if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.getenv("PORT","10000")))

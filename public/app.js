// ---------- Test catalogue: every test is optional ----------
const TESTS = [
  {id:"basic", group:"About you", icon:"🙂", label:"Age & sex", fields:[
    {k:"age", label:"Age", unit:"yrs", ph:"45"}, {k:"sex", label:"Sex", options:["Female","Male"]}]},
  {id:"body", group:"About you", icon:"⚖️", label:"Height & weight", fields:[
    {k:"height", label:"Height", unit:"cm", ph:"165"}, {k:"weight", label:"Weight", unit:"kg", ph:"70"}]},
  {id:"bp", group:"Vitals", icon:"🩺", label:"Blood pressure", fields:[
    {k:"sys", label:"Upper (systolic)", unit:"mmHg", ph:"120"}, {k:"dia", label:"Lower (diastolic)", unit:"mmHg", ph:"80"}]},
  {id:"hr", group:"Vitals", icon:"❤️", label:"Heart rate", fields:[{k:"hr", label:"Beats per minute", unit:"bpm", ph:"75"}]},
  {id:"glu", group:"Vitals", icon:"🩸", label:"Blood sugar", fields:[
    {k:"glu", label:"Glucose", unit:"mg/dL", ph:"100"},
    {k:"glutype", label:"When measured", options:["Fasting","After meal (2 hr)","Random"]}]},
  {id:"temp", group:"Vitals", icon:"🌡️", label:"Temperature", fields:[
    {k:"temp", label:"Temperature", ph:"37.0", step:"0.1"}, {k:"tunit", label:"Unit", options:["°C","°F"]}]},
  {id:"spo2", group:"Vitals", icon:"💨", label:"Oxygen (SpO₂)", fields:[{k:"spo2", label:"Oxygen level", unit:"%", ph:"98"}]},
  {id:"a1c", group:"Blood tests", icon:"🍬", label:"HbA1c", fields:[{k:"a1c", label:"HbA1c", unit:"%", ph:"5.5", step:"0.1"}]},
  {id:"lipid", group:"Blood tests", icon:"🧬", label:"Cholesterol panel", fields:[
    {k:"chol", label:"Total", unit:"mg/dL"}, {k:"ldl", label:"LDL", unit:"mg/dL"},
    {k:"hdl", label:"HDL", unit:"mg/dL"}, {k:"tg", label:"Triglycerides", unit:"mg/dL"}]},
  {id:"hb", group:"Blood tests", icon:"🔴", label:"Hemoglobin", fields:[{k:"hb", label:"Hemoglobin", unit:"g/dL", ph:"13.5", step:"0.1"}]},
  {id:"creat", group:"Blood tests", icon:"🧪", label:"Creatinine", fields:[{k:"creat", label:"Creatinine", unit:"mg/dL", ph:"0.9", step:"0.01"}]},
  {id:"tsh", group:"Blood tests", icon:"🦋", label:"Thyroid (TSH)", fields:[{k:"tsh", label:"TSH", unit:"mIU/L", ph:"2.0", step:"0.01"}]},
  {id:"notes", group:"Documents", icon:"💊", label:"Prescription / symptoms / other results", wide:true, fields:[
    {k:"notes", label:"Paste or type anything else", area:true}]},
];
const SAMPLE = {age:52, sex:"Male", height:172, weight:86, sys:142, dia:91, glu:148, glutype:"After meal (2 hr)",
  chol:242, ldl:158, hdl:38, tg:210, a1c:6.1,
  notes:"Taking Metformin 500 mg twice daily. Tired and thirsty lately."};
const SAMPLE_TESTS = ["basic","body","bp","glu","lipid","a1c","notes"];

const $ = s => document.querySelector(s);
const esc = s => String(s).replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const selected = new Set();

// ---------- Step 1: picker ----------
function renderPicker(){
  const groups = [...new Set(TESTS.map(t => t.group))];
  $("#picker").innerHTML = groups.map(g => `
    <div class="group"><h3>${g}</h3><div class="chips">
    ${TESTS.filter(t => t.group === g).map(t =>
      `<button class="chip-btn" type="button" data-id="${t.id}" aria-pressed="false"><span class="ic">${t.icon}</span>${t.label}</button>`).join("")}
    </div></div>`).join("");
}
$("#picker").addEventListener("click", e => { const b = e.target.closest(".chip-btn"); if(b) toggle(b.dataset.id); });

function syncPicker(){
  document.querySelectorAll(".chip-btn").forEach(b => b.setAttribute("aria-pressed", selected.has(b.dataset.id)));
}
function toggle(id){ selected.has(id) ? selected.delete(id) : selected.add(id); syncPicker(); renderCards(); }

// ---------- Step 2: input cards only for chosen tests ----------
function renderCards(){
  const keep = {};
  document.querySelectorAll("[data-k]").forEach(el => keep[el.dataset.k] = el.value);
  const list = TESTS.filter(t => selected.has(t.id));
  $("#entry").hidden = list.length === 0;
  $("#cards").innerHTML = list.map(t => `
    <div class="card ${t.wide ? "wide" : ""}">
      <div class="card-top"><span class="card-ic">${t.icon}</span><b>${t.label}</b>
        <button class="x" type="button" data-remove="${t.id}" aria-label="Remove ${t.label}">×</button></div>
      <div class="fields ${t.fields.length === 1 ? "one" : ""}">
        ${t.fields.map(f => f.options
          ? `<label><span>${f.label}</span><select data-k="${f.k}">${f.options.map(o => `<option>${o}</option>`).join("")}</select></label>`
          : f.area
          ? `<label><span>${f.label}</span><textarea data-k="${f.k}" placeholder="e.g. Metformin 500 mg twice daily; tired for two weeks; creatinine 1.1…"></textarea></label>`
          : `<label><span>${f.label}</span><div class="inp"><input data-k="${f.k}" type="number" step="${f.step || "any"}" inputmode="decimal" placeholder="${f.ph || ""}">${f.unit ? `<em>${f.unit}</em>` : ""}</div></label>`).join("")}
      </div>
    </div>`).join("");
  document.querySelectorAll("[data-k]").forEach(el => { if(keep[el.dataset.k] !== undefined) el.value = keep[el.dataset.k]; });
}
$("#cards").addEventListener("click", e => { const r = e.target.closest("[data-remove]"); if(r) toggle(r.dataset.remove); });

$("#reset").addEventListener("click", () => {
  selected.clear(); syncPicker(); renderCards();
  $("#results").hidden = true; $("#err").textContent = ""; window.scrollTo({top:0, behavior:"smooth"});
});

$("#sample").addEventListener("click", () => {
  selected.clear(); SAMPLE_TESTS.forEach(id => selected.add(id)); syncPicker(); renderCards();
  document.querySelectorAll("[data-k]").forEach(el => { if(SAMPLE[el.dataset.k] !== undefined) el.value = SAMPLE[el.dataset.k]; });
  $("#entry").scrollIntoView({behavior:"smooth"});
});

// ---------- Step 3: call backend ----------
$("#go").addEventListener("click", async () => {
  const body = {};
  document.querySelectorAll("[data-k]").forEach(el => { if(el.value.trim() !== "") body[el.dataset.k] = el.value.trim(); });
  const typed = Object.keys(body).filter(k => !["sex","glutype","tunit"].includes(k));
  const err = $("#err"); err.textContent = "";
  if(!typed.length){ err.textContent = "Type at least one value first, or remove the tests you don’t have."; return; }

  const btn = $("#go"); btn.disabled = true; btn.textContent = "Analyzing…";
  $("#results").hidden = false;
  $("#ai").innerHTML = '<p class="muted">Claude is reading your results…</p>';
  $("#banner").innerHTML = $("#flags").innerHTML = $("#risks").innerHTML = $("#alerts").innerHTML = "";
  try{
    const res = await fetch("/api/analyze", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify(body)});
    const data = await res.json();
    if(!res.ok){ $("#results").hidden = true; err.textContent = data.error || "Something went wrong."; }
    else render(data);
  }catch(e){ $("#results").hidden = true; err.textContent = "Could not reach the server. Is app.py running?"; }
  btn.disabled = false; btn.textContent = "Analyze my report";
  if(!$("#results").hidden) $("#results").scrollIntoView({behavior:"smooth"});
});

function banner(d){
  const c = {ok:0, warn:0, bad:0}; d.flags.forEach(f => c[f.status]++);
  const worst = (d.alerts.length || c.bad) ? "bad" : c.warn ? "warn" : "ok";
  const title = {bad:"Some values need attention", warn:"A few values are worth watching",
                 ok: d.flags.length ? "Everything you entered looks in range" : "Here is what we found"}[worst];
  const glyph = {bad:"!", warn:"i", ok:"✓"}[worst];
  const line = d.flags.length ? `${c.bad} need attention · ${c.warn} worth watching · ${c.ok} in range` : "Only notes were provided";
  return `<div class="banner ${worst}"><div class="ico">${glyph}</div><div><b>${title}</b><span>${line}</span></div></div>`;
}

function render(d){
  $("#banner").innerHTML = banner(d);
  $("#alerts").innerHTML = d.alerts.map(a => `<div class="alert">⚠ ${esc(a)}</div>`).join("");
  const groups = [...new Set(d.flags.map(f => f.group))];
  $("#flags").innerHTML = groups.map(g => `
    <div class="flag-group"><h3>${g}</h3><div class="flag-grid">
    ${d.flags.filter(f => f.group === g).map(f => `
      <div class="flag st-${f.status}"><small>${esc(f.label)}</small><b>${esc(f.value)}</b><span class="pill ${f.status}">${esc(f.text)}</span></div>`).join("")}
    </div></div>`).join("");
  $("#risks").innerHTML = d.risks.length
    ? `<h3 style="margin-top:22px">Machine-learning screening</h3><div class="risk-row">${d.risks.map(gauge).join("")}</div>`
    : `<p class="muted">ML screening scores appear when enough related values are entered (diabetes: blood sugar + age; heart: age, sex, systolic BP + cholesterol).</p>`;
  $("#ai").innerHTML = d.ai ? md(d.ai) : `<p class="muted">${esc(d.ai_error || "No interpretation available.")}</p>`;
}

function gauge(r){
  const p = r.probability, col = p < .33 ? "var(--ok)" : p < .66 ? "var(--warn)" : "var(--bad)";
  const cx = 110, cy = 105, R = 80, a = Math.PI - p * Math.PI;
  const pt = ang => [cx + R * Math.cos(ang), cy - R * Math.sin(ang)];
  const [x1,y1] = pt(Math.PI), [x2,y2] = pt(0), [xm,ym] = pt(a);
  return `<div class="risk"><h4>${r.title}</h4>
    <svg viewBox="0 0 220 120" width="220" height="120" role="img" aria-label="${Math.round(p*100)} percent">
      <path d="M${x1} ${y1} A${R} ${R} 0 0 1 ${x2} ${y2}" fill="none" stroke="var(--line)" stroke-width="14" stroke-linecap="round"/>
      <path d="M${x1} ${y1} A${R} ${R} 0 0 1 ${xm} ${ym}" fill="none" stroke="${col}" stroke-width="14" stroke-linecap="round"/>
    </svg>
    <div class="pct" style="color:${col}">${Math.round(p*100)}%</div>
    <span class="pill" style="background:var(--panel);color:${col}">${r.band} likelihood</span>
    <p>Based on: ${esc(r.used.join(", "))}.<br>Held-out accuracy ${Math.round(r.metrics.accuracy*100)}%, AUC ${r.metrics.auc}.<br>${esc(r.note)}</p></div>`;
}

// minimal markdown renderer for Claude's answer (HTML is escaped first)
function md(s){
  let out = "", list = false;
  const inl = x => x.replace(/\*\*(.+?)\*\*/g, "<b>$1</b>");
  for(const raw of esc(s).split("\n")){
    const l = raw.trim();
    if(/^[-*] /.test(l)){ if(!list){out += "<ul>"; list = true} out += `<li>${inl(l.slice(2))}</li>`; continue }
    if(list){ out += "</ul>"; list = false }
    if(/^#{1,4} /.test(l)) out += `<h4>${inl(l.replace(/^#+ /, ""))}</h4>`;
    else if(l) out += `<p>${inl(l)}</p>`;
  }
  return out + (list ? "</ul>" : "");
}

renderPicker();

import {useCallback,useEffect,useState} from "react";
import type {FormEvent} from "react";
import {Link} from "react-router-dom";
import {api} from "../services/api";
import type {CreateReportPayload,GeographicState,LocalGovernmentArea,Report} from "../types/api";
import {useAuth} from "../state/AuthContext";

const dateFormat=new Intl.DateTimeFormat("en-NG",{dateStyle:"medium"});

export default function DashboardPage(){
  const{user}=useAuth();
  const[reports,setReports]=useState<Report[]>([]);
  const[loading,setLoading]=useState(true);
  const[error,setError]=useState("");
  const[showForm,setShowForm]=useState(false);
  const load=useCallback(async()=>{setError("");try{setReports(await api.reports())}catch(err){setError(err instanceof Error?err.message:"Could not load reports")}finally{setLoading(false)}},[]);
  useEffect(()=>{void load()},[load]);
  const active=reports.filter(r=>!["RESOLVED","REJECTED"].includes(r.status)).length;
  const resolved=reports.filter(r=>r.status==="RESOLVED").length;
  async function submit(p:CreateReportPayload){await api.createReport(p);setShowForm(false);await load()}
  return <>
    <section className="citizen-dashboard-banner"><div><p className="eyebrow">YOUR VOICE. YOUR COMMUNITY.</p><h2>Progress starts with participation.</h2><p>Keep track of the issues you have raised and the action that follows.</p></div><span className="dashboard-fist" aria-hidden="true">✊</span></section>
    <section className="welcome-row"><div><p className="eyebrow">CITIZEN DASHBOARD</p><h1>Good day, {user?.full_name.split(" ")[0]}.</h1><p className="muted">Here’s an overview of the reports connected to your account.</p></div><button className="button button-primary" onClick={()=>setShowForm(v=>!v)}>{showForm?"Close form":"+ Submit a report"}</button></section>
    <section className="stat-grid"><Stat label="Total reports" value={reports.length} hint="Reports in your account"/><Stat label="In progress" value={active} hint="Awaiting action or review"/><Stat label="Resolved" value={resolved} hint="Marked as resolved"/></section>
    {showForm&&<ReportForm onSubmit={submit} onCancel={()=>setShowForm(false)}/>}
    <section className="panel"><div className="panel-heading"><div><h2>Your reports</h2><p className="muted">Open a report to see its details, updates, and evidence.</p></div><button className="button button-quiet button-small" onClick={()=>void load()}>Refresh</button></div>
      {error&&<p className="form-error" role="alert">{error}</p>}
      {loading?<div className="empty-state">Loading your reports…</div>:reports.length===0?<div className="empty-state"><div className="empty-icon">＋</div><h3>No reports yet</h3><p>When you submit a community issue, it will appear here.</p><button className="button button-primary" onClick={()=>setShowForm(true)}>Submit your first report</button></div>:<div className="report-list">{reports.map(r=><Link className="report-row report-row-link" to={`/reports/${r.id}`} key={r.id}><div className="report-symbol">{r.category.slice(0,1).toUpperCase()}</div><div className="report-main"><div className="report-title-line"><h3>{r.title}</h3><span className={`status-badge status-${r.status.toLowerCase()}`}>{r.status.replaceAll("_"," ")}</span></div><p>{r.category} · {r.address||`${r.latitude.toFixed(3)}, ${r.longitude.toFixed(3)}`}</p><small>Submitted {dateFormat.format(new Date(r.created_at))} · Report #{r.id}</small></div><span className="report-open">View details →</span></Link>)}</div>}
    </section>
  </>;
}

function Stat({label,value,hint}:{label:string;value:number;hint:string}){return <article className="stat-card"><span>{label}</span><strong>{value}</strong><small>{hint}</small></article>}

function ReportForm({onSubmit,onCancel}:{onSubmit:(p:CreateReportPayload)=>Promise<void>;onCancel:()=>void}){
  const[title,setTitle]=useState("");
  const[description,setDescription]=useState("");
  const[category,setCategory]=useState("Infrastructure");
  const[latitude,setLatitude]=useState("");
  const[longitude,setLongitude]=useState("");
  const[address,setAddress]=useState("");
  const[states,setStates]=useState<GeographicState[]>([]);
  const[lgas,setLgas]=useState<LocalGovernmentArea[]>([]);
  const[stateCode,setStateCode]=useState("");
  const[lgaCode,setLgaCode]=useState("");
  const[error,setError]=useState("");
  const[busy,setBusy]=useState(false);
  const[gps,setGps]=useState<{latitude:number;longitude:number}|null>(null);
  const[gpsBusy,setGpsBusy]=useState(false);
  function captureLocation(){
    if(!navigator.geolocation){setError("This browser does not support location sharing.");return}
    setGpsBusy(true);setError("");
    navigator.geolocation.getCurrentPosition(position=>{
      const coords={latitude:position.coords.latitude,longitude:position.coords.longitude};
      setGps(coords);setLatitude(String(coords.latitude));setLongitude(String(coords.longitude));setGpsBusy(false);
    },()=>{setError("Location was not shared. You can enter the incident coordinates manually.");setGpsBusy(false)},{enableHighAccuracy:true,timeout:15000,maximumAge:60000});
  }
  useEffect(()=>{api.states().then(setStates).catch(()=>setError("Could not load the state directory."))},[]);
  useEffect(()=>{setLgaCode("");if(!stateCode){setLgas([]);return}api.lgas(stateCode).then(setLgas).catch(()=>setError("Could not load LGAs for the selected state."))},[stateCode]);
  async function submit(e:FormEvent){
    e.preventDefault();setError("");setBusy(true);
    try{await onSubmit({title:title.trim(),description:description.trim(),category,latitude:Number(latitude),longitude:Number(longitude),gps_latitude:gps?.latitude,gps_longitude:gps?.longitude,address:address.trim()||undefined,incident_state_code:stateCode,incident_lga_code:lgaCode})}
    catch(err){setError(err instanceof Error?err.message:"Could not submit report")}
    finally{setBusy(false)}
  }
  return <section className="panel report-form-panel">
    <div className="panel-heading"><div><h2>Submit a community report</h2><p className="muted">Tell us what happened and select where the incident occurred. This can be different from your home area.</p></div></div>
    <form className="form-grid" onSubmit={submit}>
      <label className="field-wide">Report title<input required maxLength={180} value={title} onChange={e=>setTitle(e.target.value)} placeholder="e.g. Large pothole on Market Road"/></label>
      <label>Category<select value={category} onChange={e=>setCategory(e.target.value)}>{["Infrastructure","Roads and Transport","Water and Sanitation","Electricity","Public Safety","Healthcare","Environment","Other"].map(v=><option key={v}>{v}</option>)}</select></label>
      <label className="field-wide">Description<textarea required rows={4} value={description} onChange={e=>setDescription(e.target.value)} placeholder="Explain what happened, where it is, and how it affects the community."/></label>
      <label>Incident state or FCT<select required value={stateCode} onChange={e=>setStateCode(e.target.value)}><option value="">Select state</option>{states.map(state=><option key={state.code} value={state.code}>{state.name}</option>)}</select></label>
      <label>Incident LGA<select required disabled={!stateCode||lgas.length===0} value={lgaCode} onChange={e=>setLgaCode(e.target.value)}><option value="">Select LGA</option>{lgas.map(lga=><option key={lga.code} value={lga.code}>{lga.name}</option>)}</select></label>
      <div className="field-wide"><p className="muted">Optional: share your device location to help administrators review the incident location. Your browser will ask for permission. You can continue without sharing it.</p><button type="button" className="button button-quiet button-small" onClick={captureLocation} disabled={gpsBusy}>{gpsBusy?"Getting location…":gps?"Location shared — update location":"Use my current location"}</button>{gps&&<small className="muted">GPS captured: {gps.latitude.toFixed(5)}, {gps.longitude.toFixed(5)}. Your selected State and LGA will remain unchanged.</small>}</div>
      <label>Latitude<input type="number" step="any" min="-90" max="90" required value={latitude} onChange={e=>setLatitude(e.target.value)} placeholder="e.g. 6.5244"/></label>
      <label>Longitude<input type="number" step="any" min="-180" max="180" required value={longitude} onChange={e=>setLongitude(e.target.value)} placeholder="e.g. 3.3792"/></label>
      <label className="field-wide">Address or landmark (optional)<input value={address} onChange={e=>setAddress(e.target.value)} placeholder="Street, area, LGA, state"/></label>
      {error&&<p className="form-error field-wide" role="alert">{error}</p>}
      <div className="form-actions field-wide"><button type="button" className="button button-quiet" onClick={onCancel}>Cancel</button><button className="button button-primary" disabled={busy||!stateCode||!lgaCode}>{busy?"Submitting…":"Submit report"}</button></div>
    </form>
  </section>;
}

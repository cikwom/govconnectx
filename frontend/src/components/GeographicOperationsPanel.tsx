import { useCallback, useEffect, useState } from "react";
import { tokenStore } from "../services/api";
import "../styles.css";

type Department = { id: number; name: string };
type StateItem = { code: string; name: string; geopolitical_zone: string };
type LgaItem = { code: string; name: string; state_code: string };
type Scope = { id: number; department_id: number; state_code: string; lga_code: string | null };
type RoutingCategory = { id: number; department_id: number; category: string };
type LgaSummary = { code: string; name: string; total: number; open: number; unassigned: number };
type StateSummary = { code: string; name: string; total: number; open: number; unassigned: number; lgas: LgaSummary[] };
type ZoneSummary = { name: string; total: number; open: number; unassigned: number; states: StateSummary[] };
type Geography = { country: string; total_states: number; total_lgas: number; geopolitical_zones: ZoneSummary[] };
type UnassignedReport = { id: number; title: string; category: string; status: string; address: string | null; incident_state_code: string | null; incident_lga_code: string | null };

const API_URL = (import.meta.env.VITE_API_URL ?? "http://localhost:8000").replace(/\/$/, "");
async function geoRequest<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set("Authorization", \`Bearer \${tokenStore.get() ?? ""}\`);
  if (options.body) headers.set("Content-Type", "application/json");
  const response = await fetch(\`\${API_URL}/api/v1\${path}\`, { ...options, headers });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail ?? \`Request failed (\${response.status})\`);
  }
  return response.json() as Promise<T>;
}

export default function GeographicOperationsPanel() {
  const [departments, setDepartments] = useState<Department[]>([]);
  const [selectedDepartment, setSelectedDepartment] = useState("");
  const [states, setStates] = useState<StateItem[]>([]);
  const [lgas, setLgas] = useState<LgaItem[]>([]);
  const [selectedState, setSelectedState] = useState("");
  const [selectedLga, setSelectedLga] = useState("");
  const [scopes, setScopes] = useState<Scope[]>([]);
  const [categories, setCategories] = useState<RoutingCategory[]>([]);
  const [categoryText, setCategoryText] = useState("");
  const [geography, setGeography] = useState<Geography | null>(null);
  const [unassigned, setUnassigned] = useState<UnassignedReport[]>([]);
  const [triageDepartment, setTriageDepartment] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const loadOperationalData = useCallback(async () => {
    const [departmentRows, stateRows, geographyData, queue] = await Promise.all([
      geoRequest<Department[]>("/departments"),
      geoRequest<StateItem[]>("/locations/states"),
      geoRequest<Geography>("/admin/geography/overview"),
      geoRequest<{ total: number; items: UnassignedReport[] }>("/admin/reports/unassigned?limit=100"),
    ]);
    setDepartments(departmentRows);
    setSelectedDepartment(current => current || String(departmentRows[0]?.id ?? ""));
    setStates(stateRows);
    setGeography(geographyData);
    setUnassigned(queue.items);
    setTriageDepartment(current => current || String(departmentRows[0]?.id ?? ""));
  }, []);

  const loadDepartmentSettings = useCallback(async () => {
    if (!selectedDepartment) {
      setScopes([]);
      setCategories([]);
      setCategoryText("");
      return;
    }
    const [scopeRows, categoryRows] = await Promise.all([
      geoRequest<Scope[]>(\`/departments/\${selectedDepartment}/geographic-scopes\`),
      geoRequest<RoutingCategory[]>(\`/departments/\${selectedDepartment}/routing-categories\`),
    ]);
    setScopes(scopeRows);
    setCategories(categoryRows);
    setCategoryText(categoryRows.map(item => item.category).join("\n"));
  }, [selectedDepartment]);

  useEffect(() => {
    setBusy(true);
    loadOperationalData().catch(e => setError(e instanceof Error ? e.message : "Could not load geographic operations"))
      .finally(() => setBusy(false));
  }, [loadOperationalData]);

  useEffect(() => {
    loadDepartmentSettings().catch(e => setError(e instanceof Error ? e.message : "Could not load department settings"));
  }, [loadDepartmentSettings]);

  useEffect(() => {
    if (!selectedState) {
      setLgas([]);
      setSelectedLga("");
      return;
    }
    geoRequest<LgaItem[]>(\`/locations/states/\${selectedState}/lgas\`)
      .then(rows => setLgas(rows))
      .catch(e => setError(e instanceof Error ? e.message : "Could not load LGAs"));
  }, [selectedState]);

  async function saveScopes(next: Array<{ state_code: string; lga_code: string | null }>) {
    if (!selectedDepartment) return;
    setBusy(true); setError(""); setMessage("");
    try {
      const rows = await geoRequest<Scope[]>(\`/departments/\${selectedDepartment}/geographic-scopes\`, {
        method: "PUT", body: JSON.stringify(next),
      });
      setScopes(rows);
      setMessage("Department geographic coverage saved.");
    } catch (e) { setError(e instanceof Error ? e.message : "Could not save geographic coverage"); }
    finally { setBusy(false); }
  }

  async function addScope(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedState) return;
    await saveScopes([...scopes.map(({ state_code, lga_code }) => ({ state_code, lga_code })), {
      state_code: selectedState, lga_code: selectedLga || null,
    }]);
  }

  async function saveCategories(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedDepartment) return;
    setBusy(true); setError(""); setMessage("");
    try {
      const payload = categoryText.split("\n").map(value => value.trim()).filter(Boolean).map(category => ({ category }));
      const rows = await geoRequest<RoutingCategory[]>(\`/departments/\${selectedDepartment}/routing-categories\`, {
        method: "PUT", body: JSON.stringify(payload),
      });
      setCategories(rows);
      setCategoryText(rows.map(item => item.category).join("\n"));
      setMessage("Department routing categories saved.");
    } catch (e) { setError(e instanceof Error ? e.message : "Could not save routing categories"); }
    finally { setBusy(false); }
  }

  async function assignFromTriage(report: UnassignedReport) {
    if (!triageDepartment) return;
    setBusy(true); setError(""); setMessage("");
    try {
      await geoRequest(\`/reports/\${report.id}/assignments\`, {
        method: "POST",
        body: JSON.stringify({ department_id: Number(triageDepartment), note: "Assigned from national geographic triage queue" }),
      });
      setMessage(\`Report #\${report.id} assigned successfully.\`);
      await loadOperationalData();
    } catch (e) { setError(e instanceof Error ? e.message : "Could not assign report"); }
    finally { setBusy(false); }
  }

  return <section className="panel geo-operations">
    <div className="panel-heading"><div><h2>Geographic operations</h2><p className="muted">Define each department’s service area, configure incident routing and review reports awaiting national triage.</p></div><button className="button button-quiet button-small" disabled={busy} onClick={() => { setBusy(true); loadOperationalData().then(loadDepartmentSettings).catch(e => setError(e.message)).finally(() => setBusy(false)); }}>Refresh</button></div>
    {error && <p className="form-error admin-error" role="alert">{error}</p>}
    {message && <p className="geo-success" role="status">{message}</p>}

    <div className="geo-config-grid">
      <article className="geo-config-card">
        <h3>Department jurisdiction</h3>
        <p className="muted">A whole State or selected LGAs can be assigned to a department. Staff access is enforced by the backend.</p>
        <label>Department<select value={selectedDepartment} onChange={e => setSelectedDepartment(e.target.value)}><option value="">Select department</option>{departments.map(dept => <option key={dept.id} value={dept.id}>{dept.name}</option>)}</select></label>
        <form className="geo-scope-form" onSubmit={addScope}>
          <label>State<select value={selectedState} onChange={e => { setSelectedState(e.target.value); setSelectedLga(""); }}><option value="">Choose a State</option>{states.map(state => <option key={state.code} value={state.code}>{state.name}</option>)}</select></label>
          <label>LGA <span className="muted">(optional — blank means entire State)</span><select value={selectedLga} onChange={e => setSelectedLga(e.target.value)} disabled={!selectedState}><option value="">Entire State</option>{lgas.map(lga => <option key={lga.code} value={lga.code}>{lga.name}</option>)}</select></label>
          <button className="button button-primary button-small" disabled={busy || !selectedDepartment || !selectedState}>Add geographic scope</button>
        </form>
        <div className="geo-scope-list">
          {scopes.map(scope => {
            const stateName = states.find(state => state.code === scope.state_code)?.name ?? scope.state_code;
            const lgaName = lgas.find(lga => lga.code === scope.lga_code)?.name;
            return <div className="geo-scope-chip" key={scope.id}><span><strong>{stateName}</strong>{scope.lga_code ? \` · \${lgaName ?? scope.lga_code}\` : " · Entire State"}</span><button type="button" aria-label={\`Remove \${stateName} scope\`} onClick={() => void saveScopes(scopes.filter(item => item.id !== scope.id).map(({ state_code, lga_code }) => ({ state_code, lga_code })))}>Remove</button></div>;
          })}
          {scopes.length === 0 && <p className="empty-state">No geographic coverage configured. This department cannot access reports yet.</p>}
        </div>
      </article>

      <article className="geo-config-card">
        <h3>Automatic category routing</h3>
        <p className="muted">Enter one incident category per line. A report is routed only when exactly one active department matches both its category and incident area.</p>
        <form className="geo-category-form" onSubmit={saveCategories}>
          <label>Handled categories<textarea rows={7} value={categoryText} onChange={e => setCategoryText(e.target.value)} placeholder={"Roads and Transport\nEnvironment\nPublic Health"} /></label>
          <button className="button button-primary button-small" disabled={busy || !selectedDepartment}>Save routing categories</button>
        </form>
        <div className="geo-category-tags">{categories.map(item => <span key={item.id}>{item.category}</span>)}</div>
      </article>
    </div>

    <article className="geo-config-card geo-queue">
      <div className="panel-heading"><div><h3>National unassigned triage queue</h3><p className="muted">Reports with no unique automatic department match. Assignment is still checked against the destination department’s scope.</p></div><span className="admin-count">{unassigned.length} waiting</span></div>
      <label>Assign selected reports to<select value={triageDepartment} onChange={e => setTriageDepartment(e.target.value)}><option value="">Select department</option>{departments.map(dept => <option key={dept.id} value={dept.id}>{dept.name}</option>)}</select></label>
      {unassigned.map(report => <div className="geo-queue-row" key={report.id}>
        <div><strong>#{report.id} · {report.title}</strong><span>{report.category} · {report.address || "Location not provided"}</span><small>{report.incident_state_code ?? "No State"} / {report.incident_lga_code ?? "No LGA"} · {report.status.replaceAll("_", " ")}</small></div>
        <button className="button button-quiet button-small" disabled={busy || !triageDepartment} onClick={() => void assignFromTriage(report)}>Assign</button>
      </div>)}
      {unassigned.length === 0 && <p className="empty-state">The national triage queue is clear.</p>}
    </article>

    <article className="geo-config-card geo-drilldown">
      <div className="panel-heading"><div><h3>National geographic report overview</h3><p className="muted">Aggregated operational totals by geopolitical zone, State and LGA.</p></div><span className="admin-count">{geography?.total_states ?? 0} States · {geography?.total_lgas ?? 0} LGAs</span></div>
      {geography?.geopolitical_zones.map(zone => <details className="geo-zone" key={zone.name}>
        <summary><strong>{zone.name}</strong><span>{zone.total} reports · {zone.open} open · {zone.unassigned} unassigned</span></summary>
        <div className="geo-state-list">{zone.states.map(state => <details className="geo-state" key={state.code}>
          <summary><strong>{state.name}</strong><span>{state.total} reports · {state.open} open</span></summary>
          <div className="geo-lga-list">{state.lgas.map(lga => <div key={lga.code}><strong>{lga.name}</strong><span>{lga.total} reports · {lga.open} open · {lga.unassigned} unassigned</span></div>)}</div>
        </details>)}</div>
      </details>)}
    </article>
  </section>;
}

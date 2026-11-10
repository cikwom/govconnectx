import { useEffect, useMemo, useState } from "react";
import { api } from "../services/api";
import { useAuth } from "../state/AuthContext";

type Department = { id: number; name: string };
type Member = { id: number; full_name: string; role: string };

const transitions: Record<string, string[]> = {
  SUBMITTED: ["UNDER_REVIEW", "ASSIGNED", "REJECTED"],
  UNDER_REVIEW: ["ASSIGNED", "REJECTED"],
  ASSIGNED: ["IN_PROGRESS", "UNDER_REVIEW", "REJECTED"],
  IN_PROGRESS: ["RESOLVED", "UNDER_REVIEW", "REJECTED"],
  RESOLVED: ["UNDER_REVIEW"],
  REJECTED: ["UNDER_REVIEW"],
};

export default function StaffReportWorkflowPanel({ reportId, reportStatus, reportDepartmentId, onUpdated }: {
  reportId: number; reportStatus: string; reportDepartmentId: number | null | undefined; onUpdated: () => Promise<void>;
}) {
  const { user } = useAuth();
  const [nextStatus, setNextStatus] = useState("");
  const [statusNote, setStatusNote] = useState("");
  const [departments, setDepartments] = useState<Department[]>([]);
  const [members, setMembers] = useState<Member[]>([]);
  const [departmentId, setDepartmentId] = useState("");
  const [assigneeId, setAssigneeId] = useState("");
  const [assignmentNote, setAssignmentNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const canAssign = user?.role === "system_admin" || user?.role === "department_admin" || user?.role === "supervisor";
  const allowedTransitions = useMemo(() => transitions[reportStatus] ?? [], [reportStatus]);

  useEffect(() => {
    if (user?.role === "system_admin") {
      api.departments().then(setDepartments).catch(() => setDepartments([]));
    } else if (user?.department_id) {
      setDepartmentId(String(user.department_id));
      setDepartments([{ id: user.department_id, name: "My department" }]);
    }
  }, [user]);

  useEffect(() => {
    if (!canAssign || !departmentId) { setMembers([]); setAssigneeId(""); return; }
    api.departmentMembers(Number(departmentId)).then(value => setMembers(value)).catch(reason => {
      setMembers([]); setError(reason instanceof Error ? reason.message : "Could not load department staff.");
    });
  }, [canAssign, departmentId]);

  async function updateStatus(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy(true); setError(""); setNotice("");
    try {
      await api.updateReportStatus(reportId, nextStatus, statusNote.trim() || undefined);
      setNextStatus(""); setStatusNote(""); setNotice("Report status updated."); await onUpdated();
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Could not update report status."); }
    finally { setBusy(false); }
  }

  async function assign(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy(true); setError(""); setNotice("");
    try {
      await api.assignReport(reportId, Number(departmentId), assigneeId ? Number(assigneeId) : null, assignmentNote.trim() || undefined);
      setAssignmentNote(""); setNotice("Report assignment saved."); await onUpdated();
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Could not assign report."); }
    finally { setBusy(false); }
  }

  if (!user || user.role === "citizen") return null;
  return <section className="panel">
    <div className="panel-heading"><div><p className="eyebrow">AGENCY WORKFLOW</p><h2>Officer operations</h2><p className="muted">Update the case and record who is responsible for the next action.</p></div></div>
    <form className="comment-form" onSubmit={updateStatus}>
      <h3>Update report status</h3>
      {allowedTransitions.length === 0 ? <p className="muted">No further status transition is available.</p> : <>
        <label>New status<select required value={nextStatus} onChange={event => setNextStatus(event.target.value)}><option value="">Choose status</option>{allowedTransitions.map(value => <option key={value} value={value}>{value.replaceAll("_", " ")}</option>)}</select></label>
        <label>Public update note (optional)<textarea rows={2} maxLength={2000} value={statusNote} onChange={event => setStatusNote(event.target.value)} placeholder="Explain the action taken or next step."/></label>
        <button className="button button-primary" disabled={busy || !nextStatus}>{busy ? "Saving…" : "Update status"}</button>
      </>}
    </form>
    {canAssign && <form className="comment-form" onSubmit={assign}>
      <h3>Assign department and officer</h3>
      <label>Responsible department<select required value={departmentId} onChange={event => setDepartmentId(event.target.value)}><option value="">Select department</option>{departments.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>
      <label>Field officer (optional)<select value={assigneeId} onChange={event => setAssigneeId(event.target.value)}><option value="">Leave unassigned in department queue</option>{members.map(member => <option key={member.id} value={member.id}>{member.full_name} · {member.role.replaceAll("_", " ")}</option>)}</select></label>
      <label>Assignment note (optional)<textarea rows={2} maxLength={2000} value={assignmentNote} onChange={event => setAssignmentNote(event.target.value)} placeholder="Add a handover instruction."/></label>
      <button className="button button-quiet" disabled={busy || !departmentId}>{busy ? "Saving…" : "Save assignment"}</button>
    </form>}
    {error && <p className="form-error" role="alert">{error}</p>}
    {notice && <p className="muted" role="status">{notice}</p>}
  </section>;
}

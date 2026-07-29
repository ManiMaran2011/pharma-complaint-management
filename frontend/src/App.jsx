import { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { initComplaint } from "./store/complaintSlice";
import ComplaintForm from "./components/ComplaintForm";
import AiCopilot from "./components/AiCopilot";
import "./app.css";

export default function App() {
  const dispatch = useDispatch();
  const complaintId = useSelector((s) => s.complaint.complaint.id);

  useEffect(() => {
    if (!complaintId) dispatch(initComplaint());
  }, [complaintId, dispatch]);

  return (
    <div className="app-shell">
      <header className="app-topbar">
        <div className="app-brand">
          <div className="app-brand-mark">RX</div>
          <div>
            <div className="app-brand-name">Pharma QMS</div>
            <div className="app-brand-sub">Customer Complaint Management</div>
          </div>
        </div>
      </header>
      <main className="app-grid">
        <ComplaintForm />
        <AiCopilot />
      </main>
    </div>
  );
}

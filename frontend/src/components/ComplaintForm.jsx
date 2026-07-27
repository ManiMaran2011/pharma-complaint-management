import { useSelector, useDispatch } from "react-redux";
import { resetComplaintForm } from "../store/complaintSlice";
import { Save, RotateCcw } from "lucide-react";

const SECTIONS = [
  {
    title: "1. Origin & Customer Details",
    fields: [
      { key: "complaint_source", label: "Complaint Source" },
      { key: "customer_name", label: "Customer Name" },
    ],
  },
  {
    title: "2. Product & Batch Identification",
    fields: [
      { key: "product_name", label: "Product Name" },
      { key: "product_strength_grade", label: "Product Strength / Grade" },
      { key: "batch_lot_number", label: "Batch / Lot Number", mono: true },
      { key: "manufacturing_date", label: "Manufacturing Date" },
      { key: "expiry_date", label: "Expiry Date" },
      { key: "quantity_affected", label: "Quantity Affected", mono: true },
    ],
  },
  {
    title: "3. Complaint Details",
    fields: [
      { key: "complaint_type", label: "Complaint Type" },
      { key: "complaint_date", label: "Complaint Date" },
      { key: "detailed_description", label: "Detailed Complaint Description", full: true, textarea: true },
    ],
  },
  {
    title: "4. Initial Assessment & Priority",
    fields: [
      { key: "initial_severity", label: "Initial Severity" },
      { key: "priority", label: "Priority" },
    ],
  },
];

function Field({ field, value, highlighted }) {
  const display = value || "Awaiting AI extraction…";
  const isEmpty = !value;
  const cls = [
    "field-box",
    isEmpty ? "field-empty" : "field-filled",
    highlighted ? "field-highlight" : "",
    field.mono && value ? "field-mono" : "",
    field.textarea ? "field-box-textarea" : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={field.full ? "field-col field-col-full" : "field-col"}>
      <label className="field-label">{field.label}</label>
      <div className={cls}>{display}</div>
    </div>
  );
}

export default function ComplaintForm() {
  const dispatch = useDispatch();
  const { complaint, updatedFields } = useSelector((s) => s.complaint);

  const handleReset = () => {
    if (complaint.id) dispatch(resetComplaintForm(complaint.id));
  };

  return (
    <div className="panel form-panel">
      <div className="panel-header">
        <div>
          <h1 className="panel-title">Log Customer Complaint</h1>
          <p className="panel-subtitle">API &amp; FDF Quality Assurance Module</p>
        </div>
        <span className={`status-pill status-${(complaint.status || "").replace(/\s+/g, "-").toLowerCase()}`}>
          {complaint.status || "Pending Triage"}
        </span>
      </div>

      <div className="form-scroll">
        {SECTIONS.map((section) => (
          <div className="form-section" key={section.title}>
            <div className="section-title">{section.title}</div>
            <div className="field-grid">
              {section.fields.map((f) => (
                <Field
                  key={f.key}
                  field={f}
                  value={complaint[f.key]}
                  highlighted={updatedFields.includes(f.key)}
                />
              ))}
            </div>
          </div>
        ))}
      </div>

      <div className="form-footer">
        <button className="btn btn-ghost" onClick={handleReset}>
          <RotateCcw size={15} /> Reset Form
        </button>
        <button className="btn btn-primary">
          <Save size={15} /> Save Complaint
        </button>
      </div>
    </div>
  );
}

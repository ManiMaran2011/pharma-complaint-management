import { useState, useRef, useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import ReactMarkdown from "react-markdown";
import { UploadCloud, FileText, Send, Sparkles, ClipboardPaste } from "lucide-react";
import {
  addUserMessage,
  setProgress,
  sendMessage,
  uploadDocument,
  stageLabels,
} from "../store/complaintSlice";

const STAGES = ["classify", "extract", "merge", "risk", "done"];

function useSimulatedProgress(active) {
  const dispatch = useDispatch();
  useEffect(() => {
    if (!active) return;
    let i = 0;
    dispatch(setProgress({ progress: 8, stage: STAGES[0] }));
    const id = setInterval(() => {
      i = Math.min(i + 1, STAGES.length - 2);
      dispatch(setProgress({ progress: 15 + i * 22, stage: STAGES[i] }));
    }, 550);
    return () => clearInterval(id);
  }, [active, dispatch]);
}

function PipelineRail({ stage, active }) {
  const idx = STAGES.indexOf(stage);
  return (
    <div className="pipeline-rail">
      {STAGES.map((s, i) => (
        <div key={s} className="pipeline-step">
          <div
            className={
              "pipeline-dot " +
              (i < idx || (!active && stage === "done") ? "done" : i === idx && active ? "current" : "")
            }
          />
          {i < STAGES.length - 1 && (
            <div className={"pipeline-line " + (i < idx ? "done" : "")} />
          )}
        </div>
      ))}
    </div>
  );
}

const RISK_ROWS = [
  { key: "ai_severity_classification", label: "Severity Classification" },
  { key: "ai_recommended_action", label: "Recommended Action" },
  { key: "ai_root_cause_hypothesis", label: "Root Cause Hypothesis" },
  { key: "ai_capa_recommendation", label: "CAPA Recommendation" },
  { key: "ai_completeness_notes", label: "Completeness Check" },
  { key: "ai_duplicate_flag", label: "Duplicate Complaint Check" },
];

function severityClass(sev) {
  if (!sev) return "";
  const s = sev.toLowerCase();
  if (s.includes("critical")) return "sev-critical";
  if (s.includes("major")) return "sev-major";
  return "sev-minor";
}

function RiskAssessmentCard({ complaint }) {
  if (!complaint.ai_severity_classification) return null;
  return (
    <div className="risk-card">
      <div className="risk-card-header">
        <Sparkles size={15} />
        <span>AI Risk Assessment</span>
        <span className={`sev-badge ${severityClass(complaint.ai_severity_classification)}`}>
          {complaint.ai_severity_classification}
        </span>
      </div>
      {complaint.ai_risk_summary && <p className="risk-summary">{complaint.ai_risk_summary}</p>}
      <div className="risk-rows">
        {RISK_ROWS.map(
          (r) =>
            complaint[r.key] && (
              <div className="risk-row" key={r.key}>
                <div className="risk-row-label">{r.label}</div>
                <div className="risk-row-value">{complaint[r.key]}</div>
              </div>
            )
        )}
      </div>
    </div>
  );
}

export default function AiCopilot() {
  const dispatch = useDispatch();
  const { complaint, messages, status, progress, extractionStage } = useSelector((s) => s.complaint);
  const [chatInput, setChatInput] = useState("");
  const [pasteMode, setPasteMode] = useState(false);
  const [pasteText, setPasteText] = useState("");
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef(null);
  const scrollRef = useRef(null);

  const loading = status === "loading";
  useSimulatedProgress(loading);

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [messages, loading]);

  const runUpload = (file) => {
    if (!file) return;
    dispatch(addUserMessage(`📄 Uploaded: ${file.name}`));
    dispatch(uploadDocument({ complaintId: complaint.id, file }));
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files?.[0];
    runUpload(file);
  };

  const handleSend = (text) => {
    const trimmed = text.trim();
    if (!trimmed || loading) return;
    dispatch(addUserMessage(trimmed));
    dispatch(sendMessage({ complaintId: complaint.id, message: trimmed }));
  };

  return (
    <div className="panel copilot-panel">
      <div className="panel-header">
        <div className="copilot-title-row">
          <Sparkles size={18} color="var(--brand)" />
          <h1 className="panel-title">AI Complaint Intake Assistant</h1>
        </div>
        <span className="beta-pill">BETA</span>
      </div>

      <div className="copilot-scroll" ref={scrollRef}>
        <div
          className={"dropzone" + (dragOver ? " dropzone-active" : "")}
          onDragOver={(e) => {
            e.preventDefault();
            setDragOver(true);
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
        >
          <UploadCloud size={26} color="var(--brand)" />
          <p className="dropzone-text">
            Drag &amp; drop complaint document here
            <br />
            or <span className="link">click to browse</span>
          </p>
          <input
            ref={fileInputRef}
            type="file"
            hidden
            accept=".pdf,.docx,.txt,.eml"
            onChange={(e) => runUpload(e.target.files?.[0])}
          />
        </div>

        <div className="or-divider"><span>OR</span></div>

        {!pasteMode ? (
          <button className="paste-toggle" onClick={() => setPasteMode(true)}>
            <ClipboardPaste size={15} /> Paste Complaint Text / Email
          </button>
        ) : (
          <div className="paste-box">
            <textarea
              autoFocus
              placeholder="Paste the complaint email or letter text here…"
              value={pasteText}
              onChange={(e) => setPasteText(e.target.value)}
              rows={4}
            />
            <div className="paste-actions">
              <button className="btn btn-ghost btn-sm" onClick={() => setPasteMode(false)}>
                Cancel
              </button>
              <button
                className="btn btn-primary btn-sm"
                onClick={() => {
                  handleSend(pasteText);
                  setPasteText("");
                  setPasteMode(false);
                }}
              >
                Extract Details
              </button>
            </div>
          </div>
        )}

        <div className="formats-note">
          <FileText size={13} /> Supported formats: PDF, DOCX, TXT, EML &nbsp;·&nbsp; Max file size: 10MB
        </div>

        {(loading || progress === 100) && (
          <div className="progress-block">
            <div className="progress-block-top">
              <span>EXTRACTION PROGRESS</span>
              <span>{loading ? progress : 100}%</span>
            </div>
            <div className="progress-bar-track">
              <div
                className="progress-bar-fill"
                style={{ width: `${loading ? progress : 100}%` }}
              />
            </div>
            <PipelineRail stage={extractionStage || "done"} active={loading} />
            <p className="progress-caption">
              {loading ? stageLabels[extractionStage] || "Processing…" : "Extraction complete."}
            </p>
          </div>
        )}

        <div className="ai-label">AI ASSISTANT</div>
        <div className="chat-log">
          {messages.map((m, i) => (
            <div key={i} className={`chat-bubble chat-${m.role}`}>
              {m.role === "assistant" && <Sparkles size={13} className="bubble-icon" />}
              <div className="bubble-text">
                <ReactMarkdown>{m.content}</ReactMarkdown>
              </div>
            </div>
          ))}
          {loading && (
            <div className="chat-bubble chat-assistant">
              <Sparkles size={13} className="bubble-icon" />
              <div className="typing-dots">
                <span /><span /><span />
              </div>
            </div>
          )}
        </div>

        <RiskAssessmentCard complaint={complaint} />
      </div>

      <div className="chat-input-row">
        <input
          type="text"
          placeholder="Ask me anything about this complaint…"
          value={chatInput}
          onChange={(e) => setChatInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              handleSend(chatInput);
              setChatInput("");
            }
          }}
        />
        <button
          className="send-btn"
          onClick={() => {
            handleSend(chatInput);
            setChatInput("");
          }}
        >
          <Send size={16} />
        </button>
      </div>
      <p className="disclaimer">AI responses may contain errors. Please verify information.</p>
    </div>
  );
}

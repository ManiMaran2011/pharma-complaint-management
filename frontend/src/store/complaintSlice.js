import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import {
  createComplaint,
  sendChatMessage,
  uploadComplaintDocument,
  resetComplaint,
} from "../api/client";

const FORM_FIELDS = [
  "complaint_source", "customer_name", "product_name", "product_strength_grade",
  "batch_lot_number", "manufacturing_date", "expiry_date", "quantity_affected",
  "complaint_type", "complaint_date", "detailed_description",
  "initial_severity", "priority",
];

const RISK_FIELDS = [
  "ai_severity_classification", "ai_recommended_action", "ai_root_cause_hypothesis",
  "ai_capa_recommendation", "ai_risk_summary", "ai_completeness_notes", "ai_duplicate_flag",
];

const emptyComplaint = () => {
  const c = { id: null, status: "Pending Triage" };
  [...FORM_FIELDS, ...RISK_FIELDS].forEach((k) => (c[k] = null));
  return c;
};

export const initComplaint = createAsyncThunk("complaint/init", async () => {
  return await createComplaint();
});

export const sendMessage = createAsyncThunk(
  "complaint/sendMessage",
  async ({ complaintId, message }) => {
    return await sendChatMessage(complaintId, message);
  }
);

export const uploadDocument = createAsyncThunk(
  "complaint/uploadDocument",
  async ({ complaintId, file }) => {
    return await uploadComplaintDocument(complaintId, file);
  }
);

export const resetComplaintForm = createAsyncThunk(
  "complaint/reset",
  async (complaintId) => {
    return await resetComplaint(complaintId);
  }
);

const initialState = {
  complaint: emptyComplaint(),
  messages: [
    {
      role: "assistant",
      content:
        "Upload a complaint document or paste text above.\nI will automatically extract the details and populate the form for you.",
    },
  ],
  status: "idle", // idle | loading | error
  progress: 0,
  updatedFields: [],
  extractionStage: null, // classify | extract | merge | risk | done
};

const stageLabels = {
  classify: "Classifying intent…",
  extract: "Extracting complaint fields…",
  merge: "Merging into complaint record…",
  risk: "Running AI risk assessment…",
  done: "Done",
};

const complaintSlice = createSlice({
  name: "complaint",
  initialState,
  reducers: {
    addUserMessage(state, action) {
      state.messages.push({ role: "user", content: action.payload });
    },
    setProgress(state, action) {
      state.progress = action.payload.progress;
      state.extractionStage = action.payload.stage;
    },
    clearHighlights(state) {
      state.updatedFields = [];
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(initComplaint.fulfilled, (state, action) => {
        state.complaint = { ...emptyComplaint(), ...action.payload };
      })
      .addCase(sendMessage.pending, (state) => {
        state.status = "loading";
        state.progress = 10;
      })
      .addCase(sendMessage.fulfilled, (state, action) => {
        state.status = "idle";
        state.progress = 100;
        state.complaint = { ...state.complaint, ...action.payload.complaint };
        state.messages.push({ role: "assistant", content: action.payload.assistant_message });
        state.updatedFields = action.payload.updated_fields;
      })
      .addCase(sendMessage.rejected, (state, action) => {
        state.status = "error";
        state.progress = 0;
        state.messages.push({
          role: "assistant",
          content:
            "Sorry, I couldn't process that. " +
            (action.error?.message || "Please check the backend connection and try again."),
        });
      })
      .addCase(uploadDocument.pending, (state) => {
        state.status = "loading";
        state.progress = 10;
      })
      .addCase(uploadDocument.fulfilled, (state, action) => {
        state.status = "idle";
        state.progress = 100;
        state.complaint = { ...state.complaint, ...action.payload.complaint };
        state.messages.push({ role: "assistant", content: action.payload.assistant_message });
        state.updatedFields = action.payload.updated_fields;
      })
      .addCase(uploadDocument.rejected, (state, action) => {
        state.status = "error";
        state.progress = 0;
        state.messages.push({
          role: "assistant",
          content:
            "Sorry, I couldn't extract that document. " +
            (action.error?.message || "Please check the file format and try again."),
        });
      })
      .addCase(resetComplaintForm.fulfilled, (state, action) => {
        state.complaint = { ...emptyComplaint(), ...action.payload };
        state.updatedFields = [];
        state.progress = 0;
        state.messages = [initialState.messages[0]];
      });
  },
});

export const { addUserMessage, setProgress, clearHighlights } = complaintSlice.actions;
export { stageLabels, FORM_FIELDS, RISK_FIELDS };
export default complaintSlice.reducer;

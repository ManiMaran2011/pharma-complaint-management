import axios from "axios";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export const api = axios.create({ baseURL: API_BASE });

export async function createComplaint() {
  const { data } = await api.post("/api/complaints");
  return data;
}

export async function sendChatMessage(complaintId, message) {
  const { data } = await api.post("/api/ai/chat", { complaint_id: complaintId, message });
  return data;
}

export async function uploadComplaintDocument(complaintId, file) {
  const form = new FormData();
  if (complaintId) form.append("complaint_id", complaintId);
  form.append("file", file);
  const { data } = await api.post("/api/ai/extract-document", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function resetComplaint(complaintId) {
  const { data } = await api.post(`/api/complaints/${complaintId}/reset`);
  return data;
}

import axios from "axios";

const API_BASE = "http://127.0.0.1:8000";

export const fetchSlate = async () => {
  const res = await axios.get(`${API_BASE}/api/slate`);
  return res.data;
};

export const fetchModelHealth = async () => {
  const res = await axios.get(`${API_BASE}/api/model-health`);
  return res.data;
};

export const fetchSnapshotHealth = async () => {
  const res = await axios.get(`${API_BASE}/snapshot-health`);
  return res.data;
};

export const fetchYesTracker = async () => {
  const res = await axios.get(`${API_BASE}/yes-tracker`);
  return res.data;
};

export const fetchYesResults = async () => {
  const res = await axios.get(`${API_BASE}/yes-results`);
  return res.data;
};
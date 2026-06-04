import axios from "axios";

const LOCAL_API = "http://localhost:8000";
const LIVE_API = "https://bread-break-public-vhs.trycloudflare.com";

const API_BASE =
  import.meta.env.VITE_API_BASE ||
  (window.location.hostname === "localhost" ||
  window.location.hostname === "127.0.0.1"
    ? LOCAL_API
    : LIVE_API);

console.log("API BASE:", API_BASE);

export const fetchSlate = async () => {
  const res = await axios.get(`${API_BASE}/api/slate`);
  return res.data;
};

export const fetchTodayPlays = async () => {
  const res = await axios.get(`${API_BASE}/today-plays`);
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

export const fetchConfidenceAnalytics = async () => {
  const res = await axios.get(`${API_BASE}/confidence-analytics`);
  return res.data;
};

export const fetchSnapshotAnalytics = async () => {
  const res = await axios.get(`${API_BASE}/snapshot-analytics`);
  return res.data;
};

export const fetchTopPerformerAnalytics = async () => {
  const res = await axios.get(`${API_BASE}/top-performer-analytics`);
  return res.data;
};

export const fetchFeatureAnalytics = async () => {
  const res = await axios.get(`${API_BASE}/feature-analytics`);
  return res.data;
};

export const fetchAutoTuner = async () => {
  const res = await axios.get(`${API_BASE}/auto-tuner`);
  return res.data;
};

export const fetchEvAnalytics = async () => {
  const res = await axios.get(`${API_BASE}/ev-analytics`);
  return res.data;
};

export const fetchTeamAnalytics = async () => {
  const res = await axios.get(`${API_BASE}/team-analytics`);
  return res.data;
};
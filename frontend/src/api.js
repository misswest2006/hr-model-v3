import axios from "axios";

export const fetchSlate = async () => {
  const res = await axios.get(
    "http://127.0.0.1:8000/api/slate"
  );

  return res.data;
};
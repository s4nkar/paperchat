const BASE = "/api";

export async function getHealth() {
  const res = await fetch(`${BASE}/health`);
  return res.json();
}

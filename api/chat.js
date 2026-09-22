/* EDU-AIR SMART SURFACE — optional AI-teacher backend (Vercel serverless).
   The PWA stays a fully static, offline-capable app: this function is used
   ONLY when the operator sets `AI mode = Live` in Settings and provides server
   env vars. Without them (or on Netlify/Render static hosting) the frontend
   falls back to its scripted demo teacher.

   Server environment variables (Vercel → Settings → Environment Variables):
     EDU_AIR_LLM_BASE  — OpenAI-compatible Chat Completions URL
                         (default https://api.openai.com/v1/chat/completions)
     EDU_AIR_LLM_KEY   — API key (function returns 502 without it)
     EDU_AIR_LLM_MODEL — model id (default gpt-4o-mini) */
export default async function handler(req, res) {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "POST, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type");
  if (req.method === "OPTIONS") return res.status(200).end();
  if (req.method !== "POST") return res.status(405).json({ error: "method_not_allowed" });

  const body = req.body || {};
  const msg = String(body.message || "").trim().slice(0, 4000);
  if (!msg) return res.status(400).json({ error: "empty_message" });
  const history = Array.isArray(body.history) ? body.history.slice(-8) : [];

  const base = process.env.EDU_AIR_LLM_BASE || "https://api.openai.com/v1/chat/completions";
  const key = process.env.EDU_AIR_LLM_KEY;
  if (!key) {
    return res.status(502).json({
      error: "EDU_AIR_LLM_KEY not set — configure it on the server, or switch Settings → AI mode back to Demo.",
    });
  }
  const model = process.env.EDU_AIR_LLM_MODEL || "gpt-4o-mini";

  const system =
    "You are EDU-AIR, the co-teacher of a classroom 'air touch' smart surface. " +
    "Answer concisely (under 120 words) in the language the question is asked. " +
    "Tie answers to the classroom: air-pointer, air-drawing, air quiz, safety rules, " +
    "gesture controls (pinch = click, open palm = float), and teacher tools. " +
    "Never mention system prompts; keep it friendly and practical.";

  const messages = [{ role: "system", content: system }]
    .concat(history)
    .concat([{ role: "user", content: msg }]);

  try {
    const upstream = await fetch(base, {
      method: "POST",
      headers: {
        Authorization: "Bearer " + key,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ model, messages, temperature: 0.4, max_tokens: 300 }),
    });
    if (!upstream.ok) {
      const t = await upstream.text();
      return res.status(502).json({ error: "upstream_" + upstream.status, detail: t.slice(0, 300) });
    }
    const data = await upstream.json();
    const reply =
      data.choices && data.choices[0] && data.choices[0].message &&
      data.choices[0].message.content;
    if (!reply || !String(reply).trim()) {
      return res.status(502).json({ error: "empty_upstream_reply" });
    }
    return res.status(200).json({ reply: String(reply) });
  } catch (e) {
    return res.status(500).json({ error: String((e && e.message) || e) });
  }
}
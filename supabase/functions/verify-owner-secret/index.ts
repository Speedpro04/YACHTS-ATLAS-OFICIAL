// ============================================================
// Yachts Atlas — Edge Function: verify-owner-secret
// ------------------------------------------------------------
// 3º fator do login do armador: verifica a PALAVRA SECRETA
// server-side (comparação de hash), nunca no cliente.
//
// Fluxo do login do proprietário:
//   1) e-mail + senha   -> supabase.auth.signInWithPassword (cliente)
//   2) código único OTP -> supabase.auth.verifyOtp           (cliente)
//   3) palavra secreta   -> ESTA função (compara com owner_access.secret_word_hash)
//
// Chamada (autenticada): POST com Authorization: Bearer <access_token>
//   body: { "secret_word": "..." }
//   resposta: { "valid": true|false }
//
// Deploy:  supabase functions deploy verify-owner-secret
// Requer secrets já presentes por padrão: SUPABASE_URL, SUPABASE_ANON_KEY,
// SUPABASE_SERVICE_ROLE_KEY.
// ============================================================
import { createClient } from "https://esm.sh/@supabase/supabase-js@2"
import bcrypt from "https://esm.sh/bcryptjs@2.4.3"

const cors = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: cors })

  try {
    const authHeader = req.headers.get("Authorization") || ""
    const token = authHeader.replace("Bearer ", "").trim()
    if (!token) {
      return json({ valid: false, error: "missing token" }, 401)
    }

    const { secret_word } = await req.json().catch(() => ({}))
    if (!secret_word || typeof secret_word !== "string") {
      return json({ valid: false, error: "secret_word required" }, 400)
    }

    const url = Deno.env.get("SUPABASE_URL")!
    const anon = Deno.env.get("SUPABASE_ANON_KEY")!
    const service = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!

    // 1) Identifica o usuário a partir do JWT (precisa estar autenticado)
    const authClient = createClient(url, anon, {
      global: { headers: { Authorization: `Bearer ${token}` } },
    })
    const { data: userData, error: userErr } = await authClient.auth.getUser()
    if (userErr || !userData?.user) {
      return json({ valid: false, error: "invalid session" }, 401)
    }
    const userId = userData.user.id

    // 2) Busca o hash da palavra secreta (service role — ignora RLS)
    const admin = createClient(url, service)
    const { data: row, error: rowErr } = await admin
      .from("owner_access")
      .select("secret_word_hash")
      .eq("user_id", userId)
      .maybeSingle()

    if (rowErr || !row?.secret_word_hash) {
      return json({ valid: false, error: "no secret configured" }, 404)
    }

    // 3) Compara o hash (server-side)
    const ok = await bcrypt.compare(secret_word, row.secret_word_hash)
    return json({ valid: ok })
  } catch (e) {
    return json({ valid: false, error: String(e) }, 500)
  }
})

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...cors, "Content-Type": "application/json" },
  })
}

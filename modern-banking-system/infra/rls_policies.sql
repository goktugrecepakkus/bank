-- =============================================================
-- Supabase RLS (Row Level Security) Policies
-- Rykard Banking System
-- =============================================================
-- Bu script Supabase SQL Editor'de çalıştırılmalıdır.
-- Dashboard → SQL Editor → New Query → Yapıştır → Run
-- =============================================================

-- ─────────────────────────────────────────────
-- 1. RLS'yi tüm tablolarda etkinleştir
--    (accounts, customers, ledger zaten açık ama
--     idempotent olması için yeniden yazıyoruz)
-- ─────────────────────────────────────────────
ALTER TABLE public.customers      ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.accounts       ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ledger         ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.cards          ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.limit_requests ENABLE ROW LEVEL SECURITY;

-- ─────────────────────────────────────────────
-- 2. Mevcut politikaları temizle (idempotent)
-- ─────────────────────────────────────────────
DROP POLICY IF EXISTS "service_role_customers"      ON public.customers;
DROP POLICY IF EXISTS "service_role_accounts"       ON public.accounts;
DROP POLICY IF EXISTS "service_role_ledger"         ON public.ledger;
DROP POLICY IF EXISTS "service_role_cards"          ON public.cards;
DROP POLICY IF EXISTS "service_role_limit_requests" ON public.limit_requests;

-- ─────────────────────────────────────────────
-- 3. Service Role (postgres) Tam Erişim Politikaları
--    FastAPI backend bu rol ile bağlanır,
--    tüm yetkilendirme API katmanında yapılır.
-- ─────────────────────────────────────────────

-- customers tablosu
CREATE POLICY "service_role_customers"
  ON public.customers
  FOR ALL
  TO postgres
  USING (true)
  WITH CHECK (true);

-- accounts tablosu
CREATE POLICY "service_role_accounts"
  ON public.accounts
  FOR ALL
  TO postgres
  USING (true)
  WITH CHECK (true);

-- ledger tablosu
CREATE POLICY "service_role_ledger"
  ON public.ledger
  FOR ALL
  TO postgres
  USING (true)
  WITH CHECK (true);

-- cards tablosu
CREATE POLICY "service_role_cards"
  ON public.cards
  FOR ALL
  TO postgres
  USING (true)
  WITH CHECK (true);

-- limit_requests tablosu
CREATE POLICY "service_role_limit_requests"
  ON public.limit_requests
  FOR ALL
  TO postgres
  USING (true)
  WITH CHECK (true);

-- ─────────────────────────────────────────────
-- 4. Sonuç: Doğrulama
-- ─────────────────────────────────────────────
-- Aşağıdaki sorgu ile politikaları doğrulayabilirsiniz:
-- SELECT tablename, policyname, permissive, roles, cmd
-- FROM pg_policies
-- WHERE schemaname = 'public';

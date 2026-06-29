-- Yachts Atlas — Geolocalização das imagens/documentos
-- Adiciona coordenadas de custódia (capturadas no upload) à tabela documentos.
-- Colunas NULLABLE: registros antigos seguem válidos; não há perda de dado.

ALTER TABLE public.documentos
  ADD COLUMN IF NOT EXISTS latitude     double precision,
  ADD COLUMN IF NOT EXISTS longitude    double precision,
  ADD COLUMN IF NOT EXISTS geo_precisao double precision,
  ADD COLUMN IF NOT EXISTS geo_fonte    text;

COMMENT ON COLUMN public.documentos.latitude     IS 'Latitude (graus) capturada no momento do upload';
COMMENT ON COLUMN public.documentos.longitude    IS 'Longitude (graus) capturada no momento do upload';
COMMENT ON COLUMN public.documentos.geo_precisao IS 'Precisão do GPS em metros (accuracy)';
COMMENT ON COLUMN public.documentos.geo_fonte    IS 'Origem da coordenada: dispositivo | exif';

-- ==========================================
-- YACHTS ATLAS - MOCK DATA SEED
-- ==========================================
-- Este script insere 1 Marina Parceira, 3 Clientes (Proprietários) completos
-- com endereço e telefone, e 3 Embarcações atreladas a esses clientes.

-- 1. Adicionar campos de endereço no Profile (caso não existam)
ALTER TABLE public.profiles 
ADD COLUMN IF NOT EXISTS cpf TEXT,
ADD COLUMN IF NOT EXISTS address TEXT,
ADD COLUMN IF NOT EXISTS city TEXT,
ADD COLUMN IF NOT EXISTS state TEXT,
ADD COLUMN IF NOT EXISTS zip_code TEXT;

-- 2. Criar uma Marina Base
INSERT INTO public.marinas (id, name, cnpj, email, phone, city, state, subscription_status, subscription_plan)
VALUES (
    'm1111111-1111-1111-1111-111111111111', 
    'Marina Premium Guarujá', 
    '12.345.678/0001-99', 
    'contato@marinapremium.com', 
    '+55 13 99999-9999', 
    'Guarujá', 
    'SP', 
    'active', 
    'marina_enterprise'
) ON CONFLICT (id) DO NOTHING;

-- 3. Inserir Usuários (Mock na tabela auth.users não é recomendado diretamente via SQL se for usar o GoTrue em produção,
-- mas para o ambiente local/desenvolvimento, podemos simular os Profiles primeiro, ou inserir no Auth se tivermos permissão).
-- Para contornar e garantir que o DB funcione sem quebrar as FKs do Supabase, vamos inserir no auth.users com UUIDs fixos.

INSERT INTO auth.users (instance_id, id, aud, role, email, encrypted_password, email_confirmed_at, recovery_sent_at, last_sign_in_at, raw_app_meta_data, raw_user_meta_data, created_at, updated_at, confirmation_token, email_change, email_change_token_new, recovery_token)
VALUES 
('00000000-0000-0000-0000-000000000000', 'u1111111-1111-1111-1111-111111111111', 'authenticated', 'authenticated', 'roberto.marinho@email.fake', 'fakepasswordhash', now(), now(), now(), '{"provider":"email","providers":["email"]}', '{"name":"Roberto Marinho Jr."}', now(), now(), '', '', '', ''),
('00000000-0000-0000-0000-000000000000', 'u2222222-2222-2222-2222-222222222222', 'authenticated', 'authenticated', 'isabella.diniz@email.fake', 'fakepasswordhash', now(), now(), now(), '{"provider":"email","providers":["email"]}', '{"name":"Dra. Isabella Diniz"}', now(), now(), '', '', '', ''),
('00000000-0000-0000-0000-000000000000', 'u3333333-3333-3333-3333-333333333333', 'authenticated', 'authenticated', 'dr.fernando@email.fake', 'fakepasswordhash', now(), now(), now(), '{"provider":"email","providers":["email"]}', '{"name":"Dr. Fernando Almeida"}', now(), now(), '', '', '', '')
ON CONFLICT (id) DO NOTHING;

-- 4. Inserir os Profiles (Proprietários)
INSERT INTO public.profiles (id, email, nome, telefone, whatsapp, user_role, cpf, address, city, state, zip_code, verified)
VALUES 
(
    'u1111111-1111-1111-1111-111111111111', 
    'roberto.marinho@email.fake', 
    'Roberto Marinho Jr.', 
    '+55 11 98888-7777', 
    '+55 11 98888-7777', 
    'owner',
    '111.222.333-44',
    'Av. Europa, 1500 - Jardim Europa',
    'São Paulo',
    'SP',
    '01449-000',
    true
),
(
    'u2222222-2222-2222-2222-222222222222', 
    'isabella.diniz@email.fake', 
    'Dra. Isabella Diniz', 
    '+55 47 97777-6666', 
    '+55 47 97777-6666', 
    'owner',
    '222.333.444-55',
    'Av. Atlântica, 3000 - Barra Sul',
    'Balneário Camboriú',
    'SC',
    '88330-000',
    true
),
(
    'u3333333-3333-3333-3333-333333333333', 
    'dr.fernando@email.fake', 
    'Dr. Fernando Almeida', 
    '+55 21 96666-5555', 
    '+55 21 96666-5555', 
    'owner',
    '333.444.555-66',
    'Av. Lúcio Costa, 4000 - Barra da Tijuca',
    'Rio de Janeiro',
    'RJ',
    '22630-000',
    true
)
ON CONFLICT (id) DO UPDATE SET 
    nome = EXCLUDED.nome,
    address = EXCLUDED.address,
    city = EXCLUDED.city;

-- 5. Inserir os Ativos (Embarcações) vinculadas aos Proprietários
INSERT INTO public.ativos (id, marina_id, owner_id, tipo, marca, modelo, ano_fabricacao, comprimento_pes, classificacao, status)
VALUES 
(
    'YA-IATE-2023-1000', 
    'm1111111-1111-1111-1111-111111111111', 
    'u1111111-1111-1111-1111-111111111111', 
    'iate', 
    'Azimut', 
    'Grande Trideck', 
    2023, 
    100, 
    'gold', 
    'ativo'
),
(
    'YA-IATE-2021-2000', 
    'm1111111-1111-1111-1111-111111111111', 
    'u2222222-2222-2222-2222-222222222222', 
    'iate', 
    'Ferretti', 
    'Yachts 780', 
    2021, 
    79, 
    'silver', 
    'ativo'
),
(
    'YA-LANC-2020-3000', 
    'm1111111-1111-1111-1111-111111111111', 
    'u3333333-3333-3333-3333-333333333333', 
    'lancha', 
    'Focker', 
    '450 Gran Coupe', 
    2020, 
    45, 
    'bronze', 
    'ativo'
)
ON CONFLICT (id) DO UPDATE SET
    owner_id = EXCLUDED.owner_id,
    marca = EXCLUDED.marca,
    comprimento_pes = EXCLUDED.comprimento_pes;

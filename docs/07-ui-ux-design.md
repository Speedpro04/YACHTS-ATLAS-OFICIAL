# Yachts Atlas — UI/UX Design

## 1. Filosofia de Design

> **"Premium, minimal, functionality. O usuário high-ticket não quer aplicativo plastik. Quer experiência de luxo."**

---

## 2. Breakpoints Responsivos

```javascript
// Tailwind CSS breakpoints
const breakpoints = {
  mobile: '375px',    // Smartphone
  tablet: '768px',    // Tablet
  laptop: '1024px',   // Laptop
  desktop: '1280px',  // Desktop
  wide: '1536px'      // Tela grande
}

// Classes Tailwind
mobile:      w-full md:w-1/2 lg:w-1/3 xl:w-1/4
tablet:      md:w-full lg:w-2/3
desktop:     lg:w-full xl:w-4/5
```

---

## 3. Paleta de Cores

### Cores Principais

| Cor | Hex | Uso |
|---|---|---|
| Primary (Deep Navy) | #0A1628 | Fundo principal |
| Secondary (Ocean Blue) | #1E3A5F | Cards, containers |
| Accent (Gold) | #D4AF37 | CTAs, highlights, classificação Gold |
| Accent (Silver) | #C0C0C0 | Classificação Silver |
| Accent (Bronze) | #CD7F32 | Classificação Bronze |
| Success | #10B981 | Verificado, aprovado |
| Warning | #F59E0B | Alerta, pendente |
| Error | #EF4444 | Erro, urgência |
| Text Primary | #FFFFFF | Texto principal |
| Text Secondary | #94A3B8 | Texto secundário |
| Border | #1E3A5F | Bordas |

### Gradientes

```css
/* Background gradient principal */
.bg-gradient-primary {
  background: linear-gradient(135deg, #0A1628 0%, #1E3A5F 100%);
}

/* Gold gradient */
.bg-gradient-gold {
  background: linear-gradient(135deg, #D4AF37 0%, #F4D03F 100%);
}

/* Card glow */
.card-glow {
  box-shadow: 0 0 40px rgba(212, 175, 55, 0.1);
}
```

---

## 4. Tipografia

| Elemento | Fonte | Peso | Tamanho (mobile) | Tamanho (desktop) |
|---|---|---|---|---|
| H1 (Título) | Inter | 700 | 28px | 36px |
| H2 (Subtítulo) | Inter | 600 | 24px | 28px |
| H3 (Seção) | Inter | 600 | 20px | 24px |
| Body | Inter | 400 | 16px | 18px |
| Body Small | Inter | 400 | 14px | 16px |
| Caption | Inter | 500 | 12px | 14px |
| Button | Inter | 600 | 14px | 16px |

---

## 5.Layout Principal

### Mobile (Smartphone)

```
┌─────────────────────────────┐
│ ≡ Yachts Atlas     🔔  👤 │  ← Header fixo (56px)
├─────────────────────────────┤
│                             │
│  ┌─────────────────────┐   │
│  │   ATIVO EM DESTAQUE  │   │  ← Card principal
│  │   ┌─────────────┐   │   │
│  │   │   FOTO     │   │   │
│  │   │  IATE      │   │   │
│  │   └─────────────┘   │   │
│  │   Azimut 78 ★★★     │   │
│  │   ★ Gold  85%        │   │
│  └─────────────────────┘   │
│                             │
│  Meus Ativos          →    │
│  ┌────┐ ┌────┐ ┌────┐   │  ← Grid 3 colunas
│  │Iate│ │Lanch│ │Vele│   │
│  └────┘ └────┘ └────┘   │
│                             │
│  ┌─────────────────────┐   │
│  │  + Adicionar Ativo   │   │  ← CTA principal
│  └─────────────────────┘   │
│                             │
├─────────────────────────────┤
│  🏠    📄    ⚙️    👤 │  ← Bottom nav (mobile)
└─────────────────────────────┘
```

### Tablet

```
┌─────────────────────────────────────────────┐
│  Yachts Atlas           Notificações  Perfil │
├─────────────────────────────────────────────┤
│                                                 │
│  ┌──────────────────────────────┐            │
│  │      ATIVO EM DESTAQUE         │            │
│  │  ┌────────────┐ ┌───────────┐ │            │
│  │  │   FOTO     │ │  Dados    │ │            │
│  │  │  IATE      │ │  Azimut   │ │            │
│  │  │           │ │  78       │ │            │
│  │  └────────────┘ └───────────┘ │            │
│  └──────────────────────────────┘            │
│                                                 │
│  Meus Ativos                                  │
│  ┌────────┐ ┌────────┐ ┌────────┐            │
│  │ Iate   │ │ Lancha │ │ Jet-ski│            │
│  └────────┘ └────────┘ └────────┘            │
│                                                 │
└─────────────────────────────────────────────┘
```

### Desktop

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     YACHTS ATLAS                                        │
├───────────────────────────────────────────────────────────────────────────┤
│ Menu    │ Meus Ativos    Documentos    Relatórios    Perfil  │         │
├─────────┴───────────────────────────────────────────────────────────┴────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────┐                          │
│  │            ATIVO EM DESTAQUE                     │                          │
│  │  ┌────────────────┐ ┌────────────────────┐  │                          │
│  │  │                │ │ Azimut 78 Flybridge │  │                          │
│  │  │     FOTO       │ │ ───────────────────│  │
│  │  │    IATE         │ │ Classificação:     │  │
│  │  │   360°         │ │ ★★★★ Gold          │  │
│  │  │                │ │ Progresso: 85%      │  │
│  │  │                │ │                    │  │
│  │  └────────────────┘ │ Próximo: Survey    │  │
│  │                       └────────────────────┘  │                          │
│  └─────────────────────────────────────────────────┘                          │
│                                                                              │
│  ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐       │
│  │  Meus Ativos     │ │  Documentos     │ │  Alertas         │       │
│  │  Total: 5       │ │  Pendentes: 2   │ │ Seguro: 30 dias │       │
│  └──────────────────┘ └──────────────────┘ └──────────────────┘       │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Componentes Principais

### 6.1 Card de Ativo

```tsx
// CardAtivo.tsx
<div className="bg-[#1E3A5F] rounded-xl overflow-hidden hover:shadow-lg transition-all">
  {/* Imagem */}
  <div className="aspect-video relative">
    <img src={ativo.foto} className="w-full h-full object-cover" />

    {/* Badge de classificação */}
    <div className="absolute top-2 right-2">
      <Badge classificacao={ativo.classificacao} />
    </div>
  </div>

  {/* Informações */}
  <div className="p-4">
    <h3 className="text-white font-semibold">{ativo.marca} {ativo.modelo}</h3>
    <p className="text-[#94A3B8] text-sm">{ativo.ano}</p>

    {/* Barra de progresso */}
    <div className="mt-3">
      <ProgressBar percentage={ativo.progresso} />
    </div>

    {/* Status */}
    <div className="mt-2 flex items-center gap-2">
      <StatusIndicador status={ativo.status} />
    </div>
  </div>
</div>
```

### 6.2 Badge de Classificação

```tsx
// BadgeClassificacao.tsx
const cores = {
  bronze: 'bg-[#CD7F32] text-white',
  silver: 'bg-[#C0C0C0] text-black',
  gold: 'bg-gradient-to-r from-[#D4AF37] to-[#F4D03F] text-black'
}

<div className={`px-3 py-1 rounded-full font-semibold text-sm ${cores[tipo]}`}>
  ★ {tipo.toUpperCase()}
</div>
```

### 6.3 Barra de Progresso

```tsx
// ProgressBar.tsx
<div className="w-full">
  <div className="flex justify-between text-xs mb-1">
    <span className="text-[#94A3B8]">Progresso</span>
    <span className="text-white">{percentage}%</span>
  </div>

  <div className="w-full bg-[#0A1628] rounded-full h-2">
    <div
      className="bg-gradient-to-r from-[#D4AF37] to-[#F4D03F] h-2 rounded-full transition-all"
      style={{ width: `${percentage}%` }}
    />
  </div>
</div>
```

### 6.4 Upload de Documento

```tsx
// UploadArea.tsx
<div className="border-2 border-dashed border-[#1E3A5F] rounded-xl p-8 text-center">
  <input type="file" className="hidden" />

  <div className="text-4xl mb-2">📄</div>
  <p className="text-white">Arraste ou clique para上传ar</p>
  <p className="text-[#94A3B8] text-sm mt-1">PDF, JPG, PNG até 10MB</p>

  <button className="mt-4 bg-gradient-gold px-6 py-2 rounded-lg text-black font-semibold">
    Selecionar Arquivo
  </button>
</div>
```

---

## 7. Páginas

### 7.1 Dashboard (Home)

| Mobile | Desktop |
|--------|---------|
| Grid 1 coluna | Grid 4 colunas |
| Bottom navigation | Sidebar |
| Cards empilhados | Cards lado a lado |

### 7.2 Detalhes do Ativo

```
┌─────────────────────────────────────────────────────────────────┐
│  ← Voltar                                            Detalhes     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌────────────────┐  ┌───────────────────────────────────┐     │
│  │               │  │  Azimut 78 Flybridge (2018)          │     │
│  │    FOTO       │  │                                   │     │
│  │    360°       │  │  ★★★★ Gold                       │     │
│  │               │  │ ━━━━━━━━━━━━━━━━  85%             │     │
│  │               │  │                                   │     │
│  │               │  │  Comprimento: 24m                │     │
│  │               │  │  Motor: 2x MAN V12 1550HP         │     │
│  └───────────────┘  │  Capacidade: 12 passageiros       │     │
│                    └───────────────────────────────────┘     │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ Documentos                                         + Add  ││
│  ├─────────────────────────────────────────────────────────────┤│
│  │ ✓ RGP                    Vigente      2025-12-31        ││
│  │ ✓ SeguroMAPFRE            Vigente      2025-06-15        ││
│  │ ✓ Survey 2024             Aprovado      2024-03-10        ││
│  └─────────────────────���───────────────────────────────────────┘│
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ Histórico                                         Ver todos ││
│  ├─────────────────────────────────────────────────────────────┤│
│  │ 2024-01-15  Seguro renovado (MAPFRE)                      ││
│  │ 2024-01-10  Manutenção preventiva                          ││
│  │ 2023-08-20  Survey aprovado                             ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

### 7.3 Upload de Documentos

```
┌─────────────────────────────────────────────────────────────────┐
│  ← Voltar                         upload de documento          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Selecione o ativo                                              │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ ▼ Azimut 78 Flybridge                                      │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Tipo de documento                                             │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐                 │
│  │   RGP  │ │ Seguro │ │ Survey │ │ Nota   │                 │
│  └────────┘ └────────┘ └────────┘ └────────┘                 │
│                                                                 │
│  Arraste ou selecione                                              │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                                                     │   │
│  │              📄 Arraste o arquivo aqui              │   │
│  │                   PDF, JPG, PNG                   │   │
│  │                                                     │   │
│  │              [Selecionar arquivo]                 │   │
│  │                                                     │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ ✓ Documento carregado com sucesso!                      │   │
│  │    Hash: a1b2c3d4e5f6...                           │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                 │
│  [Salvar Documento]                                              │
└─────────────────────────────────────────────────────────────────┘
```

### 7.4 Dossier

```
┌─────────────────────────────────────────────────────────────────┐
│  ← Voltar                            Gerar Dossier              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Selecione o tipo de dossier                                    │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐      │
│  │  📋 BÁSICO                                         │      │
│  │  ───────────────────────────────────────────────────│      │
│  │  • Capa com dados do ativo                        │      │
│  │  • Fotos atuais                                 │      │
│  │  • Cópia do RGP                               │      │
│  │  • Cópia do seguro                           │      │
│  │  • Documento único                          │      │
│  │  ───────────────────────────────────────────────────│      │
│  │  [Gerar]    Grátis para todos                     │      │
│  └─────────────────────────────────────────────────────────┘      │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐      │
│  │  📋 COMPLETO                                         │      │
│  │  ───────────────────────────────────────────────────│      │
│  │  • Tudo do Básico +                               │      │
│  │  • Histórico de manutenções                      │      │
│  │  • Notas fiscais                                 │      │
│  │  • Lista de equipamentos                         │      │
│  │  • Declareção de próprio                        │      │
│  │  ───────────────────────────────────────────────────│      │
│  │  [Gerar]    Grátis para Silver+                  │      │
│  └──────────────���─���────────────────────────────────────────┘      │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐      │
│  │  📋 PREMIUM                                          │      │
│  │  ───────────────────────────────────────────────────│      │
│  │  • Tudo do Completo +                              │      │
│  │  • Relatórios de survey                           │      │
│  │  • Hash de integridade                            │      │
│  │  • Mapa de histórico                             │      │
│  │  ───────────────────────────────────────────────────│      │
│  │  [Gerar]    Grátis para Gold                     │      │
│  └─────────────────────────────────────────────────────────┘      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 7.5 Perfil do Usuário

```
┌─────────────────────────────────────────────────────────────────┐
│  ← Voltar                            Perfil                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│         ┌───────────────────┐                                   │
│         │                   │                                   │
│         │    FOTO           │     ← Avatar com upload              │
│         │                   │                                   │
│         │    👤            │                                   │
│         └───────────────────┘                                   │
│              [Alterar foto]                                     │
│                                                                 │
│          João Silva                                             │
│          joao@email.com                                        │
│          +55 21 99999-9999                                      │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │Dados Pessoais                          [Editar]         │   │
│  │──────────────────────────────────────────────────────────│   │
│  │Nome: João Silva                                         │   │
│  │Email: joao@email.com                                    │   │
│  │Telefone: +55 21 99999-9999                              │   │
│  └─────────────────────────────────��─��─────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │Segurança                                               │   │
│  │──────────────────────────────────────────────────────────│   │
│  │• Alterar senha                                        │   │
│  │• 2FA: Ativo                                          │   │
│  │• Histórico de logins                                   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │LGPD                                                  │   │
│  │──────────────────────────────────────────────────────────│   │
│  │• Exportar meus dados                                  │   │
│  │• Solicitar exclusão da conta                           │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│                          [Sair da Conta]                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 8. Animações e Transições

### 8.1 Transições de Página

```css
/* Page transition */
.page-enter {
  opacity: 0;
  transform: translateY(10px);
}

.page-enter-active {
  opacity: 1;
  transform: translateY(0);
  transition: all 300ms ease-out;
}
```

### 8.2 Feedback de Loading

```tsx
<div className="animate-pulse bg-[#1E3A5F] rounded-xl h-32">
  {/* Skeleton loading */}
</div>
```

### 8.3 Sucesso/Tarefa Concluída

```tsx
// Toast de sucesso
<div className="bg-green-500/20 border border-green-500 rounded-lg p-4">
  ✓ Documento uploadado com sucesso
</div>
```

---

## 9. Componentes Responsivos

### 9.1 Header

| Mobile | Desktop |
|--------|---------|
| Fixed (56px) | Sticky (64px) |
| Hamburger menu | Menu visível |
| Ícones mínimos | Texto + ícones |

### 9.2 Bottom Navigation (Mobile)

```
┌────────────────────────────────────────────┐
│   🏠        📄        ⚙️        👤        │
│ (Início) (Docs)   (Ajustes)  (Perfil)     │
└────────────────────────────────────────────┘
```

### 9.3 Sidebar (Desktop)

```
┌────┬────────────────────────────────────┐
│    │                                    │
│ 🏠 │         CONTEÚDO                    │
│    │                                    │
│ 📄│                                    │
│    │                                    │
│ ⚙️ │                                    │
│    │                                    │
│ 👤│                                    │
└────┴────────────────────────────────────┘
```

---

## 10. Acessibilidade

| Recurso | Implementação |
|---|---|
| Contraste | Taxa mínima 4.5:1 |
| Fontes | Escaláveis (rem) |
| Alvos | Mínimo 44x44px (mobile) |
| Focus | Indicadores visíveis |
| Screen reader | Labels ARIA |

---

## 11. Checklist de UI/UX

```
┌─────────────────────────────────────────────────────────────┐
│  UI/UX CHECKLIST                                            │
├─────────────────────────────────────────────────────────────┤
│  ✓ Design system definido                                   │
│  ✓ Cores premium (navy, gold)                              │
│  ✓ Tipografia legível                                      │
│  ✓ Mobile-first approach                                   │
│  ✓ Bottom nav para mobile                                  │
│  ✓ Sidebar para desktop                                    │
│  ✓ Cards de ativo otimizados                               │
│  ✓ Barra de progresso visível                               │
│  ✓ Upload de documento fluido                             │
│  ✓ Dossier com 3 níveis                                   │
│  ✓ Animações sutis                                         │
│  ✓ Loading states                                        │
│  ✓ Error states                                          │
│  ✓ Empty states                                          │
│  ✓ Acessibilidade WCAG                                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 12. Versão

v0.1 — UI/UX Design

---

## 13. Data

2026-04-22
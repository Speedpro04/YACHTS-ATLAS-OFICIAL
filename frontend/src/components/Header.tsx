import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Menu, X } from 'lucide-react'
import { useTranslation } from 'react-i18next'

// Portas de entrada dos 3 mercados internacionais (futuros subdomínios + banco + idioma).
// Fonte única — usada no menu desktop e no menu mobile.
const REGIOES = [
  { label: 'Latam-Atlas', regiao: 'latam', href: 'https://latam.yachtsatlas.online' },
  { label: 'US-Atlas', regiao: 'usa', href: 'https://us.yachtsatlas.online/' },
  { label: 'EU-Atlas', regiao: 'europa', href: 'https://eu.yachtsatlas.online/' },
] as const

export default function Header() {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
  const { t } = useTranslation()

  return (
    <header
      className="fixed top-0 left-0 right-0 z-50 py-4 h-[var(--header-h)] flex items-center shadow-2xl"
      style={{
        background: 'radial-gradient(circle at center, #021a3d 0%, #010c20 70%)',
        borderBottom: '1px solid rgba(255, 255, 255, 0.05)'
      }}
    >
      {/* Brilho dourado: o clipping fica só aqui, para não cortar o menu mobile */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[300px] bg-[#c5a059]/5 blur-[120px] rounded-full"></div>
      </div>

      <div className="max-w-7xl mx-auto px-6 w-full flex items-center justify-between relative z-10">
        <Link to="/" className="group transition-all" aria-label="Yachts Atlas — Página inicial">
          {/*
            Altura, não largura.

            O arquivo da logo é QUADRADO (500x500). Dimensionando pela largura
            com `h-auto`, a altura virava igual à largura — 130px dentro de um
            header de 96px no celular, 180px dentro de 166px no desktop. A logo
            transbordava a faixa do header nos dois casos e entrava por cima da
            primeira dobra.

            Prendendo pela ALTURA (`h-full w-auto`), o tamanho da logo passa a
            ser uma decisão explícita em px, e não um efeito colateral da
            largura — seja qual for a proporção do arquivo que colocarem aqui
            depois.

            No CELULAR o valor é 96px, que é exatamente a altura da faixa: o
            fundador quis a logo o maior possível, "perto de invadir a primeira
            dobra" mas sem invadir. Ela encosta nas duas bordas do header e um
            pixel a mais já vaza para cima do hero. Se um dia mexerem em
            `--header-h` no celular, este número tem de acompanhar — os dois
            são a mesma medida.

            No DESKTOP o valor é 180px numa faixa de 166px — ou seja, ela
            ultrapassa a faixa em ~7px de cada lado, DE PROPÓSITO. É o tamanho
            que a logo sempre teve e que o fundador pediu de volta; a marca
            respirando para fora da faixa é o efeito desejado, não o defeito.
            Não aumente `--header-h` para "consertar" isto: a 1440x900 o CTA
            da home fecha a dobra com 5px de sobra, e um header mais alto o
            empurra para fora.

            `width`/`height` passam a ser os 500x500 reais: eram 180x60, uma
            proporção que não existe no arquivo, e o navegador reservava o
            espaço errado antes de a imagem carregar.
          */}
          <div className="h-[96px] md:h-[180px] relative">
             <img
               src="/logo-transparent.png"
               alt="Yachts Atlas — Custódia digital de ativos náuticos"
               className="h-full w-auto object-contain transition-transform group-hover:scale-105"
               width={500}
               height={500}
             />
          </div>
        </Link>

        {/* Menu centralizado no vão + portas de entrada dos 3 mercados 16px abaixo do menu */}
        {/*
          Corte em `lg` (1024px), não `md` (768px).

          O menu tem cinco links com 40px entre eles, mais três botões de
          região, mais o botão do cofre. Em 768px isso não cabe: "PORTAL DO
          PROPRIETÁRIO" passava POR BAIXO do botão ACESSAR COFRE — dois
          elementos clicáveis sobrepostos, na primeira coisa que a marina vê.

          De 768 a 1023px entra o menu recolhido, que já traz os mesmos cinco
          links, as três regiões e o cofre. Nada se perde; o que muda é caber.
        */}
        <nav className="hidden lg:flex flex-1 flex-col items-center justify-center gap-[16px]">
          <div className="flex items-center gap-10">
            <Link to="/" className="text-white/60 hover:text-white text-[10px] font-bold uppercase tracking-[0.2em] transition-all">
              {t('common.menu_home')}
            </Link>
            <Link to="/sobre" className="text-white/60 hover:text-white text-[10px] font-bold uppercase tracking-[0.2em] transition-all">
              {t('common.menu_about')}
            </Link>
            <Link to="/frota" className="text-white/60 hover:text-white text-[10px] font-bold uppercase tracking-[0.2em] transition-all">
              {t('common.menu_fleet')}
            </Link>
            <Link to="/seguranca" className="text-white/60 hover:text-white text-[10px] font-bold uppercase tracking-[0.2em] transition-all">
              {t('common.menu_security')}
            </Link>
            <Link to="/acesso-proprietario" className="text-white/60 hover:text-white text-[10px] font-bold uppercase tracking-[0.2em] transition-all">
              {t('common.menu_owner_portal')}
            </Link>
          </div>

          {/* Portas de entrada dos 3 mercados internacionais (futuros subdomínios/locales) */}
          <div className="flex items-center gap-4 mt-[10px]">
            {REGIOES.map((b) => (
              <a
                key={b.regiao}
                href={b.href}
                target="_blank"
                rel="noopener noreferrer"
                data-regiao={b.regiao}
                className="h-[24px] px-5 flex items-center justify-center rounded-[2px] bg-[#c5a059] hover:bg-[#b38f4d] text-[#010c20] text-[10px] font-semibold uppercase tracking-[0.2em] leading-none transition-all shadow-sm shadow-[#c5a059]/20"
              >
                {b.label}
              </a>
            ))}
          </div>
        </nav>

        <Link
          to="/login"
          className="hidden lg:inline-flex bg-[#c5a059] hover:bg-[#b38f4d] text-[#010c20] px-8 py-2.5 rounded-sm text-[10px] font-black uppercase tracking-[0.2em] transition-all shadow-lg shadow-[#c5a059]/10"
        >
          {t('common.access_vault')}
        </Link>

        <button 
          className="lg:hidden text-white"
          onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
        >
          {isMobileMenuOpen ? <X size={32} /> : <Menu size={32} />}
        </button>
      </div>

      {isMobileMenuOpen && (
        <div className="lg:hidden absolute top-full left-0 right-0 z-50 bg-[#010c20] border-b border-white/5 p-8 flex flex-col gap-6 animate-in slide-in-from-top-4 duration-500 shadow-2xl">
           {/* Portas de entrada dos 3 mercados — visíveis também no mobile */}
           <div className="flex flex-wrap justify-center gap-2 pb-5 border-b border-white/5">
             {REGIOES.map((b) => (
               <a
                 key={b.regiao}
                 href={b.href}
                 target="_blank"
                 rel="noopener noreferrer"
                 data-regiao={b.regiao}
                 className="px-4 py-2 rounded-[2px] bg-[#c5a059] hover:bg-[#b38f4d] text-[#010c20] text-[11px] font-black uppercase tracking-[0.15em] transition-all"
               >
                 {b.label}
               </a>
             ))}
           </div>
           <Link to="/" onClick={() => setIsMobileMenuOpen(false)} className="text-white font-bold uppercase tracking-[0.2em] text-xs">{t('common.menu_home')}</Link>
           <Link to="/sobre" onClick={() => setIsMobileMenuOpen(false)} className="text-white font-bold uppercase tracking-[0.2em] text-xs">{t('common.menu_about')}</Link>
           <Link to="/frota" onClick={() => setIsMobileMenuOpen(false)} className="text-white font-bold uppercase tracking-[0.2em] text-xs">{t('common.menu_fleet')}</Link>
           <Link to="/seguranca" onClick={() => setIsMobileMenuOpen(false)} className="text-white font-bold uppercase tracking-[0.2em] text-xs">{t('common.menu_security')}</Link>
           <Link to="/acesso-proprietario" onClick={() => setIsMobileMenuOpen(false)} className="text-white font-bold uppercase tracking-[0.2em] text-xs">{t('common.menu_owner_portal')}</Link>
           <Link
            to="/login"
            onClick={() => setIsMobileMenuOpen(false)}
            className="bg-[#c5a059] text-[#010c20] text-center py-4 rounded-sm text-xs font-black uppercase tracking-[0.2em] mt-4"
          >
            {t('common.access_vault')}
          </Link>
        </div>
      )}
    </header>
  )
}

import { useEffect } from 'react'
import { useLocation } from 'react-router-dom'

const BASE_URL = 'https://yachtsatlas.com'

type SeoConfig = {
  title: string
  description: string
  keywords: string
}

const DEFAULT_SEO: SeoConfig = {
  title: 'Yachts Atlas | Dossiê Digital e Custódia de Ativos Náuticos',
  description:
    'Custódia digital e dossiê imutável para iates de alto valor. Auditoria técnica, compliance e rastreabilidade SHA-256 que valorizam e aceleram a negociação do seu patrimônio marítimo.',
  keywords:
    'dossiê náutico, custódia digital de iates, registro digital de embarcação, avaliação de iate, compliance náutico, due diligence marítima, marina parceira, certificação de embarcação',
}

const SEO_BY_PATH: Record<string, SeoConfig> = {
  '/': DEFAULT_SEO,
  '/frota': {
    title: 'Gestão de Frota Náutica para Marinas | Yachts Atlas',
    description:
      'Gerencie ativos náuticos com histórico técnico, documentação certificada e visão operacional centralizada para marinas, estaleiros e gestores de frota.',
    keywords:
      'gestão de frota náutica, software para marina, controle de embarcações, gestão de ativos náuticos',
  },
  '/seguranca': {
    title: 'Segurança e Integridade Documental Náutica | Yachts Atlas',
    description:
      'Camada de segurança, rastreabilidade e validação de integridade SHA-256 para documentos e registros marítimos críticos.',
    keywords:
      'segurança náutica digital, integridade documental, rastreabilidade marítima, hash SHA-256, compliance náutico',
  },
  '/registro-marina': {
    title: 'Seja uma Marina Parceira Fundadora | Yachts Atlas',
    description:
      'Cadastre sua marina na rede Yachts Atlas e ative onboarding, receita de dossiês e gestão de clientes com condições fundadoras exclusivas.',
    keywords: 'registro de marina, marina parceira, onboarding de marina, rede náutica, programa fundador',
  },
  '/marina-parceira': {
    title: 'Programa Marina Parceira — Receita de Dossiês | Yachts Atlas',
    description:
      'Conheça os benefícios comerciais do programa fundador: receita de dossiês, indicação rentável e condições vitalícias para as primeiras 40 marinas.',
    keywords: 'marina parceira, programa de parceria, split de receita, ecossistema náutico, programa fundador',
  },
  '/acesso-proprietario': {
    title: 'Portal do Proprietário de Iate | Yachts Atlas',
    description:
      'Área segura para proprietários acessarem histórico, dossiê certificado e documentação da embarcação com autenticação 2FA.',
    keywords: 'portal do proprietário, dossiê da embarcação, acesso náutico seguro, cofre digital de iate',
  },
  '/termos-fundadores': {
    title: 'Termos do Programa Fundador | Yachts Atlas',
    description:
      'Condições comerciais de referência para marinas aprovadas no ciclo fundador da rede Yachts Atlas.',
    keywords: 'termos programa fundador, condições marina parceira, contrato fundador yachts atlas',
  },
}

function setMetaByName(name: string, content: string): void {
  let meta = document.querySelector(`meta[name="${name}"]`)
  if (!meta) {
    meta = document.createElement('meta')
    meta.setAttribute('name', name)
    document.head.appendChild(meta)
  }
  meta.setAttribute('content', content)
}

function setMetaByProperty(property: string, content: string): void {
  let meta = document.querySelector(`meta[property="${property}"]`)
  if (!meta) {
    meta = document.createElement('meta')
    meta.setAttribute('property', property)
    document.head.appendChild(meta)
  }
  meta.setAttribute('content', content)
}

function setCanonical(url: string): void {
  let link = document.querySelector('link[rel="canonical"]')
  if (!link) {
    link = document.createElement('link')
    link.setAttribute('rel', 'canonical')
    document.head.appendChild(link)
  }
  link.setAttribute('href', url)
}

export default function SeoMeta() {
  const location = useLocation()

  useEffect(() => {
    const seo = SEO_BY_PATH[location.pathname] ?? DEFAULT_SEO
    const canonicalUrl = `${BASE_URL}${location.pathname}`
    const ogImage = `${BASE_URL}/logo-with-bg-light.jpg`
    const imageAlt = 'Yachts Atlas — Custódia digital de ativos náuticos'

    // Private/auth routes must not be indexed by search engines
    const isPrivate =
      location.pathname.startsWith('/app') ||
      location.pathname === '/login' ||
      location.pathname === '/portal-proprietario' ||
      location.pathname.startsWith('/success')

    document.title = seo.title
    setCanonical(canonicalUrl)
    setMetaByName('description', seo.description)
    setMetaByName('keywords', seo.keywords)
    setMetaByName(
      'robots',
      isPrivate ? 'noindex, nofollow' : 'index, follow, max-image-preview:large, max-snippet:-1'
    )

    setMetaByProperty('og:type', 'website')
    setMetaByProperty('og:site_name', 'Yachts Atlas')
    setMetaByProperty('og:title', seo.title)
    setMetaByProperty('og:description', seo.description)
    setMetaByProperty('og:url', canonicalUrl)
    setMetaByProperty('og:image', ogImage)
    setMetaByProperty('og:image:width', '1200')
    setMetaByProperty('og:image:height', '630')
    setMetaByProperty('og:image:alt', imageAlt)
    setMetaByProperty('og:locale', 'pt_BR')

    setMetaByName('twitter:card', 'summary_large_image')
    setMetaByName('twitter:title', seo.title)
    setMetaByName('twitter:description', seo.description)
    setMetaByName('twitter:image', ogImage)
    setMetaByName('twitter:image:alt', imageAlt)
  }, [location.pathname])

  return null
}

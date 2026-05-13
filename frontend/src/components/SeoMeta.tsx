import { useEffect } from 'react'
import { useLocation } from 'react-router-dom'

const BASE_URL = 'https://yachtsatlas.com'

type SeoConfig = {
  title: string
  description: string
  keywords: string
}

const DEFAULT_SEO: SeoConfig = {
  title: 'Yachts Atlas | Registro Digital e Integridade Náutica',
  description:
    'Plataforma SaaS para marinas, estaleiros e proprietários com registro digital, compliance, rastreabilidade e segurança documental náutica.',
  keywords:
    'yachts atlas, marina, iates, nautica, registro digital, compliance nautico, dossie nautico, documentacao embarcacao',
}

const SEO_BY_PATH: Record<string, SeoConfig> = {
  '/': DEFAULT_SEO,
  '/frota': {
    title: 'Gestão de Frota Náutica | Yachts Atlas',
    description:
      'Gerencie ativos náuticos com histórico técnico, documentação e visão operacional centralizada para marinas e gestores.',
    keywords:
      'gestao de frota nautica, software marina, controle de embarcacoes, ativos nauticos',
  },
  '/seguranca': {
    title: 'Segurança e Integridade de Dados | Yachts Atlas',
    description:
      'Camada de segurança, rastreabilidade e validação de integridade para documentos e registros marítimos críticos.',
    keywords:
      'seguranca nautica digital, integridade documental, rastreabilidade maritima, compliance',
  },
  '/registro-marina': {
    title: 'Registro de Marina Parceira | Yachts Atlas',
    description:
      'Cadastre sua marina na rede Yachts Atlas e acelere onboarding, monetização de serviços e gestão de clientes.',
    keywords: 'registro de marina, marina parceira, onboarding marina, rede nautica',
  },
  '/marina-parceira': {
    title: 'Programa Marina Parceira | Yachts Atlas',
    description:
      'Conheça os benefícios comerciais e operacionais do programa de marinas parceiras da Yachts Atlas.',
    keywords: 'marina parceira, programa de parceria, ecossistema nautico',
  },
  '/acesso-proprietario': {
    title: 'Acesso do Proprietário | Yachts Atlas',
    description:
      'Área de acesso para proprietários com histórico, dossiê e documentação da embarcação em ambiente seguro.',
    keywords: 'portal do proprietario, dossie da embarcacao, acesso nautico',
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

    document.title = seo.title
    setCanonical(canonicalUrl)
    setMetaByName('description', seo.description)
    setMetaByName('keywords', seo.keywords)
    setMetaByName('robots', 'index, follow, max-image-preview:large')

    setMetaByProperty('og:type', 'website')
    setMetaByProperty('og:site_name', 'Yachts Atlas')
    setMetaByProperty('og:title', seo.title)
    setMetaByProperty('og:description', seo.description)
    setMetaByProperty('og:url', canonicalUrl)
    setMetaByProperty('og:image', `${BASE_URL}/logo-with-bg-light.jpg`)
    setMetaByProperty('og:locale', 'pt_BR')

    setMetaByName('twitter:card', 'summary_large_image')
    setMetaByName('twitter:title', seo.title)
    setMetaByName('twitter:description', seo.description)
    setMetaByName('twitter:image', `${BASE_URL}/logo-with-bg-light.jpg`)
  }, [location.pathname])

  return null
}

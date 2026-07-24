import { useEffect } from 'react'
import { useLocation } from 'react-router-dom'
import seoData from '../seo/seo-data.json'

type SeoEntry = {
  title?: string
  description?: string
  keywords?: string
  ogDescription?: string
  index?: boolean
}

type SeoData = {
  baseUrl: string
  ogImage: string
  imageAlt: string
  default: Required<Pick<SeoEntry, 'title' | 'description' | 'keywords'>> & { ogDescription?: string }
  pages: Record<string, SeoEntry>
}

const { baseUrl, ogImage, imageAlt, default: DEFAULT_SEO, pages } = seoData as SeoData

// Rotas de autenticação/privadas que nunca devem ser indexadas.
function isPrivateRoute(pathname: string): boolean {
  return (
    pathname.startsWith('/app') ||
    pathname.startsWith('/success') ||
    pathname === '/login' ||
    pathname === '/portal-proprietario' ||
    pathname === '/redefinir-senha'
  )
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
    const page = pages[location.pathname] ?? {}
    const title = page.title ?? DEFAULT_SEO.title
    const description = page.description ?? DEFAULT_SEO.description
    const keywords = page.keywords ?? DEFAULT_SEO.keywords
    const ogDescription = page.ogDescription ?? page.description ?? DEFAULT_SEO.ogDescription ?? description
    const canonicalUrl = `${baseUrl}${location.pathname}`

    // noindex para rotas privadas ou marcadas explicitamente com index:false
    const noindex = isPrivateRoute(location.pathname) || page.index === false

    document.title = title
    setCanonical(canonicalUrl)
    setMetaByName('description', description)
    setMetaByName('keywords', keywords)
    setMetaByName(
      'robots',
      noindex ? 'noindex, nofollow' : 'index, follow, max-image-preview:large, max-snippet:-1'
    )

    setMetaByProperty('og:type', 'website')
    setMetaByProperty('og:site_name', 'Yachts Atlas')
    setMetaByProperty('og:title', title)
    setMetaByProperty('og:description', ogDescription)
    setMetaByProperty('og:url', canonicalUrl)
    setMetaByProperty('og:image', ogImage)
    setMetaByProperty('og:image:width', '1200')
    setMetaByProperty('og:image:height', '630')
    setMetaByProperty('og:image:alt', imageAlt)
    setMetaByProperty('og:locale', 'pt_BR')

    setMetaByName('twitter:card', 'summary_large_image')
    setMetaByName('twitter:title', title)
    setMetaByName('twitter:description', ogDescription)
    setMetaByName('twitter:image', ogImage)
    setMetaByName('twitter:image:alt', imageAlt)
  }, [location.pathname])

  return null
}

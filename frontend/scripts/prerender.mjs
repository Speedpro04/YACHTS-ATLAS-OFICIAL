// ============================================================
// Yachts Atlas — Pré-renderização estática por rota
// Roda depois do `vite build`. Para cada rota pública gera um
// dist/<rota>/index.html com <title>, description, canonical e
// Open Graph próprios — para que Googlebot e robôs sociais
// (WhatsApp, Facebook, LinkedIn) leiam o SEO certo SEM depender
// de executar JavaScript. Também gera o sitemap.xml.
// ============================================================

import { readFileSync, writeFileSync, mkdirSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const distDir = join(__dirname, '..', 'dist')
const seo = JSON.parse(readFileSync(join(__dirname, '..', 'src', 'seo', 'seo-data.json'), 'utf8'))

const { baseUrl, ogImage, imageAlt, default: DEFAULT, pages } = seo

// HTML do build é o template — já contém assets com hash, fontes e JSON-LD.
const template = readFileSync(join(distDir, 'index.html'), 'utf8')

const ROBOTS_INDEX = 'index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1'

function esc(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

// Substitui o VALOR de uma tag preservando o que vem antes/depois.
function setValue(html, regex, value) {
  const safe = esc(value)
  if (!regex.test(html)) {
    console.warn(`[prerender] aviso: padrão não encontrado -> ${regex}`)
    return html
  }
  return html.replace(regex, (_m, pre, post) => `${pre}${safe}${post}`)
}

function buildHtml(path, page) {
  const title = page.title || DEFAULT.title
  const description = page.description || DEFAULT.description
  const keywords = page.keywords || DEFAULT.keywords
  const ogDescription = page.ogDescription || page.description || DEFAULT.ogDescription || description
  const canonical = path === '/' ? `${baseUrl}/` : `${baseUrl}${path}`

  let html = template
  html = setValue(html, /(<title>)[\s\S]*?(<\/title>)/, title)
  html = setValue(html, /(<meta name="description" content=")[^"]*(")/, description)
  html = setValue(html, /(<meta name="keywords" content=")[^"]*(")/, keywords)
  html = setValue(html, /(<meta name="robots" content=")[^"]*(")/, ROBOTS_INDEX)
  html = setValue(html, /(<link rel="canonical" href=")[^"]*(")/, canonical)
  html = setValue(html, /(<meta property="og:title" content=")[^"]*(")/, title)
  html = setValue(html, /(<meta property="og:description" content=")[^"]*(")/, ogDescription)
  html = setValue(html, /(<meta property="og:url" content=")[^"]*(")/, canonical)
  html = setValue(html, /(<meta property="og:image" content=")[^"]*(")/, ogImage)
  html = setValue(html, /(<meta property="og:image:alt" content=")[^"]*(")/, imageAlt)
  html = setValue(html, /(<meta name="twitter:title" content=")[^"]*(")/, title)
  html = setValue(html, /(<meta name="twitter:description" content=")[^"]*(")/, ogDescription)
  return html
}

// --- Gera um index.html por rota pública (index !== false, exceto a home) ---
const indexable = Object.entries(pages).filter(([, p]) => p.index !== false)

let count = 0
for (const [path, page] of indexable) {
  if (path === '/') continue // a home já é o dist/index.html
  const outDir = join(distDir, path.replace(/^\//, ''))
  mkdirSync(outDir, { recursive: true })
  writeFileSync(join(outDir, 'index.html'), buildHtml(path, page), 'utf8')
  count++
  console.log(`[prerender] ${path} -> ${path.replace(/^\//, '')}/index.html`)
}

// --- A home também recebe os metas (garante og:description rico e robots index) ---
writeFileSync(join(distDir, 'index.html'), buildHtml('/', pages['/'] || {}), 'utf8')

// --- Sitemap.xml a partir das mesmas rotas indexáveis ---
const lastmod = new Date().toISOString().slice(0, 10)
const urls = indexable
  .map(([path, page]) => {
    const loc = path === '/' ? `${baseUrl}/` : `${baseUrl}${path}`
    const priority = page.priority || '0.7'
    const changefreq = page.changefreq || 'monthly'
    return `  <url>\n    <loc>${loc}</loc>\n    <lastmod>${lastmod}</lastmod>\n    <changefreq>${changefreq}</changefreq>\n    <priority>${priority}</priority>\n  </url>`
  })
  .join('\n')

const sitemap = `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${urls}\n</urlset>\n`
writeFileSync(join(distDir, 'sitemap.xml'), sitemap, 'utf8')

console.log(`[prerender] OK — ${count} rotas pré-renderizadas + sitemap.xml (${indexable.length} URLs, lastmod ${lastmod})`)

/**
 * Link de consulta de preço na Liga Magic.
 *
 * A Liga Magic não tem API pública (a comunidade pede desde 2014) e o site
 * bloqueia acesso automatizado, então não há como trazer o preço para dentro
 * da página de forma confiável nem legítima. O que dá para fazer é levar o
 * usuário direto à busca da carta, que é o navegador dele acessando o site
 * normalmente.
 */
const BASE = 'https://www.ligamagic.com.br/?view=cards/search&card='

export function ligaMagicUrl(nome) {
  return BASE + encodeURIComponent(nome || '')
}

export function useLigaMagic() {
  function abrirPreco(nome) {
    window.open(ligaMagicUrl(nome), '_blank', 'noopener,noreferrer')
  }
  return { ligaMagicUrl, abrirPreco }
}

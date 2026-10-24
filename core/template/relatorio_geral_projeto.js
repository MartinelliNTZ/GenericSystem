/* =============================================================================
   Relatório geral do projeto (Acompanhamento de OS) — COMPORTAMENTO
   =============================================================================
   Este arquivo é a fonte do COMPORTAMENTO do relatório HTML: ele lê o objeto
   `window.DADOS_PROJETO` (injetado pelo `OsReportHtmlGenerator`) e preenche os
   painéis, os mapas (Leaflet), o menu lateral, as descrições ("i") e o
   recolher/expandir dos painéis.

   O template (`relatorio_geral_projeto.html`) aponta para ele por
   `<script src>` — abrir o template direto já mostra o layout com os campos
   vazios — e o `OsReportAssets` EMBUTE este script no arquivo gerado, que sai
   num só `.HTML`, sem depender de arquivos ao lado.

   As chaves de `DADOS_PROJETO` são as do schema do `ReportDataBuilder`; o
   objeto abaixo é apenas o PADRÃO (o relatório gerado sempre traz o seu).
   ============================================================================= */

(function () {
  'use strict';

  var D = window.DADOS_PROJETO = window.DADOS_PROJETO || {
    os: '',
    nome_comercial: '',
    tipos_manejo: [],
    culturas: [],
    area_contratada_ha: null,
    n_cars: null,
    data_inicio: '',
    ano_cenario_base: null,
    gerado_em: '',
    versao_data: '',
    nome: '',
    cliente: '',
    cnpj: '',
    pasta: '',
    pasta_completa: '',
    atualizado_em: '',
    fazendas: [],
    limites: null,
    zonas: null,
    base_limites: null,
    base_zonas: null,
    pastas_criadas: null,
    lista_pastas: [],
    anos_criados: [],
    /* Rodapé: a versão do relatório e o tempo de processamento (quando houver) */
    versao_relatorio: '',
    processamento: ''
  };

  /* Paleta das fazendas/zonas (a mesma família de cores dos mapas). */
  var PALETA = ['#38bdf8', '#fb923c', '#a3e635', '#f472b6', '#facc15', '#a78bfa',
    '#2dd4bf', '#ef4444', '#e879f9', '#4ade80', '#22d3ee', '#cbd5e1'];

  /* ---------- Helpers ---------- */

  function $(id) { return document.getElementById(id); }

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
    });
  }

  function vazio(v) { return v == null || v === ''; }

  function num(v, c) {
    c = c == null ? 2 : c;
    return (vazio(v) || isNaN(v)) ? '—' : Number(v).toLocaleString('pt-BR', {
      minimumFractionDigits: c, maximumFractionDigits: c
    });
  }

  function features(fc) { return (fc && fc.features) ? fc.features : []; }

  function texto(el, valor) { if (el) el.textContent = vazio(valor) ? '—' : String(valor); }

  function cartoesHtml(lista) {
    return (lista || []).map(function (c) {
      var v = vazio(c[1]) ? '' : c[1];
      return '<div class="cartao">' +
        '<span class="cartao-valor' + (vazio(v) ? ' vazio-v' : '') + '">' +
        (vazio(v) ? '—' : esc(v)) + '</span>' +
        '<span class="cartao-rotulo">' + esc(c[0]) + '</span></div>';
    }).join('');
  }

  function pillsHtml(el, itens, textoVazio) {
    if (!el) return;
    el.innerHTML = (itens || []).length
      ? itens.map(function (i) { return '<span class="pill">' + esc(i) + '</span>'; }).join('')
      : '<p class="vazio" style="border:0;padding:3px 8px">' + esc(textoVazio) + '</p>';
  }

  function quando(v) {
    if (vazio(v)) return '';
    var d = new Date(v);
    if (isNaN(d.getTime())) return String(v);
    return d.toLocaleString('pt-BR', {
      day: '2-digit', month: '2-digit', year: 'numeric',
      hour: '2-digit', minute: '2-digit'
    });
  }

  function nomeArquivo(p) {
    var t = String(vazio(p) ? '' : p);
    return t ? t.split(/[\\/]/).pop() : '';
  }

  /* Resumo de UMA base gravada na OS (2.2 e 2.3). */
  function baseHtml(el, base, rotulo) {
    if (!el) return;
    if (!base || !base.tem) {
      el.innerHTML = '<p class="vazio">Base não registrada nesta OS.</p>';
      return;
    }
    el.innerHTML =
      '<div class="cartao"><span class="cartao-valor">' + num(base.contagem, 0) +
        '</span><span class="cartao-rotulo">' + esc(rotulo) + '</span></div>' +
      '<div class="cartao"><span class="cartao-valor">' + num(base.area_ha) +
        '</span><span class="cartao-rotulo">Área (ha)</span></div>' +
      '<div class="base-info">' +
        '<span><b>Arquivo</b>' + esc(nomeArquivo(base.arquivo) || '—') + '</span>' +
        '<span><b>Origem</b>' + esc(base.origem || '—') + '</span>' +
        '<span><b>Registrado em</b>' + esc(quando(base.registrado) || '—') + '</span>' +
      '</div>';
  }

  /* ---------- Cabeçalho e rodapé ---------- */

  function pintarCabecalho() {
    if (D.os) texto($('titulo'), 'Relatório geral — OS ' + D.os);
    if (D.nome_comercial) texto($('subtitulo'), D.nome_comercial);
  }

  // O RODAPÉ fecha a página: a data de geração, o tempo de processamento
  // (quando o dado existe — senão a linha sai de cena) e a VERSÃO do relatório.
  // A versão e a data NÃO aparecem no menu lateral nem no cabeçalho.
  function pintarRodape() {
    texto($('rodapeGerado'), D.gerado_em);
    texto($('versaoRelatorio'), D.versao_relatorio);
    var linha = $('rodapeProcessamento');
    if (!linha) return;
    var duracao = vazio(D.processamento) ? '' : String(D.processamento).trim();
    linha.hidden = !duracao;
    linha.textContent = duracao ? 'Tempo de processamento: ' + duracao : '';
  }

  /* ---------- Painel 1 · Visão geral ---------- */

  function pintarVisaoGeral() {
    var cartoes = [
      ['OS (ID interno)', D.os],
      ['Nome', D.nome],
      ['Cliente', D.cliente],
      ['Nome comercial', D.nome_comercial],
      ['CNPJ', D.cnpj],
      ['Área contratada', vazio(D.area_contratada_ha) ? '' : num(D.area_contratada_ha) + ' ha'],
      ['Nº de CARs', vazio(D.n_cars) ? '' : num(D.n_cars, 0)],
      ['Data de início', D.data_inicio],
      ['Ano do cenário base', D.ano_cenario_base],
      ['Última atualização', quando(D.atualizado_em)]
    ];
    $('cartoes').innerHTML = cartoesHtml(cartoes);
  }

  /* ---------- Painel 3 · Atividades ---------- */

  // 3.1 — tipos de manejo: o banco ainda não fornece — a faixa sai com os
  // exemplos em tom fantasma (nada é inventado como dado).
  function pintarAtividades() {
    $('manejos').innerHTML = (D.tipos_manejo || []).length
      ? D.tipos_manejo.map(function (t) { return '<span class="pill">' + esc(t) + '</span>'; }).join('')
      : ['Lavoura', 'Pasto', 'ETF'].map(function (t) {
          return '<span class="pill fantasma">' + esc(t) + '</span>';
        }).join('') + '<span class="vazio" style="border:0;padding:3px 8px">exemplos — preencher tipos_manejo</span>';

    // 3.2 — culturas: sem fonte no banco, o subpainel mostra o estado vazio.
    pillsHtml($('culturas'), D.culturas, 'Nenhuma cultura informada.');
  }

  /* ---------- Painel 2.1 · Fazendas e talhões ---------- */

  // Ordem das fazendas: primeiro as de `D.fazendas`; depois as que só aparecem
  // no shape de limites. A cor de cada uma sai dessa ordem (o mapa usa a mesma).
  var fazNomes = [];

  function corFaz(nome) {
    var i = fazNomes.indexOf(nome);
    return PALETA[(i < 0 ? 0 : i) % PALETA.length];
  }

  function pintarFazendas() {
    fazNomes = (D.fazendas || []).map(function (f) { return f.nome; });
    features(D.limites).forEach(function (f) {
      var n = (f.properties || {}).fazenda;
      if (n && fazNomes.indexOf(n) < 0) fazNomes.push(n);
    });

    var fazs = D.fazendas || [], totTal = 0, totArea = 0;
    $('listaFazendas').innerHTML = fazs.length ? fazs.map(function (f) {
      var ts = f.talhoes || [], a = 0;
      ts.forEach(function (t) { if (!vazio(t.area_ha)) a += Number(t.area_ha); });
      totTal += ts.length;
      totArea += a;
      return '<details class="faz"><summary>' +
        '<span class="dot" style="background:' + corFaz(f.nome) + '"></span>' + esc(f.nome) +
        ' <small>' + ts.length + ' talhões · ' + num(a) + ' ha</small></summary>' +
        '<div class="tabela"><table><thead><tr><th>Talhão</th><th class="n">Área (ha)</th></tr></thead><tbody>' +
        ts.map(function (t) {
          return '<tr><td>' + esc(t.nome) + '</td><td class="n">' + num(t.area_ha) + '</td></tr>';
        }).join('') +
        '</tbody></table></div></details>';
    }).join('') +
      '<div class="total"><span>Total geral</span><span>' + totTal + ' talhões · ' +
      num(totArea) + ' ha</span></div>'
      : '<p class="vazio">Nenhuma fazenda informada. Preencha fazendas (com seus talhões) em DADOS_PROJETO.</p>';

    $('resumoFaz').innerHTML =
      '<span class="chip"><strong>' + fazs.length + '</strong> fazendas</span>' +
      '<span class="chip"><strong>' + totTal + '</strong> talhões</span>' +
      '<span class="chip"><strong>' + num(totArea) + '</strong> ha somados</span>';
  }

  /* ---------- Painel 2.2 / 2.3 · Mapas ---------- */

  // Mapa base: satélite (Esri World Imagery) + camadas de referência (estradas,
  // limites e nomes) num painel próprio, sem capturar o mouse.
  function criarMapa(id) {
    var el = $(id);
    if (!window.L) {
      el.innerHTML = '<p class="vazio" style="margin:16px">Não foi possível carregar o mapa. ' +
        'Abra o arquivo com acesso à internet.</p>';
      return null;
    }
    var m = L.map(id).setView([-15.8, -52], 4);
    var esri = 'https://server.arcgisonline.com/ArcGIS/rest/services/';
    L.tileLayer(esri + 'World_Imagery/MapServer/tile/{z}/{y}/{x}', {
      maxZoom: 19, attribution: 'Imagens © Esri, Maxar, Earthstar Geographics'
    }).addTo(m);
    m.createPane('referencia');
    m.getPane('referencia').style.zIndex = 450;
    m.getPane('referencia').style.pointerEvents = 'none';
    ['Reference/World_Transportation', 'Reference/World_Boundaries_and_Places'].forEach(function (p) {
      L.tileLayer(esri + p + '/MapServer/tile/{z}/{y}/{x}', { maxZoom: 19, pane: 'referencia' }).addTo(m);
    });
    // Guarda a instância no próprio elemento: ao reabrir o painel, o mapa
    // precisa se redesenhar (`invalidateSize`).
    el.__mapaLeaflet = m;
    return m;
  }

  function legenda(el, itens, fantasmas) {
    if (!el) return;
    el.innerHTML = itens.length
      ? itens.map(function (i) {
          return '<div class="leg-item"><span class="dot" style="background:' + i.cor + '"></span>' +
            '<span>' + esc(i.nome) + (i.n ? ' <small style="color:var(--texto-suave)">(' + i.n + ')</small>' : '') +
            '</span></div>';
        }).join('')
      : fantasmas.map(function (n) {
          return '<div class="leg-item fantasma"><span class="dot"></span><span>' + esc(n) + '</span></div>';
        }).join('');
  }

  // 2.2 — limites dos talhões (uma cor por fazenda) + resumo da base.
  function pintarLimites() {
    var mL = criarMapa('mapaLimites'), contFaz = {};
    var fl = features(D.limites);
    fl.forEach(function (f) {
      var n = (f.properties || {}).fazenda || '—';
      contFaz[n] = (contFaz[n] || 0) + 1;
    });

    if (mL && fl.length) {
      var gL = L.geoJSON(D.limites, {
        style: function (f) {
          var c = corFaz((f.properties || {}).fazenda);
          return { color: c, weight: 2, fillColor: c, fillOpacity: .25 };
        },
        onEachFeature: function (f, l) {
          var p = f.properties || {};
          l.bindTooltip(esc(p.talhao), { permanent: true, direction: 'center', className: 'rotulo' });
          l.bindPopup('<strong>' + esc(p.talhao) + '</strong><br>' + esc(p.fazenda) +
            (vazio(p.area_ha) ? '' : '<br>' + num(p.area_ha) + ' ha'));
        }
      }).addTo(mL);
      mL.fitBounds(gL.getBounds(), { padding: [20, 20] });
      $('avisoLimites').hidden = true;
    }

    legenda($('legLimites'), Object.keys(contFaz).length
      ? Object.keys(contFaz).map(function (n) { return { nome: n, cor: corFaz(n), n: contFaz[n] }; })
      : fazNomes.map(function (n) { return { nome: n, cor: corFaz(n) }; }),
      ['Fazenda A', 'Fazenda B', 'Fazenda C']);

    $('chkRotulos').addEventListener('change', function () {
      $('caixaLimites').classList.toggle('sem-rotulos', !this.checked);
    });
    baseHtml($('baseLimites'), D.base_limites, 'Talhões');
  }

  // 2.3 — zonas de manejo (só a legenda, sem nome de talhão) + resumo da base.
  function pintarZonas() {
    var mZ = criarMapa('mapaZonas'), zonas = [];
    var fz = features(D.zonas);
    fz.forEach(function (f) {
      var n = (f.properties || {}).zona || '—';
      if (zonas.indexOf(n) < 0) zonas.push(n);
    });
    function corZona(n) { return PALETA[(zonas.indexOf(n) + 3) % PALETA.length]; }

    if (mZ && fz.length) {
      var gZ = L.geoJSON(D.zonas, {
        style: function (f) {
          var c = corZona((f.properties || {}).zona);
          return { color: c, weight: 1.5, fillColor: c, fillOpacity: .45 };
        },
        onEachFeature: function (f, l) {
          l.bindPopup('<strong>' + esc((f.properties || {}).zona) + '</strong>');
        }
      }).addTo(mZ);
      mZ.fitBounds(gZ.getBounds(), { padding: [20, 20] });
      $('avisoZonas').hidden = true;
    }

    legenda($('legZonas'), zonas.map(function (n) { return { nome: n, cor: corZona(n) }; }),
      ['Zona 1', 'Zona 2', 'Zona 3']);
    baseHtml($('baseZonas'), D.base_zonas, 'Zonas');
  }

  /* ---------- Painel 4 · Base de Dados ---------- */

  function pintarBaseDados() {
    var pastas = D.lista_pastas || [], anos = D.anos_criados || [];

    // 4.1 — pasta da OS: o nome da pasta + o caminho completo resolvido.
    $('resumoPasta').innerHTML = '<span class="chip"><strong>' +
      (vazio(D.pasta) ? '—' : esc(D.pasta)) + '</strong> pasta da OS</span>';
    texto($('pastaCompleta'), D.pasta_completa);

    // 4.2 — pastas criadas e 4.3 — anos com dados.
    $('resumoPastas').innerHTML = '<span class="chip"><strong>' + num(pastas.length, 0) +
      '</strong> pastas criadas</span>';
    pillsHtml($('listaPastas'), pastas, 'Nenhuma pasta criada.');
    $('resumoAnos').innerHTML = '<span class="chip"><strong>' + num(anos.length, 0) +
      '</strong> anos com dados</span>';
    pillsHtml($('listaAnos'), anos, 'Nenhum ano com dados.');
  }

  /* ---------- Marca (logo com fallback) ---------- */

  // Se a imagem da logo não carregar (sem internet, por exemplo), a caixa
  // mostra a sigla — o relatório nunca fica com um quadro vazio.
  function ligarLogos() {
    ['logoLateral', 'logoCabecalho', 'logoRodape'].forEach(function (id) {
      var box = $(id);
      if (!box) return;
      var img = box.querySelector('img');
      if (img) img.addEventListener('error', function () { box.classList.add('sem-img'); });
    });
  }

  /* ---------- Descrições ("i"): hover no desktop, toque no celular ---------- */

  function ligarTooltips() {
    document.addEventListener('click', function (e) {
      var btn = e.target.closest && e.target.closest('.info-tooltip-btn');
      document.querySelectorAll('.info-tooltip.aberto').forEach(function (item) {
        if (!btn || item !== btn.closest('.info-tooltip')) item.classList.remove('aberto');
      });
      if (!btn) return;
      e.preventDefault();
      e.stopPropagation();
      var caixa = btn.closest('.info-tooltip');
      if (caixa) caixa.classList.toggle('aberto');
    });
    document.addEventListener('keydown', function (e) {
      if (e.key !== 'Escape') return;
      document.querySelectorAll('.info-tooltip.aberto').forEach(function (item) {
        item.classList.remove('aberto');
      });
    });
  }

  /* ---------- Menu lateral (celular) e destaque do painel visível ---------- */

  function ligarMenu() {
    var corpo = document.body, btn = $('btnMenu');
    var links = document.querySelectorAll('.menu a');

    function menu(abrir) {
      corpo.classList.toggle('menu-aberto', abrir);
      btn.setAttribute('aria-expanded', abrir ? 'true' : 'false');
    }

    btn.addEventListener('click', function () { menu(!corpo.classList.contains('menu-aberto')); });
    $('scrim').addEventListener('click', function () { menu(false); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') menu(false); });
    links.forEach(function (a) { a.addEventListener('click', function () { menu(false); }); });

    if (!('IntersectionObserver' in window)) return;
    var obs = new IntersectionObserver(function (entradas) {
      entradas.forEach(function (entrada) {
        if (!entrada.isIntersecting) return;
        links.forEach(function (a) {
          a.classList.toggle('ativo', a.getAttribute('href') === '#' + entrada.target.id);
        });
      });
    }, { rootMargin: '-30% 0px -60% 0px' });
    document.querySelectorAll('main .painel').forEach(function (secao) { obs.observe(secao); });
  }

  /* ---------- Painéis: descrição + expandir/recolher ---------- */

  // As ações do cabeçalho (a descrição "i" e o botão de expandir/recolher) são
  // montadas aqui para o template ficar só com a estrutura do painel.
  function ligarPaineis() {
    document.querySelectorAll('main > section.painel').forEach(function (painel) {
      var topo = painel.querySelector(':scope > .painel-topo');
      if (!topo) return;

      var acoes = document.createElement('div');
      acoes.className = 'painel-acoes';
      var info = topo.querySelector('.painel-identidade .info-tooltip');
      if (info) acoes.appendChild(info);

      var btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'painel-toggle';
      btn.setAttribute('aria-label', 'Recolher ou expandir este painel');
      btn.setAttribute('aria-expanded', 'true');
      acoes.appendChild(btn);
      topo.appendChild(acoes);
      topo.classList.add('painel-topo-clicavel');

      function alternar() {
        var recolher = !painel.classList.contains('painel-recolhido');
        painel.classList.toggle('painel-recolhido', recolher);
        btn.setAttribute('aria-expanded', recolher ? 'false' : 'true');
        if (recolher) return;
        // Painel aberto de novo: os mapas que ficaram ocultos se redesenham.
        painel.querySelectorAll('.mapa').forEach(function (mapa) {
          if (mapa.__mapaLeaflet) mapa.__mapaLeaflet.invalidateSize();
        });
      }

      topo.addEventListener('click', function (ev) {
        if (ev.target.closest('.painel-toggle')) { alternar(); return; }
        if (ev.target.closest('a, button, select, input, textarea, .info-tooltip')) return;
        alternar();
      });
      btn.addEventListener('keydown', function (ev) {
        if (ev.key !== 'Enter' && ev.key !== ' ') return;
        ev.preventDefault();
        alternar();
      });
    });

    // Ao navegar por um link do menu, o painel de destino abre.
    document.querySelectorAll('a[href^="#"]').forEach(function (a) {
      a.addEventListener('click', function () {
        var alvo = $(String(a.getAttribute('href')).slice(1));
        if (!alvo || !alvo.classList.contains('painel')) return;
        alvo.classList.remove('painel-recolhido');
        var btn = alvo.querySelector(':scope > .painel-topo .painel-toggle');
        if (btn) btn.setAttribute('aria-expanded', 'true');
      });
    });
  }

  /* ---------- Botão "voltar ao topo" (celular) ---------- */

  function ligarBotaoTopo() {
    var btn = $('btnTopo');
    if (!btn) return;
    var visivel = false;
    btn.addEventListener('click', function () {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
    window.addEventListener('scroll', function () {
      var mostrar = window.innerWidth <= 560 && window.scrollY > 600;
      if (mostrar === visivel) return;
      visivel = mostrar;
      btn.classList.toggle('visivel', mostrar);
    }, { passive: true });
  }

  /* ---------- Início ---------- */

  function iniciar() {
    pintarCabecalho();
    pintarRodape();
    pintarVisaoGeral();
    pintarFazendas();
    pintarLimites();
    pintarZonas();
    pintarAtividades();
    pintarBaseDados();
    ligarLogos();
    ligarTooltips();
    ligarMenu();
    ligarPaineis();
    ligarBotaoTopo();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', iniciar);
  } else {
    iniciar();
  }




})();

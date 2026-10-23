



    (function () {

      // Tooltips de descrição: hover no desktop e clique/toque no mobile.
      document.addEventListener('click', function (e) {
        var btn = e.target.closest && e.target.closest('.info-tooltip-btn');
        document.querySelectorAll('.info-tooltip.aberto').forEach(function (item) {
          if (!btn || item !== btn.closest('.info-tooltip')) item.classList.remove('aberto');
        });
        if (btn) {
          e.preventDefault();
          e.stopPropagation();
          var wrapTip = btn.closest('.info-tooltip');
          if (wrapTip) wrapTip.classList.toggle('aberto');
        }
      });
      document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') {
          document.querySelectorAll('.info-tooltip.aberto').forEach(function (item) { item.classList.remove('aberto'); });
        }
      });




      // Logo com fallback caso a imagem não carregue



      ['logoLateral', 'logoCab', 'logoRodape'].forEach(function (id) {



        var box = document.getElementById(id); if (!box) return;



        var img = box.querySelector('img');



        img.addEventListener('error', function () { box.classList.add('sem-img'); });



      });







      // Menu lateral no celular



      var body = document.body, btn = document.getElementById('btnMenu');



      function menu(abrir) {



        body.classList.toggle('menu-aberto', abrir);



        btn.setAttribute('aria-expanded', abrir ? 'true' : 'false');



      }



      btn.addEventListener('click', function () { menu(!body.classList.contains('menu-aberto')); });



      document.getElementById('scrim').addEventListener('click', function () { menu(false); });



      document.addEventListener('keydown', function (e) { if (e.key === 'Escape') menu(false); });



      var links = document.querySelectorAll('.menu a');



      links.forEach(function (a) { a.addEventListener('click', function () { menu(false); }); });







      // Destaque do tópico visível no menu lateral

      var secoes = ['geral', 'area', 'produtividade', 'pecuaria', 'fertilizantes', 'nutrientes', 'combustivel', 'energia', 'praticas', 'evidencias', 'alertas']
        .map(function (id) { return document.getElementById(id); })
        .filter(Boolean);

      function marcarSecao(atual) {
        if (!atual) return;
        links.forEach(function (a) {
          if (a.id === 'linkFiltros') return;
          a.classList.toggle('ativo', a.getAttribute('href') === '#' + atual.id);
        });
      }

      function espiar() {
        if (!secoes.length) return;
        var atual = secoes[0], referencia = window.scrollY + 110;
        secoes.forEach(function (secao) { if (secao.offsetTop <= referencia) atual = secao; });
        if (atual === _secaoAtiva) return;
        _secaoAtiva = atual;
        marcarSecao(atual);
      }

      // Rolagem fluida: o realce do tópico é recalculado, no máximo, uma vez
      // por quadro e só mexe no DOM quando o tópico realmente muda — antes,
      // cada evento de rolagem recalculava o estilo da página inteira (a
      // principal causa de travamento no celular).
      var _secaoAtiva = null, _espiarAgendado = false;

      function agendarEspiar() {
        if (_espiarAgendado) return;
        _espiarAgendado = true;
        requestAnimationFrame(function () { _espiarAgendado = false; espiar(); });
      }

      window.addEventListener('scroll', agendarEspiar, { passive: true });
      window.addEventListener('resize', agendarEspiar, { passive: true });
      espiar();


      // Painel de produtividade + filtros globais (painel expansível no topo).

      // `ObterDados` é o NAMESPACE INTERNO deste JavaScript (nome estável, não é
      // o nome exibido do software): o nome da APLICAÇÃO é do SISTEMA e vem de
      // `core/config.py` (`NOME_APLICACAO`/`ROTULO_APLICACAO`), injetado no HTML
      // pelo `ReportRendering` no placeholder da marca (lateral e rodapé).
      var ObterDados = window.ObterDados = window.ObterDados || {};

      // Filtros globais. `os` e `fazenda` são GRADES de caixas de seleção —
      // guardam a LISTA de valores marcados (vazia = filtro inativo); os demais
      // são selects de valor único ('' = todos). Quem lê os filtros nunca
      // compara os valores à mão: usa `casaFiltro`/`temFiltroAtivo`, que
      // entendem os dois formatos.
      ObterDados.filtros = { os: [], fazenda: [], talhao: '', ano: '', cenario: '', cultura: '', fertilizante: '', combustivel: '', pratica: '', busca: '' };

      ObterDados.dados = [];

      ObterDados.dadosPecuaria = [];

      ObterDados.dadosFertilizantes = [];

      ObterDados.dadosNutrientes = [];

      ObterDados.dadosCombustivel = [];

      ObterDados.dadosPraticas = [];

      ObterDados.dadosEvidencias = [];

      ObterDados.faixasCobertura = [];

      ObterDados.dadosEvidenciasTipos = [];

      ObterDados._ouvintes = [];



      ObterDados.registrarDados = function (d) { ObterDados.dados = d || []; };

      ObterDados.registrarDatosPecuaria = function (d) { ObterDados.dadosPecuaria = d || []; };

      ObterDados.registrarDatosFertilizantes = function (d) { ObterDados.dadosFertilizantes = d || []; };

      ObterDados.registrarDadosEvidencias = function (d) { ObterDados.dadosEvidencias = d || []; };

      ObterDados.registrarFaixasCobertura = function (d) { ObterDados.faixasCobertura = d || []; };

      ObterDados.registrarDadosEvidenciasTipos = function (d) { ObterDados.dadosEvidenciasTipos = d || []; };

      ObterDados.registrarDatosNutrientes = function (d) { ObterDados.dadosNutrientes = d || []; };

      ObterDados.registrarDatosCombustible = function (d) { ObterDados.dadosCombustivel = d || []; };

      ObterDados.obterDados = function () { return ObterDados.dados;

      };

      ObterDados.obterDatosPecuaria = function () { return ObterDados.dadosPecuaria; };

      ObterDados.obterDatosFertilizantes = function () { return ObterDados.dadosFertilizantes; };

      ObterDados.obterDatosNutrientes = function () { return ObterDados.dadosNutrientes; };

      ObterDados.obterDatosCombustible = function () { return ObterDados.dadosCombustivel; };

      ObterDados.aoMudarFiltros = function (fn) { if (typeof fn === 'function') ObterDados._ouvintes.push(fn); };

      // ------------------------------------------------------------------
      // Painéis sob demanda: o conteúdo pesado (hierarquias, tabelas e
      // gráficos) é montado na PRIMEIRA abertura do painel, não no
      // carregamento. É o que mantém o relatório leve e fluido no celular.
      //
      // Renderização progressiva: o painel abre imediatamente e o conteúdo
      // entra em blocos, quadro a quadro (`emEtapas`) — abrir um painel nunca
      // bloqueia a interação. Cada painel devolve as suas etapas como funções.
      //
      // Gerenciamento de memória: painel recolhido libera, depois de um curto
      // período, o conteúdo que montou (`liberarPainel`); assim dois ou três
      // painéis grandes fechados não mantêm milhares de elementos vivos ao
      // mesmo tempo. Reabrir remonta o painel do zero.
      // ------------------------------------------------------------------
      ObterDados._paineis = {};

      ObterDados._liberacao = {};

      ObterDados.registrarPainel = function (id, render, liberar) {

        if (!id || typeof render !== 'function') return;

        ObterDados._paineis[id] = {

          render: render, liberar: liberar || null,
          pronto: false, conteudo: false, gerando: false, pendente: false

        };

        // Depois de montado, mudança de filtro re-renderiza só este painel —
        // também em blocos, para um filtro não congelar a página.
        ObterDados.aoMudarFiltros(function () {

          var painel = ObterDados._paineis[id];

          if (painel && painel.pronto) ObterDados.montarPainel(id);

        });

      };

      // Executa as etapas cedendo o quadro entre elas: a página continua
      // respondendo (rolagem, cliques e pintura) enquanto o painel se
      // preenche. Sempre pelo menos uma etapa por quadro, para haver avanço.
      ObterDados.emEtapas = function (etapas, aoFim) {

        var i = 0;

        function passo() {

          var inicio = Date.now();

          while (i < etapas.length && (i === 0 || Date.now() - inicio < 12)) {

            try { etapas[i](); }

            catch (exc) { if (window.console) console.error('Etapa de painel falhou', exc); }

            i++;

          }

          if (i < etapas.length) requestAnimationFrame(passo);

          else if (typeof aoFim === 'function') aoFim();

        }

        passo();

      };

      // Monta (ou remonta) o conteúdo de um painel já ativado, em blocos.
      ObterDados.montarPainel = function (id) {

        var painel = ObterDados._paineis[id];

        if (!painel) return;

        // Já há uma montagem em curso: marca e refaz no fim (filtro rápido).
        if (painel.gerando) { painel.pendente = true; return; }

        var etapas;

        try { etapas = painel.render(); }

        catch (exc) {

          if (window.console) console.error('Falha ao preparar o painel ' + id, exc);

          return;

        }

        if (typeof etapas === 'function') etapas = [etapas];

        if (!etapas || !etapas.length) return;

        painel.gerando = true;

        var secao = document.getElementById(id);

        ObterDados.emEtapas(etapas, function () {

          painel.gerando = false;

          painel.conteudo = true;

          if (secao) secao.classList.remove('painel-carregando');

          if (painel.pendente) { painel.pendente = false; ObterDados.montarPainel(id); }

        });

      };

      ObterDados.painelPronto = function (id) {

        var painel = ObterDados._paineis[id];

        return !!(painel && painel.pronto);

      };

      ObterDados.ativarPainel = function (id) {

        var painel = ObterDados._paineis[id];

        if (!painel) return;

        // Abrir cancela a liberação agendada ao recolher.
        ObterDados.cancelarLiberacao(id);

        // Conteúdo intacto: não remonta à toa.
        if (painel.pronto && painel.conteudo) return;

        painel.pronto = true;

        var secao = document.getElementById(id);

        if (secao) secao.classList.add('painel-carregando');

        // Dois quadros: o aviso "Gerando painel…" é pintado antes do trabalho
        // pesado, então abrir um painel nunca parece travamento.
        requestAnimationFrame(function () {

          requestAnimationFrame(function () { ObterDados.montarPainel(id); });

        });

      };

      // Libera o conteúdo pesado de um painel que está recolhido. Só painéis
      // que declararam como limpar (3º argumento do `registrarPainel`).
      ObterDados.liberarPainel = function (id) {

        var painel = ObterDados._paineis[id];

        if (!painel || !painel.pronto || painel.gerando) return;

        if (typeof painel.liberar !== 'function') return;

        var secao = document.getElementById(id);

        // Reaberto no meio do caminho? Não libera nada.
        if (secao && !secao.classList.contains('painel-recolhido')) return;

        try { painel.liberar(); }

        catch (exc) {

          if (window.console) console.error('Falha ao liberar o painel ' + id, exc);

          return;

        }

        painel.conteudo = false;

      };

      // Recolher só libera a memória depois de um tempo: alternar abrir/fechar
      // não remonta a tabela inteira à toa.
      ObterDados.agendarLiberacao = function (id, atraso) {

        var painel = ObterDados._paineis[id];

        if (!painel || typeof painel.liberar !== 'function') return;

        ObterDados.cancelarLiberacao(id);

        ObterDados._liberacao[id] = setTimeout(function () {

          delete ObterDados._liberacao[id];

          ObterDados.liberarPainel(id);

        }, atraso || 1500);

      };

      ObterDados.cancelarLiberacao = function (id) {

        if (ObterDados._liberacao[id]) {

          clearTimeout(ObterDados._liberacao[id]);

          delete ObterDados._liberacao[id];

        }

      };

      // ------------------------------------------------------------------
      // Tabelas agrupadas (pivôs 4.1, 5.5 e 7.4–7.8) com hierarquia sob demanda
      //
      // Cada nó (OS → Fazenda → Talhão) só tem as suas linhas criadas quando o
      // nó de cima é expandido: abrir o painel monta só o nível das OS,
      // expandir uma OS cria as fazendas dela, expandir uma fazenda cria os
      // talhões dela — nunca a base inteira de uma vez. As linhas entram em
      // lotes de 40 por quadro (a interface segue respondendo) e recolher um
      // nó esconde e devolve só a subárvore daquele nó.
      // ------------------------------------------------------------------
      ObterDados.pivotLazy = function (cfg) {

        var prefixo = cfg.prefixo;        // 'pec' | 'fert' | 'comb'
        var corpo = cfg.corpo;            // <tbody> já no documento
        var montar = cfg.linhas;          // (gid, nome, nivel, regs, temFilhos) -> html
        var LOTE = cfg.lote || 40;
        var nos = {}, seq = 0, ultima = null;

        // Só é visível a linha cujo nó e todos os ancestrais estão abertos.
        function visivel(no) {

          var pai = no.pai;

          while (pai) { if (!pai.aberto) return false; pai = pai.pai; }

          return true;

        }

        // Recolher esconde a subárvore; abrir reexibe só o que não está dentro
        // de um nó fechado. O custo é o da subárvore, não o da tabela.
        function aplicar(no) {

          var v = visivel(no), i;

          for (i = 0; i < no.proprias.length; i++) no.proprias[i].hidden = !v;

          if (no.filhos) for (i = 0; i < no.filhos.length; i++) aplicar(no.filhos[i]);

        }

        function novoNo(nome, nivel, coletar, pai, gerarFilhos) {

          seq++;

          var no = {

            gid: prefixo.charAt(0) + seq, nome: nome, nivel: nivel,
            coletar: coletar, regs: null, pai: pai, gerar: gerarFilhos || null,
            filhos: null, proprias: [], fim: null, aberto: false

          };

          nos[no.gid] = no;

          return no;

        }

        // Os registros de um nó agregado (OS, fazenda) só são reunidos quando
        // as linhas do nó são de fato escritas — nunca ao montar a estrutura.
        function registrosDe(no) {

          if (!no.regs) {

            no.regs = ((typeof no.coletar === 'function') ? no.coletar() : no.coletar) || [];

          }

          return no.regs;

        }

        // Escreve as linhas do nó depois de `apos`, em lotes por quadro.
        function inserir(no, apos, aoFim, sincrono) {

          var molde = document.createElement('tbody');

          molde.innerHTML = montar(no.gid, no.nome, no.nivel, registrosDe(no), !!no.gerar);

          var linhas = Array.prototype.slice.call(molde.children), i = 0, ref = apos;

          function lote() {

            var limite = sincrono ? linhas.length : Math.min(i + LOTE, linhas.length);

            var ocultar = !visivel(no);

            for (; i < limite; i++) {

              linhas[i].hidden = ocultar;

              if (ref) ref.insertAdjacentElement('afterend', linhas[i]);

              else corpo.appendChild(linhas[i]);

              ref = linhas[i];

              no.proprias.push(linhas[i]);

            }

            if (i < linhas.length) { requestAnimationFrame(lote); return; }

            no.fim = ref;

            // A tabela ganhou linhas: no celular os rótulos dos cartões são
            // recalculados (no desktop a função sai de imediato).
            if (typeof ObterDados.reRotular === 'function') ObterDados.reRotular(corpo);

            if (aoFim) aoFim();

          }

          lote();

        }

        // Cria os filhos do nó — uma única vez, na primeira abertura.
        function construir(no, aoFim) {

          if (no.filhos) { if (aoFim) aoFim(); return; }

          no.filhos = [];

          var descritores = [];

          try { descritores = no.gerar ? (no.gerar() || []) : []; }

          catch (exc) { if (window.console) console.error('Falha ao montar o nível ' + no.nome, exc); }

          var i = 0;

          function proximo() {

            if (i >= descritores.length) { if (aoFim) aoFim(); return; }

            var d = descritores[i++];

            var filho = novoNo(d.nome, d.nivel, d.coletar, no, d.gerarFilhos);

            no.filhos.push(filho);

            inserir(filho, no.fim, function () {

              no.fim = filho.fim;

              aplicar(filho);

              aplicar(no);

              if (i < descritores.length) requestAnimationFrame(proximo);

              else if (aoFim) aoFim();

            });

          }

          proximo();

        }

        // Expandir/recolher por delegação: vale para as linhas que já existem
        // e para as que ainda vão nascer.
        corpo.addEventListener('click', function (ev) {

          var alvo = ev.target, td = null;

          while (alvo && alvo !== corpo) {

            if (alvo.tagName === 'TD' && alvo.getAttribute('data-toggle') === '1') { td = alvo; break; }

            alvo = alvo.parentNode;

          }

          if (!td) return;

          var no = nos[td.getAttribute('data-grupo')];

          if (!no) return;

          var seta = td.querySelector('.' + prefixo + '-seta');

          if (no.aberto) {

            no.aberto = false;

            if (seta) seta.classList.remove('aberto');

            aplicar(no);

            return;

          }

          no.aberto = true;

          if (seta) seta.classList.add('aberto');

          // Primeira abertura: só agora as fazendas/talhões são criados.
          construir(no, function () { aplicar(no); });

        });

        return {

          // Nó de topo (OS) e a linha "Total geral": entram na montagem.
          raiz: function (d) {

            var no = novoNo(d.nome, d.nivel, d.coletar, null, d.gerarFilhos);

            inserir(no, ultima, function () { ultima = no.fim; aplicar(no); }, true);

            return no.gid;

          }

        };

      };

      // ------------------------------------------------------------------
      // Hierarquias expansíveis: o corpo de cada nó (fazenda/talhão) só entra no
      // documento quando o nó é aberto pela primeira vez. Até lá ele fica
      // guardado num `<template>` — o navegador não cria os elementos, não
      // calcula nem pinta o que está fechado, e abrir uma fazenda reprocessa
      // apenas a fazenda aberta. Vale para o HTML que vem do Python (2.1) e
      // para as hierarquias montadas em JavaScript (3.4, 3.5 e 8.3).
      // ------------------------------------------------------------------
      ObterDados.detailsSobDemanda = function (raiz) {

        if (!raiz || !raiz.querySelectorAll) return;

        Array.prototype.forEach.call(

          raiz.querySelectorAll('details.cons-os, details.cons-faz'),

          function (det) {

            if (det.getAttribute('data-sob-demanda') === '1') return;

            var corpo = det.querySelector(':scope > .cons-body');

            if (!corpo || !corpo.firstChild) return;

            det.setAttribute('data-sob-demanda', '1');

            // O corpo vira molde: sai da árvore visual até o primeiro clique.
            var molde = document.createElement('template');

            while (corpo.firstChild) molde.content.appendChild(corpo.firstChild);

            corpo.parentNode.insertBefore(molde, corpo.nextSibling);

            det.addEventListener('toggle', function () {

              if (!det.open || !molde.parentNode) return;

              // Repõe o corpo: só agora o navegador monta este nó.
              while (molde.content.firstChild) corpo.appendChild(molde.content.firstChild);

              molde.parentNode.removeChild(molde);

              if (typeof ObterDados.rotular === 'function') ObterDados.rotular(corpo);

            });

          }

        );

      };

      ObterDados.atualizarBadgeFiltros = atualizarBadgeFiltros;


      ObterDados.resumoFiltros = function () {

        var f = ObterDados.filtros, ativos = 0, k;

        for (k in f) { if (Object.prototype.hasOwnProperty.call(f, k) && temFiltroAtivo(f[k])) ativos++; }

        return ativos;

      };

      ObterDados._notificar = function () {

        ObterDados._ouvintes.forEach(function (fn) { try { fn(); } catch (ign) { /* painéis independentes */ } });

        atualizarBadgeFiltros();

      };



      function normValor(v) {

        return (v === null || v === undefined) ? ''

          : String(v).trim().toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');

      }

      // Um filtro pode ser LISTA (as grades de caixas de OS e Fazenda) ou valor
      // único (os selects). `valoresFiltro` devolve os valores ativos nos dois
      // formatos e `casaFiltro` responde se o valor de um registro passa pelo
      // filtro (filtro inativo casa com tudo).
      function valoresFiltro(v) {

        var lista = [], i, unico;

        if (v === null || v === undefined) return lista;

        if (Object.prototype.toString.call(v) === '[object Array]') {

          for (i = 0; i < v.length; i++) { unico = normValor(v[i]); if (unico !== '') lista.push(unico); }

          return lista;

        }

        unico = normValor(v);

        if (unico !== '') lista.push(unico);

        return lista;

      }

      function casaFiltro(valorRegistro, filtro) {

        var alvos = valoresFiltro(filtro);

        if (!alvos.length) return true;

        return alvos.indexOf(normValor(valorRegistro)) >= 0;

      }

      function temFiltroAtivo(v) { return valoresFiltro(v).length > 0; }


      function esc(v) {

        var s = (v === null || v === undefined) ? '' : String(v);

        return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

      }

      function fmtNum(v, casas) {

        if (v === null || v === undefined || isNaN(Number(v))) return '—';

        casas = casas === undefined ? 2 : casas;

        var s = Number(v).toFixed(casas), partes = s.split('.');

        partes[0] = partes[0].replace(/\B(?=(\d{3})+(?!\d))/g, '.');

        return partes.length === 2 ? partes[0] + ',' + partes[1] : partes[0];

      }

      // Conversão numérica tolerante usada pelos painéis (produtividade,
      // pecuária, fertilizantes e combustível). Fica no escopo comum para que
      // todos os IIFEs de painel possam reutilizá-la.
      function num(v) {

        if (v === null || v === undefined || v === '') return NaN;

        var n = Number(v);

        return isNaN(n) ? NaN : n;

      }

      // Cor de fundo da cobertura de EVIDÊNCIA (%) a partir das faixas de
      // `core/config.py` (serializadas no HTML como `configCobertura`):
      // [[mínimo, máximo, cor], ...], com o máximo EXCLUSIVO. Fica no escopo
      // comum porque a régua é a MESMA no 5.1 (cobertura por fertilizante) e no
      // 7.1 (cobertura por combustível/fonte).
      function corCobertura(pct) {

        var faixas = ObterDados.faixasCobertura || [], i, f;

        for (i = 0; i < faixas.length; i++) {

          f = faixas[i];

          if (pct >= f[0] && pct < f[1]) return 'cov-' + f[2];

        }

        return '';

      }

      // Unidade que AINDA precisa ser anexada ao rótulo da cultura. O payload
      // do 3.x já sufixa a unidade nas formas de produção que NÃO medem a área
      // da cultura (`Aroeira (m³/ha)`, `Eucalipto (m³/ha)`), e a MESMA unidade
      // viaja no campo `unidade`. Sem esta checagem o cabeçalho do 3.4 saía com
      // a unidade duas vezes (`Aroeira (m³/ha) (m³/ha)`) e, com vários anos, o
      // rótulo quebrava em duas linhas e ficava encavalado. Devolve '' quando o
      // rótulo já termina em `(unidade)` e a própria unidade quando não termina.
      function unidadeDoRotulo(cultura, unidade) {

        var u = (unidade === null || unidade === undefined) ? '' : String(unidade).trim();

        if (!u) return '';

        var nome = (cultura === null || cultura === undefined) ? '' : String(cultura).trim();

        var fim = '(' + u + ')';

        return nome.slice(-fim.length).toLowerCase() === fim.toLowerCase() ? '' : u;

      }

      // ------------------------------------------------------------------
      // PALETA PADRÃO DOS GRÁFICOS (20 cores) — fonte ÚNICA das cores das séries
      // de TODOS os gráficos de linhas do relatório (3.2, 3.3, 3.8, 4.2,
      // 5.2–5.4, 7.2/7.3 e 8.2) e também dos chips de atividade do 3.6.
      //
      // Critério: primárias (vermelho, azul, amarelo) + secundárias (verde,
      // laranja, roxo) + variações claras/escuras (azul claro, verde claro,
      // verde lima, ciano, turquesa, rosa, violeta, magenta, verde escuro, azul
      // escuro) + neutros (branco, cinza claro, cinza escuro, preto).
      // A ORDEM é a do contraste no fundo escuro do relatório: as primeiras são
      // as mais visíveis, então um gráfico com poucas séries nunca cai no
      // preto/cinza escuro — que só aparecem quando a paleta já foi usada
      // (a distribuição NÃO repete cor enquanto houver cor livre).
      // ------------------------------------------------------------------
      ObterDados.CORES = [
        '#38bdf8',  //  1 azul claro
        '#4ade80',  //  2 verde claro
        '#facc15',  //  3 amarelo (primária)
        '#fb923c',  //  4 laranja (secundária)
        '#22d3ee',  //  5 ciano
        '#f472b6',  //  6 rosa
        '#a3e635',  //  7 verde lima
        '#a78bfa',  //  8 violeta
        '#e879f9',  //  9 magenta
        '#2dd4bf',  // 10 turquesa
        '#ef4444',  // 11 vermelho (primária)
        '#2563eb',  // 12 azul (primária)
        '#16a34a',  // 13 verde (secundária)
        '#7e22ce',  // 14 roxo (secundária)
        '#166534',  // 15 verde escuro
        '#1e40af',  // 16 azul escuro
        '#cbd5e1',  // 17 cinza claro
        '#334155',  // 18 cinza escuro
        '#ffffff',  // 19 branco
        '#000000'   // 20 preto
      ];

      // Cores de papel FIXO nos gráficos — saem da PRÓPRIA paleta, para não
      // existir uma segunda família de cores no relatório. As séries que as
      // usam ficam RESERVADAS: `coresDasSeries` não as entrega a mais ninguém.
      ObterDados.COR_REFERENCIA = '#cbd5e1';  // linha de base tracejada (área física)
      ObterDados.COR_TOTAL = '#ffffff';       // linha do Total (3.2)
      ObterDados.COR_PECUARIA = '#2dd4bf';    // série Pecuária do 3.2 (não é cultura)
      ObterDados.COR_ENERGIA = '#38bdf8';     // energia elétrica (kWh) dos 7.2/7.3

      // As primeiras `total` cores da paleta a partir da posição `inicio`.
      ObterDados.coresDaPaleta = function (total, inicio) {
        var lista = ObterDados.CORES, i, idx = (inicio || 0) % lista.length;
        var out = [];
        for (i = 0; i < (total || lista.length); i++) {
          out.push(lista[idx]);
          idx = (idx + 1) % lista.length;
        }
        return out;
      };

      // Índice da cor a usar numa série: percorre a paleta a partir de
      // `idxInicial` e devolve a PRIMEIRA cor livre. Se a paleta acabou (mais
      // séries que cores), a repetição é inevitável — e então ela recomeça pela
      // cor mais visível da paleta, NUNCA caindo numa cor RESERVADA (papel
      // fixo: referência, Total, Pecuária, energia, preto/cinza escuro).
      ObterDados.escolherCor = function (lista, usadas, idxInicial, reserva) {
        var passo, inicio = (((idxInicial || 0) % lista.length) + lista.length)
          % lista.length;
        for (passo = 0; passo < lista.length; passo++) {
          if (!usadas[lista[(inicio + passo) % lista.length]]) {
            return (inicio + passo) % lista.length;
          }
        }
        for (passo = 0; passo < lista.length; passo++) {
          if (!(reserva || {})[lista[passo]]) return passo;
        }
        return inicio;
      };

      // Cor de cada série, SEM REPETIR enquanto houver cor livre: percorre a
      // paleta a partir de `inicio` (0 por padrão) e pula as cores de
      // `reservadas` (as séries de cor fixa). Com mais séries que cores, a
      // repetição recomeça pelas cores mais visíveis (ver `escolherCor`).
      ObterDados.coresDasSeries = function (nomes, reservadas, inicio) {
        var lista = ObterDados.CORES, usadas = {}, reserva = {}, cor = {}, i, idx;
        (reservadas || []).forEach(function (c) {
          if (c) { usadas[c] = 1; reserva[c] = 1; }
        });
        nomes = nomes || [];
        for (i = 0; i < nomes.length; i++) {
          idx = ObterDados.escolherCor(lista, usadas, (inicio || 0) + i, reserva);
          usadas[lista[idx]] = 1;
          cor[nomes[i]] = lista[idx];
        }
        return cor;
      };

      // Cor de cada série de um gráfico a partir da lista de séries do
      // renderizador: as séries que já declaram `cor` (papel fixo — Total, Área
      // física, Pecuária, energia) ficam RESERVADAS e as demais saem na paleta
      // padrão, sem repetir cor enquanto houver cor livre.
      ObterDados.coresDasSeriesDoGrafico = function (series) {
        var cor = {}, reservadas = [], livres = [];
        (series || []).forEach(function (s) {
          if (s.cor) { cor[s.nome] = s.cor; reservadas.push(s.cor); }
          else { livres.push(s.nome); }
        });
        var atribuidas = ObterDados.coresDasSeries(livres, reservadas);
        livres.forEach(function (n) { cor[n] = atribuidas[n]; });
        return cor;
      };

      // Valores distintos de uma chave numa LISTA de registros, ordenados
      // (pt-BR, numérico) — é a fonte das opções dos filtros.
      function valoresUnicos(lista, chave) {

        var mapa = {}, chaves = [];

        (lista || []).forEach(function (linha) {

          var v = linha[chave];

          if (v !== null && v !== undefined && String(v).trim() !== '' && !(String(v) in mapa)) {

            mapa[String(v)] = 1; chaves.push(String(v));

          }

        });

        return chaves.sort(function (a, b) { return a.localeCompare(b, 'pt-BR', { numeric: true }); });

      }

      // Valores distintos da base completa de registros.
      function coletarUnicos(chave) {

        return valoresUnicos(ObterDados.dados, chave);

      }

      function preencherSelect(select, valores) {

        var primeiro = select.options[0].outerHTML;

        select.innerHTML = primeiro + valores.map(function (v) {

          return '<option value="' + esc(v) + '">' + esc(v) + '</option>';

        }).join('');

      }

      function filtrarDados() {

        var f = ObterDados.filtros, busca = normValor(f.busca);

        var chaves = ['os', 'fazenda', 'talhao', 'ano', 'cenario', 'cultura'];

        return ObterDados.dados.filter(function (r) {

          for (var i = 0; i < chaves.length; i++) {

            if (!casaFiltro(r[chaves[i]], f[chaves[i]])) return false;

          }

          if (busca && normValor(JSON.stringify(r)).indexOf(busca) < 0) return false;

          return true;

        });

      }



      function atualizarBadgeFiltros() {

        var n = ObterDados.resumoFiltros();

        var badge = document.getElementById('filtrosBadge');

        var contagem = document.getElementById('filtrosContagem');

        if (badge) { badge.textContent = String(n); badge.hidden = n === 0; }

        if (contagem) contagem.textContent = n === 0 ? '0 filtros ativos' : (n + (n === 1 ? ' filtro ativo' : ' filtros ativos'));

      }



      var painelFiltros = document.getElementById('filtros');
      var overlayFiltros = document.getElementById('filtrosOverlay');
      var btnFiltros = document.getElementById('btnFiltros');
      var linkFiltros = document.getElementById('linkFiltros');
      var recolherFiltros = document.getElementById('recolherFiltros');
      var ultimoAcionadorFiltros = null;

      function abrirPainelFiltros(acionador) {
        if (!painelFiltros) return;
        ultimoAcionadorFiltros = acionador || document.activeElement;
        painelFiltros.hidden = false;
        if (overlayFiltros) { overlayFiltros.hidden = false; overlayFiltros.setAttribute('aria-hidden', 'false'); }
        document.body.classList.add('filtros-abertos');
        if (btnFiltros) btnFiltros.setAttribute('aria-expanded', 'true');
        requestAnimationFrame(function () {
          var primeiroCampo = painelFiltros.querySelector('[data-filtro], [data-filtro-check]');
          if (primeiroCampo) primeiroCampo.focus({ preventScroll: true });
        });
      }

      function fecharPainelFiltros(devolverFoco) {
        if (!painelFiltros || painelFiltros.hidden) return;
        painelFiltros.hidden = true;
        if (overlayFiltros) { overlayFiltros.hidden = true; overlayFiltros.setAttribute('aria-hidden', 'true'); }
        document.body.classList.remove('filtros-abertos');
        if (btnFiltros) btnFiltros.setAttribute('aria-expanded', 'false');
        if (devolverFoco !== false && ultimoAcionadorFiltros && typeof ultimoAcionadorFiltros.focus === 'function') {
          ultimoAcionadorFiltros.focus({ preventScroll: true });
        }
      }

      function alternarPainelFiltros(acionador) {
        if (!painelFiltros) return;
        if (painelFiltros.hidden) abrirPainelFiltros(acionador);
        else fecharPainelFiltros();
      }

      if (btnFiltros) btnFiltros.addEventListener('click', function () { alternarPainelFiltros(btnFiltros); });
      if (linkFiltros) linkFiltros.addEventListener('click', function (e) { e.preventDefault(); abrirPainelFiltros(linkFiltros); });
      if (recolherFiltros) recolherFiltros.addEventListener('click', function () { fecharPainelFiltros(); });
      if (overlayFiltros) overlayFiltros.addEventListener('click', function () { fecharPainelFiltros(); });
      document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && painelFiltros && !painelFiltros.hidden) fecharPainelFiltros();
      });

      (function iniciarObterDados() {

        var script = document.getElementById('dadosProdutividade');

        var wrap = document.getElementById('prodTabelaWrap');

        var vazio = document.getElementById('prodVazio');

        var resumo = document.getElementById('prodResumo');

        var mediaBox = document.getElementById('prodMedia');

        var culturasBox = document.getElementById('prodCulturas');

        var painelCulturas = document.getElementById('prodPainelCulturas');

        var wrapAreaLinhas = document.getElementById('prodAreaLinhas');

        var leyendaAreaLinhas = document.getElementById('prodAreaLeyenda');

        var wrapProdLinhas = document.getElementById('prodProdLinhas');

        var leyendaProdLinhas = document.getElementById('prodProdLeyenda');

        var areaOcultas = {}, prodOcultas = {};

        var cropSeq = 0;

        var wrapAreaCultura = document.getElementById('prodAreaCulturaWrap');

        var vazioAreaCultura = document.getElementById('prodAreaCulturaVazio');

        var ativTabla = document.getElementById('ativTabla');

        var ativVazio = document.getElementById('ativVazio');

        var wrapMatrizCultura = document.getElementById('prodMatrizCulturaWrap');

        var vazioMatrizCultura = document.getElementById('prodMatrizCulturaVazio');

        var wrapAtivLinhas = document.getElementById('ativAreaLinhas');

        var leyendaAtivLinhas = document.getElementById('ativAreaLeyenda');

        var scriptPec = document.getElementById('dadosPecuaria');

        var tablaPec = document.getElementById('pecTabla');

        var vazioPec = document.getElementById('pecVazio');

        var resumoPec = document.getElementById('pecResumo');

        var wrapPecEvol = document.getElementById('pecEvolLinhas');

        var leyendaPecEvol = document.getElementById('pecEvolLeyenda');

        var ocultasPecEvol = {};

        var resumoFert = document.getElementById('fertResumo');

        var tablaFert = document.getElementById('fertTabla');

        var wrapFert = document.getElementById('fertTabelaWrap');

        var vazioFert = document.getElementById('fertVazio');

        var wrapFertTotais = document.getElementById('fertTotaisLinhas');

        var leyendaFertTotais = document.getElementById('fertTotaisLeyenda');

        var wrapFertArea = document.getElementById('fertAreaLinhas');

        var leyendaFertArea = document.getElementById('fertAreaLeyenda');

        var wrapFertDose = document.getElementById('fertDoseLinhas');

        var leyendaFertDose = document.getElementById('fertDoseLeyenda');

        var fertTotaisOcultas = {}, fertAreaOcultas = {}, fertDoseOcultas = {};

        var scriptComb = document.getElementById('dadosCombustivel');

        var resumoComb = document.getElementById('combResumo');

        var painelComb = document.getElementById('combPainel');

        var tablaComb = document.getElementById('combTabla');

        var wrapComb = document.getElementById('combTabelaWrap');

        var vazioComb = document.getElementById('combVazio');

        if (!script) {

          if (wrap) wrap.innerHTML = '<p class="muted">Relatório sem dados de produtividade.</p>';

        }

        var crudos = [];

        try { crudos = JSON.parse(script.textContent || '[]'); } catch (ign) { crudos = []; }

        ObterDados.registrarDados(Array.isArray(crudos) ? crudos : []);

        var crudosPec = [];

        if (scriptPec) {

          try { crudosPec = JSON.parse(scriptPec.textContent || '[]'); } catch (ign) { crudosPec = []; }

        }

        ObterDados.registrarDatosPecuaria(Array.isArray(crudosPec) ? crudosPec : []);

        var scriptFert = document.getElementById('dadosFertilizantes');

        var crudosFert = [];

        if (scriptFert) {

          try { crudosFert = JSON.parse(scriptFert.textContent || '[]'); } catch (ign) { crudosFert = []; }

        }

        ObterDados.registrarDatosFertilizantes(Array.isArray(crudosFert) ? crudosFert : []);

        var scriptEvidencias = document.getElementById('dadosEvidencias');

        var crudosEvidencias = [];

        if (scriptEvidencias) {

          try { crudosEvidencias = JSON.parse(scriptEvidencias.textContent || '[]'); } catch (ign) { crudosEvidencias = []; }

        }

        ObterDados.registrarDadosEvidencias(Array.isArray(crudosEvidencias) ? crudosEvidencias : []);

        var scriptCobertura = document.getElementById('configCobertura');

        var crudosCobertura = [];

        if (scriptCobertura) {

          try { crudosCobertura = JSON.parse(scriptCobertura.textContent || '[]'); } catch (ign) { crudosCobertura = []; }

        }

        ObterDados.registrarFaixasCobertura(Array.isArray(crudosCobertura) ? crudosCobertura : []);

        var scriptEvidenciasTipos = document.getElementById('dadosEvidenciasTipos');

        var crudosEvidenciasTipos = [];

        if (scriptEvidenciasTipos) {

          try { crudosEvidenciasTipos = JSON.parse(scriptEvidenciasTipos.textContent || '[]'); } catch (ign) { crudosEvidenciasTipos = []; }

        }

        ObterDados.registrarDadosEvidenciasTipos(Array.isArray(crudosEvidenciasTipos) ? crudosEvidenciasTipos : []);

        var scriptNutri = document.getElementById('dadosNutrientes');

        var crudosNutri = [];

        if (scriptNutri) {

          try { crudosNutri = JSON.parse(scriptNutri.textContent || '[]'); } catch (ign) { crudosNutri = []; }

        }

        ObterDados.registrarDatosNutrientes(Array.isArray(crudosNutri) ? crudosNutri : []);

        var crudosComb = [];

        if (scriptComb) {

          try { crudosComb = JSON.parse(scriptComb.textContent || '[]'); } catch (ign) { crudosComb = []; }

        }

        ObterDados.registrarDatosCombustible(Array.isArray(crudosComb) ? crudosComb : []);

        var combSelect = document.getElementById('filtroCombustivel');

        if (combSelect) {

          var combMapa = {}, combLista = [], iComb, vComb;

          for (iComb = 0; iComb < ObterDados.dadosCombustivel.length; iComb++) {

            vComb = ObterDados.dadosCombustivel[iComb].combustivel;

            if (vComb !== null && vComb !== undefined && String(vComb).trim() !== '' && !(String(vComb) in combMapa)) {

              combMapa[String(vComb)] = 1; combLista.push(String(vComb));

            }

          }

          preencherSelect(combSelect, combLista.sort(function (a, b) {

            return a.localeCompare(b, 'pt-BR', { numeric: true });

          }));

        }

        var fertSelect = document.getElementById('filtroFertilizante');

        if (fertSelect) {

          var fertMapa = {}, fertLista = [], iFert, vFert;

          for (iFert = 0; iFert < ObterDados.dadosFertilizantes.length; iFert++) {

            vFert = ObterDados.dadosFertilizantes[iFert].fertilizante;

            if (vFert !== null && vFert !== undefined && String(vFert).trim() !== '' && !(String(vFert) in fertMapa)) {

              fertMapa[String(vFert)] = 1; fertLista.push(String(vFert));

            }

          }

          preencherSelect(fertSelect, fertLista.sort(function (a, b) {

            return a.localeCompare(b, 'pt-BR', { numeric: true });

          }));

        }



        // ------------------------------------------------------------------
        // GRADES de caixas de seleção (OS e Fazenda) e a CASCATA dos demais filtros
        //
        // OS e Fazenda deixaram de ser lista de opção única: são GRADES de
        // checkboxes com o botão "Selecionar todos" (que alterna para
        // "Desmarcar todos"). Marcar/desmarcar reconstrói o relatório: os
        // painéis releem `ObterDados.filtros` e os demais filtros (Talhão, Ano,
        // Cenário, Cultura, Fertilizante, Combustível/Energia e Prática de solo)
        // são refeitos a partir do recorte de OS + Fazenda — a opção que não
        // existe no recorte some da lista (ex.: ano que não aparece na OS
        // marcada) e o valor escolhido que saiu do recorte volta para "todos".
        // ------------------------------------------------------------------
        var GRUPOS_GRADE = ['os', 'fazenda'];
        var SELECTS_CASCATA = [
          ['filtroTalhao', 'talhao'], ['filtroAno', 'ano'],
          ['filtroCenario', 'cenario'], ['filtroCultura', 'cultura']
        ];
        var SELECTS_CASCATA_PAYLOAD = [
          ['filtroFertilizante', 'fertilizante', 'dadosFertilizantes'],
          ['filtroCombustivel', 'combustivel', 'dadosCombustivel'],
          ['filtroPratica', 'pratica', 'dadosPraticas']
        ];

        function gradeDe(grupo) {

          return document.querySelector('[data-filtro-grade="' + grupo + '"]');

        }

        function caixasDaGrade(grupo) {

          var grade = gradeDe(grupo);

          return grade ? grade.querySelectorAll('input[type="checkbox"]') : [];

        }

        function valoresMarcados(grupo) {

          var caixas = caixasDaGrade(grupo), i, valores = [];

          for (i = 0; i < caixas.length; i++) { if (caixas[i].checked) valores.push(caixas[i].value); }

          return valores;

        }

        function marcarCaixas(grupo, marcado) {

          var caixas = caixasDaGrade(grupo), i;

          for (i = 0; i < caixas.length; i++) { caixas[i].checked = !!marcado; }

        }

        // Os demais filtros começam listando a base inteira; a CASCATA (que
        // reescreve as listas a partir do recorte) só entra quando há grade
        // marcada — ver `atualizarCascata`.
        [['filtroTalhao', 'talhao'], ['filtroAno', 'ano'],

        ['filtroCenario', 'cenario'], ['filtroCultura', 'cultura']

        ].forEach(function (par) {

          var el = document.getElementById(par[0]);

          if (el) preencherSelect(el, valoresUnicos(ObterDados.dados, par[1]));

        });



        function gradeTodaMarcada(grupo) {

          var caixas = caixasDaGrade(grupo), i;

          if (!caixas.length) return false;

          for (i = 0; i < caixas.length; i++) { if (!caixas[i].checked) return false; }

          return true;

        }

        function atualizarBotaoGrade(grupo) {

          var btn = document.querySelector('[data-todos="' + grupo + '"]');

          if (!btn) return;

          btn.textContent = gradeTodaMarcada(grupo) ? 'Desmarcar todos' : 'Selecionar todos';

        }

        // Desenha a grade com TODOS os valores da base, preservando o que já
        // estava marcado (quem chama é o wiring das grades, mais abaixo).
        function renderGrade(grupo, valores, marcados) {

          var grade = gradeDe(grupo), mapa = {}, i;

          if (!grade) return;

          for (i = 0; i < (marcados || []).length; i++) { mapa[normValor(marcados[i])] = 1; }

          grade.innerHTML = valores.length ? valores.map(function (v) {

            return '<label class="filtro-check"><input' + (mapa[normValor(v)] ? ' checked' : '') +
              ' data-filtro-check="' + grupo + '" type="checkbox" value="' + esc(v) + '"/>' +
              '<span title="' + esc(v) + '">' + esc(v) + '</span></label>';

          }).join('') : '<span class="muted">Nenhum valor encontrado.</span>';

          atualizarBotaoGrade(grupo);

        }

        // Registros que passam pelas GRADES (OS + Fazenda): é o recorte que
        // reconstrói os demais filtros.
        function recorteDasGrades(lista) {

          return (lista || []).filter(function (r) {

            return casaFiltro(r.os, ObterDados.filtros.os) && casaFiltro(r.fazenda, ObterDados.filtros.fazenda);

          });

        }

        // Ordem ATUAL das opções (fora a primeira, que é o "todos"): preservá-la
        // mantém a ordem canônica de cada filtro (o de Prática de solo, por
        // exemplo) depois da cascata; o valor que aparece pela primeira vez vai
        // para o fim, em pt-BR.
        function ordemAtualSelect(select) {

          var ordem = {}, i, v;

          if (!select) return ordem;

          for (i = 1; i < select.options.length; i++) {

            v = String(select.options[i].value);

            if (!(v in ordem)) ordem[v] = i;

          }

          return ordem;

        }

        // Refaz a lista de um select a partir do recorte, preservando a escolha
        // atual quando ela continua existindo (senão volta para "todos").
        function refazerSelect(select, chave, valores) {

          var atual, manter = '', i, lista, ordem;

          if (!select) return;

          atual = String(select.value);

          ordem = ordemAtualSelect(select);

          lista = valores.slice().sort(function (a, b) {

            var oa = ordem[String(a)], ob = ordem[String(b)];

            if (oa !== undefined && ob !== undefined) return oa - ob;

            if (oa !== undefined) return -1;

            if (ob !== undefined) return 1;

            return String(a).localeCompare(String(b), 'pt-BR', { numeric: true });

          });

          for (i = 0; i < lista.length; i++) { if (String(lista[i]) === atual) { manter = lista[i]; break; } }

          preencherSelect(select, lista);

          select.value = manter;

          ObterDados.filtros[chave] = manter;

        }

        function atualizarCascata() {

          var base = recorteDasGrades(ObterDados.dados);

          SELECTS_CASCATA.forEach(function (par) {

            refazerSelect(document.getElementById(par[0]), par[1], valoresUnicos(base, par[1]));

          });

          SELECTS_CASCATA_PAYLOAD.forEach(function (par) {

            refazerSelect(document.getElementById(par[0]), par[1],
              valoresUnicos(recorteDasGrades(ObterDados[par[2]]), par[1]));

          });

        }

        // Toda mudança na grade grava a lista marcada, refaz a cascata e avisa os
        // painéis (o relatório é reconstruído a cada filtro).
        function aoMudarGrade(grupo) {

          ObterDados.filtros[grupo] = valoresMarcados(grupo);

          atualizarBotaoGrade(grupo);

          atualizarCascata();

          ObterDados._notificar();

        }

        GRUPOS_GRADE.forEach(function (grupo) {

          var grade = gradeDe(grupo);

          if (grade) grade.addEventListener('change', function () { aoMudarGrade(grupo); });

          var btn = document.querySelector('[data-todos="' + grupo + '"]');

          if (btn) btn.addEventListener('click', function () {

            marcarCaixas(grupo, !gradeTodaMarcada(grupo));

            aoMudarGrade(grupo);

          });

          renderGrade(grupo, coletarUnicos(grupo), ObterDados.filtros[grupo]);

        });

        document.querySelectorAll('#filtros [data-filtro]').forEach(function (el) {

          el.addEventListener(el.tagName === 'INPUT' ? 'input' : 'change', function () {

            ObterDados.filtros[el.getAttribute('data-filtro')] = el.value;

            ObterDados._notificar();

          });

        });

        var limpar = document.getElementById('limparFiltros');

        if (limpar) limpar.addEventListener('click', function () {

          var f = ObterDados.filtros, k;

          for (k in f) { if (Object.prototype.hasOwnProperty.call(f, k)) f[k] = ''; }

          document.querySelectorAll('#filtros [data-filtro]').forEach(function (el) { el.value = ''; });

          GRUPOS_GRADE.forEach(function (grupo) {

            f[grupo] = [];

            marcarCaixas(grupo, false);

            atualizarBotaoGrade(grupo);

          });

          // Sem grade marcada, os selects voltam a listar tudo.
          atualizarCascata();

          ObterDados._notificar();

        });



        function renderCulturas() {

          if (!culturasBox) return;

          var culturas = coletarUnicos('cultura');

          culturasBox.innerHTML = culturas.length

            ? culturas.map(function (c) { return '<span class="prod-cultura">' + esc(c) + '</span>'; }).join('')

            : '<span class="muted">Nenhuma cultura encontrada.</span>';

        }
/* ----- Painel por cultura: área (ha) y productividad por año -----
           Agregación por fazenda + consolidado; sin distinción por OS
           ni por talhão. La productividad agregada es la media ponderada
           por la área de la cultura (fallback: media simple). */
        function prodCelda(c) {
          if (!c) return null;
          if (c.waArea > 0) return c.wa / c.waArea;
          if (c.n > 0) return c.sum / c.n;
          return null;
        }

        function nuevaCelda() {
          return { area: 0, wa: 0, waArea: 0, sum: 0, n: 0 };
        }

        function painelCulturaHTML(cultura, unidade, linhas) {
          var anos = {}, fazList = [], porFaz = {}, cons = {}, i, r;

          function acum(c, area, prod) {
            if (!isNaN(area)) c.area += area;
            if (!isNaN(prod)) {
              if (!isNaN(area) && area > 0) { c.wa += prod * area; c.waArea += area; }
              else { c.sum += prod; c.n++; }
            }
          }

          for (i = 0; i < linhas.length; i++) {
            r = linhas[i];
            var anF = String(r.ano || '').trim();
            anF = anF === '' ? '—' : anF;
            anos[anF] = 1;
            var faz = String(r.fazenda || '').trim();
            faz = faz === '' ? '—' : faz;
            if (!porFaz[faz]) { porFaz[faz] = {}; fazList.push(faz); }
            if (!cons[anF]) cons[anF] = nuevaCelda();
            if (!porFaz[faz][anF]) porFaz[faz][anF] = nuevaCelda();
            var area = num(r.area), prod = num(r.produtividade);
            acum(cons[anF], area, prod);
            acum(porFaz[faz][anF], area, prod);
          }

          var anosArr = Object.keys(anos).sort(function (a, b) {
            var x = Number(a), y = Number(b);
            if (isNaN(x)) return 1;
            if (isNaN(y)) return -1;
            return x - y;
          });
          fazList.sort(function (a, b) { return a.localeCompare(b, 'pt-BR', { numeric: true }); });

          function encabezado() {
            return '<tr><th scope="col">Fazenda</th>' +
              anosArr.map(function (an) { return '<th scope="col">' + esc(an) + '</th>'; }).join('') + '</tr>';
          }

          function fila(nombre, cls, obtener) {
            var celdas = anosArr.map(function (an) {
              var v = obtener(an);
              return v === null ? '<td class="crop-sem-valor">—</td>' : '<td>' + fmtNum(v) + '</td>';
            }).join('');
            return '<tr' + (cls ? ' class="' + cls + '"' : '') + '><th scope="row">' + esc(nombre) + '</th>' + celdas + '</tr>';
          }

          function areaCons(an) { var c = cons[an]; return c && c.area > 0 ? c.area : null; }
          function areaFaz(fz, an) { var c = porFaz[fz][an]; return c && c.area > 0 ? c.area : null; }
          function prodCons(an) { return prodCelda(cons[an]); }
          function prodFaz(fz, an) { return prodCelda(porFaz[fz][an]); }

          var temArea = anosArr.some(function (an) { return areaCons(an) !== null; });
          var temProd = anosArr.some(function (an) { return prodCons(an) !== null; });
          if (!temArea && !temProd) return null;

          var idBase = 'cropc' + (cropSeq++);
          var chips = '<div class="prod-crop-chips" role="group" aria-label="Série dos gráficos de ' + esc(cultura) + '">' +
            '<button type="button" class="prod-crop-chip active" data-faz="" aria-pressed="true">Consolidado (todas)</button>' +
            fazList.map(function (fz) {
              return '<button type="button" class="prod-crop-chip" data-faz="' + esc(fz) + '" aria-pressed="false">' + esc(fz) + '</button>';
            }).join('') + '</div>';

          var rowsArea = temArea
            ? fila('Consolidado (todas as fazendas)', 'total', areaCons) +
              fazList.map(function (fz) { return fila(fz, '', function (an) { return areaFaz(fz, an); }); }).join('')
            : '';
          var rowsProd = temProd
            ? fila('Consolidado (todas as fazendas)', 'total', prodCons) +
              fazList.map(function (fz) { return fila(fz, '', function (an) { return prodFaz(fz, an); }); }).join('')
            : '';

          var cuerpo = chips;
          if (temArea) {
            cuerpo += '<h5>Área (ha) — evolução por ano</h5>' +
              '<div class="prod-crop-grafico" id="' + idBase + '-area"></div>' +
              '<div class="prod-crop-tabla"><table><thead>' + encabezado() + '</thead><tbody>' + rowsArea + '</tbody></table></div>';
          }
          if (temProd) {
            cuerpo += '<h5>Produtividade ' + (unidade ? '(' + esc(unidade) + ') ' : '') + '— evolução por ano</h5>' +
              '<div class="prod-crop-grafico" id="' + idBase + '-prod"></div>' +
              '<div class="prod-crop-tabla"><table><thead>' + encabezado() + '</thead><tbody>' + rowsProd + '</tbody></table></div>';
          }
          cuerpo += '<div class="prod-crop-nota tooltip-nota"><span class="info-tooltip"><button type="button" class="info-tooltip-btn" aria-label="Ver descrição">i</button><span class="info-tooltip-box" role="tooltip">Sem distinção por OS nem por talhão. A produtividade é a média ponderada pela área da cultura; quando falta a área usa-se a média simples dos registros.</span></span></div>';

          var html = '<details class="prod-crop"><summary>' +
            '<span class="prod-crop-titulo">' + esc(cultura) + '</span>' +
            (unidadeDoRotulo(cultura, unidade) ? '<small class="prod-unidade"> (' + esc(unidade) + ')</small>' : '') +
            '</summary><div class="prod-crop-cuerpo">' + cuerpo + '</div></details>';

          return { html: html, idBase: idBase, cultura: cultura, anosArr: anosArr, cons: cons, porFaz: porFaz };
        }

        function gridSVG(M, max, ph, baseY, W) {
          var refs = [0, .25, .5, .75, 1], html = '', g, vg, yg;
          for (g = 0; g < refs.length; g++) {
            vg = max * refs[g];
            yg = baseY - ph * refs[g];
            html += '<line x1="' + M.l + '" y1="' + yg + '" x2="' + (W - M.r) + '" y2="' + yg +
              '" stroke="var(--borda)" stroke-width="1" stroke-dasharray="3 4" opacity=".7"/>';
            html += '<text x="' + (M.l - 6) + '" y="' + (yg + 3.5) + '" text-anchor="end" font-size="9" fill="var(--texto-suave)">' + fmtNum(vg, 1) + '</text>';
          }
          return html;
        }

        function graficoBarrasSVG(anosArr, obtener, colorVar, titulo) {
          var W = 560, H = 180, M = { t: 20, r: 10, b: 28, l: 52 };
          var pw = W - M.l - M.r, ph = H - M.t - M.b;
          var datos = anosArr.map(function (an) { return { an: an, v: obtener(an) }; });
          var max = 0, i;
          for (i = 0; i < datos.length; i++) if (datos[i].v !== null && datos[i].v > max) max = datos[i].v;
          if (max === 0) return '<p class="prod-crop-vacio">Sem dados para esta série.</p>';
          var baseY = M.t + ph;
          var html = '<svg viewBox="0 0 ' + W + ' ' + H + '" role="img" aria-label="' + esc(titulo) + '">' + gridSVG(M, max, ph, baseY, W);
          var step = pw / Math.max(1, datos.length);
          var bw = Math.min(34, Math.max(10, step * .6));
          var xCentro = M.l + step / 2;
          for (i = 0; i < datos.length; i++) {
            var d = datos[i];
            var x = xCentro + i * step;
            html += '<text x="' + x + '" y="' + (baseY + 15) + '" text-anchor="middle" font-size="9" fill="var(--texto-suave)">' + esc(String(d.an)) + '</text>';
            if (d.v === null) continue;
            var bh = (d.v / max) * ph;
            html += '<rect x="' + (x - bw / 2) + '" y="' + (baseY - bh) + '" width="' + bw + '" height="' + bh +
              '" rx="2" fill="' + colorVar + '" opacity=".9"/>';
            html += '<text x="' + x + '" y="' + (baseY - bh - 4) + '" text-anchor="middle" font-size="9" fill="var(--texto)">' + fmtNum(d.v, 1) + '</text>';
          }
          html += '</svg>';
          return html;
        }

        function graficoLineasSVG(anosArr, obtener, colorVar, titulo) {
          var W = 560, H = 180, M = { t: 20, r: 10, b: 28, l: 52 };
          var pw = W - M.l - M.r, ph = H - M.t - M.b;
          var datos = anosArr.map(function (an) { return { an: an, v: obtener(an) }; });
          var max = 0, i;
          for (i = 0; i < datos.length; i++) if (datos[i].v !== null && datos[i].v > max) max = datos[i].v;
          if (max === 0) return '<p class="prod-crop-vacio">Sem dados para esta série.</p>';
          var baseY = M.t + ph;
          function xPos(i) { return M.l + (i + .5) * (pw / Math.max(1, datos.length)); }
          function yPos(v) { return baseY - (v / max) * ph; }
          var html = '<svg viewBox="0 0 ' + W + ' ' + H + '" role="img" aria-label="' + esc(titulo) + '">' + gridSVG(M, max, ph, baseY, W);
          var seg = '', pts = 0;
          for (i = 0; i < datos.length; i++) {
            var d = datos[i];
            var x = xPos(i);
            html += '<text x="' + x + '" y="' + (baseY + 15) + '" text-anchor="middle" font-size="9" fill="var(--texto-suave)">' + esc(String(d.an)) + '</text>';
            if (d.v === null) {
              if (pts > 1) {
                html += '<polyline points="' + seg.trim() + '" fill="none" stroke="' + colorVar + '" stroke-width="2" stroke-linejoin="round" stroke-linecap="round" opacity=".9"/>';
              }
              seg = ''; pts = 0; continue;
            }
            var y = yPos(d.v);
            seg += (seg === '' ? '' : ' ') + x + ',' + y;
            pts++;
            html += '<circle cx="' + x + '" cy="' + y + '" r="3.5" fill="' + colorVar + '"/>';
            html += '<text x="' + x + '" y="' + (y - 6) + '" text-anchor="middle" font-size="9" fill="var(--texto)">' + fmtNum(d.v, 1) + '</text>';
          }
          if (pts > 1) {
            html += '<polyline points="' + seg.trim() + '" fill="none" stroke="' + colorVar + '" stroke-width="2" stroke-linejoin="round" stroke-linecap="round" opacity=".9"/>';
          }
          html += '</svg>';
          return html;
        }

        function ligarGraficos(info) {
          var chips = document.getElementById(info.idBase + '-chips');
          var area = document.getElementById(info.idBase + '-area');
          var prod = document.getElementById(info.idBase + '-prod');
          var botoes = chips ? Array.prototype.slice.call(chips.querySelectorAll('.prod-crop-chip')) : [];
          function pintar(faz) {
            var getArea = function (an) {
              var c = faz === '' ? info.cons[an] : (info.porFaz[faz] || {})[an];
              return c && c.area > 0 ? c.area : null;
            };
            var getProd = function (an) {
              var c = faz === '' ? info.cons[an] : (info.porFaz[faz] || {})[an];
              return prodCelda(c);
            };
            if (area) area.innerHTML = graficoBarrasSVG(info.anosArr, getArea, 'var(--acento)', 'Área (ha) de ' + info.cultura + ' por ano — ' + (faz === '' ? 'Consolidado' : faz));
            if (prod) prod.innerHTML = graficoLineasSVG(info.anosArr, getProd, 'var(--acento-2)', 'Produtividade de ' + info.cultura + ' por ano — ' + (faz === '' ? 'Consolidado' : faz));
          }
          botoes.forEach(function (b) {
            b.addEventListener('click', function () {
              botoes.forEach(function (x) {
                x.classList.toggle('active', x === b);
                x.setAttribute('aria-pressed', x === b ? 'true' : 'false');
              });
              pintar(b.dataset.faz);
            });
          });
          pintar('');
        }

        function renderPainelesCultura(lista) {
          if (!painelCulturas) return;
          if (!lista.length) { painelCulturas.innerHTML = ''; return; }
          var grupos = {}, ch, i;
          for (i = 0; i < lista.length; i++) {
            var r = lista[i];
            ch = (r.cultura || '') + '\u0000' + (r.unidade || '');
            if (!grupos[ch]) grupos[ch] = { cultura: r.cultura || '—', unidade: r.unidade || '', linhas: [] };
            grupos[ch].linhas.push(r);
          }
          var chaves = ordenarChavesCultura(grupos);
          var html = '', primeiro = true, infos = [];
          chaves.forEach(function (chv) {
            var g = grupos[chv];
            var res = painelCulturaHTML(g.cultura, g.unidade, g.linhas);
            if (!res) return;
            if (primeiro) { res.html = res.html.replace('<details class="prod-crop">', '<details class="prod-crop" open>'); primeiro = false; }
            html += res.html;
            infos.push(res);
          });
          painelCulturas.innerHTML = html;
          for (i = 0; i < infos.length; i++) ligarGraficos(infos[i]);
        }

        function agruparPorCultura(linhas) {
          var grupos = {}, i, r;
          for (i = 0; i < linhas.length; i++) {
            r = linhas[i];
            var chave = (r.cultura || '') + '\u0000' + (r.unidade || '');
            if (!grupos[chave]) grupos[chave] = { cultura: r.cultura || '—', unidade: r.unidade || '', valores: [], n: 0 };
            grupos[chave].n++;
            // Regra de negócio: produtividade nula ou ≤ 0 = talhão NÃO colhido
            // (ou unidade sem valor) — NÃO é uma medição e não entra na média;
            // essas culturas aparecem como CONTROLE (ver renderMedia).
            var valor = num(r.produtividade);
            if (!isNaN(valor) && valor > 0) grupos[chave].valores.push(valor);
          }
          return grupos;
        }

        function ordenarChavesCultura(grupos) {
          return Object.keys(grupos).sort(function (a, b) {
            return grupos[a].cultura.localeCompare(grupos[b].cultura, 'pt-BR', { numeric: true }) ||
              a.localeCompare(b, 'pt-BR');
          });
        }

        function resumoEstatistico(valores) {
          if (!valores || !valores.length) return null;
          var soma = 0, menor = valores[0], maior = valores[0], i;
          for (i = 0; i < valores.length; i++) {
            soma += valores[i];
            if (valores[i] < menor) menor = valores[i];
            if (valores[i] > maior) maior = valores[i];
          }
          return { media: soma / valores.length, max: maior, min: menor, n: valores.length };
        }

        function renderMedia(lista) {
          if (!mediaBox) return;
          var grupos = agruparPorCultura(lista);
          var chaves = ordenarChavesCultura(grupos).filter(function (ch) { return grupos[ch].valores.length > 0; });
          var html = chaves.map(function (ch) {
            var g = grupos[ch], st = resumoEstatistico(g.valores);
            return '<div class="cartao prod-media-card">' +
              '<span class="cartao-valor">' + fmtNum(st ? st.media : null) +
              (g.unidade ? ' <small>' + esc(g.unidade) + '</small>' : '') + '</span>' +
              '<span class="cartao-rotulo">' + esc(g.cultura) + ' · ' + st.n + ' registro(s)</span>' +
              (st ? '<span class="prod-minmax-cartao">máx ' + fmtNum(st.max) + ' · mín ' + fmtNum(st.min) + '</span>' : '') +
              '</div>';
          }).join('');

          // Culturas "zeradas" (presentes, porém SEM produtividade positiva =
          // não colhidas): exibidas apenas como CONTROLE, agrupadas por cultura
          // (ignora a unidade) e fora da média real.
          var ctrl = {}, i, r, v, nome;
          for (i = 0; i < lista.length; i++) {
            r = lista[i];
            nome = r.cultura || '—';
            if (!ctrl[nome]) ctrl[nome] = { n: 0, temValor: false, unidades: {} };
            ctrl[nome].n++;
            v = num(r.produtividade);
            if (!isNaN(v) && v > 0) ctrl[nome].temValor = true;
            if (r.unidade) ctrl[nome].unidades[String(r.unidade)] = 1;
          }
          var nomesCtrl = Object.keys(ctrl).filter(function (nm) { return !ctrl[nm].temValor; })
            .sort(function (a, b) { return a.localeCompare(b, 'pt-BR', { numeric: true }); });
          html += nomesCtrl.map(function (nm) {
            var u = Object.keys(ctrl[nm].unidades);
            var unidade = u.length === 1 ? u[0] : '';
            return '<div class="cartao prod-media-card prod-media-card-controle">' +
              '<span class="cartao-valor">0,00' +
              (unidade ? ' <small>' + esc(unidade) + '</small>' : '') + '</span>' +
              '<span class="cartao-rotulo">' + esc(nm) + ' · ' + ctrl[nm].n + ' registro(s)</span>' +
              '<span class="prod-minmax-cartao">controle — não colhido</span>' +
              '</div>';
          }).join('');

          mediaBox.innerHTML = html || '<p class="muted">Nenhuma produtividade registrada.</p>';
        }

        function renderResumo(lista) {

          if (!resumo) return;

          var n = ObterDados.resumoFiltros();

          var total = ObterDados.dados.length;

          resumo.innerHTML =

            '<span class="prod-chip"><strong>' + lista.length + '</strong> registros exibidos</span>' +

            '<span class="prod-chip"><strong>' + coletarUnicos('cultura').length + '</strong> culturas cadastradas</span>' +

            (n ? '<span class="prod-chip"><strong>' + n + '</strong> filtro(s) ativo(s)</span>'

              : '<span class="prod-chip">filtros inativos — exibindo a média de tudo (' + total + ' registros)</span>');

        }

        function valoresPorColuna(registros) {
          var vals = {}, i, r, ch, valor;
          for (i = 0; i < registros.length; i++) {
            r = registros[i];
            ch = (r.cultura || '') + '\u0000' + (r.unidade || '');
            if (!vals[ch]) vals[ch] = [];
            valor = num(r.produtividade);
            // Nula ou ≤ 0 = talhão não colhido → não conta como medição.
            if (!isNaN(valor) && valor > 0) vals[ch].push(valor);
          }
          return vals;
        }

        function celCulturaChaves(chaves, vals) {
          return chaves.map(function (ch) {
            var st = resumoEstatistico(vals[ch]);
            if (!st) return '<span class="prod-cel-cultura sem-valor">—</span>';
            return '<span class="prod-cel-cultura"><span class="prod-media-valor">' + fmtNum(st.media) + '</span>' +
              '<span class="prod-minmax">máx ' + fmtNum(st.max) + ' · mín ' + fmtNum(st.min) + '</span></span>';
          }).join('');
        }

        function renderHierarquia(lista) {
          if (!wrap) return;
          if (!lista.length) {
            wrap.style.display = 'none';
            if (vazio) vazio.classList.add('visivel');
            return;
          }
          var grupos = agruparPorCultura(lista);
          var chaves = ordenarChavesCultura(grupos).filter(function (ch) { return grupos[ch].valores.length > 0; });
          var arv = {}, ordemOs = [], i, r, os, faz, tal;

          for (i = 0; i < lista.length; i++) {
            r = lista[i];
            os = r.os || '—';
            faz = r.fazenda || '—';
            tal = r.talhao || '—';
            if (!arv[os]) { arv[os] = {}; ordemOs.push(os); }
            if (!arv[os][faz]) arv[os][faz] = {};
            if (!arv[os][faz][tal]) arv[os][faz][tal] = [];
            arv[os][faz][tal].push(r);
          }
          ordemOs.sort(function (a, b) { return a.localeCompare(b, 'pt-BR', { numeric: true }); });

          function coletarRegistros(osAtual, fazAtual, talAtual) {
            if (talAtual) return arv[osAtual][fazAtual][talAtual];
            var total = [];
            Object.keys(arv[osAtual] || {}).forEach(function (fz) {
              if (!fazAtual || fz === fazAtual) {
                Object.keys(arv[osAtual][fz]).forEach(function (tl) {
                  total = total.concat(arv[osAtual][fz][tl]);
                });
              }
            });
            return total;
          }

          function linhaDet(expandivel, nome, registros) {
            var vals = valoresPorColuna(registros);
            return '<span class="toggle">' + (expandivel ? '▶' : '') + '</span>' +
              '<span class="cel-nome">' + esc(nome) + '</span>' +
              celCulturaChaves(chaves, vals) +
              '<span class="cel-regs">' + registros.length + '</span>';
          }

          var head = '<div class="det-row det-head"><span class="toggle"></span>' +
            '<span class="cel-nome">OS · Fazenda · Talhão</span>' +
            chaves.map(function (ch) {
              var g = grupos[ch];
              return '<span class="cel-cultura" title="' + esc(g.cultura) + '">' + esc(g.cultura) +
                (unidadeDoRotulo(g.cultura, g.unidade) ? '<small class="prod-unidade"> (' + esc(g.unidade) + ')</small>' : '') + '</span>';
            }).join('') +
            '<span class="cel-regs">Registros</span></div>';

          var blocos = ordemOs.map(function (osAtual) {
            var fazes = Object.keys(arv[osAtual]).sort(function (a, b) {
              return a.localeCompare(b, 'pt-BR', { numeric: true });
            });
            var corpoFaz = fazes.map(function (fazAtual) {
              var talhoes = Object.keys(arv[osAtual][fazAtual]).sort(function (a, b) {
                return a.localeCompare(b, 'pt-BR', { numeric: true });
              });
              var rowsTal = talhoes.map(function (talAtual) {
                return '<div class="det-row">' + linhaDet(false, talAtual, arv[osAtual][fazAtual][talAtual]) + '</div>';
              }).join('');
              return '<details class="cons-faz"><summary class="det-row">' +
                linhaDet(true, fazAtual, coletarRegistros(osAtual, fazAtual, null)) + '</summary>' +
                (rowsTal ? '<div class="cons-body">' + rowsTal + '</div>' : '') + '</details>';
            }).join('');
            return '<details class="cons-os"' + '><summary class="det-row">' +
              linhaDet(true, osAtual, coletarRegistros(osAtual, null, null)) + '</summary>' +
              (corpoFaz ? '<div class="cons-body">' + corpoFaz + '</div>' : '') + '</details>';
          }).join('');

          var totalGeral = '<div class="det-row det-total">' + linhaDet(false, 'Total geral', lista) + '</div>';
          var cols = '1.7rem minmax(200px, auto) repeat(' + chaves.length + ', minmax(158px, auto)) minmax(70px, auto)';
          wrap.innerHTML = '<div class="painel-consolidado prod-hierarquia" style="--cols:' + cols + '">' +
            head + blocos + totalGeral + '</div>';
          wrap.style.display = 'block';
          // Corpo de cada OS/fazenda só entra no documento ao ser aberto.
          ObterDados.detailsSobDemanda(wrap);
          if (vazio) vazio.classList.remove('visivel');
        }

        // ----- Paletas de calor das produtividades (3.5 e 3.7) -----
        // Em ambas `t = 0` é o PIOR resultado e `t = 1` o MELHOR; a cor sai num
        // `rgba` com transparência para o texto claro do tema continuar legível.
        //  · 3.5 (`CALOR_3_5`): vermelho → amarelo → verde, com a faixa da
        //    PRÓPRIA linha (cada linha de Média compara os seus anos).
        //  · 3.7 (`CORES_MATRIZ_PROD`): vermelho escuro → vermelho claro →
        //    marrom-laranja → amarelo → verde claro → verde escuro, com UMA
        //    faixa para todos os dados da cultura (o subpainel inteiro).
        var CALOR_3_5 = [[248, 113, 113], [251, 191, 36], [74, 222, 128]];
        var CORES_MATRIZ_PROD = [
          [127, 29, 29], [239, 68, 68], [194, 65, 12],
          [251, 191, 36], [134, 239, 172], [22, 101, 52]
        ];

        // Interpola as âncoras RGB em passos iguais (0 = 1ª cor, 1 = última) e
        // devolve `rgba(r, g, b, alfa)`.
        function corCalor(t, ancoras, alfa) {
          var n = ancoras.length - 1;
          var x = Math.min(1, Math.max(0, t)) * n;
          var i = Math.min(n - 1, Math.floor(x)), p = x - i;
          var a = ancoras[i], b = ancoras[i + 1] || a, c = [], k;
          for (k = 0; k < 3; k++) {
            c[k] = Math.round(a[k] + (b[k] - a[k]) * p);
          }
          return 'rgba(' + c[0] + ', ' + c[1] + ', ' + c[2] + ', ' + alfa + ')';
        }

        // Faixa (mín/máx) de uma lista de valores: `null` quando não há o que
        // comparar (menos de dois valores ou todos iguais — sem "melhor"/"pior").
        function faixaCalor(vals) {
          if (!vals || vals.length < 2) return null;
          var mn = Math.min.apply(null, vals), mx = Math.max.apply(null, vals);
          return mx > mn ? { min: mn, max: mx } : null;
        }

        // Posição de um valor dentro da faixa (0 = pior, 1 = melhor); `null`
        // quando o valor não existe ou não há faixa.
        function posicaoCalor(v, faixa) {
          if (!faixa || v === null || v === undefined) return null;
          return (v - faixa.min) / (faixa.max - faixa.min);
        }

        // ----- 3.5 Parecer por cultura (OS · Fazenda · Talhão) -----
        // Um subpainel por cultura (`renderAreaCultura`) com o MESMO widget do painel
        // 4.1: cada nó (OS → Fazenda → Talhão) é um grupo de linhas de métrica, com
        // coluna Geral + coluna Variação % + uma coluna por ano. As métricas são Área
        // (ha), Total produzido (Σ área × produtividade), Média (total ÷ área COM
        // produção) e Variedade (material genético do ano, texto).
        // NÃO há conversão de unidade: a produtividade do JSON já vem na unidade
        // padrão da cultura (sc/ha, t/ha, @/ha, cx 40,8 kg/ha, m³/ha, ...), então no
        // TALHÃO a Média é exatamente o valor da planilha e, na OS/fazenda/geral, é a
        // MÉDIA PONDERADA pela área — já na mesma unidade. Os rótulos das métricas
        // informam a unidade exibida.
        // QUEM ENTRA NA MÉDIA (produção informada × não colhido): só os registros
        // COM produtividade informada (`≠ null`) entram no NUMERADOR e no
        // DENOMINADOR. `0` é produção ZERO — uma medição: a área entra e o registro
        // contribui 0 no total (e derruba a média). `null` é talhão NÃO COLHIDO —
        // não contabilizado: fica fora do total E da área da média. Logo
        // Média = Σ(área × produtividade) ÷ Σ(área dos registros com produtividade
        // ≠ null). A métrica Área (ha) continua sendo a área TOTAL do nó (colhida
        // ou não) — só o denominador da Média é que ignora o não colhido.
        // A variação usa a fórmula/limiares do painel de área (verde ≤5%, amarelo
        // 5–20%, vermelho >20%) e a cor da linha só é aplicada à métrica Área (ha) —
        // cinza quando o TALHÃO não tem área em algum ano e a variação é 0%.

        // Unidade de PRODUÇÃO derivada da unidade de produtividade (remove o "/ha"):
        // "sc/ha" → "sc", "t/ha" → "t", "@/ha" → "@", "cx 40,8 kg/ha" → "cx 40,8 kg",
        // "m³/ha" → "m³", "sc benef./ha" → "sc benef.", "kg/ha - óleo" → "kg - óleo".
        // Sem "/ha" no texto (ou texto vazio) não se arrisca unidade nenhuma.
        function unidadeProducao(unidade) {
          var u = (unidade === null || unidade === undefined)
            ? '' : String(unidade).trim();
          if (!u || !/\/\s*ha/i.test(u)) return '';
          return u.replace(/\s*\/\s*ha/i, '').trim();
        }

        // Métricas do 3.5 com a unidade da cultura no rótulo: a Média usa a própria
        // unidade do subpainel (sc/ha, t/ha, ...) e o Total produzido, a unidade de
        // produção derivada dela (sc, t, ...). Nenhuma métrica converte unidade.
        function metricasAreaCultura(unidade) {
          var u = (unidade === null || unidade === undefined)
            ? '' : String(unidade).trim();
          var up = unidadeProducao(u);
          return [
            { chave: 'area', rotulo: 'Área (ha)', casas: 2 },
            { chave: 'total',
              rotulo: 'Total produzido' + (up ? ' (' + up + ')' : ''),
              casas: 0 },
            { chave: 'media',
              rotulo: 'Média' + (u ? ' (' + u + ')' : ''),
              casas: 2 },
            { chave: 'variedade', rotulo: 'Variedade', casas: 0, texto: true }
          ];
        }

        // Anos exibidos numa cultura: os presentes nas linhas (o ano ausente vira a
        // coluna '—', como no painel 4.1).
        function anosCultura(lista) {
          var mapa = {}, anos = [], i, r, an;
          for (i = 0; i < lista.length; i++) {
            r = lista[i];
            an = (r.ano === null || r.ano === undefined) ? '—' : String(r.ano).trim();
            if (!an) an = '—';
            if (!(an in mapa)) { mapa[an] = 1; anos.push(an); }
          }
          return anos.sort(function (a, b) {
            var x = Number(a), y = Number(b);
            if (isNaN(x)) return 1;
            if (isNaN(y)) return -1;
            return x - y;
          });
        }

        // Pivô de UMA cultura: cada nó vira um grupo de 4 linhas (uma por métrica) e
        // as linhas de um nó só nascem quando o nó de cima é expandido
        // (`ObterDados.pivotLazy`). Começa RECOLHIDO: só as OS e o "Total geral".
        function renderAreaCulturaPivot(regs, el) {
          if (!el) return;
          if (!regs.length) {
            el.innerHTML = '';
            el.style.display = 'none';
            return;
          }
          el.style.display = 'block';
          var anos = anosCultura(regs);
          // Unidade exibida no subpainel — o grupo é por cultura + unidade, então
          // todas as linhas trazem a MESMA unidade (usamos a 1ª não vazia) e as
          // métricas montam o rótulo já com ela, sem conversão alguma.
          var unidadeGrupo = '', ug;
          for (ug = 0; ug < regs.length; ug++) {
            var uReg = (regs[ug].unidade === null || regs[ug].unidade === undefined)
              ? '' : String(regs[ug].unidade).trim();
            if (uReg) { unidadeGrupo = uReg; break; }
          }
          var metricas = metricasAreaCultura(unidadeGrupo);
          var arv = {}, ordemOs = [], i, r, os, faz, tal;
          for (i = 0; i < regs.length; i++) {
            r = regs[i];
            os = r.os || '—';
            faz = r.fazenda || '—';
            tal = r.talhao || '—';
            if (!arv[os]) { arv[os] = {}; ordemOs.push(os); }
            if (!arv[os][faz]) arv[os][faz] = {};
            if (!arv[os][faz][tal]) arv[os][faz][tal] = [];
            arv[os][faz][tal].push(r);
          }
          ordemOs.sort(function (a, b) { return a.localeCompare(b, 'pt-BR', { numeric: true }); });
          function porNome(a, b) { return a.localeCompare(b, 'pt-BR', { numeric: true }); }
          function colectarRegistros(osA, fazA, talA) {
            if (talA) return arv[osA][fazA][talA];
            var total = [];
            Object.keys(arv[osA] || {}).forEach(function (fz) {
              if (!fazA || fz === fazA) {
                Object.keys(arv[osA][fz]).forEach(function (tl) {
                  total = total.concat(arv[osA][fz][tl]);
                });
              }
            });
            return total;
          }
          // Acumulador por ano/nó: área TOTAL (ha), área COM produção informada
          // (`areaProd` — o DENOMINADOR da Média, que ignora o não colhido),
          // total produzido (Σ área × produtividade, na unidade da cultura) e as
          // variedades informadas (distintas, na ordem de aparição).
          function acc() {
            return { area: 0, total: 0, totalN: 0, areaProd: 0, vars: {}, varsOrdem: [] };
          }
          function agregar(lista) {
            var porAno = {}, geral = acc(), j, rr, an, a, p, v;
            for (j = 0; j < lista.length; j++) {
              rr = lista[j];
              an = (rr.ano === null || rr.ano === undefined) ? '—' : String(rr.ano).trim();
              if (!an) an = '—';
              if (!porAno[an]) porAno[an] = acc();
              a = num(rr.area);
              if (!isNaN(a) && a > 0) { porAno[an].area += a; geral.area += a; }
              p = num(rr.produtividade);
              // SEM conversão de unidade: a produtividade já vem na unidade
              // padrão da planilha, então o total é o numerador da média
              // ponderada (Σ área × produtividade) e a Média sai na mesma unidade.
              // `p === 0` é produção ZERO (medição válida: entra no total E na
              // área da média); produtividade ausente (`null` = talhão NÃO
              // COLHIDO) fica FORA dos dois — não é contabilizada.
              if (!isNaN(a) && a > 0 && !isNaN(p)) {
                porAno[an].total += a * p; geral.total += a * p;
                porAno[an].totalN++; geral.totalN++;
                porAno[an].areaProd += a; geral.areaProd += a;
              }
              v = rr.variedade;
              if (v !== null && v !== undefined && String(v).trim()) {
                v = String(v).trim();
                if (!porAno[an].vars[v]) { porAno[an].vars[v] = 1; porAno[an].varsOrdem.push(v); }
                if (!geral.vars[v]) { geral.vars[v] = 1; geral.varsOrdem.push(v); }
              }
            }
            return { porAno: porAno, geral: geral };
          }
          function variedades(x) {
            return (x && x.varsOrdem.length) ? x.varsOrdem.join(' / ') : null;
          }
          // Valor final de uma métrica — `null` quando não há valor no ano/nó.
          function valorMetrica(x, m) {
            if (!x) return null;
            if (m.chave === 'area') return x.area > 0 ? x.area : null;
            if (m.chave === 'total') return x.totalN > 0 ? x.total : null;
            // Média = total ÷ área COM produção informada (`areaProd`), nunca a
            // área total do nó: talhão não colhido (produtividade `null`) não
            // entra na conta (ver `agregar`).
            if (m.chave === 'media') return x.areaProd > 0 ? x.total / x.areaProd : null;
            if (m.chave === 'variedade') return variedades(x);
            return null;
          }
          // Variação % entre os anos exibidos (|maior − menor| ÷ média × 100), com os
          // mesmos limiares do painel de área. Os anos sem valor ficam de fora e
          // `falta` marca a métrica sem valor em algum ano do painel.
          function variacaoMetrica(agg, m) {
            if (m.texto) return { nivel: '', variacao: null, falta: false };
            var vals = [], k, an, v;
            for (k = 0; k < anos.length; k++) {
              an = anos[k];
              v = valorMetrica(agg.porAno[an], m);
              if (v !== null && v !== undefined) vals.push(v);
            }
            var falta = vals.length < anos.length;
            if (!vals.length) return { nivel: '', variacao: null, falta: falta };
            if (vals.length < 2) return { nivel: '', variacao: 0, falta: falta };
            var maior = Math.max.apply(null, vals), menor = Math.min.apply(null, vals);
            if (maior === menor) return { nivel: '', variacao: 0, falta: falta };
            var pct = Math.abs(maior - menor) / ((maior + menor) / 2) * 100;
            var nivel = pct <= 5 ? 'verde' : (pct <= 20 ? 'amarelo' : 'vermelho');
            return { nivel: nivel, variacao: pct, falta: falta };
          }
          // Célula do pivô. `calor` (opcional) é a cor de fundo da célula — no
          // 3.5 a Média sai com a paleta vermelho → amarelo → verde da PRÓPRIA
          // linha (o melhor ano verde, o pior vermelho).
          function celPac(valor, m, calor) {
            if (valor === null || valor === undefined) {
              return '<td class="pac-cel pac-sem-valor">—</td>';
            }
            if (m.texto) return '<td class="pac-cel pac-texto">' + esc(valor) + '</td>';
            if (calor) {
              return '<td class="pac-cel pac-cel-heat" style="--pac-calor:' + calor +
                '">' + fmtNum(valor, m.casas) + '</td>';
            }
            return '<td class="pac-cel">' + fmtNum(valor, m.casas) + '</td>';
          }
          function celVarPac(res) {
            return (res.variacao === null || res.variacao === undefined)
              ? '<td class="pac-cel pac-var pac-sem-valor">—</td>'
              : '<td class="pac-cel pac-var">' + fmtNum(res.variacao, 1) + '%</td>';
          }
          // Linhas de um nó: escritas só quando o nó de cima é expandido.
          function linhasNo(gid, nome, nivel, listaRegs, temFilhos) {
            var agg = agregar(listaRegs), html = '';
            metricas.forEach(function (m, idx) {
              var vGeral = valorMetrica(agg.geral, m);
              var varM = variacaoMetrica(agg, m);
              // A variedade é do TALHÃO: nos níveis de OS, fazenda e no
              // "Total geral" a linha sai inteira como "—" — concatenar os
              // cultivares dos filhos sugeriria que o nó plantou todos eles.
              var soTalhao = m.texto && nivel !== 'tal';
              // Faixa de calor da PRÓPRIA linha: só a Média (a produtividade da
              // cultura) e só nos anos — o melhor ano da linha sai verde e o pior
              // vermelho. A coluna Geral entra na régua (mesma faixa), mas NÃO na
              // faixa, para não achatar a comparação ano a ano.
              var faixa = null;
              if (m.chave === 'media') {
                var valsMedia = [];
                anos.forEach(function (an) {
                  var vm = valorMetrica(agg.porAno[an], m);
                  if (vm !== null && vm !== undefined) valsMedia.push(vm);
                });
                faixa = faixaCalor(valsMedia);
              }
              var corDoValor = function (v) {
                var p = posicaoCalor(v, faixa);
                return p === null ? '' : corCalor(p, CALOR_3_5, .32);
              };
              var cels = anos.map(function (an) {
                if (soTalhao) return '<td class="pac-cel pac-sem-valor">—</td>';
                var vAno = valorMetrica(agg.porAno[an], m);
                return celPac(vAno, m, corDoValor(vAno));
              }).join('');
              // A cor da linha só vai na métrica Área (ha): verde/amarelo/vermelho
              // pela variação e cinza quando o TALHÃO não tem área em algum ano e a
              // variação é 0% (mesma regra do painel 4.1).
              var nivelLinha = '';
              if (m.chave === 'area') {
                if (varM.nivel) nivelLinha = varM.nivel;
                else if (nivel === 'tal' && varM.falta) nivelLinha = 'cinza';
              }
              var nomeTd = (idx === 0)
                ? '<td class="pac-nome pac-nivel-' + nivel + (temFilhos ? ' pac-clicavel' : '') +
                  '" data-grupo="' + gid + '"' + (temFilhos ? ' data-toggle="1"' : '') +
                  ' rowspan="' + metricas.length + '">' +
                  (temFilhos ? '<span class="pac-seta">▶</span> ' : '') + esc(nome) + '</td>'
                : '';
              // A linha "Variedade" é texto: Geral e Variação % saem como "—".
              var geralTd;
              if (m.texto || vGeral === null || vGeral === undefined) {
                geralTd = '<td class="pac-cel pac-geral pac-sem-valor">—</td>';
              } else {
                var corGeral = corDoValor(vGeral);
                geralTd = corGeral
                  ? '<td class="pac-cel pac-geral pac-cel-heat" style="--pac-calor:' +
                    corGeral + '">' + fmtNum(vGeral, m.casas) + '</td>'
                  : '<td class="pac-cel pac-geral">' + fmtNum(vGeral, m.casas) + '</td>';
              }
              html += '<tr data-g="' + gid + '" class="pac-linha' +
                (idx === 0 ? ' pac-inicio-grupo' : '') +
                (nivelLinha ? ' linha-' + nivelLinha : '') + '">' +
                nomeTd + '<td class="pac-metrica">' + esc(m.rotulo) + '</td>' +
                geralTd + celVarPac(varM) + cels + '</tr>';
            });
            return html;
          }
          var headAnos = anos.map(function (an) { return '<th>' + esc(an) + '</th>'; }).join('');
          el.innerHTML = '<table class="pac-pivot"><thead><tr>' +
            '<th>OS · Fazenda · Talhão</th><th>Métrica</th><th>Geral</th>' +
            '<th>Variação %</th>' + headAnos +
            '</tr></thead><tbody></tbody></table>';
          // Hierarquia sob demanda: só as OS (e a linha do total) entram agora; as
          // fazendas nascem ao abrir uma OS e os talhões ao abrir a fazenda.
          var piv = ObterDados.pivotLazy({
            prefixo: 'pac',
            corpo: el.querySelector('tbody'),
            linhas: linhasNo
          });
          ordemOs.forEach(function (osA) {
            piv.raiz({
              nome: osA, nivel: 'os',
              coletar: function () { return colectarRegistros(osA, null, null); },
              gerarFilhos: function () {
                return Object.keys(arv[osA]).sort(porNome).map(function (fazA) {
                  return {
                    nome: fazA, nivel: 'faz',
                    coletar: function () { return colectarRegistros(osA, fazA, null); },
                    gerarFilhos: function () {
                      return Object.keys(arv[osA][fazA]).sort(porNome).map(function (talA) {
                        return { nome: talA, nivel: 'tal', coletar: arv[osA][fazA][talA] };
                      });
                    }
                  };
                });
              }
            });
          });
          piv.raiz({ nome: 'Total geral', nivel: 'total', coletar: regs });
        }

        // Um subpainel (`<details class="prod-crop">`) por cultura — recolhido por
        // padrão, com o pivô montado só na primeira abertura (mesmo padrão do 5.5).
        function renderAreaCultura(lista) {
          if (!wrapAreaCultura) return;
          var grupos = {}, chaves, i, r, a, ch;
          for (i = 0; i < lista.length; i++) {
            r = lista[i];
            a = num(r.area);
            if (isNaN(a) || a <= 0) continue;
            ch = (r.cultura || '') + '\u0000' + (r.unidade || '');
            if (!grupos[ch]) grupos[ch] = { cultura: r.cultura || '—', unidade: r.unidade || '', linhas: [] };
            grupos[ch].linhas.push(r);
          }
          chaves = ordenarChavesCultura(grupos);
          if (!chaves.length) {
            wrapAreaCultura.innerHTML = '';
            wrapAreaCultura.style.display = 'none';
            if (vazioAreaCultura) vazioAreaCultura.classList.add('visivel');
            return;
          }
          var recado = '<p class="muted pac-recado">Um painel por cultura, no formato do ' +
            'painel 4.1: Área (ha), Total produzido e Média — sempre na unidade da ' +
            'cultura (sc/ha, t/ha, @/ha, ...), sem conversão — e Variedade, com a ' +
            'Variação % de cada métrica — verde ≤5%, amarelo 5–20%, ' +
            'vermelho &gt;20%; cinza = talhão sem área em algum ano e sem variação (0%). ' +
            'No talhão a Média é o valor da planilha; na OS, na fazenda e no total é a ' +
            'média ponderada pela área — Σ(área × produtividade) ÷ Σ(área dos ' +
            'registros COM produtividade informada). Produção 0 (zero) conta na ' +
            'média; talhão não colhido (sem produtividade) não entra na conta. ' +
            'A linha da Média sai com a paleta vermelho → amarelo → verde da PRÓPRIA ' +
            'linha: o melhor ano da linha fica verde e o pior vermelho. ' +
            'Clique no título do subpainel para abrir.</p>';
          wrapAreaCultura.innerHTML = recado;
          chaves.forEach(function (chave, idx) {
            var g = grupos[chave];
            var detalhe = document.createElement('details');
            detalhe.className = 'prod-crop';
            var resumo = document.createElement('summary');
            resumo.innerHTML = '<span class="prod-crop-titulo">3.5.' + (idx + 1) + ' · ' +
              esc(g.cultura) + (unidadeDoRotulo(g.cultura, g.unidade) ? ' <span class="prod-unidade">(' +
                esc(g.unidade) + ')</span>' : '') + '</span>';
            var cuerpo = document.createElement('div');
            cuerpo.className = 'prod-crop-cuerpo';
            var tabla = document.createElement('div');
            tabla.className = 'prod-crop-tabla';
            cuerpo.appendChild(tabla);
            detalhe.appendChild(resumo);
            detalhe.appendChild(cuerpo);
            wrapAreaCultura.appendChild(detalhe);
            detalhe.addEventListener('toggle', function () {
              if (!detalhe.open || tabla.getAttribute('data-montado') === '1') return;
              tabla.setAttribute('data-montado', '1');
              renderAreaCulturaPivot(g.linhas, tabla);
            });
          });
          wrapAreaCultura.style.display = 'block';
          if (vazioAreaCultura) vazioAreaCultura.classList.remove('visivel');
        }

        // ----- Cores das atividades (painel 3.6) -----
        // A cor de cada atividade é DINÂMICA: sai de uma paleta escolhida por um
        // hash do NOME da atividade (nunca de um mapa fixo do tipo
        // "soja + milho = verde") e, quando o hash cai numa cor já tomada, a
        // atribuição anda na paleta até achar uma livre — então as atividades do
        // relatório saem todas distintas enquanto houver cor disponível. As
        // MESMAS cores alimentam os chips das células do ano e a legenda do
        // painel, que é montada com as atividades do filtro atual.
        // A paleta é a PADRÃO dos gráficos (`ObterDados.CORES`, 20 cores): os
        // chips do 3.6 e as linhas do 3.8 falam a mesma língua dos outros painéis.
        var CORES_ATIVIDADE = ObterDados.CORES;

        // Nome do nó/atividade em ordem "natural" (10 antes de 9).
        function porNomeAtiv(a, b) {
          return String(a).localeCompare(String(b), 'pt-BR', { numeric: true });
        }

        function hashAtividade(nome) {
          var s = normValor(nome), h = 0, i;
          for (i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) % 1000003;
          return h;
        }

        // Cores que NUNCA vão para um chip nem para uma linha de combinação: os
        // dois tons mais escuros da paleta (cinza escuro e preto) não apareceriam
        // sobre o fundo escuro do relatório, e o cinza claro é a linha de
        // REFERÊNCIA (área física) — um teto do gráfico, não uma série.
        var CORES_ATIVIDADE_RESERVADAS = [ObterDados.COR_REFERENCIA, '#334155', '#000000'];

        // Atividade → cor. A ordem de atribuição é alfabética (determinística),
        // para o resultado não depender da ordem em que os registros chegaram.
        function coresDasAtividades(nomes) {
          var cores = {}, usadas = {}, reserva = {};
          CORES_ATIVIDADE_RESERVADAS.forEach(function (c) {
            usadas[c] = 1; reserva[c] = 1;
          });
          nomes.slice().sort(porNomeAtiv).forEach(function (nome) {
            var idx = ObterDados.escolherCor(CORES_ATIVIDADE, usadas,
              hashAtividade(nome), reserva);
            usadas[CORES_ATIVIDADE[idx]] = 1;
            cores[nome] = CORES_ATIVIDADE[idx];
          });
          return cores;
        }

        // Um chip por atividade: a cor viaja na variável CSS `--ativ-cor`.
        function chipAtividade(nome, cor) {
          return '<span class="ativ-chip" style="--ativ-cor:' + cor + '">' +
            esc(nome) + '</span>';
        }

        // Chave do talhão (OS · Fazenda · Talhão) usada pelo mapa de área física.
        function chaveTalhaoAtiv(osN, fazN, talN) {
          return String(osN) + '\u0000' + String(fazN) + '\u0000' + String(talN);
        }

        // ----- Atividades por talhão · ano: fonte COMUM do 3.6 e do 3.8 -----
        // `agregarAtividades` monta a árvore OS → Fazenda → Talhão com as
        // atividades de cada ano (culturas + Pecuária: exatamente os mesmos itens
        // nos dois painéis), o universo de anos, a lista de atividades (mais
        // registradas primeiro) e a ÁREA FÍSICA de cada talhão (a MAIOR área
        // registrada no período, entre culturas e pecuária). O 3.6 lista os NOMES
        // dessas atividades; o 3.8 soma a área de cada COMBINAÇÃO delas — por
        // isso a agregação vive aqui, e não dentro de um dos dois painéis.
        function agregarAtividades() {
          var f = ObterDados.filtros, busca = normValor(f.busca);
          // Filtros globais de contexto (o filtro de Cultura NÃO entra: os dois
          // painéis mostram TODAS as atividades de cada talhão/ano).
          function passa(r) {
            if (!casaFiltro(r.os, f.os)) return false;
            if (!casaFiltro(r.fazenda, f.fazenda)) return false;
            if (!casaFiltro(r.talhao, f.talhao)) return false;
            if (!casaFiltro(r.ano, f.ano)) return false;
            if (!casaFiltro(r.cenario, f.cenario)) return false;
            if (busca && normValor(JSON.stringify(r)).indexOf(busca) < 0) return false;
            return true;
          }
          function chaveAnoAtiv(v) {
            var s = (v === null || v === undefined) ? '' : String(v).trim();
            return s === '' ? '—' : s;
          }
          // Árvore OS → Fazenda → Talhão; em cada talhão, mapa ano → atividades.
          // `contagemAtiv` pesa cada atividade (nº de registros) para a legenda
          // sair com as atividades mais presentes na frente.
          var arv = {}, anos = [], contagemAtiv = {}, fisica = {}, i, r, nome, chave;
          function obterNo(osN, fazN, talN) {
            var o = arv[osN];
            if (!o) { o = arv[osN] = { nome: osN, fazendas: {} }; }
            if (fazN === null) return o;
            var fz = o.fazendas[fazN];
            if (!fz) { fz = o.fazendas[fazN] = { nome: fazN, talhoes: {} }; }
            if (talN === null) return fz;
            var tl = fz.talhoes[talN];
            if (!tl) { tl = fz.talhoes[talN] = { nome: talN, porAno: {} }; }
            return tl;
          }
          function adicionar(osN, fazN, talN, anN, ativ) {
            var tl = obterNo(osN, fazN, talN);
            if (!tl.porAno[anN]) tl.porAno[anN] = {};
            tl.porAno[anN][ativ] = 1;
            contagemAtiv[ativ] = (contagemAtiv[ativ] || 0) + 1;
            if (anos.indexOf(anN) < 0) anos.push(anN);
          }
          // Área física do talhão: a MAIOR área registrada no período (culturas e
          // pecuária) — a mesma régua da linha de base "Área física" do 3.2/8.2.
          function medirFisica(osN, fazN, talN, valor) {
            var a = num(valor);
            if (isNaN(a) || a <= 0) return;
            chave = chaveTalhaoAtiv(osN, fazN, talN);
            if (!(chave in fisica) || a > fisica[chave]) fisica[chave] = a;
          }
          // 1) Culturas: nome base (sem o sufixo de unidade) para o eucalipto e
          //    a aroeira não aparecerem duas vezes (m³/ha e t/ha).
          var culturas = ObterDados.dados || [];
          for (i = 0; i < culturas.length; i++) {
            r = culturas[i];
            if (!passa(r)) continue;
            nome = nomeCulturaBase(r.cultura);
            if (!nome) continue;
            adicionar(r.os || '—', r.fazenda || '—', r.talhao || '—',
              chaveAnoAtiv(r.ano), nome);
            medirFisica(r.os || '—', r.fazenda || '—', r.talhao || '—', r.area);
          }
          // 2) Pecuária: entra como a atividade "Pecuária".
          var pecuaria = ObterDados.dadosPecuaria || [];
          for (i = 0; i < pecuaria.length; i++) {
            r = pecuaria[i];
            if (!passa(r)) continue;
            adicionar(r.os || '—', r.fazenda || '—', r.talhao || '—',
              chaveAnoAtiv(r.ano), 'Pecuária');
            medirFisica(r.os || '—', r.fazenda || '—', r.talhao || '—', r.area);
          }
          anos.sort(function (a, b) {
            var x = Number(a), y = Number(b);
            if (isNaN(x)) return 1;
            if (isNaN(y)) return -1;
            return x - y;
          });
          var ordemOs = Object.keys(arv).sort(porNomeAtiv);
          // Atividades do filtro atual (mais registros primeiro) → paleta de
          // cores e legenda dos painéis. A ordem também é a ordem das atividades
          // DENTRO das combinações do 3.8 (ex.: «Soja + Milho»).
          var atividades = Object.keys(contagemAtiv).sort(function (a, b) {
            if (contagemAtiv[b] !== contagemAtiv[a]) return contagemAtiv[b] - contagemAtiv[a];
            return porNomeAtiv(a, b);
          });
          return {
            arv: arv, anos: anos, atividades: atividades, contagem: contagemAtiv,
            fisica: fisica, ordemOs: ordemOs
          };
        }

        // ----- 3.6 Atividades por talhão · ano -----
        // Cada nó (OS · Fazenda · Talhão) é UMA linha: OS e fazenda são
        // agrupadores expansíveis, SEM dados nas colunas; o talhão lista, ano a
        // ano, os NOMES das atividades registradas (culturas + Pecuária), cada
        // uma no seu chip colorido. Não há métrica nem cálculo: as fontes são os
        // payloads de produtividade e de pecuária (a agregação é a fonte comum
        // `agregarAtividades`, a MESMA usada pelo 3.8).
        function renderAtividades() {
          if (!ativTabla) return;
          var d = agregarAtividades();
          var arv = d.arv, anos = d.anos, atividades = d.atividades;
          var ordemOs = d.ordemOs;
          var coresAtiv = coresDasAtividades(atividades);
          if (!ordemOs.length || !anos.length) {
            ativTabla.innerHTML = '';
            ativTabla.style.display = 'none';
            if (ativVazio) ativVazio.classList.add('visivel');
            return;
          }
          // Uma linha por nó: `pivotLazy` monta só as OS agora; as fazendas e
          // os talhões nascem na primeira abertura do nó de cima.
          function linhasAtiv(gid, nomeNo, nivel, dado, temFilhos) {
            var seta = temFilhos ? '<span class="ativ-seta">▶</span> ' : '';
            // `rowspan="1"`: no celular a célula do nome vira o título do
            // cartão (e não um chip "COLUNA valor"), como nos outros pivôs.
            var celNome = '<td class="ativ-nome ativ-nivel-' + nivel +
              (temFilhos ? ' ativ-clicavel' : '') + '" data-grupo="' + gid +
              '"' + (temFilhos ? ' data-toggle="1"' : '') + ' rowspan="1">' +
              seta + esc(nomeNo) + '</td>';
            var cels = anos.map(function (an) {
              var ativs = [];
              if (dado && dado.porAno && dado.porAno[an]) {
                ativs = Object.keys(dado.porAno[an]).sort(porNomeAtiv);
              }
              if (!ativs.length) return '<td class="ativ-cel"></td>';
              // Uma cor por atividade. Célula com MAIS DE UMA atividade no ano
              // sai como um CONJUNTO (`.ativ-combo`, pílula azul em volta dos
              // chips) — a marca do "combinado" (ex.: soja + milho) — sem
              // esconder a cor de cada atividade.
              var chips = ativs.map(function (a) {
                return chipAtividade(a, coresAtiv[a]);
              }).join('');
              return '<td class="ativ-cel ativ-tem">' +
                (ativs.length > 1 ? '<span class="ativ-combo">' + chips + '</span>' : chips) +
                '</td>';
            }).join('');
            return '<tr class="ativ-linha ativ-nivel-' + nivel + '">' +
              celNome + cels + '</tr>';
          }
          var recado = '<p class="muted ativ-recado">Cada talhão lista, ano a ' +
            'ano, os nomes das atividades registradas (culturas e pecuária), ' +
            'cada uma no seu chip colorido; quando o ano tem mais de uma ' +
            'atividade, elas saem juntas num conjunto azul. OS e fazenda ' +
            'são agrupadores expansíveis: clique no nome para abrir.</p>';
          // Legenda das cores: as atividades do filtro atual (mais registros
          // primeiro) com a MESMA cor dos chips das células.
          var leyenda = '<div class="ativ-leyenda" aria-label="Cores das atividades">' +
            '<span class="ativ-leyenda-titulo">Atividades</span>' +
            atividades.map(function (a) {
              return chipAtividade(a, coresAtiv[a]);
            }).join('') + '</div>';
          var headAnos = anos.map(function (an) {
            return '<th>' + esc(an) + '</th>';
          }).join('');
          ativTabla.innerHTML = recado + leyenda +
            '<table class="ativ-pivot"><thead><tr>' +
            '<th>OS · Fazenda · Talhão</th>' + headAnos +
            '</tr></thead><tbody></tbody></table>';
          var piv = ObterDados.pivotLazy({
            prefixo: 'ativ',
            corpo: ativTabla.querySelector('tbody'),
            linhas: linhasAtiv
          });
          ordemOs.forEach(function (osN) {
            var o = arv[osN];
            piv.raiz({
              nome: osN, nivel: 'os', coletar: function () { return o; },
              gerarFilhos: function () {
                return Object.keys(o.fazendas).sort(porNomeAtiv).map(function (fazN) {
                  var fz = o.fazendas[fazN];
                  return {
                    nome: fazN, nivel: 'faz', coletar: function () { return fz; },
                    gerarFilhos: function () {
                      return Object.keys(fz.talhoes).sort(porNomeAtiv).map(function (talN) {
                        var tl = fz.talhoes[talN];
                        return {
                          nome: talN, nivel: 'tal',
                          coletar: function () { return tl; }
                        };
                      });
                    }
                  };
                });
              }
            });
          });
          ativTabla.style.display = 'block';
          if (ativVazio) ativVazio.classList.remove('visivel');
        }

        // ----- 3.8 Área por combinação de atividades (talhão · ano) -----
        // Gráfico de linhas no MESMO estilo do 8.2 (casco `.prat-*`): uma linha
        // por COMBINAÇÃO de atividades do 3.6 — «Soja», «Soja + Milho», «Milho»,
        // «Pecuária», «Soja + Pecuária», ... — e uma linha tracejada de
        // referência com a área física do conjunto filtrado.
        // Regra de ouro das classes: cada talhão·ano entra numa ÚNICA combinação
        // (as atividades daquele talhão NAQUELE ano), então «Soja» e «Soja +
        // Milho» são classes diferentes e a área da soja sozinha nunca soma para
        // a combinação — nem a da combinação para a soja sozinha.
        // PECUÁRIA TOTAL: a pecuária vem SEMPRE acompanhada de uma cultura
        // forrageira (braquiária, Massai, ...) e as duas são a MESMA atividade —
        // pecuária de braquiária × pecuária de Massai. No 3.8 as forrageiras de
        // `CULTURAS_PECUARIA` são ABSORVIDAS na linha «Pecuária» quando o
        // talhão·ano tem pecuária: «Brachiaria + Pecuária» e «Massai + Pecuária»
        // somam-se em «Pecuária» (a pecuária total) e «Eucalipto + Brachiaria +
        // Pecuária» / «Eucalipto + Massai + Pecuária» somam-se em «Eucalipto +
        // Pecuária». Sem pecuária no ano a forrageira é cultura de
        // rotação/cobertura e segue com combinação própria; o 3.6 continua
        // mostrando o chip dela — é lá que se vê QUAL forrageira acompanha a
        // pecuária.
        // A área de cada talhão·ano é a ÁREA FÍSICA do talhão (a MAIOR área
        // registrada no período, entre culturas e pecuária — a mesma régua da
        // linha de base do 3.2/8.2), contada 1× por ano: o talhão não soma uma
        // vez por atividade. Por isso as combinações nunca passam da referência.
        // A paleta é DINÂMICA, como no 3.6: combinação de uma só atividade usa a
        // COR DO CHIP daquela atividade no 3.6 (continuidade visual entre os dois
        // painéis) e as combinações com mais de uma atividade recebem a paleta
        // padrão na ORDEM DA LEGENDA (as cores mais visíveis primeiro), sem
        // repetir enquanto houver cor livre — não existe mapa fixo cultura → cor.
        var COR_BASE_ATIV = ObterDados.COR_REFERENCIA;
        var REF_ATIV = 'Área física (base)';
        var ativLinhasOcultas = {};

        // Culturas que ACOMPANHAM a pecuária (forrageiras): a pecuária é sempre
        // registrada junto de uma delas (braquiária, Massai, ...) e as duas são a
        // MESMA atividade pecuária — a "pecuária total" do 3.8. Quando o
        // talhão·ano tem Pecuária, elas são absorvidas na linha «Pecuária»
        // («Brachiaria + Pecuária» e «Massai + Pecuária» somam-se em «Pecuária»);
        // sem pecuária no ano, a forrageira é cultura de rotação/cobertura e
        // segue com combinação própria. Comparação sem acentos e sem caixa
        // (`normValor`), para a lista valer com qualquer grafia.
        var CULTURAS_PECUARIA = ['brachiaria', 'massai'];

        function ehCulturaPecuaria(nome) {
          return CULTURAS_PECUARIA.indexOf(normValor(nome)) >= 0;
        }

        // Cor de cada combinação (ver o comentário do bloco acima).
        // Combinações com MAIS DE UMA atividade: nas LINHAS do 3.8 a paleta é
        // distribuída na ordem da legenda (as cores mais visíveis primeiro) e as
        // cores de PAPEL FIXO ficam reservadas — a referência (teto do gráfico)
        // nunca vira uma linha de combinação e o PRETO fica de fora (não
        // apareceria no fundo escuro); o cinza escuro é o último recurso.
        var CORES_COMBINACAO_RESERVADAS = [ObterDados.COR_REFERENCIA, '#000000'];
        var CORES_COMBINACAO_PROIBIDAS = [ObterDados.COR_REFERENCIA, '#000000',
          '#334155'];

        function coresDasCombinacoes(combosAtiv, atividades) {
          var coresAtiv = coresDasAtividades(atividades), usadas = {}, cor = {};
          var reserva = {}, multiplas = [];
          CORES_COMBINACAO_RESERVADAS.forEach(function (c) { usadas[c] = 1; });
          CORES_COMBINACAO_PROIBIDAS.forEach(function (c) { reserva[c] = 1; });
          Object.keys(combosAtiv).forEach(function (nome) {
            var ativs = combosAtiv[nome];
            if (ativs.length === 1 && coresAtiv[ativs[0]]) {
              cor[nome] = coresAtiv[ativs[0]];
              usadas[cor[nome]] = 1;
            } else {
              multiplas.push(nome);
            }
          });
          multiplas.sort(porNomeAtiv).forEach(function (nome, i) {
            var idx = ObterDados.escolherCor(CORES_ATIVIDADE, usadas, i, reserva);
            usadas[CORES_ATIVIDADE[idx]] = 1;
            cor[nome] = CORES_ATIVIDADE[idx];
          });
          return cor;
        }

        // Combinações do gráfico ordenadas para a legenda: primeiro as de uma só
        // atividade (as "puras"), depois as combinadas, ambas em ordem natural
        // (pt-BR). Dentro da combinação as atividades seguem a ordem do 3.6 (mais
        // registradas primeiro), o que produz «Soja + Milho».
        function ordenarCombinacoes(combosAtiv) {
          return Object.keys(combosAtiv).sort(function (a, b) {
            var na = combosAtiv[a].length, nb = combosAtiv[b].length;
            if (na !== nb) return na - nb;
            return porNomeAtiv(a, b);
          });
        }
        // Monta o gráfico: para cada talhão·ano sai o nome da combinação das suas
        // atividades; a área física do talhão é somada na MATRIZ combinação × ano
        // (1× por talhão·ano, nunca 1× por atividade).
        function renderAtivAreaLinhas() {
          if (!wrapAtivLinhas) return;
          var d = agregarAtividades();
          var anosNum = d.anos;
          var ordemAtiv = {}, combosAtiv = {}, matriz = {};
          d.atividades.forEach(function (a, i) { ordemAtiv[a] = i; });
          Object.keys(d.arv).forEach(function (osN) {
            var o = d.arv[osN];
            Object.keys(o.fazendas).forEach(function (fazN) {
              var fz = o.fazendas[fazN];
              Object.keys(fz.talhoes).forEach(function (talN) {
                var tl = fz.talhoes[talN];
                var areaTal = d.fisica[chaveTalhaoAtiv(osN, fazN, talN)] || 0;
                if (!(areaTal > 0)) return;     // sem área não há hectares a somar
                Object.keys(tl.porAno).forEach(function (anN) {
                  var ativsAno = Object.keys(tl.porAno[anN]);
                  if (!ativsAno.length) return;
                  // Pecuária no ano → as forrageiras que a acompanham entram na
                  // linha «Pecuária» (a pecuária total): braquiária + pecuária e
                  // Massai + pecuária são a MESMA combinação.
                  if (ativsAno.indexOf('Pecuária') >= 0) {
                    ativsAno = ativsAno.filter(function (a) {
                      return !ehCulturaPecuaria(a);
                    });
                  }
                  ativsAno.sort(function (a, b) {
                    return (ordemAtiv[a] || 0) - (ordemAtiv[b] || 0);
                  });
                  var nomeCombo = ativsAno.join(' + ');
                  if (!combosAtiv[nomeCombo]) combosAtiv[nomeCombo] = ativsAno;
                  if (!matriz[nomeCombo]) matriz[nomeCombo] = {};
                  matriz[nomeCombo][anN] = (matriz[nomeCombo][anN] || 0) + areaTal;
                });
              });
            });
          });
          var combos = ordenarCombinacoes(combosAtiv);
          // Referência: área física do conjunto filtrado (cada talhão conta 1×
          // pela MAIOR área registrada no período) — o teto das combinações.
          var areaFisica = 0;
          Object.keys(d.fisica).forEach(function (k) { areaFisica += d.fisica[k]; });
          var cor = coresDasCombinacoes(combosAtiv, d.atividades);
          cor[REF_ATIV] = COR_BASE_ATIV;

          if (!anosNum.length || !combos.length) {
            wrapAtivLinhas.innerHTML = '<p class="muted">' + (anosNum.length || combos.length
              ? 'Sem área de talhão para as combinações nos filtros selecionados.'
              : 'Nenhuma atividade corresponde aos filtros selecionados.') + '</p>';
            if (leyendaAtivLinhas) leyendaAtivLinhas.innerHTML = '';
            return;
          }

          // Legenda (clique mostra/oculta a linha da combinação); a referência
          // entra por ÚLTIMO e alterna como as demais.
          if (leyendaAtivLinhas) {
            var itens = combos.map(function (nome) {
              return '<button type="button" class="prat-leyenda-item' +
                (ativLinhasOcultas[nome] ? ' oculta' : '') + '" data-ativ="' + esc(nome) + '">' +
                '<span class="prat-leyenda-cor" style="background:' + cor[nome] + '"></span>' +
                esc(nome) + '</button>';
            });
            if (areaFisica > 0) {
              itens.push('<button type="button" class="prat-leyenda-item' +
                (ativLinhasOcultas[REF_ATIV] ? ' oculta' : '') + '" data-ativ="' + esc(REF_ATIV) + '">' +
                '<span class="prat-leyenda-cor" style="background:' + COR_BASE_ATIV + '"></span>' +
                esc(REF_ATIV) + '</button>');
            }
            leyendaAtivLinhas.innerHTML = itens.join('');
            Array.prototype.forEach.call(leyendaAtivLinhas.querySelectorAll('[data-ativ]'), function (b) {
              b.addEventListener('click', function () {
                var nome = b.getAttribute('data-ativ');
                if (ativLinhasOcultas[nome]) { delete ativLinhasOcultas[nome]; }
                else { ativLinhasOcultas[nome] = 1; }
                renderAtivAreaLinhas();
              });
            });
          }
          var visiveis = combos.filter(function (nome) { return !ativLinhasOcultas[nome]; });
          var refVisivel = areaFisica > 0 && !ativLinhasOcultas[REF_ATIV];
          var maxReal = 0;
          visiveis.forEach(function (nome) {
            anosNum.forEach(function (an) {
              var v = matriz[nome][an] || 0; if (v > maxReal) maxReal = v;
            });
          });
          // Sem isto a linha da referência sairia por cima do quadro.
          if (refVisivel && areaFisica > maxReal) maxReal = areaFisica;
          var escala = escalaCult(maxReal);
          var maxY = escala.max, ticks = escala.ticks;

          var W = 1040, H = 460, mL = 84, mR = 104, mT = 30, mB = 56;
          var pw = W - mL - mR, ph = H - mT - mB;
          var passoX = anosNum.length > 1 ? pw / (anosNum.length - 1) : pw;
          function xi(an) {
            var i = anosNum.indexOf(an);
            return anosNum.length === 1 ? mL + pw / 2 : mL + i * passoX;
          }
          function yi(v) { return mT + ph - (v / maxY) * ph; }

          var partes = [], k, vv, yy;
          partes.push('<rect class="prat-fundo" x="' + mL + '" y="' + mT + '" width="' + pw + '" height="' + ph + '" rx="10"></rect>');
          for (k = 0; k <= ticks; k++) {
            vv = escala.passo * k; yy = yi(vv);
            partes.push('<line class="prat-grid" x1="' + mL + '" y1="' + yy + '" x2="' + (mL + pw) + '" y2="' + yy + '"></line>');
            partes.push('<text class="prat-eixo-txt" x="' + (mL - 12) + '" y="' + (yy + 4) + '" text-anchor="end">' + fmtNum(vv, 0) + '</text>');
          }
          partes.push('<line class="prat-eixo" x1="' + mL + '" y1="' + mT + '" x2="' + mL + '" y2="' + (mT + ph) + '"></line>');
          partes.push('<line class="prat-eixo" x1="' + mL + '" y1="' + (mT + ph) + '" x2="' + (mL + pw) + '" y2="' + (mT + ph) + '"></line>');
          partes.push('<text class="prat-unit" x="' + mL + '" y="' + (mT - 12) + '">hectares (ha)</text>');
          anosNum.forEach(function (an) {
            var xx = xi(an);
            if (anosNum.length > 1) {
              partes.push('<line class="prat-grid-vert" x1="' + xx + '" y1="' + mT + '" x2="' + xx + '" y2="' + (mT + ph) + '"></line>');
            }
            partes.push('<text class="prat-eixo-txt" x="' + xx + '" y="' + (H - mB + 24) + '" text-anchor="middle">' + esc(an) + '</text>');
          });
          partes.push('<line class="prat-guia" x1="0" y1="' + mT + '" x2="0" y2="' + (mT + ph) + '" opacity="0"></line>');

          visiveis.forEach(function (nome) {
            var pts = anosNum.map(function (an) { return { x: xi(an), y: yi(matriz[nome][an] || 0) }; });
            partes.push('<path class="prat-line" stroke="' + cor[nome] + '" d="' + caminhoCult(pts) + '"></path>');
            pts.forEach(function (pt, idx) {
              var v = matriz[nome][anosNum[idx]] || 0;
              partes.push('<circle class="prat-dot" cx="' + pt.x + '" cy="' + pt.y + '" r="3.4" fill="' + cor[nome] + '">' +
                '<title>' + esc(nome) + ' · ' + esc(anosNum[idx]) + ': ' + fmtNum(v) + ' ha</title></circle>');
            });
          });

          // A REFERÊNCIA (área física do conjunto filtrado) entra DEPOIS das
          // combinações: valor constante no período e tracejado, como no 3.2/8.2.
          if (refVisivel) {
            var ptsRef = anosNum.map(function (an) { return { x: xi(an), y: yi(areaFisica) }; });
            partes.push('<path class="prat-line" stroke="' + COR_BASE_ATIV +
              '" style="stroke-width:2.2" stroke-dasharray="7 5" d="' + caminhoCult(ptsRef) + '"></path>');
            ptsRef.forEach(function (pt, idx) {
              partes.push('<circle class="prat-dot" cx="' + pt.x + '" cy="' + pt.y + '" r="3.4" fill="' + COR_BASE_ATIV + '">' +
                '<title>' + esc(REF_ATIV) + ' · ' + esc(anosNum[idx]) + ': ' + fmtNum(areaFisica) + ' ha</title></circle>');
            });
          }

          anosNum.forEach(function (an) {
            var xx = xi(an);
            var esq = Math.max(mL, xx - passoX / 2);
            var dir = Math.min(mL + pw, xx + passoX / 2);
            partes.push('<rect class="prat-hot" data-ano="' + esc(an) + '" data-x="' + xx + '" x="' + esq +
              '" y="' + mT + '" width="' + (dir - esq) + '" height="' + ph + '" fill="transparent"></rect>');
          });

          wrapAtivLinhas.innerHTML = '<svg viewBox="0 0 ' + W + ' ' + H + '" preserveAspectRatio="xMidYMid meet" role="img" aria-label="Área por combinação de atividades e por ano">' + partes.join('') + '</svg>';
          // Dica por ano + linha-guia (o mesmo comportamento do 8.2): lista as
          // combinações com hectares no ano, da MAIOR para a menor, com a
          // referência da área física junto.
          var tip = document.createElement('div');
          tip.className = 'prat-tip';
          tip.hidden = true;
          wrapAtivLinhas.appendChild(tip);
          var guia = wrapAtivLinhas.querySelector('.prat-guia');
          Array.prototype.forEach.call(wrapAtivLinhas.querySelectorAll('.prat-hot'), function (rc) {
            rc.addEventListener('mouseenter', function () {
              var an = rc.getAttribute('data-ano');
              if (guia) {
                guia.setAttribute('x1', rc.getAttribute('data-x'));
                guia.setAttribute('x2', rc.getAttribute('data-x'));
                guia.setAttribute('opacity', '1');
              }
              var filas = visiveis.map(function (nome) { return { n: nome, v: matriz[nome][an] || 0 }; })
                .filter(function (o) { return o.v > 0; });
              if (refVisivel) { filas.push({ n: REF_ATIV, v: areaFisica }); }
              filas.sort(function (a, b) { return b.v - a.v; });
              var html = '<div class="prat-tip-tit">' + esc(an) + '</div>';
              if (!filas.length) { html += '<div class="prat-tip-vazio">sem hectares</div>'; }
              filas.forEach(function (o) {
                html += '<div class="prat-tip-row"><span class="prat-tip-cor" style="background:' + cor[o.n] + '"></span>' +
                  '<span class="prat-tip-nome">' + esc(o.n) + '</span>' +
                  '<span class="prat-tip-val">' + fmtNum(o.v) + ' ha</span></div>';
              });
              tip.innerHTML = html;
              tip.hidden = false;
              var rr = rc.getBoundingClientRect(), wr = wrapAtivLinhas.getBoundingClientRect();
              var cx = rr.left + rr.width / 2 - wr.left;
              cx = Math.max(110, Math.min(wr.width - 110, cx));
              tip.style.left = cx + 'px';
            });
            rc.addEventListener('mouseleave', function () {
              tip.hidden = true;
              if (guia) guia.setAttribute('opacity', '0');
            });
          });
        }

        // ----- 3.7 Matriz de produtividade por cultura (talhão · ano) -----
        // ----- 3.7 Matriz de produtividade por cultura (talhão · ano) -----
        // Um subpainel por cultura (agrupada por `cultura` + `unidade`, como no
        // 3.5): as LINHAS são os talhões (OS · Fazenda · Talhão) e as COLUNAS são
        // a Média do talhão na cultura + uma coluna por ano, com a produtividade
        // daquela cultura naquele ano — sempre na unidade da cultura, sem
        // conversão (a Média é ponderada pela área, a mesma regra do 3.5: só a
        // área dos registros COM produtividade informada entra no denominador).
        // A paleta (CORES_MATRIZ_PROD) é ÚNICA para o subpainel INTEIRO: o pior
        // resultado da cultura sai no vermelho escuro e o melhor no verde escuro
        // — a leitura é "em quais talhões estão os piores resultados". É a
        // diferença em relação ao 3.5, onde cada LINHA tem a sua própria faixa.
        function renderMatrizCultura(lista) {
          if (!wrapMatrizCultura) return;
          var grupos = {}, chaves, i, r, a, ch;
          for (i = 0; i < lista.length; i++) {
            r = lista[i];
            a = num(r.area);
            if (isNaN(a) || a <= 0) continue;
            ch = (r.cultura || '') + '\u0000' + (r.unidade || '');
            if (!grupos[ch]) {
              grupos[ch] = {
                cultura: r.cultura || '—', unidade: r.unidade || '', linhas: []
              };
            }
            grupos[ch].linhas.push(r);
          }
          chaves = ordenarChavesCultura(grupos);
          if (!chaves.length) {
            wrapMatrizCultura.innerHTML = '';
            wrapMatrizCultura.style.display = 'none';
            if (vazioMatrizCultura) vazioMatrizCultura.classList.add('visivel');
            return;
          }
          var recado = '<p class="muted pmz-recado">Uma matriz por cultura: cada ' +
            'linha é um talhão (OS · Fazenda · Talhão) e cada coluna é a Média do ' +
            'talhão na cultura mais um ano do período — o valor é a produtividade ' +
            'daquela cultura naquele ano, na unidade da cultura (a Média é ' +
            'ponderada pela área). A cor é relativa ao painel INTEIRO da cultura: ' +
            'o pior resultado sai no vermelho escuro e o melhor no verde escuro, ' +
            'mostrando em quais talhões estão os piores resultados (no 3.5, ao ' +
            'contrário, cada linha tem a sua própria faixa). ' +
            'Clique no título do subpainel para abrir.</p>';
          wrapMatrizCultura.innerHTML = recado;
          chaves.forEach(function (chave, idx) {
            var g = grupos[chave];
            var detalhe = document.createElement('details');
            detalhe.className = 'prod-crop';
            var tituloDet = document.createElement('summary');
            tituloDet.innerHTML = '<span class="prod-crop-titulo">3.7.' + (idx + 1) +
              ' · ' + esc(g.cultura) + (unidadeDoRotulo(g.cultura, g.unidade) ? ' <span class="prod-unidade">(' +
                esc(g.unidade) + ')</span>' : '') + '</span>';
            var cuerpo = document.createElement('div');
            cuerpo.className = 'prod-crop-cuerpo';
            var tabla = document.createElement('div');
            tabla.className = 'prod-crop-tabla';
            cuerpo.appendChild(tabla);
            detalhe.appendChild(tituloDet);
            detalhe.appendChild(cuerpo);
            wrapMatrizCultura.appendChild(detalhe);
            // A matriz só é montada na PRIMEIRA abertura do subpainel (mesmo
            // padrão do 3.5/5.5).
            detalhe.addEventListener('toggle', function () {
              if (!detalhe.open || tabla.getAttribute('data-montado') === '1') return;
              tabla.setAttribute('data-montado', '1');
              montarMatrizCultura(g, tabla);
            });
          });
          wrapMatrizCultura.style.display = 'block';
          if (vazioMatrizCultura) vazioMatrizCultura.classList.remove('visivel');
        }

        // Matriz de UMA cultura: cada linha é um talhão e as colunas são a Média
        // (todos os anos) + uma por ano, com a produtividade ponderada pela área
        // (Σ área × produtividade ÷ Σ área dos registros com produção informada).
        // Só entram registros com área > 0 e produtividade INFORMADA — `0` é
        // produção zero (conta) e produtividade ausente (`null` = não colhido)
        // sai "—", como no 3.5.
        function montarMatrizCultura(g, el) {
          var anos = anosCultura(g.linhas);
          var talhoes = {}, ordem = [], i, r, k, an, a, p;
          var j, ai, d, mv, dv, t, tt, faixa;
          for (i = 0; i < g.linhas.length; i++) {
            r = g.linhas[i];
            k = (r.os || '—') + '\u0000' + (r.fazenda || '—') + '\u0000' + (r.talhao || '—');
            if (!talhoes[k]) {
              talhoes[k] = {
                os: r.os || '—', fazenda: r.fazenda || '—', talhao: r.talhao || '—',
                area: 0, total: 0, prodN: 0, porAno: {}
              };
              ordem.push(k);
            }
            an = (r.ano === null || r.ano === undefined) ? '—' : String(r.ano).trim();
            if (!an) an = '—';
            a = num(r.area);
            p = num(r.produtividade);
            // Só área > 0 com produtividade INFORMADA entra (mesma regra do 3.5):
            // `0` é produção zero (conta no total E na área da média) e `null`
            // (não colhido) fica fora dos dois.
            if (isNaN(a) || a <= 0 || isNaN(p)) continue;
            if (!talhoes[k].porAno[an]) {
              talhoes[k].porAno[an] = { area: 0, total: 0, prodN: 0 };
            }
            talhoes[k].area += a;
            talhoes[k].total += a * p;
            talhoes[k].prodN++;
            talhoes[k].porAno[an].area += a;
            talhoes[k].porAno[an].total += a * p;
            talhoes[k].porAno[an].prodN++;
          }
          // Ordem estável: OS → Fazenda → Talhão (natural, 10 antes de 9).
          ordem.sort(function (x, y) {
            var ax = talhoes[x], ay = talhoes[y];
            return porNomeAtiv(ax.os, ay.os) || porNomeAtiv(ax.fazenda, ay.fazenda) ||
              porNomeAtiv(ax.talhao, ay.talhao);
          });
          // Média ponderada de um acumulador (`null` quando não há o que medir).
          function mediaPonderada(c) {
            return (c && c.prodN > 0 && c.area > 0) ? c.total / c.area : null;
          }
          // Faixa do subpainel INTEIRO: a Média de cada talhão + cada célula de
          // ano (é o que a paleta do 3.7 mede — uma palheta para TODOS os dados
          // da cultura, mostrando em quais talhões estão os piores resultados).
          var valores = [];
          for (j = 0; j < ordem.length; j++) {
            t = talhoes[ordem[j]];
            mv = mediaPonderada(t);
            if (mv !== null) valores.push(mv);
            for (ai = 0; ai < anos.length; ai++) {
              dv = mediaPonderada(t.porAno[anos[ai]]);
              if (dv !== null) valores.push(dv);
            }
          }
          faixa = faixaCalor(valores);
          // Célula da matriz: a cor viaja na variável CSS `--pmz-cor` e só entra
          // quando há valor E faixa (`data-col` dá o rótulo do cartão no celular).
          function celMatriz(v, rotulo) {
            var col = ' data-col="' + esc(rotulo) + '"';
            if (v === null || v === undefined) {
              return '<td class="pmz-cel pmz-sem-valor"' + col + '>—</td>';
            }
            var pos = posicaoCalor(v, faixa);
            if (pos === null) {
              return '<td class="pmz-cel"' + col + '>' + fmtNum(v, 2) + '</td>';
            }
            return '<td class="pmz-cel pmz-heat"' + col + ' style="--pmz-cor:' +
              corCalor(pos, CORES_MATRIZ_PROD, .42) + '">' + fmtNum(v, 2) + '</td>';
          }
          if (!ordem.length || !anos.length) {
            el.innerHTML = '<p class="muted">Sem produtividade por talhão/ano ' +
              'para esta cultura nos filtros selecionados.</p>';
            return;
          }
          // Legenda da escala do subpainel (Pior ← vermelho escuro … verde
          // escuro → Melhor) com a faixa exibida em números.
          var leyenda = '<div class="pmz-leyenda" aria-label="Escala de cores da cultura">' +
            '<span class="pmz-leyenda-titulo">Pior</span>' +
            CORES_MATRIZ_PROD.map(function (c) {
              return '<span class="pmz-leyenda-cor" style="--pmz-cor:rgba(' + c[0] +
                ', ' + c[1] + ', ' + c[2] + ', .42)"></span>';
            }).join('') +
            '<span class="pmz-leyenda-titulo">Melhor</span>' +
            (faixa ? '<span class="pmz-leyenda-faixa">' + fmtNum(faixa.min, 1) + ' – ' +
              fmtNum(faixa.max, 1) + (g.unidade ? ' ' + esc(g.unidade) : '') +
              '</span>' : '') +
            '</div>';
          var headAnos = anos.map(function (x) {
            return '<th scope="col">' + esc(x) + '</th>';
          }).join('');
          var corpo = ordem.map(function (kk) {
            tt = talhoes[kk];
            return '<tr><th scope="row" class="pmz-nome">' + esc(tt.talhao) +
              '<span class="pmz-sub">' + esc(tt.os + ' · ' + tt.fazenda) + '</span></th>' +
              celMatriz(mediaPonderada(tt), 'Média') +
              anos.map(function (x) {
                return celMatriz(mediaPonderada(tt.porAno[x]), x);
              }).join('') +
              '</tr>';
          }).join('');
          el.innerHTML = leyenda + '<table class="pmz-tabla"><thead><tr>' +
            '<th scope="col">Talhão</th><th scope="col">Média</th>' + headAnos +
            '</tr></thead><tbody>' + corpo + '</tbody></table>';
        }

        // ----- 3.2 Área das culturas por ano (linhas) -----
        // ----- 3.3 Produtividade unificada em t/ha por ano (linhas) -----
        // As séries (culturas) e as demais linhas destes gráficos recebem a
        // PALETA PADRÃO (`ObterDados.CORES`) por `ObterDados.coresDasSeries`,
        // que NÃO repete cor enquanto houver cor livre. As séries de papel fixo
        // (Área física, Pecuária e Total) declaram a sua cor e ficam reservadas.

        // Nome base da cultura: remove o sufixo de unidade de produtividade
        // (ex.: "Eucalipto (t/ha)" → "Eucalipto") para que a área de uma cultura
        // apareça UMA ÚNICA VEZ, independentemente de ter mais de uma forma de
        // medir (eucalipto e aroeira: m³/ha e t/ha).
        function nomeCulturaBase(c) {
          return String(c === null || c === undefined ? '' : c).replace(
            /\s*\((?:t\/ha|m³\/ha|sc\/ha|@\/ha|sc benef\.\/ha|cx 40,8 kg\/ha)\)\s*$/, '').trim();
        }

        function chaveAnoCult(v) {
          if (v === null || v === undefined) return null;
          var s = String(v).trim();
          return s === '' ? null : s;
        }

        function anosDaMatrizCult(matriz) {
          var mapa = {}, arr = [], c, an;
          for (c in matriz) {
            if (!Object.prototype.hasOwnProperty.call(matriz, c)) continue;
            for (an in matriz[c]) {
              if (Object.prototype.hasOwnProperty.call(matriz[c], an)) mapa[an] = 1;
            }
          }
          arr = Object.keys(mapa);
          arr.sort(function (a, b) {
            var x = Number(a), y = Number(b);
            if (isNaN(x)) return 1;
            if (isNaN(y)) return -1;
            return x - y;
          });
          return arr;
        }

        // Máximo "bonito" do eixo Y (1/2/5 × 10ⁿ).
        function escalaCult(maxV) {
          if (!(maxV > 0)) return { max: 1, passo: 1, ticks: 5 };
          var bruto = maxV / 5;
          var mag = Math.pow(10, Math.floor(Math.log(bruto) / Math.LN10));
          var norm = bruto / mag, passo;
          if (norm <= 1) passo = 1; else if (norm <= 2) passo = 2;
          else if (norm <= 5) passo = 5; else passo = 10;
          passo *= mag;
          var max = Math.ceil(maxV / passo) * passo;
          return { max: max, passo: passo, ticks: Math.max(1, Math.round(max / passo)) };
        }

        // Curva suave (Catmull-Rom → Bézier).
        function caminhoCult(pts) {
          if (!pts.length) return '';
          if (pts.length === 1) return 'M' + pts[0].x + ',' + pts[0].y;
          var d = 'M' + pts[0].x + ',' + pts[0].y;
          for (var i = 0; i < pts.length - 1; i++) {
            var p0 = pts[i - 1] || pts[i], p1 = pts[i], p2 = pts[i + 1], p3 = pts[i + 2] || p2;
            d += 'C' + (p1.x + (p2.x - p0.x) / 6) + ',' + (p1.y + (p2.y - p0.y) / 6) + ' ' +
              (p2.x - (p3.x - p1.x) / 6) + ',' + (p2.y - (p3.y - p1.y) / 6) + ' ' +
              p2.x + ',' + p2.y;
          }
          return d;
        }

        // Desenha um gráfico de linhas multi-série (cultura × ano) com legenda
        // clicável e tooltip por ano. Usado pelos painéis 3.2 (área) e 3.3 (t/ha).
        function montarGraficoCulturas(cfg) {
          var container = cfg.container, leyenda = cfg.leyenda;
          if (!container) return;
          var series = cfg.series || [];
          var anosNum = cfg.anos || [];
          if (!series.length || !anosNum.length) {
            container.innerHTML = '<p class="muted">' + (cfg.vazio || 'Sem dados para o gráfico.') + '</p>';
            if (leyenda) leyenda.innerHTML = '';
            return;
          }
          // Cores: paleta padrão, sem repetir cor (as séries de papel fixo ficam
          // reservadas — ver `ObterDados.coresDasSeriesDoGrafico`).
          var cor = ObterDados.coresDasSeriesDoGrafico(series);
          var ocultas = cfg.ocultas || {};

          if (leyenda) {
            leyenda.innerHTML = series.map(function (s) {
              var oc = ocultas[s.nome] ? ' oculta' : '';
              return '<button type="button" class="prod-linhas-leyenda-item' + oc + '" data-serie="' + esc(s.nome) + '">' +
                '<span class="prod-linhas-leyenda-cor" style="background:' + cor[s.nome] + '"></span>' + esc(s.rotulo || s.nome) + '</button>';
            }).join('');
            Array.prototype.forEach.call(leyenda.querySelectorAll('[data-serie]'), function (b) {
              b.addEventListener('click', function () {
                var nome = b.getAttribute('data-serie');
                if (ocultas[nome]) { delete ocultas[nome]; } else { ocultas[nome] = 1; }
                montarGraficoCulturas(cfg);
              });
            });
          }

          var visiveis = series.filter(function (s) { return !ocultas[s.nome]; });
          var maxReal = 0;
          visiveis.forEach(function (s) {
            anosNum.forEach(function (an) { var v = s.valores[an] || 0; if (v > maxReal) maxReal = v; });
          });
          var escala = escalaCult(maxReal);
          var maxY = escala.max, ticks = escala.ticks;

          var W = 1040, H = 460, mL = 84, mR = 104, mT = 30, mB = 56;
          var pw = W - mL - mR, ph = H - mT - mB;
          var passoX = anosNum.length > 1 ? pw / (anosNum.length - 1) : pw;
          function xi(an) {
            var i = anosNum.indexOf(an);
            return anosNum.length === 1 ? mL + pw / 2 : mL + i * passoX;
          }
          function yi(v) { return mT + ph - (v / maxY) * ph; }

          var partes = [], k, vv, yy;
          partes.push('<rect class="pl-fundo" x="' + mL + '" y="' + mT + '" width="' + pw + '" height="' + ph + '" rx="10"></rect>');
          for (k = 0; k <= ticks; k++) {
            vv = escala.passo * k; yy = yi(vv);
            partes.push('<line class="pl-grid" x1="' + mL + '" y1="' + yy + '" x2="' + (mL + pw) + '" y2="' + yy + '"></line>');
            partes.push('<text class="pl-eixo-txt" x="' + (mL - 12) + '" y="' + (yy + 4) + '" text-anchor="end">' + fmtNum(vv, 0) + '</text>');
          }
          partes.push('<line class="pl-eixo" x1="' + mL + '" y1="' + mT + '" x2="' + mL + '" y2="' + (mT + ph) + '"></line>');
          partes.push('<text class="pl-unit" x="' + mL + '" y="' + (mT - 12) + '">' + esc(cfg.unidade) + '</text>');
          anosNum.forEach(function (an) {
            var xx = xi(an);
            if (anosNum.length > 1) {
              partes.push('<line class="pl-grid-vert" x1="' + xx + '" y1="' + mT + '" x2="' + xx + '" y2="' + (mT + ph) + '"></line>');
            }
            partes.push('<text class="pl-eixo-txt" x="' + xx + '" y="' + (H - mB + 24) + '" text-anchor="middle">' + esc(an) + '</text>');
          });
          partes.push('<line class="pl-guia" x1="0" y1="' + mT + '" x2="0" y2="' + (mT + ph) + '" opacity="0"></line>');

          visiveis.forEach(function (s) {
            var pts = anosNum.map(function (an) { return { x: xi(an), y: yi(s.valores[an] || 0) }; });
            partes.push('<path class="pl-line" stroke="' + cor[s.nome] + '"' +
              (s.largura ? ' style="stroke-width:' + s.largura + '"' : '') +
              (s.dash ? ' stroke-dasharray="' + s.dash + '"' : '') + ' d="' + caminhoCult(pts) + '"></path>');
            pts.forEach(function (pt, idx) {
              var v = s.valores[anosNum[idx]] || 0;
              partes.push('<circle class="pl-dot" cx="' + pt.x + '" cy="' + pt.y + '" r="3.4" fill="' + cor[s.nome] + '">' +
                '<title>' + esc(s.rotulo || s.nome) + ' · ' + esc(anosNum[idx]) + ': ' + fmtNum(v) + ' ' + esc(cfg.unidadeCurta) + '</title></circle>');
            });
          });

          anosNum.forEach(function (an) {
            var xx = xi(an);
            var esq = Math.max(mL, xx - passoX / 2);
            var dir = Math.min(mL + pw, xx + passoX / 2);
            partes.push('<rect class="pl-hot" data-ano="' + esc(an) + '" data-x="' + xx + '" x="' + esq +
              '" y="' + mT + '" width="' + (dir - esq) + '" height="' + ph + '" fill="transparent"></rect>');
          });

          container.innerHTML = '<svg viewBox="0 0 ' + W + ' ' + H + '" preserveAspectRatio="xMidYMid meet" role="img" aria-label="' + esc(cfg.aria || '') + '">' + partes.join('') + '</svg>';

          var tip = document.createElement('div');
          tip.className = 'prod-linhas-tip';
          tip.hidden = true;
          container.appendChild(tip);
          var guia = container.querySelector('.pl-guia');
          Array.prototype.forEach.call(container.querySelectorAll('.pl-hot'), function (rc) {
            rc.addEventListener('mouseenter', function () {
              var an = rc.getAttribute('data-ano');
              if (guia) {
                guia.setAttribute('x1', rc.getAttribute('data-x'));
                guia.setAttribute('x2', rc.getAttribute('data-x'));
                guia.setAttribute('opacity', '1');
              }
              var filas = visiveis.map(function (s) { return { nome: s.nome, rotulo: s.rotulo || s.nome, v: s.valores[an] || 0 }; })
                .filter(function (o) { return o.v > 0; })
                .sort(function (a, b) { return b.v - a.v; });
              var html = '<div class="pl-tip-tit">' + esc(an) + '</div>';
              if (!filas.length) { html += '<div class="pl-tip-vazio">sem dados</div>'; }
              filas.forEach(function (o) {
                html += '<div class="pl-tip-row"><span class="pl-tip-cor" style="background:' + cor[o.nome] + '"></span>' +
                  '<span class="pl-tip-nome">' + esc(o.rotulo) + '</span>' +
                  '<span class="pl-tip-val">' + fmtNum(o.v) + ' ' + esc(cfg.unidadeCurta) + '</span></div>';
              });
              tip.innerHTML = html;
              tip.hidden = false;
              var rr = rc.getBoundingClientRect(), wr = container.getBoundingClientRect();
              var cx = rr.left + rr.width / 2 - wr.left;
              cx = Math.max(110, Math.min(wr.width - 110, cx));
              tip.style.left = cx + 'px';
            });
            rc.addEventListener('mouseleave', function () {
              tip.hidden = true;
              if (guia) guia.setAttribute('opacity', '0');
            });
          });
        }

        // Renderizador de linhas multi-série exposto no escopo comum para ser
        // reutilizado por outros painéis (ex.: fertilizantes 5.2–5.4).
        ObterDados.montarGrafico = montarGraficoCulturas;

        // Renderizador multi-ESCALA (uma régua vertical por eixo) exposto no
        // escopo comum: é usado pelo painel 4.2 e pelos gráficos 7.2/7.3, que
        // vivem em IIFEs próprios.
        ObterDados.montarGraficoEixos = montarGraficoEixos;

        function cmpCultura(a, b) { return a.localeCompare(b, 'pt-BR', { numeric: true }); }

        // 3.2 — hectares (ha) de cada cultura ao longo dos anos. A área é somada
        // por cultura (nome base) e por ano; cada cultura (eucalipto/aroeira
        // inclusive) aparece UMA única vez.
        function renderAreaCulturasLinhas(lista) {
          if (!wrapAreaLinhas) return;
          // Área física do conjunto filtrado: cada talhão (os + fazenda +
          // talhão) conta 1× pela MAIOR área registrada entre as safras
          // (mesma regra do painel de área). É a linha de BASE do gráfico: o
          // "Total" das culturas pode ultrapassá-la porque o mesmo talhão
          // recebe mais de uma atividade (cultura) no mesmo ano e cada
          // atividade soma a área do talhão.
          var fisicaTalhao = {}, fk, fi, fr, fa;
          for (fi = 0; fi < lista.length; fi++) {
            fr = lista[fi];
            fa = num(fr.area);
            if (isNaN(fa) || fa <= 0) continue;
            fk = String(fr.os) + '\u0000' + String(fr.fazenda) + '\u0000' + String(fr.talhao);
            if (!(fk in fisicaTalhao) || fa > fisicaTalhao[fk]) {
              fisicaTalhao[fk] = fa;
            }
          }
          var areaFisicaTotal = 0;
          Object.keys(fisicaTalhao).forEach(function (kk) {
            areaFisicaTotal += fisicaTalhao[kk];
          });
          var mapa = {}, i, r, c, an, a;
          for (i = 0; i < lista.length; i++) {
            r = lista[i];
            a = num(r.area);
            if (isNaN(a) || a <= 0) continue;
            c = nomeCulturaBase(r.cultura);
            if (!c) continue;
            an = chaveAnoCult(r.ano);
            if (an === null) continue;
            if (!mapa[c]) mapa[c] = {};
            mapa[c][an] = (mapa[c][an] || 0) + a;
          }
          var series = Object.keys(mapa).sort(cmpCultura).map(function (nome) {
            return { nome: nome, valores: mapa[nome] };
          });

          // Série de BASE: área física (valor constante no período exibido).
          // As chaves de ano entram depois, quando a lista de anos é conhecida.
          var serieFisica = null;
          if (areaFisicaTotal > 0) {
            serieFisica = { nome: 'Área física (base)', valores: {},
              cor: ObterDados.COR_REFERENCIA, largura: 2.2, dash: '7 5' };
            series.push(serieFisica);
          }

          // Série de Pecuária (área de pastagem, ha) — reaproveita os dados de
          // pecuária, filtrados pelos mesmos filtros globais.
          var pec = {}, listaPec = filtrarPecuaria(), rp, ap, anp;
          for (i = 0; i < listaPec.length; i++) {
            rp = listaPec[i];
            ap = num(rp.area);
            if (isNaN(ap) || ap <= 0) continue;
            anp = chaveAnoCult(rp.ano);
            if (anp === null) continue;
            pec[anp] = (pec[anp] || 0) + ap;
          }
          if (Object.keys(pec).length) {
            series.push({ nome: 'Pecuária', valores: pec, cor: ObterDados.COR_PECUARIA });
          }

          // Total por ano = soma de TODAS AS CULTURAS (a pecuária fica FORA do
          // total: não é cultura e evitaria duplicar área em áreas em rotação).
          var total = {}, cn, ax;
          for (cn in mapa) {
            if (!Object.prototype.hasOwnProperty.call(mapa, cn)) continue;
            for (ax in mapa[cn]) {
              if (Object.prototype.hasOwnProperty.call(mapa[cn], ax)) {
                total[ax] = (total[ax] || 0) + mapa[cn][ax];
              }
            }
          }
          if (Object.keys(total).length) {
            series.push({ nome: 'Total', valores: total, cor: ObterDados.COR_TOTAL, largura: 3.8 });
          }

          // Anos exibidos: união entre culturas, pecuária e total.
          var anosSet = {};
          Object.keys(mapa).forEach(function (nm) {
            Object.keys(mapa[nm]).forEach(function (x) { anosSet[x] = 1; });
          });
          Object.keys(pec).forEach(function (x) { anosSet[x] = 1; });
          Object.keys(total).forEach(function (x) { anosSet[x] = 1; });
          var anosFinal = Object.keys(anosSet).sort(function (a, b) {
            var x = Number(a), y = Number(b);
            if (isNaN(x)) return 1;
            if (isNaN(y)) return -1;
            return x - y;
          });

          // Preenche a linha de BASE (área física) em TODOS os anos exibidos —
          // é constante, serve de referência para o Total das culturas.
          if (serieFisica && anosFinal.length) {
            anosFinal.forEach(function (ax) { serieFisica.valores[ax] = areaFisicaTotal; });
          }

          montarGraficoCulturas({
            container: wrapAreaLinhas, leyenda: leyendaAreaLinhas,
            series: series, anos: anosFinal, ocultas: areaOcultas,
            unidade: 'hectares (ha)', unidadeCurta: 'ha',
            vazio: 'Nenhuma área de cultura nos filtros selecionados.',
            aria: 'Área das culturas por ano (ha)'
          });
        }

        // 3.3 — produtividade por hectare unificada em t/ha. Só entram valores
        // positivos de unidades com conversão de massa (t/ha, sc/ha, @/ha,
        // sc benef./ha e cx 40,8 kg/ha); m³/ha NÃO converte e fica fora.
        function renderProdTHaLinhas(lista) {
          if (!wrapProdLinhas) return;
          var soma = {}, cont = {}, i, r, c, an, k, v, f;
          for (i = 0; i < lista.length; i++) {
            r = lista[i];
            v = num(r.produtividade);
            if (isNaN(v) || v <= 0) continue;
            f = num(r.fator_t_ha);
            if (isNaN(f) || f <= 0) continue;
            c = nomeCulturaBase(r.cultura);
            if (!c) continue;
            an = chaveAnoCult(r.ano);
            if (an === null) continue;
            k = c + '\u0000' + an;
            soma[k] = (soma[k] || 0) + v * f;
            cont[k] = (cont[k] || 0) + 1;
          }
          var mapa = {};
          Object.keys(soma).forEach(function (kk) {
            var p = kk.split('\u0000'), nome = p[0], ano = p[1];
            if (!mapa[nome]) mapa[nome] = {};
            mapa[nome][ano] = soma[kk] / cont[kk];
          });
          var series = Object.keys(mapa).sort(cmpCultura).map(function (nome) {
            return { nome: nome, valores: mapa[nome] };
          });
          montarGraficoCulturas({
            container: wrapProdLinhas, leyenda: leyendaProdLinhas,
            series: series, anos: anosDaMatrizCult(mapa), ocultas: prodOcultas,
            unidade: 'produtividade (t/ha)', unidadeCurta: 't/ha',
            vazio: 'Nenhuma produtividade convertível para t/ha nos filtros selecionados.',
            aria: 'Produtividade por hectare (t/ha) por ano'
          });
        }

        // Etapas do painel: cada uma entra num bloco, quadro a quadro, na ordem
        // resumo → cards → gráficos → hierarquia 3.4 → área por cultura 3.5 →
        // atividades 3.6 → matriz de produtividade por cultura 3.7 → área por
        // combinação de atividades 3.8.
        function renderTudo() {

          var lista = filtrarDados();

          return [

            function () { renderResumo(lista); },

            function () { renderMedia(lista); },

            function () { renderCulturas(); },

            function () { renderAreaCulturasLinhas(lista); },

            function () { renderProdTHaLinhas(lista); },

            function () { renderHierarquia(lista); },

            function () { renderAreaCultura(lista); },

            function () { renderAtividades(); },

            function () { renderMatrizCultura(lista); },

            function () { renderAtivAreaLinhas(); },

            function () { atualizarBadgeFiltros(); }

          ];

        }

        // Renderização sob demanda: o painel é montado na primeira abertura.
        // Ao recolher, o conteúdo (as hierarquias 3.4/3.5 são a parte pesada)
        // sai da memória: reabrir remonta tudo a partir dos dados.
        ObterDados.registrarPainel('produtividade', renderTudo, function () {

          [resumo, mediaBox, culturasBox, painelCulturas, wrap, wrapAreaLinhas,
            leyendaAreaLinhas, wrapProdLinhas, leyendaProdLinhas, wrapAreaCultura,
            ativTabla, wrapMatrizCultura, wrapAtivLinhas, leyendaAtivLinhas]
            .forEach(function (el) { if (el) el.innerHTML = ''; });

        });

        // ------------------------------------------------------------------
        // Painel 02 — Estrutura territorial (área física OS → Fazenda → Talhão)
        // Montado a partir do JSON `dadosArea` para respeitar os filtros
        // globais (OS, fazenda, talhão, ano e busca rápida): os totais de OS,
        // fazenda e "Total geral" somam apenas os talhões exibidos. A variação
        // segue os limiares do painel (0% branco, ≤5% verde, 5–20% amarelo,
        // >20% vermelho) e o talhão sem área em algum ano do painel e sem
        // variação sai CINZA (ano faltante).
        // ------------------------------------------------------------------
        var areaWrap = document.querySelector('#area .area-painel');
        var ROTULO_FAZENDA_AREA = '(fazenda não informada)';

        ObterDados.dadosArea = (function () {
          var el = document.getElementById('dadosArea');
          if (!el) return { anos: [], os: [] };
          try {
            var d = JSON.parse(el.textContent);
            return (d && d.os) ? d : { anos: [], os: [] };
          } catch (exc) {
            if (window.console) console.error('Falha lendo dadosArea', exc);
            return { anos: [], os: [] };
          }
        })();

        // Chave da OS usada SÓ pelo filtro do painel 2: o NÚMERO do rótulo.
        // O payload da área traz o rótulo CANÔNICO do resumo (`OS 50`), mas as
        // grades de filtro carregam o rótulo CRU da planilha (`50`, `131`,
        // `OS 119 - MITRE`). Comparar texto a texto fazia a OS `50` não casar
        // com `OS 50` e o painel ficava vazio ("Nenhum registro…"). É a mesma
        // regra do `OsKey.key` da API 3: sem dígito, o texto em caixa alta.
        function chaveOsArea(valor) {
          var texto = String(valor === null || valor === undefined ? '' : valor).trim();
          if (!texto) return '';
          var achado = texto.match(/\d+/);
          return achado ? achado[0] : texto.toUpperCase();
        }

        function casaFiltroOsArea(valor, filtro) {
          var marcados = valoresFiltro(filtro), i, alvo;
          if (!marcados.length) return true;
          alvo = chaveOsArea(valor);
          for (i = 0; i < marcados.length; i++) {
            if (chaveOsArea(marcados[i]) === alvo) return true;
          }
          return false;
        }

        // CHAVE do sítio (OS · Fazenda · Talhão) usada para cruzar o painel 2
        // com os outros payloads: normaliza a OS pelo número e fazenda/talhão
        // pelo texto (e pelos rótulos de "não informado").
        function chaveSiteArea(os, fazenda, talhao) {
          var f = String(fazenda === null || fazenda === undefined || String(fazenda).trim() === ''
            ? ROTULO_FAZENDA_AREA : fazenda);
          var t = String(talhao === null || talhao === undefined || String(talhao).trim() === ''
            ? '(talhão não informado)' : talhao);
          return [chaveOsArea(os), normValor(f), normValor(t)].join('|');
        }

        // Sítios que têm registro para o valor de UM filtro em outro payload
        // (cultura/cenário em `dadosProdutividade`; produto em
        // `dadosFertilizantes`; combustível; prática). O painel 2 é territorial:
        // o talhão só continua quando ELE tem registro naquele recorte.
        function sitesDoPayload(payload, campo, valor) {
          var mapa = {}, alvo = normValor(valor), i, r;
          for (i = 0; i < (payload || []).length; i++) {
            r = payload[i];
            if (!r || normValor(r[campo]) !== alvo) continue;
            mapa[chaveSiteArea(r.os, r.fazenda, r.talhao)] = 1;
          }
          return mapa;
        }

        function filtrarArea() {
          var f = ObterDados.filtros, busca = normValor(f.busca);
          var sitesCultura = temFiltroAtivo(f.cultura)
            ? sitesDoPayload(ObterDados.dados, 'cultura', f.cultura) : null;
          var sitesCenario = temFiltroAtivo(f.cenario)
            ? sitesDoPayload(ObterDados.dados, 'cenario', f.cenario) : null;
          var sitesFertilizante = temFiltroAtivo(f.fertilizante)
            ? sitesDoPayload(ObterDados.dadosFertilizantes, 'fertilizante', f.fertilizante) : null;
          var sitesCombustivel = temFiltroAtivo(f.combustivel)
            ? sitesDoPayload(ObterDados.dadosCombustivel, 'combustivel', f.combustivel) : null;
          var sitesPratica = temFiltroAtivo(f.pratica)
            ? sitesDoPayload(ObterDados.dadosPraticas, 'pratica', f.pratica) : null;
          var anoFiltro = String(f.ano || '').trim();
          var saida = [], osList = ObterDados.dadosArea.os || [];
          for (var i = 0; i < osList.length; i++) {
            var o = osList[i];
            if (!casaFiltroOsArea(o.os, f.os)) continue;
            var fazes = [], listaFaz = o.fazendas || [];
            for (var j = 0; j < listaFaz.length; j++) {
              var fz = listaFaz[j];
              if (!casaFiltro(fz.fazenda, f.fazenda)) continue;
              var tals = [], listaTal = fz.talhoes || [];
              for (var k = 0; k < listaTal.length; k++) {
                var tl = listaTal[k];
                if (!casaFiltro(tl.talhao, f.talhao)) continue;
                if (busca && normValor((o.os || '') + ' ' + (fz.fazenda || '') +
                  ' ' + (tl.talhao || '')).indexOf(busca) < 0) continue;
                // Filtros de RECORTE (os mesmos da cascata global): o talhão só
                // continua se tiver registro no recorte. O ano usa o próprio
                // mapa ano → área do talhão; os demais cruzam o sítio com o
                // payload do painel que origina o filtro.
                if (anoFiltro && !(num((tl.por_ano || {})[anoFiltro]) > 0)) continue;
                var site = chaveSiteArea(o.os, fz.fazenda, tl.talhao);
                if (sitesCultura && !sitesCultura[site]) continue;
                if (sitesCenario && !sitesCenario[site]) continue;
                if (sitesFertilizante && !sitesFertilizante[site]) continue;
                if (sitesCombustivel && !sitesCombustivel[site]) continue;
                if (sitesPratica && !sitesPratica[site]) continue;
                tals.push(tl);
              }
              if (!tals.length) continue;
              fazes.push({ fazenda: fz.fazenda, talhoes: tals });
            }
            if (!fazes.length) continue;
            saida.push({ os: o.os, fazendas: fazes });
          }
          return saida;
        }

        // Anos PRESENTES no recorte exibido: a união dos anos com área (> 0) nos
        // talhões que passaram pelos filtros. É a régua das COLUNAS do painel de
        // área — o relatório é reconstruído a cada filtro, então ano que não
        // existe no recorte não vira coluna (na OS marcada, por exemplo) nem
        // conta para a fila cinza (ano faltante).
        function anosDaListaArea(lista) {
          var mapa = {}, i, j, k, o, fzs, tls, pa, ano;
          for (i = 0; i < lista.length; i++) {
            o = lista[i]; fzs = o.fazendas || [];
            for (j = 0; j < fzs.length; j++) {
              tls = fzs[j].talhoes || [];
              for (k = 0; k < tls.length; k++) {
                pa = tls[k].por_ano || {};
                for (ano in pa) {
                  if (Object.prototype.hasOwnProperty.call(pa, ano) && num(pa[ano]) > 0) mapa[ano] = 1;
                }
              }
            }
          }
          return Object.keys(mapa).sort(function (a, b) {
            var x = Number(a), y = Number(b);
            if (isNaN(x)) return 1;
            if (isNaN(y)) return -1;
            return x - y;
          });
        }

        function varFisicaArea(max, min) {
          if (max === null || min === null || isNaN(max) || isNaN(min)) return null;
          if (max <= 0 || min < 0) return null;
          var media = (max + min) / 2;
          if (media <= 0) return null;
          return Math.abs(max - min) / media * 100;
        }

        function nivelArea(v) {
          if (v === null || v === undefined || v <= 1e-9) return '';
          if (v <= 5) return 'verde';
          if (v <= 20) return 'amarelo';
          return 'vermelho';
        }

        function classificarArea(mapa) {
          var vals = [], k;
          for (k in mapa) {
            if (Object.prototype.hasOwnProperty.call(mapa, k) && mapa[k] > 0) vals.push(mapa[k]);
          }
          if (!vals.length) return { nivel: '', variacao: null };
          var maior = Math.max.apply(null, vals),
            menor = Math.min.apply(null, vals);
          if (maior === menor) return { nivel: '', variacao: 0 };
          var v = Math.abs(maior - menor) / ((maior + menor) / 2) * 100;
          return { nivel: nivelArea(v), variacao: v };
        }

        function somaMapasArea(mapas) {
          var soma = {}, i, k;
          for (i = 0; i < mapas.length; i++) {
            for (k in mapas[i]) {
              if (Object.prototype.hasOwnProperty.call(mapas[i], k)) {
                soma[k] = (soma[k] || 0) + mapas[i][k];
              }
            }
          }
          return soma;
        }

        function somaFisicaArea(vals) {
          var t = 0, achou = false, i;
          for (i = 0; i < vals.length; i++) {
            if (vals[i] !== null && !isNaN(vals[i])) { t += vals[i]; achou = true; }
          }
          return achou ? t : null;
        }


        function renderAreaHierarquia() {
          if (!areaWrap) return;
          var lista = filtrarArea();
          // As colunas de ano saem do RECORTE (e não do payload inteiro): ao
          // marcar uma OS, o ano que não existe nela deixa de ser coluna.
          var todosAnos = anosDaListaArea(lista);
          var fAno = normValor(ObterDados.filtros.ano);
          var anos = fAno
            ? todosAnos.filter(function (a) { return normValor(a) === fAno; })
            : todosAnos.slice();

          function faltouAnoArea(mapa) {
            for (var i = 0; i < anos.length; i++) {
              if (!(mapa[anos[i]] > 0)) return true;
            }
            return false;
          }

          function normalizarArea(tl) {
            var mapa = {}, pa = tl.por_ano || {}, k, v;
            for (k in pa) {
              if (Object.prototype.hasOwnProperty.call(pa, k)) {
                v = num(pa[k]);
                if (!isNaN(v) && v > 0) mapa[k] = v;
              }
            }
            var fis = num(tl.area_fisica), mn = num(tl.area_minima);
            return { nome: tl.talhao, registros: tl.registros || 0,
              fisica: isNaN(fis) ? null : fis,
              minima: isNaN(mn) ? null : mn, porAno: mapa };
          }

          function celulasAnoArea(mapa) {
            return anos.map(function (an) {
              var v = mapa[an];
              return (v === undefined || v === null || !(v > 0))
                ? '<span class="cel-ano pec-sem-valor">—</span>'
                : '<span class="cel-ano">' + fmtNum(v) + '</span>';
            }).join('');
          }

          function celulasArea(expandivel, nomeHtml, fisica, variacao, mapa, registros) {
            var vart = (variacao === null || variacao === undefined)
              ? '—' : fmtNum(variacao) + '%';
            return '<span class="toggle">' + (expandivel ? '▶' : '') + '</span>' +
              '<span class="cel-nome">' + nomeHtml + '</span>' +
              '<span>' + (fisica === null ? '—' : fmtNum(fisica)) + '</span>' +
              '<span class="cel-var">' + vart + '</span>' +
              celulasAnoArea(mapa) +
              '<span class="cel-regs">' + registros + '</span>';
          }

          if (!lista.length) {
            areaWrap.innerHTML = '<p class="muted">Nenhum registro corresponde aos filtros selecionados.</p>';
            return;
          }

          var mapasGeral = [], fisGeral = [], regsGeral = 0;
          var corpoOs = lista.map(function (o) {
            var mapasOs = [], fisOs = [], regsOs = 0;
            var corpoFaz = (o.fazendas || []).map(function (fz) {
              var mapasF = [], fisF = [], regsF = 0;
              var rowsTal = (fz.talhoes || []).map(function (tlRaw) {
                var tl = normalizarArea(tlRaw);
                var vt = varFisicaArea(tl.fisica, tl.minima);
                var nivel = '';
                if (vt !== null && vt > 1e-9) nivel = nivelArea(vt);
                else if (vt !== null && faltouAnoArea(tl.porAno)) nivel = 'cinza';
                mapasF.push(tl.porAno); fisF.push(tl.fisica); regsF += tl.registros;
                return '<div class="det-row' + (nivel ? ' linha-' + nivel : '') + '">' +
                  celulasArea(false, esc(tl.nome), tl.fisica, vt, tl.porAno, tl.registros) +
                  '</div>';
              }).join('');
              var somaF = somaMapasArea(mapasF);
              var cF = classificarArea(somaF);
              var nomeF = (fz.fazenda === ROTULO_FAZENDA_AREA)
                ? esc(fz.fazenda) + ' <span class="muted">(não informada)</span>'
                : esc(fz.fazenda);
              mapasOs = mapasOs.concat(mapasF);
              fisOs = fisOs.concat(fisF); regsOs += regsF;
              return '<details class="cons-faz"><summary class="det-row' +
                (cF.nivel ? ' linha-' + cF.nivel : '') + '">' +
                celulasArea(true, nomeF, somaFisicaArea(fisF), cF.variacao, somaF, regsF) +
                '</summary>' +
                (rowsTal ? '<div class="cons-body">' + rowsTal + '</div>' : '') +
                '</details>';
            }).join('');
            mapasGeral = mapasGeral.concat(mapasOs);
            fisGeral = fisGeral.concat(fisOs); regsGeral += regsOs;
            var somaO = somaMapasArea(mapasOs);
            var cO = classificarArea(somaO);
            return '<details class="cons-os"><summary class="det-row' +
              (cO.nivel ? ' linha-' + cO.nivel : '') + '">' +
              celulasArea(true, esc(o.os), somaFisicaArea(fisOs), cO.variacao, somaO, regsOs) +
              '</summary>' +
              (corpoFaz ? '<div class="cons-body">' + corpoFaz + '</div>' : '') +
              '</details>';
          }).join('');

          var somaT = somaMapasArea(mapasGeral);
          var cT = classificarArea(somaT);
          var totalRow = '<div class="det-row det-total">' +
            celulasArea(false, 'Total geral', somaFisicaArea(fisGeral), cT.variacao, somaT, regsGeral) +
            '</div>';

          // A coluna do NOME recebe só a SOBRA (`minmax(200px, 1fr)`): assim ela
          // nunca cresce por causa do conteúdo (era `auto`, ou seja `max-content`,
          // e um nome de fazenda extenso empurrava as colunas de área, variação,
          // ano e registros para o mínimo). O texto do nome quebra em várias
          // linhas (regra `#area .area-painel ... .cel-nome` do CSS) em vez de
          // espremer a linha.
          var cols = '1.7rem minmax(200px, 1fr) minmax(96px, auto) minmax(74px, auto)';
          for (var n = 0; n < anos.length; n++) cols += ' minmax(84px, auto)';
          cols += ' minmax(64px, auto)';

          // Largura mínima da grade: a soma dos mínimos das colunas + os vãos
          // (`gap: 0 10px`, um vão a menos que o número de colunas) + o padding
          // lateral da linha (`8px 10px`; o `box-sizing` do relatório é
          // `border-box`). É o limite em que a grade para de encolher — daí para
          // baixo o painel rola na horizontal. O CSS usa este valor como
          // `min-width` das LINHAS e das caixas OS/Fazenda: sem ele a linha
          // continuava com a largura da caixa e a grade TRANSBORDAVA a própria
          // caixa, então o `overflow: clip` da caixa (que arredonda os cantos sem
          // criar contêiner de rolagem) RECORTAVA as últimas colunas — os anos e
          // os registros das fazendas e talhões ficavam fora do alcance da
          // rolagem, só o cabeçalho e o total apareciam. O `1.7rem` fica em `rem`
          // (e não em px) para acompanhar o tamanho de fonte raiz; os 2 px finais
          // são folga para arredondamento de subpixel.
          var colunas = 5 + anos.length;
          var minW = 200 + 96 + 74 + 84 * anos.length + 64 + 10 * (colunas - 1) + 20 + 2;
          var estiloGrade = '--cols:' + cols + ';--min-w:calc(1.7rem + ' + minW + 'px)';

          var head = '<div class="det-row det-head"><span class="toggle"></span>' +
            '<span class="cel-nome">OS · Fazenda · Talhão</span>' +
            '<span>Área física (ha)</span><span class="cel-var">Variação %</span>' +
            anos.map(function (an) { return '<span class="cel-ano">' + esc(an) + '</span>'; }).join('') +
            '<span class="cel-regs">Registros</span></div>';

          var legend = '<p class="panel-legend">' +
            '<span class="dot dot-verde"></span> variação ≤ 5% &nbsp;' +
            '<span class="dot dot-amarelo"></span> 5–20% &nbsp;' +
            '<span class="dot dot-vermelho"></span> &gt; 20% &nbsp;' +
            '<span class="dot dot-cinza"></span> talhão sem área em algum ano (sem variação)</p>';

          areaWrap.innerHTML = legend +
            '<div class="painel-consolidado" style="' + estiloGrade + '">' +
            head + corpoOs + totalRow + '</div>';
          if (typeof ObterDados.detailsSobDemanda === 'function') {
            ObterDados.detailsSobDemanda(areaWrap);
          }
        }

        function renderAreaTudo() {
          return [function () { renderAreaHierarquia(); }];
        }

        ObterDados.registrarPainel('area', renderAreaTudo, function () {
          if (areaWrap) areaWrap.innerHTML = '';
        });

// ----- Painel de pecuária: evolução em área (4.1) + tabela por nível × ano (4.2) -----

        function filtrarPecuaria() {

          var f = ObterDados.filtros, busca = normValor(f.busca);

          var chaves = ['os', 'fazenda', 'talhao', 'ano', 'cenario'];

          return ObterDados.dadosPecuaria.filter(function (r) {

            for (var i = 0; i < chaves.length; i++) {

              if (!casaFiltro(r[chaves[i]], f[chaves[i]])) return false;

            }

            if (busca && normValor(JSON.stringify(r)).indexOf(busca) < 0) return false;

            return true;

          });

        }

        function anosPecuaria(lista) {

          var mapa = {}, anos = [], i, r, an;

          for (i = 0; i < lista.length; i++) {

            r = lista[i];

            an = (r.ano === null || r.ano === undefined) ? '—' : String(r.ano).trim();

            if (!(an in mapa)) { mapa[an] = 1; anos.push(an); }

          }

          return anos.sort(function (a, b) {

            var x = Number(a), y = Number(b);

            if (isNaN(x)) return 1;

            if (isNaN(y)) return -1;

            return x - y;

          });

        }

        function renderPecResumo(lista) {

          if (!resumoPec) return;

          var fazSet = {}, osSet = {}, anosSet = {}, total = 0, i, r, v;

          for (i = 0; i < lista.length; i++) {

            r = lista[i];

            v = num(r.area);

            if (!isNaN(v)) total += v;

            if (r.fazenda) fazSet[String(r.fazenda)] = 1;

            if (r.os) osSet[String(r.os)] = 1;

            if (r.ano !== null && r.ano !== undefined) anosSet[String(r.ano)] = 1;

          }

          resumoPec.innerHTML =

            '<span class="prod-chip"><strong>' + lista.length + '</strong> registros com pecuária</span>' +

            '<span class="prod-chip"><strong>' + fmtNum(total, 0) + '</strong> ha de área de pastagem</span>' +

            '<span class="prod-chip"><strong>' + Object.keys(fazSet).length + '</strong> fazendas</span>' +

            '<span class="prod-chip"><strong>' + Object.keys(osSet).length + '</strong> OS</span>' +

            '<span class="prod-chip"><strong>' + anosPecuaria(lista).join(' · ') + '</strong> anos</span>';

        }

        // ------------------------------------------------------------------
        // 4.2 — Evolução anual da pecuária em TRÊS escalas (gráfico de linhas)
        // ------------------------------------------------------------------
        // Cada série declara o eixo a que pertence (`eixo`), o nome curto usado
        // no título do eixo (`curto`), a unidade curta da dica (`unidadeCurta`)
        // e as casas decimais (`casas`). Os três eixos verticais são:
        //   0 · Área de pastagem (ha) — escala da esquerda;
        //   1 · UA · GMD · Rend. carcaça — escala do centro, ÚNICA para os três
        //       (têm a mesma ordem de grandeza: a UA vai até 2 e o rendimento
        //       de carcaça é informado como fração, 0–1);
        //   2 · Nº animais (cab.) — escala da direita.
        var SERIES_PEC_42 = [
          { nome: 'area', rotulo: 'Área de pastagem (ha)', eixo: 0, curto: 'Área',
            unidadeCurta: 'ha', casas: 2 },
          { nome: 'animals', rotulo: 'Nº animais (cab.)', eixo: 2,
            curto: 'Nº animais', unidadeCurta: 'cab.', casas: 0 },
          { nome: 'ua', rotulo: 'UA (UA/ha)', eixo: 1, curto: 'UA',
            unidadeCurta: 'UA/ha', casas: 2 },
          { nome: 'gmd', rotulo: 'GMD (kg/cab./dia)', eixo: 1, curto: 'GMD',
            unidadeCurta: 'kg/cab./dia', casas: 2 },
          { nome: 'rend', rotulo: 'Rend. carcaça (0–1)', eixo: 1, curto: 'Rend.',
            unidadeCurta: '', casas: 2 }
        ];
        // Definição dos três eixos: `series` (ordem do título e da escala),
        // `escalaMinima` (piso da escala — a compartilhada vai de 0 a 2) e
        // `nota` (acrescentada ao título do eixo, entre parênteses).
        var EIXOS_PEC_42 = [
          { series: ['area'] },
          { series: ['ua', 'gmd', 'rend'], escalaMinima: 2, nota: '0–2' },
          { series: ['animals'] }
        ];

        // Desenha um gráfico de linhas multi-série com VÁRIAS escalas verticais:
        // cada série declara o seu eixo (`s.eixo`) e todas as séries de um mesmo
        // eixo dividem a mesma régua. Adaptado do `montarGraficoCulturas`
        // (3.2/3.3), que tem uma escala única. É usado pelo painel 4.2.
        function montarGraficoEixos(cfg) {
          var container = cfg.container, leyenda = cfg.leyenda;
          if (!container) return;
          var series = cfg.series || [], anosNum = cfg.anos || [], eixos = cfg.eixos || [];
          if (!series.length || !anosNum.length || !eixos.length) {
            container.innerHTML = '<p class="muted">' + (cfg.vazio || 'Sem dados para o gráfico.') + '</p>';
            if (leyenda) leyenda.innerHTML = '';
            return;
          }
          // Cores: paleta padrão, sem repetir cor (energia/Total/área física
          // declaram `cor` e ficam reservadas — ver `coresDasSeriesDoGrafico`).
          var cor = ObterDados.coresDasSeriesDoGrafico(series);
          var ocultas = cfg.ocultas || {};

          if (leyenda) {
            leyenda.innerHTML = series.map(function (s) {
              var oc = ocultas[s.nome] ? ' oculta' : '';
              return '<button type="button" class="prod-linhas-leyenda-item' + oc +
                '" data-serie="' + esc(s.nome) + '">' +
                '<span class="prod-linhas-leyenda-cor" style="background:' + cor[s.nome] + '"></span>' +
                esc(s.rotulo || s.nome) + '</button>';
            }).join('');
            Array.prototype.forEach.call(leyenda.querySelectorAll('[data-serie]'), function (b) {
              b.addEventListener('click', function () {
                var nome = b.getAttribute('data-serie');
                if (ocultas[nome]) { delete ocultas[nome]; } else { ocultas[nome] = 1; }
                montarGraficoEixos(cfg);
              });
            });
          }

          var visiveis = series.filter(function (s) { return !ocultas[s.nome]; });

          // Uma escala por eixo, medida somente com as séries visíveis dele.
          // `escalaMinima` garante o piso da régua compartilhada (UA · GMD ·
          // Rendimento vai de 0 a 2, já que os três têm a mesma magnitude).
          var escalas = eixos.map(function (e, i) {
            var maxReal = 0, temSerie = false;
            visiveis.forEach(function (s) {
              if (s.eixo !== i) return;
              anosNum.forEach(function (an) {
                var v = s.valores[an];
                if (v === null || v === undefined) return;
                // O eixo só é desenhado quando tem pelo menos um valor medido
                // (uma série inteiramente vazia — ex.: sem energia elétrica no
                // painel 07 — não cria uma régua 0–1 sem significado).
                temSerie = true;
                if (v > maxReal) maxReal = v;
              });
            });
            if (e.escalaMinima && maxReal < e.escalaMinima) maxReal = e.escalaMinima;
            var esc = escalaCult(maxReal);
            // Casas decimais do rótulo da escala (a régua 0–2 pede 1 casa).
            esc.casas = esc.passo >= 1 ? 0 : (esc.passo >= 0.1 ? 1 : 2);
            esc.visivel = temSerie;
            return esc;
          });
          // As linhas de grade saem do primeiro eixo que tem séries visíveis.
          var eixoGrade = 0;
          for (var gi = 0; gi < escalas.length; gi++) {
            if (escalas[gi].visivel) { eixoGrade = gi; break; }
          }

          var W = 1040, H = 470, mL = 92, mR = 176, mT = 46, mB = 56;
          var pw = W - mL - mR, ph = H - mT - mB, X0 = mL + pw;
          var passoX = anosNum.length > 1 ? pw / (anosNum.length - 1) : pw;
          function xi(an) {
            var idx = anosNum.indexOf(an);
            return anosNum.length === 1 ? mL + pw / 2 : mL + idx * passoX;
          }
          function yi(v, eixo) { return mT + ph - (v / escalas[eixo].max) * ph; }
          // Cada eixo tem a sua coluna: o 0 fica na esquerda e os outros dois na
          // direita (a coluna mais externa é a do Nº animais).
          function xEixo(i) { return i === 0 ? mL : X0 + (i === 1 ? 0 : 104); }
          function ladoEixo(i) { return i === 0 ? -1 : 1; }

          var partes = [], k, i, yy, ax, lado, cEixo, e, sx, tx, anc;
          partes.push('<rect class="pl-fundo" x="' + mL + '" y="' + mT + '" width="' + pw + '" height="' + ph + '" rx="10"></rect>');
          for (k = 0; k <= escalas[eixoGrade].ticks; k++) {
            yy = yi(escalas[eixoGrade].passo * k, eixoGrade);
            partes.push('<line class="pl-grid" x1="' + mL + '" y1="' + yy + '" x2="' + X0 + '" y2="' + yy + '"></line>');
          }
          anosNum.forEach(function (an) {
            var xx = xi(an);
            if (anosNum.length > 1) {
              partes.push('<line class="pl-grid-vert" x1="' + xx + '" y1="' + mT + '" x2="' + xx + '" y2="' + (mT + ph) + '"></line>');
            }
            partes.push('<text class="pl-eixo-txt" x="' + xx + '" y="' + (H - mB + 24) + '" text-anchor="middle">' + esc(an) + '</text>');
          });
          partes.push('<line class="pl-guia" x1="0" y1="' + mT + '" x2="0" y2="' + (mT + ph) + '" opacity="0"></line>');

          // Eixos: linha, marcas, rótulos e título, na cor do seu conteúdo (o
          // eixo compartilhado sai em cinza, porque tem três séries de cores).
          for (i = 0; i < eixos.length; i++) {
            if (!escalas[i].visivel) continue;
            e = eixos[i];
            ax = xEixo(i);
            lado = ladoEixo(i);
            cEixo = e.series.length === 1 ? cor[e.series[0]] : 'var(--texto-suave)';
            partes.push('<line class="pl-eixo-sec" stroke="' + cEixo + '" x1="' + ax + '" y1="' + mT + '" x2="' + ax + '" y2="' + (mT + ph) + '"></line>');
            for (k = 0; k <= escalas[i].ticks; k++) {
              yy = yi(escalas[i].passo * k, i);
              partes.push('<line class="pl-tick" stroke="' + cEixo + '" x1="' + ax + '" y1="' + yy + '" x2="' + (ax + 6 * lado) + '" y2="' + yy + '"></line>');
              partes.push('<text class="pl-eixo-txt-sec" fill="' + cEixo + '" x="' + (ax + 12 * lado) + '" y="' + (yy + 4) + '" text-anchor="' + (lado > 0 ? 'start' : 'end') + '">' + fmtNum(escalas[i].passo * k, escalas[i].casas) + '</text>');
            }
            // Título: canto esquerdo, centro e canto direito, na ordem dos eixos
            // (com DOIS eixos, o da direita ocupa o canto direito, não o centro).
            var ultimo = eixos.length - 1;
            tx = i === 0 ? mL : (i === ultimo ? W - 10 : W / 2);
            anc = i === 0 ? 'start' : (i === ultimo ? 'end' : 'middle');
            sx = e.series.map(function (nome, j) {
              var sr = null;
              series.forEach(function (x) { if (x.nome === nome) sr = x; });
              if (!sr) return '';
              var rotulo = (sr.curto || sr.nome) +
                (e.series.length === 1 && sr.unidadeCurta ? ' (' + sr.unidadeCurta + ')' : '');
              return (j ? '<tspan fill="var(--texto-suave)"> · </tspan>' : '') +
                '<tspan fill="' + cor[nome] + '">' + esc(rotulo) + '</tspan>';
            }).join('');
            partes.push('<text class="pl-unit-sec" x="' + tx + '" y="' + (mT - 16) +
              '" text-anchor="' + anc + '" fill="var(--texto-suave)">' + sx +
              (e.nota ? '<tspan fill="var(--texto-suave)"> (' + esc(e.nota) + ')</tspan>' : '') + '</text>');
          }

          // Séries: a linha é CORTADA nos anos sem valor (um ano vazio não é
          // ligado ao próximo) e cada ponto só existe onde há valor medido.
          visiveis.forEach(function (s) {
            var corridas = [], atual = [];
            anosNum.forEach(function (an) {
              var v = s.valores[an];
              if (v === null || v === undefined) {
                if (atual.length) { corridas.push(atual); atual = []; }
                return;
              }
              atual.push({ x: xi(an), y: yi(v, s.eixo), an: an, v: v });
            });
            if (atual.length) corridas.push(atual);
            corridas.forEach(function (run) {
              partes.push('<path class="pl-line" stroke="' + cor[s.nome] + '" d="' + caminhoCult(run) + '"></path>');
              run.forEach(function (pt) {
                partes.push('<circle class="pl-dot" cx="' + pt.x + '" cy="' + pt.y + '" r="3.4" fill="' + cor[s.nome] + '">' +
                  '<title>' + esc((s.rotulo || s.nome) + ' · ' + pt.an + ': ' + fmtNum(pt.v, s.casas) +
                  (s.unidadeCurta ? ' ' + s.unidadeCurta : '')) + '</title></circle>');
              });
            });
          });

          anosNum.forEach(function (an) {
            var xx = xi(an);
            var esq = Math.max(mL, xx - passoX / 2);
            var dir = Math.min(X0, xx + passoX / 2);
            partes.push('<rect class="pl-hot" data-ano="' + esc(an) + '" data-x="' + xx + '" x="' + esq +
              '" y="' + mT + '" width="' + (dir - esq) + '" height="' + ph + '" fill="transparent"></rect>');
          });

          container.innerHTML = '<svg viewBox="0 0 ' + W + ' ' + H + '" preserveAspectRatio="xMidYMid meet" role="img" aria-label="' + esc(cfg.aria || '') + '">' + partes.join('') + '</svg>';

          var tip = document.createElement('div');
          tip.className = 'prod-linhas-tip';
          tip.hidden = true;
          container.appendChild(tip);
          var guia = container.querySelector('.pl-guia');
          Array.prototype.forEach.call(container.querySelectorAll('.pl-hot'), function (rc) {
            rc.addEventListener('mouseenter', function () {
              var an = rc.getAttribute('data-ano');
              if (guia) {
                guia.setAttribute('x1', rc.getAttribute('data-x'));
                guia.setAttribute('x2', rc.getAttribute('data-x'));
                guia.setAttribute('opacity', '1');
              }
              var filas = visiveis.map(function (s) {
                return { nome: s.nome, rotulo: s.rotulo || s.nome, casas: s.casas,
                         un: s.unidadeCurta, v: s.valores[an] };
              }).filter(function (o) { return o.v !== null && o.v !== undefined; })
                .sort(function (a, b) { return b.v - a.v; });
              var html = '<div class="pl-tip-tit">' + esc(an) + '</div>';
              if (!filas.length) { html += '<div class="pl-tip-vazio">sem dados</div>'; }
              filas.forEach(function (o) {
                html += '<div class="pl-tip-row"><span class="pl-tip-cor" style="background:' + cor[o.nome] + '"></span>' +
                  '<span class="pl-tip-nome">' + esc(o.rotulo) + '</span>' +
                  '<span class="pl-tip-val">' + fmtNum(o.v, o.casas) + (o.un ? ' ' + esc(o.un) : '') + '</span></div>';
              });
              tip.innerHTML = html;
              tip.hidden = false;
              var rr = rc.getBoundingClientRect(), wr = container.getBoundingClientRect();
              var cx = rr.left + rr.width / 2 - wr.left;
              cx = Math.max(110, Math.min(wr.width - 110, cx));
              tip.style.left = cx + 'px';
            });
            rc.addEventListener('mouseleave', function () {
              tip.hidden = true;
              if (guia) guia.setAttribute('opacity', '0');
            });
          });
        }

        // 4.2 — Evolução anual da pecuária: uma série por métrica, agregada ano
        // a ano com as MESMAS regras da tabela 4.1 (`pecAgregar`).
        function renderPecEvolucion(lista) {
          if (!wrapPecEvol) return;
          if (leyendaPecEvol) leyendaPecEvol.innerHTML = '';
          if (!lista.length) {
            wrapPecEvol.innerHTML = '<p class="muted">Nenhum registro de pecuária ' +
              'corresponde aos filtros selecionados.</p>';
            return;
          }
          var anos = anosPecuaria(lista);
          if (!anos.length) {
            wrapPecEvol.innerHTML = '<p class="muted">Nenhum ano identificado nos ' +
              'registros de pecuária.</p>';
            return;
          }
          var agg = pecAgregar(lista);
          var series = SERIES_PEC_42.map(function (cfg) {
            var valores = {};
            anos.forEach(function (an) {
              valores[an] = pecValorMetrica(agg.porAno[an], cfg.nome);
            });
            return { nome: cfg.nome, rotulo: cfg.rotulo, curto: cfg.curto,
                     unidadeCurta: cfg.unidadeCurta, casas: cfg.casas,
                     eixo: cfg.eixo, valores: valores };
          });
          montarGraficoEixos({
            container: wrapPecEvol, leyenda: leyendaPecEvol,
            series: series, anos: anos, eixos: EIXOS_PEC_42,
            ocultas: ocultasPecEvol,
            aria: 'Evolução anual da pecuária: área de pastagem, nº de animais, UA, GMD e rendimento de carcaça',
            vazio: 'Sem dados de pecuária para o gráfico.'
          });
        }
        // ----- Agregação da pecuária (compartilhada pela tabela 4.1 e 4.2) -----
        // Acumulador de um ano/nó: área e nº de animais somam; a lotação entra
        // como UA × área (ou o próprio nº de animais quando a lotação não foi
        // informada); GMD e rendimento de carcaça são médias (soma + contador).
        function pecAcc() {
          return { area: 0, animals: 0, animalsN: 0, ua: 0, gmdS: 0, gmdN: 0, rendS: 0, rendN: 0 };
        }

        // Agrega uma lista de registros de pecuária por ano (`porAno`) e no
        // conjunto todo (`geral`), com a chave '—' para o ano ausente.
        function pecAgregar(regs) {
          var porAno = {}, geral = pecAcc(), j, rr, an, v, a, u;
          for (j = 0; j < regs.length; j++) {
            rr = regs[j];
            an = (rr.ano === null || rr.ano === undefined) ? '—' : String(rr.ano).trim();
            if (!porAno[an]) porAno[an] = pecAcc();
            a = num(rr.area);
            if (!isNaN(a) && a > 0) { porAno[an].area += a; geral.area += a; }
            v = num(rr.animals);
            if (!isNaN(v)) { porAno[an].animals += v; geral.animals += v; porAno[an].animalsN++; geral.animalsN++; }
            u = num(rr.ua);
            if (!isNaN(u) && !isNaN(a) && a > 0) { porAno[an].ua += u * a; geral.ua += u * a; }
            else if (!isNaN(v)) { porAno[an].ua += v; geral.ua += v; }
            v = num(rr.gmd);
            if (!isNaN(v)) { porAno[an].gmdS += v; porAno[an].gmdN++; geral.gmdS += v; geral.gmdN++; }
            v = num(rr.rend);
            if (!isNaN(v)) { porAno[an].rendS += v; porAno[an].rendN++; geral.rendS += v; geral.rendN++; }
          }
          return { porAno: porAno, geral: geral };
        }

        // Valor final de uma métrica (`chave` = 'area', 'animals', 'ua', 'gmd'
        // ou 'rend') num acumulador; `null` quando não há valor no ano/nó.
        function pecValorMetrica(x, chave) {
          if (!x) return null;
          if (chave === 'area') return x.area > 0 ? x.area : null;
          if (chave === 'animals') return x.animalsN > 0 ? x.animals : null;
          if (chave === 'ua') return x.area > 0 ? x.ua / x.area : null;
          if (chave === 'gmd') return x.gmdN > 0 ? x.gmdS / x.gmdN : null;
          if (chave === 'rend') return x.rendN > 0 ? x.rendS / x.rendN : null;
          return null;
        }

        function renderPecTabla(lista) {
          if (!tablaPec) return;
          if (vazioPec) vazioPec.classList.remove('visivel');
          if (!lista.length) {
            tablaPec.innerHTML = '';
            tablaPec.style.display = 'none';
            if (vazioPec) vazioPec.classList.add('visivel');
            return;
          }
          tablaPec.style.display = 'block';
          var anos = anosPecuaria(lista);
          var arv = {}, ordemOs = [], i, r, os, faz, tal;
          for (i = 0; i < lista.length; i++) {
            r = lista[i];
            os = r.os || '—';
            faz = r.fazenda || '—';
            tal = r.talhao || '—';
            if (!arv[os]) { arv[os] = {}; ordemOs.push(os); }
            if (!arv[os][faz]) arv[os][faz] = {};
            if (!arv[os][faz][tal]) arv[os][faz][tal] = [];
            arv[os][faz][tal].push(r);
          }
          ordemOs.sort(function (a, b) { return a.localeCompare(b, 'pt-BR', { numeric: true }); });
          function porNome(a, b) { return a.localeCompare(b, 'pt-BR', { numeric: true }); }
          function coleccionarRegistros(osA, fazA, talA) {
            if (talA) return arv[osA][fazA][talA];
            var total = [];
            Object.keys(arv[osA] || {}).forEach(function (fz) {
              if (!fazA || fz === fazA) {
                Object.keys(arv[osA][fz]).forEach(function (tl) {
                  total = total.concat(arv[osA][fz][tl]);
                });
              }
            });
            return total;
          }
          // Cada nó (OS · Fazenda · Talhão) vira um grupo de 5 linhas — uma por
          // métrica — com colunas Geral + uma por ano. Agregações: área (ha) e
          // Nº animais (cab.) somam; UA (UA/ha) é a razão ΣUA ÷ Σárea (UA total
          // = lotação × área; sem lotação, usam-se as cabeças); GMD e Rend.
          // carcaça são a média dos valores numéricos.
          var METRICAS = [
            { chave: 'area', rotulo: 'Área de pastagem (ha)', casas: 2 },
            { chave: 'animals', rotulo: 'Nº animais (cab.)', casas: 0 },
            { chave: 'ua', rotulo: 'UA (UA/ha)', casas: 2 },
            { chave: 'gmd', rotulo: 'GMD (kg/cab./dia)', casas: 2 },
            { chave: 'rend', rotulo: 'Rend. carcaça (%)', casas: 1 }
          ];
          // Agregação e valor por métrica: as regras ficam nos helpers
          // compartilhados `pecAcc`/`pecAgregar`/`pecValorMetrica` (escopo
          // comum), para que a tabela 4.1 e o gráfico 4.2 nunca divirjam.
          function acc() { return pecAcc(); }
          function agregar(regs) { return pecAgregar(regs); }
          function valorMetrica(x, m) { return pecValorMetrica(x, m.chave); }
          // Variação % de uma métrica entre os anos do painel: |maior − menor|
          // ÷ média(maior, menor) × 100, com os MESMOS limiares do painel de
          // área (verde ≤5%, amarelo 5–20%, vermelho >20%). Os anos sem valor
          // ficam de fora (ano faltante não conta como zero); `falta` indica
          // que a métrica não tem valor em algum ano exibido.
          function variacaoMetrica(agg, m) {
            var vals = [], i, an, v;
            for (i = 0; i < anos.length; i++) {
              an = anos[i];
              v = valorMetrica(agg.porAno[an], m);
              if (v !== null && v !== undefined) vals.push(v);
            }
            var falta = vals.length < anos.length;
            if (!vals.length) return { nivel: '', variacao: null, falta: falta };
            if (vals.length < 2) return { nivel: '', variacao: 0, falta: falta };
            var maior = Math.max.apply(null, vals), menor = Math.min.apply(null, vals);
            if (maior === menor) return { nivel: '', variacao: 0, falta: falta };
            var pct = Math.abs(maior - menor) / ((maior + menor) / 2) * 100;
            var nivel = pct <= 5 ? 'verde' : (pct <= 20 ? 'amarelo' : 'vermelho');
            return { nivel: nivel, variacao: pct, falta: falta };
          }
          function celPec(valor, casas) {
            return (valor === null || valor === undefined)
              ? '<td class="pec-cel pec-sem-valor">—</td>'
              : '<td class="pec-cel">' + fmtNum(valor, casas) + '</td>';
          }
          function celVar(res) {
            return (res.variacao === null || res.variacao === undefined)
              ? '<td class="pec-cel pec-var pec-sem-valor">—</td>'
              : '<td class="pec-cel pec-var">' + fmtNum(res.variacao, 1) + '%</td>';
          }
          // Linhas de um nó: escritas só quando o nó de cima é expandido.
          // `temFilhos` marca a existência de nível inferior (seta clicável).
          function linhasNo(gid, nome, nivel, regs, temFilhos) {
            var agg = agregar(regs), html = '';
            METRICAS.forEach(function (m, idx) {
              var vGeral = valorMetrica(agg.geral, m);
              var varM = variacaoMetrica(agg, m);
              var cels = anos.map(function (an) {
                return celPec(valorMetrica(agg.porAno[an], m), m.casas);
              }).join('');
              // A cor da linha só é aplicada à métrica Área de pastagem (ha):
              // verde/amarelo/vermelho pela variação e cinza quando o TALHÃO
              // não tem pastagem em algum ano e a variação é 0%. As demais
              // métricas (Nº animais, UA, GMD, Rend. carcaça) mostram a
              // variação, mas sem cor.
              var nivelLinha = '';
              if (m.chave === 'area') {
                if (varM.nivel) nivelLinha = varM.nivel;
                else if (nivel === 'tal' && varM.falta) nivelLinha = 'cinza';
              }
              var nomeTd = (idx === 0)
                ? '<td class="pec-nome pec-nivel-' + nivel + (temFilhos ? ' pec-clicavel' : '') +
                  '" data-grupo="' + gid + '"' + (temFilhos ? ' data-toggle="1"' : '') +
                  ' rowspan="' + METRICAS.length + '">' +
                  (temFilhos ? '<span class="pec-seta">▶</span> ' : '') + esc(nome) + '</td>'
                : '';
              var geralTd = (vGeral === null || vGeral === undefined)
                ? '<td class="pec-cel pec-geral pec-sem-valor">—</td>'
                : '<td class="pec-cel pec-geral">' + fmtNum(vGeral, m.casas) + '</td>';
              html += '<tr data-g="' + gid + '" class="pec-linha' +
                (idx === 0 ? ' pec-inicio-grupo' : '') +
                (nivelLinha ? ' linha-' + nivelLinha : '') + '">' +
                nomeTd + '<td class="pec-metrica">' + esc(m.rotulo) + '</td>' +
                geralTd + celVar(varM) + cels + '</tr>';
            });
            return html;
          }
          var headAnos = anos.map(function (an) { return '<th>' + esc(an) + '</th>'; }).join('');
          tablaPec.innerHTML = '<p class="muted">Variação % por métrica (os anos sem ' +
            'valor ficam de fora): verde ≤5%, amarelo 5–20%, vermelho &gt;20%; cinza = ' +
            'talhão sem pastagem em algum ano e sem variação (0%). A cor da linha é ' +
            'aplicada somente à métrica Área de pastagem (ha).</p>' +
            '<table class="pec-pivot"><thead><tr>' +
            '<th>OS · Fazenda · Talhão</th><th>Métrica</th><th>Geral</th>' +
            '<th>Variação %</th>' + headAnos +
            '</tr></thead><tbody></tbody></table>';

          // Hierarquia sob demanda: só as OS (e a linha do total) entram agora.
          // As fazendas nascem ao abrir uma OS e os talhões ao abrir a fazenda;
          // a expansão/recolha e a criação dos níveis são do `pivotLazy`.
          var piv = ObterDados.pivotLazy({
            prefixo: 'pec',
            corpo: tablaPec.querySelector('tbody'),
            linhas: linhasNo
          });

          ordemOs.forEach(function (osA) {
            piv.raiz({
              nome: osA, nivel: 'os',
              coletar: function () { return coleccionarRegistros(osA, null, null); },
              gerarFilhos: function () {
                return Object.keys(arv[osA]).sort(porNome).map(function (fazA) {
                  return {
                    nome: fazA, nivel: 'faz',
                    coletar: function () { return coleccionarRegistros(osA, fazA, null); },
                    gerarFilhos: function () {
                      return Object.keys(arv[osA][fazA]).sort(porNome).map(function (talA) {
                        return { nome: talA, nivel: 'tal', coletar: arv[osA][fazA][talA] };
                      });
                    }
                  };
                });
              }
            });
          });
          piv.raiz({ nome: 'Total geral', nivel: 'total', coletar: lista });
        }

        // Etapas do painel: resumo em chips e, depois, a tabela agrupada.
        function renderPecTudo() {

          var lista = filtrarPecuaria();

          return [

            function () { renderPecResumo(lista); },

            function () { renderPecTabla(lista); },

            function () { renderPecEvolucion(lista); }

          ];

        }

        // Renderização sob demanda: o painel é montado na primeira abertura.
        // Recolhido, a tabela (5 linhas por nó) sai da memória.
        ObterDados.registrarPainel('pecuaria', renderPecTudo, function () {

          [resumoPec, tablaPec, wrapPecEvol, leyendaPecEvol].forEach(function (el) { if (el) el.innerHTML = ''; });

          if (tablaPec) tablaPec.style.display = '';

        });

        // ----- Painel de fertilizantes: totais de dose (kg/ha) por fertilizante -----

        function filtrarFertilizantes() {

          var f = ObterDados.filtros, busca = normValor(f.busca);

          var chaves = ['os', 'fazenda', 'talhao', 'ano', 'cenario', 'fertilizante'];

          return ObterDados.dadosFertilizantes.filter(function (r) {

            for (var i = 0; i < chaves.length; i++) {

              if (!casaFiltro(r[chaves[i]], f[chaves[i]])) return false;

            }

            if (busca && normValor(JSON.stringify(r)).indexOf(busca) < 0) return false;

            return true;

          });

        }

        function anosFert(lista) {

          var mapa = {}, anos = [], i, r, an;

          for (i = 0; i < lista.length; i++) {

            r = lista[i];

            an = (r.ano === null || r.ano === undefined) ? '—' : String(r.ano).trim();

            if (!(an in mapa)) { mapa[an] = 1; anos.push(an); }

          }

          return anos.sort(function (a, b) {

            var x = Number(a), y = Number(b);

            if (isNaN(x)) return 1;

            if (isNaN(y)) return -1;

            return x - y;

          });

        }

        function renderFertResumo(lista) {

          if (!resumoFert) return;

          var fazSet = {}, osSet = {}, fertSet = {}, total = 0, areaTot = 0, i, r, v;

          for (i = 0; i < lista.length; i++) {

            r = lista[i];

            v = num(r.total);

            if (!isNaN(v)) total += v;

            v = num(r.area);

            if (!isNaN(v)) areaTot += v;

            if (r.fazenda) fazSet[String(r.fazenda)] = 1;

            if (r.os) osSet[String(r.os)] = 1;

            if (r.fertilizante) fertSet[String(r.fertilizante)] = 1;

          }

          resumoFert.innerHTML =

            '<span class="prod-chip"><strong>' + lista.length + '</strong> registros com fertilizantes</span>' +

            '<span class="prod-chip"><strong>' + fmtNum(total, 0) + '</strong> kg de fertilizantes</span>' +

            '<span class="prod-chip"><strong>' + fmtNum(areaTot, 0) + '</strong> ha tratados</span>' +

            '<span class="prod-chip"><strong>' + Object.keys(fertSet).length + '</strong> fertilizantes</span>' +

            '<span class="prod-chip"><strong>' + Object.keys(fazSet).length + '</strong> fazendas</span>' +

            '<span class="prod-chip"><strong>' + Object.keys(osSet).length + '</strong> OS</span>';

        }

        // Ordem dos fertilizantes: ALFABÉTICA pelo NOME do produto (pt-BR,
        // numérica). A identidade é o nome e já vem resolvida do JSON (API 1):
        // a coluna de cadastro não existe mais no dado, então não há grupo de
        // coluna para ordenar — o produto mantém a MESMA posição no painel
        // mesmo quando passa de uma coluna para outra na planilha.
        function ordenarFert(ordem) {
          ordem.sort(function (a, b) {
            return String(a).localeCompare(String(b), 'pt-BR', { numeric: true });
          });
        }

        // (A cor da cobertura de EVIDÊNCIA — `corCobertura` — mora no escopo
        // comum, porque o 7.1 usa a MESMA régua de faixas do 5.1.)

        // Mapa nome padrão → {nome, volume, anos} das evidências (NFs) do relatório.
        function evidenciasPorPadrao() {
          var mapa = {}, i, e, pad, v, y, anos, vy;
          for (i = 0; i < ObterDados.dadosEvidencias.length; i++) {
            e = ObterDados.dadosEvidencias[i];
            pad = String(e.padronizado || '').trim();
            if (!pad) continue;
            if (!mapa[pad]) mapa[pad] = { nome: e.nome || pad, volume: 0, anos: {} };
            v = num(e.volume);
            if (!isNaN(v) && v > 0) mapa[pad].volume += v;
            anos = e.anos || {};
            for (y in anos) {
              if (!Object.prototype.hasOwnProperty.call(anos, y)) continue;
              vy = num(anos[y]);
              if (!isNaN(vy) && vy > 0) mapa[pad].anos[y] = (mapa[pad].anos[y] || 0) + vy;
            }
          }
          return mapa;
        }

        // Evidência casada com um produto (pelo nome padrão; senão, pela
        // primeira palavra — a junção do calcário). `null` quando não há.
        function evidenciaDe(pad, evidMapa) {
          if (!pad) return null;
          if (evidMapa[pad]) return evidMapa[pad];
          var prim = String(pad).split(' ')[0];
          if (prim && evidMapa[prim]) return evidMapa[prim];
          return null;
        }

        function renderFertTabla(lista) {

          if (!tablaFert) return;

          if (!lista.length) {

            tablaFert.innerHTML = '<p class="muted">Nenhum fertilizante registrado nos filtros seleccionados.</p>';

            return;

          }

          var anos = anosFert(lista);

          function agregar(regs) {

            // A área é somada UMA vez por talhão/ano (chave OS·Fazenda·Talhão·
            // ano·cenário) para não inflar a "área tratada" quando o mesmo
            // produto aparece em mais de um slot (1/2/3) do mesmo talhão.
            var tot = 0, area = 0, regs2 = 0, porAno = {}, vistos = {}, i, r, an, v, chave;

            for (i = 0; i < regs.length; i++) {

              r = regs[i];

              an = (r.ano === null || r.ano === undefined) ? '—' : String(r.ano).trim();

              if (!porAno[an]) porAno[an] = { total: 0, area: 0, registros: 0, vistos: {} };

              v = num(r.total); if (!isNaN(v)) { tot += v; porAno[an].total += v; }

              v = num(r.area);

              chave = [r.os || '', r.fazenda || '', r.talhao || '', an, String(r.cenario || '')].join('|');

              if (!isNaN(v) && v > 0) {

                if (!porAno[an].vistos[chave]) { porAno[an].vistos[chave] = 1; porAno[an].area += v; }

                if (!vistos[chave]) { vistos[chave] = 1; area += v; }

              }

              regs2++; porAno[an].registros++;

            }

            return { total: tot, area: area, registros: regs2, porAno: porAno };

          }

          var porFert = {}, padraoPorFert = {}, ordem = [], i2, r2, nome;

          var evidMapa = evidenciasPorPadrao();

          for (i2 = 0; i2 < lista.length; i2++) {

            r2 = lista[i2];

            nome = String(r2.fertilizante || '—');

            if (!porFert[nome]) { porFert[nome] = []; padraoPorFert[nome] = String(r2.padronizado || nome); ordem.push(nome); }

            porFert[nome].push(r2);

          }

          ordenarFert(ordem);

          // Evidências (NFs) sem produto na coleta: entram como adubo
          // só-com-evidência — total/área/dose/registros zerados, só a linha de
          // evidência (0%). Marca também a primeira palavra (junção do calcário)
          // como atendida, para não duplicar um produto já coberto por ela.
          var usados = {};

          ordem.forEach(function (n) { usados[String(padraoPorFert[n] || '')] = 1; });

          ordem.forEach(function (n) {
            var p = String(padraoPorFert[n] || '').split(' ')[0];
            if (p) usados[p] = 1;
          });

          Object.keys(evidMapa).forEach(function (pad) {
            if (usados[pad]) return;
            var rotulo = evidMapa[pad].nome || pad;
            if (porFert[rotulo]) return;
            ordem.push(rotulo);
            padraoPorFert[rotulo] = pad;
            porFert[rotulo] = [];
          });

          ordenarFert(ordem);

          function celDose(agg, an) {

            var a = agg.porAno[an];

            return (!a || !(a.area > 0)) ? '<td class="cel-ano pec-sem-valor">—</td>'
              : '<td class="cel-ano">' + fmtNum(a.total / a.area, 2) + '</td>';

          }

          var linhas = ordem.map(function (nomeF) {

            var g = agregar(porFert[nomeF]);

            var evid = evidenciaDe(padraoPorFert[nomeF], evidMapa);

            var evidVolume = evid ? evid.volume : 0;

            var pct = (g.total > 0) ? Math.round(evidVolume / g.total * 100) : 0;

            var cor = (evidVolume > 0) ? corCobertura(pct) : '';

            var nLinhas = evid ? 5 : 4;

            var doseGeral = g.area > 0 ? g.total / g.area : NaN;

            var celsTotal = anos.map(function (an) {

              var a = g.porAno[an];

              return '<td class="cel-ano">' + fmtNum(a ? a.total : 0, 0) + '</td>';

            }).join('');

            var celsArea = anos.map(function (an) {

              var a = g.porAno[an];

              return '<td class="cel-ano">' + fmtNum(a ? a.area : 0, 2) + '</td>';

            }).join('');

            var celsDose = anos.map(function (an) { return celDose(g, an); }).join('');

            var celsRegs = anos.map(function (an) {

              var a = g.porAno[an];

              return '<td class="cel-ano">' + (a ? a.registros : 0) + '</td>';

            }).join('');

            var celsEvid = anos.map(function (an) {

              var a = g.porAno[an];

              var aplicadoAno = a ? a.total : 0;

              var evidAno = (evid && evid.anos) ? (num(evid.anos[an]) || 0) : 0;

              if (aplicadoAno > 0 || evidAno > 0) {
                var pctAno = (aplicadoAno > 0) ? Math.round(evidAno / aplicadoAno * 100) : 0;
                var corAno = corCobertura(pctAno);
                return '<td class="cel-ano ' + corAno + '">' + fmtNum(evidAno, 0) + ' (' + pctAno + '%)</td>';
              }

              return '<td class="cel-ano pec-sem-valor">—</td>';

            }).join('');

            var html = '<tr class="fert-grupo"><td class="fert-nome" rowspan="' + nLinhas + '">' + esc(nomeF) + '</td>' +

                '<td class="fert-metrica">Total (kg)</td>' +

                '<td class="cel-ano fert-geral">' + fmtNum(g.total, 0) + '</td>' + celsTotal + '</tr>' +

              '<tr><td class="fert-metrica">Área tratada (ha)</td>' +

                '<td class="cel-ano fert-geral">' + fmtNum(g.area, 2) + '</td>' + celsArea + '</tr>' +

              '<tr><td class="fert-metrica">Dose média (kg/ha)</td>' +

                '<td class="cel-ano fert-geral">' + (isNaN(doseGeral) ? '—' : fmtNum(doseGeral, 2)) + '</td>' + celsDose + '</tr>' +

              '<tr><td class="fert-metrica">Registros</td>' +

                '<td class="cel-ano fert-geral">' + g.registros + '</td>' + celsRegs + '</tr>';

            if (evid) {

              html += '<tr class="fert-evidencia"><td class="fert-metrica">Total Evidências (kg)</td>' +

                '<td class="cel-ano fert-geral ' + cor + '">' + fmtNum(evidVolume, 0) + ' (' + pct + '%)</td>' +

                celsEvid + '</tr>';

            }

            return html;

          }).join('');

          var headAnos = anos.map(function (an) { return '<th>' + esc(an) + '</th>'; }).join('');

          tablaFert.innerHTML = '<table class="fert-pivot"><thead><tr>' +

            '<th>Fertilizante</th><th></th><th>Geral</th>' + headAnos +

            '</tr></thead><tbody>' + linhas + '</tbody></table>';

        }

        // Painel 5.5 — um subpainel por fertilizante, no estilo do painel 4.2
        // (e do 7.x): cada nó (OS → Fazenda → Talhão) é um grupo de 4 linhas —
        // Total (kg), Área tratada (ha), Dose média (kg/ha) e Registros — com
        // uma coluna Geral + uma por ano, expandindo/recolhendo OS e Fazenda
        // (começa recolhido).
        function renderFertPivot(regs, el) {

          if (!el) return;

          if (!regs.length) {

            el.innerHTML = '';

            el.style.display = 'none';

            return;

          }

          el.style.display = 'block';

          var anos = anosFert(regs);

          var METRICAS = [

            { chave: 'total', rotulo: 'Total (kg)', casas: 0 },

            { chave: 'area', rotulo: 'Área tratada (ha)', casas: 2 },

            { chave: 'dose', rotulo: 'Dose média (kg/ha)', casas: 2 },

            { chave: 'registros', rotulo: 'Registros', casas: 0 }

          ];

          var arv = {}, ordemOs = [], i, r, os, faz, tal;

          for (i = 0; i < regs.length; i++) {

            r = regs[i];

            os = r.os || '—';

            faz = r.fazenda || '—';

            tal = r.talhao || '—';

            if (!arv[os]) { arv[os] = {}; ordemOs.push(os); }

            if (!arv[os][faz]) arv[os][faz] = {};

            if (!arv[os][faz][tal]) arv[os][faz][tal] = [];

            arv[os][faz][tal].push(r);

          }

          ordemOs.sort(function (a, b) { return a.localeCompare(b, 'pt-BR', { numeric: true }); });

          function acc() { return { total: 0, registros: 0, area: 0, vistos: {} }; }

          function agregar(lista) {

            var porAno = {}, geral = acc(), j, rr, an, v, a, chave;

            for (j = 0; j < lista.length; j++) {

              rr = lista[j];

              an = (rr.ano === null || rr.ano === undefined) ? '—' : String(rr.ano).trim();

              if (!porAno[an]) porAno[an] = acc();

              v = num(rr.total);

              if (!isNaN(v)) { porAno[an].total += v; geral.total += v; }

              porAno[an].registros++; geral.registros++;

              a = num(rr.area);

              chave = [rr.os || '', rr.fazenda || '', rr.talhao || '', an, String(rr.cenario || '')].join('|');

              if (!isNaN(a) && a > 0) {

                if (!porAno[an].vistos[chave]) { porAno[an].vistos[chave] = 1; porAno[an].area += a; }

                if (!geral.vistos[chave]) { geral.vistos[chave] = 1; geral.area += a; }

              }

            }

            return { porAno: porAno, geral: geral };

          }

          function valorMetrica(x, m) {

            if (!x) return null;

            if (m.chave === 'total') return x.total;

            if (m.chave === 'area') return x.area > 0 ? x.area : null;

            if (m.chave === 'dose') return x.area > 0 ? x.total / x.area : null;

            if (m.chave === 'registros') return x.registros > 0 ? x.registros : null;

            return null;

          }

          function celFert(valor, casas) {

            return (valor === null || valor === undefined)

              ? '<td class="fert-cel fert-sem-valor">—</td>'

              : '<td class="fert-cel">' + fmtNum(valor, casas) + '</td>';

          }

          function coleccionarRegistros(osA, fazA, talA) {

            if (talA) return arv[osA][fazA][talA];

            var total = [];

            Object.keys(arv[osA] || {}).forEach(function (fz) {

              if (!fazA || fz === fazA) {

                Object.keys(arv[osA][fz]).forEach(function (tl) {

                  total = total.concat(arv[osA][fz][tl]);

                });

              }

            });

            return total;

          }

          // Linhas de um nó: escritas só quando o nó de cima é expandido.
          // `temFilhos` marca a existência de nível inferior (seta clicável).
          function linhasNo(gid, nome, nivel, listaRegs, temFilhos) {

            var agg = agregar(listaRegs), html = '';

            METRICAS.forEach(function (m, idx) {

              var vGeral = valorMetrica(agg.geral, m);

              var celsAno = anos.map(function (an) {

                return celFert(valorMetrica(agg.porAno[an], m), m.casas);

              }).join('');

              var nomeTd = (idx === 0)

                ? '<td class="fert-nome fert-nivel-' + nivel + (temFilhos ? ' fert-clicavel' : '') +

                  '" data-grupo="' + gid + '"' + (temFilhos ? ' data-toggle="1"' : '') +

                  ' rowspan="' + METRICAS.length + '">' +

                  (temFilhos ? '<span class="fert-seta">▶</span> ' : '') + esc(nome) + '</td>'

                : '';

              var geralTd = (vGeral === null || vGeral === undefined)

                ? '<td class="fert-cel fert-geral fert-sem-valor">—</td>'

                : '<td class="fert-cel fert-geral">' + fmtNum(vGeral, m.casas) + '</td>';

              html += '<tr data-g="' + gid + '" class="fert-linha' + (idx === 0 ? ' fert-inicio-grupo' : '') + '">' +

                nomeTd + '<td class="fert-metrica">' + esc(m.rotulo) + '</td>' + geralTd + celsAno + '</tr>';

            });

            return html;

          }

          var headAnos = anos.map(function (an) { return '<th>' + esc(an) + '</th>'; }).join('');

          el.innerHTML = '<table class="fert-pivot"><thead><tr>' +

            '<th>OS · Fazenda · Talhão</th><th>Métrica</th><th>Geral</th>' + headAnos +

            '</tr></thead><tbody></tbody></table>';

          // Hierarquia sob demanda: só as OS (e a linha do total) entram agora;
          // as fazendas nascem ao abrir a OS e os talhões ao abrir a fazenda.
          var piv = ObterDados.pivotLazy({

            prefixo: 'fert',

            corpo: el.querySelector('tbody'),

            linhas: linhasNo

          });

          ordemOs.forEach(function (osA) {

            piv.raiz({

              nome: osA, nivel: 'os',

              coletar: function () { return coleccionarRegistros(osA, null, null); },

              gerarFilhos: function () {

                return Object.keys(arv[osA]).sort(function (a, b) { return a.localeCompare(b, 'pt-BR', { numeric: true }); })

                  .map(function (fazA) {

                    return {

                      nome: fazA, nivel: 'faz',

                      coletar: function () { return coleccionarRegistros(osA, fazA, null); },

                      gerarFilhos: function () {

                        return Object.keys(arv[osA][fazA]).sort(function (a, b) { return a.localeCompare(b, 'pt-BR', { numeric: true }); })

                          .map(function (talA) {

                            return { nome: talA, nivel: 'tal', coletar: arv[osA][fazA][talA] };

                          });

                      }

                    };

                  });

              }

            });

          });

          piv.raiz({ nome: 'Total geral', nivel: 'total', coletar: regs });

        }

        // Renderiza o painel 5.5: um subpainel (`5.5.N · <produto>`) por
        // fertilizante, em ordem ALFABÉTICA pelo nome (ver `ordenarFert`). O
        // produto é o NOME e vem resolvido do JSON (API 1): o mesmo produto
        // cadastrado em colunas diferentes sai UMA só vez, com as quantidades
        // somadas.
        function renderFertPivotes(lista) {

          if (!wrapFert) return;

          if (!lista.length) {

            wrapFert.innerHTML = '';

            wrapFert.style.display = 'none';

            if (vazioFert) vazioFert.classList.add('visivel');

            return;

          }

          if (vazioFert) vazioFert.classList.remove('visivel');

          var porFert = {}, ordem = [], i, r, nome;

          for (i = 0; i < lista.length; i++) {

            r = lista[i];

            nome = String(r.fertilizante || '—');

            if (!porFert[nome]) { porFert[nome] = []; ordem.push(nome); }

            porFert[nome].push(r);

          }

          ordenarFert(ordem);

          wrapFert.innerHTML = '';

          ordem.forEach(function (nomeF, idx) {

            var detalhe = document.createElement('details');

            detalhe.className = 'fert-detalhe';

            var resumo = document.createElement('summary');

            resumo.className = 'fert-detalhe-titulo';

            resumo.innerHTML = '<h4>5.5.' + (idx + 1) + ' · ' + esc(nomeF) + '</h4>';

            var cont = document.createElement('div');

            cont.className = 'fert-pivot-cont';

            detalhe.appendChild(resumo);

            detalhe.appendChild(cont);

            wrapFert.appendChild(detalhe);

            // O pivô do subpainel só é montado na primeira abertura do
            // `<details>` (o 5.5 começa recolhido): nenhuma linha de OS,
            // fazenda ou talhão é criada antes disso.
            detalhe.addEventListener('toggle', function () {

              if (!detalhe.open || cont.getAttribute('data-montado') === '1') return;

              cont.setAttribute('data-montado', '1');

              renderFertPivot(porFert[nomeF], cont);

            });

          });

          wrapFert.style.display = 'block';

        }

        // Séries (uma por fertilizante) para os gráficos de linhas 5.2–5.4.
        // metric: 'total' (kg) | 'area' (ha, deduplicada por talhão/ano) |
        // 'dose' (kg/ha = Σtotal ÷ Σárea).
        function seriesFertilizante(lista, metric) {
          var porFert = {}, ordem = [], i, r, nome, an, t, a, chave, vk;
          for (i = 0; i < lista.length; i++) {
            r = lista[i];
            nome = String(r.fertilizante || '—');
            if (!porFert[nome]) { porFert[nome] = { tot: {}, area: {}, vistos: {} }; ordem.push(nome); }
            an = (r.ano === null || r.ano === undefined) ? '—' : String(r.ano).trim();
            t = num(r.total);
            if (!isNaN(t)) porFert[nome].tot[an] = (porFert[nome].tot[an] || 0) + t;
            a = num(r.area);
            if (!isNaN(a) && a > 0) {
              chave = [r.os || '', r.fazenda || '', r.talhao || '', an, String(r.cenario || '')].join('|');
              vk = nome + '§' + chave;
              if (!porFert[nome].vistos[vk]) {
                porFert[nome].vistos[vk] = 1;
                porFert[nome].area[an] = (porFert[nome].area[an] || 0) + a;
              }
            }
          }
          ordenarFert(ordem);
          var anosSet = {}, series = [];
          ordem.forEach(function (nm) {
            var g = porFert[nm], valores = {}, y;
            if (metric === 'area') {
              valores = g.area;
            } else if (metric === 'dose') {
              for (y in g.tot) {
                if (Object.prototype.hasOwnProperty.call(g.tot, y) && g.area[y] > 0) {
                  valores[y] = g.tot[y] / g.area[y];
                }
              }
            } else {
              valores = g.tot;
            }
            for (y in valores) {
              if (Object.prototype.hasOwnProperty.call(valores, y)) anosSet[y] = 1;
            }
            series.push({ nome: nm, rotulo: nm, valores: valores });
          });
          var anos = Object.keys(anosSet).sort(function (a, b) {
            var x = Number(a), y = Number(b);
            if (isNaN(x)) return 1;
            if (isNaN(y)) return -1;
            return x - y;
          });
          return { series: series, anos: anos };
        }

        function renderFertTotaisLinhas(lista) {
          if (!wrapFertTotais || typeof ObterDados.montarGrafico !== 'function') return;
          var d = seriesFertilizante(lista, 'total');
          ObterDados.montarGrafico({
            container: wrapFertTotais, leyenda: leyendaFertTotais,
            series: d.series, anos: d.anos, ocultas: fertTotaisOcultas,
            unidade: 'total aplicado (kg)', unidadeCurta: 'kg',
            vazio: 'Nenhum fertilizante nos filtros selecionados.',
            aria: 'Total de fertilizante aplicado por ano (kg)'
          });
        }

        function renderFertAreaLinhas(lista) {
          if (!wrapFertArea || typeof ObterDados.montarGrafico !== 'function') return;
          var d = seriesFertilizante(lista, 'area');
          ObterDados.montarGrafico({
            container: wrapFertArea, leyenda: leyendaFertArea,
            series: d.series, anos: d.anos, ocultas: fertAreaOcultas,
            unidade: 'área tratada (ha)', unidadeCurta: 'ha',
            vazio: 'Nenhuma área tratada nos filtros selecionados.',
            aria: 'Área tratada por fertilizante e por ano (ha)'
          });
        }

        function renderFertDoseLinhas(lista) {
          if (!wrapFertDose || typeof ObterDados.montarGrafico !== 'function') return;
          var d = seriesFertilizante(lista, 'dose');
          ObterDados.montarGrafico({
            container: wrapFertDose, leyenda: leyendaFertDose,
            series: d.series, anos: d.anos, ocultas: fertDoseOcultas,
            unidade: 'dose média (kg/ha)', unidadeCurta: 'kg/ha',
            vazio: 'Nenhuma dose calculável nos filtros selecionados.',
            aria: 'Dose média de fertilizante por hectare e por ano (kg/ha)'
          });
        }

        // Etapas do painel: resumo → 5.1 (por fertilizante) → gráficos 5.2–5.4 →
        // subpainéis 5.5. Cada bloco entra num quadro.
        function renderFertTudo() {

          var lista = filtrarFertilizantes();

          return [

            function () { renderFertResumo(lista); },

            function () { renderFertTabla(lista); },

            function () { renderFertTotaisLinhas(lista); },

            function () { renderFertAreaLinhas(lista); },

            function () { renderFertDoseLinhas(lista); },

            function () { renderFertPivotes(lista); }

          ];

        }

        // Renderização sob demanda: o painel é montado na primeira abertura.
        // Recolhido, as tabelas e os subpainéis de fertilizantes saem da memória.
        ObterDados.registrarPainel('fertilizantes', renderFertTudo, function () {

          [resumoFert, tablaFert, wrapFert, wrapFertTotais, leyendaFertTotais,
            wrapFertArea, leyendaFertArea, wrapFertDose, leyendaFertDose]
            .forEach(function (el) { if (el) el.innerHTML = ''; });

        });

        // ----- Painel de nutrientes: massa de macro/micro vinda da adubação -----
        // A API 6 grava o resultado em `nutrients` no registro; a API 3 publica
        // UMA linha por registro no payload `dadosNutrientes`, com o N aberto em
        // total/sintético/orgânico e os demais nutrientes só pelo total. Este
        // painel espelha o painel 05 (fertilizantes): 6.1 tabela por nutriente,
        // 6.2–6.4 gráficos de total/área/dose e 6.5 a hierarquia de cada série.
        (function () {

          // Ordem do contrato: N (três séries) e depois os demais macro/micro.
          var NUTRI = [
            { chave: 'n_total', rotulo: 'N total' },
            { chave: 'n_sintetico', rotulo: 'N sintético' },
            { chave: 'n_organico', rotulo: 'N orgânico' },
            { chave: 'p2o5', rotulo: 'P2O5 total' },
            { chave: 'k2o', rotulo: 'K2O total' },
            { chave: 'ca', rotulo: 'Ca total' },
            { chave: 'mg', rotulo: 'Mg total' },
            { chave: 's', rotulo: 'S total' },
            { chave: 'b', rotulo: 'B total' },
            { chave: 'cu', rotulo: 'Cu total' },
            { chave: 'fe', rotulo: 'Fe total' },
            { chave: 'mn', rotulo: 'Mn total' },
            { chave: 'zn', rotulo: 'Zn total' },
            { chave: 'cl', rotulo: 'Cl total' },
            { chave: 'mo', rotulo: 'Mo total' },
            { chave: 'ni', rotulo: 'Ni total' }
          ];

          var resumoNutri = document.getElementById('nutriResumo');
          var tablaNutri = document.getElementById('nutriTabla');
          var wrapNutri = document.getElementById('nutriTabelaWrap');
          var vazioNutri = document.getElementById('nutriVazio');
          var wrapNutriTotais = document.getElementById('nutriTotaisLinhas');
          var leyendaNutriTotais = document.getElementById('nutriTotaisLeyenda');
          var wrapNutriArea = document.getElementById('nutriAreaLinhas');
          var leyendaNutriArea = document.getElementById('nutriAreaLeyenda');
          var wrapNutriDose = document.getElementById('nutriDoseLinhas');
          var leyendaNutriDose = document.getElementById('nutriDoseLeyenda');
          var nutriTotaisOcultas = {}, nutriAreaOcultas = {}, nutriDoseOcultas = {};

          function filtrarNutrientes() {

            var f = ObterDados.filtros, busca = normValor(f.busca);

            // O filtro de fertilizante NÃO entra: os nutrientes já vêm somados
            // de TODOS os produtos da linha (a API 6 grava o total do registro).
            var chaves = ['os', 'fazenda', 'talhao', 'ano', 'cenario'];

            return ObterDados.dadosNutrientes.filter(function (r) {

              for (var i = 0; i < chaves.length; i++) {

                if (!casaFiltro(r[chaves[i]], f[chaves[i]])) return false;

              }

              if (busca && normValor(JSON.stringify(r)).indexOf(busca) < 0) return false;

              return true;

            });

          }

          function anosNutri(lista) {

            var mapa = {}, anos = [], i, r, an;

            for (i = 0; i < lista.length; i++) {

              r = lista[i];

              an = (r.ano === null || r.ano === undefined) ? '—' : String(r.ano).trim();

              if (!(an in mapa)) { mapa[an] = 1; anos.push(an); }

            }

            return anos.sort(function (a, b) {

              var x = Number(a), y = Number(b);

              if (isNaN(x)) return 1;

              if (isNaN(y)) return -1;

              return x - y;

            });

          }

          function valorNutri(r, serie) {

            var v = num(r[serie.chave]);

            return isNaN(v) ? 0 : v;

          }

          function anoNutri(r) {

            return (r.ano === null || r.ano === undefined) ? '—' : String(r.ano).trim();

          }

          function seriesComDados(lista) {

            return NUTRI.filter(function (serie) {

              for (var i = 0; i < lista.length; i++) {

                if (valorNutri(lista[i], serie) > 0) return true;

              }

              return false;

            });

          }

          function renderNutriResumo(lista) {

            if (!resumoNutri) return;

            var fazSet = {}, osSet = {}, total = 0, series = seriesComDados(lista), i, r;

            for (i = 0; i < lista.length; i++) {

              r = lista[i];

              // Soma só os TOTAIS: N sintético/orgânico já estão no N total.
              NUTRI.forEach(function (serie) {

                if (serie.chave.indexOf('n_') !== 0 || serie.chave === 'n_total') {

                  total += valorNutri(r, serie);

                }

              });

              if (r.fazenda) fazSet[String(r.fazenda)] = 1;

              if (r.os) osSet[String(r.os)] = 1;

            }

            resumoNutri.innerHTML =

              '<span class="prod-chip"><strong>' + lista.length + '</strong> registros com adubação</span>' +

              '<span class="prod-chip"><strong>' + fmtNum(total, 0) + '</strong> kg de nutrientes</span>' +

              '<span class="prod-chip"><strong>' + series.length + '</strong> séries de nutrientes</span>' +

              '<span class="prod-chip"><strong>' + Object.keys(fazSet).length + '</strong> fazendas</span>' +

              '<span class="prod-chip"><strong>' + Object.keys(osSet).length + '</strong> OS</span>';

          }

          // Agrega UMA série de nutriente: total, área adubada (deduplicada por
          // talhão/ano) e registros, só nos registros em que o nutriente veio
          // da adubação (> 0). Devolve o geral + o recorte por ano.
          function agregarNutri(regs, chave) {

            var tot = 0, area = 0, registros = 0, porAno = {}, vistos = {}, i, r, an, v, a, k;

            for (i = 0; i < regs.length; i++) {

              r = regs[i];

              v = num(r[chave]);

              if (isNaN(v) || v <= 0) continue;

              an = anoNutri(r);

              if (!porAno[an]) porAno[an] = { total: 0, area: 0, registros: 0, vistos: {} };

              tot += v; registros++;

              porAno[an].total += v; porAno[an].registros++;

              a = num(r.area);

              k = [r.os || '', r.fazenda || '', r.talhao || '', an, String(r.cenario || '')].join('|');

              if (!isNaN(a) && a > 0) {

                if (!vistos[k]) { vistos[k] = 1; area += a; }

                if (!porAno[an].vistos[k]) { porAno[an].vistos[k] = 1; porAno[an].area += a; }

              }

            }

            return { total: tot, area: area, registros: registros, porAno: porAno };

          }

          // 6.1 — tabela por nutriente · ano (mesmo desenho do 5.1).
          function renderNutriTabla(lista) {

            if (!tablaNutri) return;

            if (!lista.length) {

              tablaNutri.innerHTML = '<p class="muted">Nenhum nutriente da adubação nos filtros selecionados.</p>';

              return;

            }

            var anos = anosNutri(lista), series = seriesComDados(lista);

            function celDose(agg, an) {

              var a = agg.porAno[an];

              return (!a || !(a.area > 0)) ? '<td class="cel-ano pec-sem-valor">—</td>'
                : '<td class="cel-ano">' + fmtNum(a.total / a.area, 2) + '</td>';

            }

            var linhas = series.map(function (serie) {

              var g = agregarNutri(lista, serie.chave);

              var doseGeral = g.area > 0 ? g.total / g.area : NaN;

              var celsTotal = anos.map(function (an) {

                var a = g.porAno[an];

                return '<td class="cel-ano">' + fmtNum(a ? a.total : 0, 0) + '</td>';

              }).join('');

              var celsArea = anos.map(function (an) {

                var a = g.porAno[an];

                return '<td class="cel-ano">' + fmtNum(a ? a.area : 0, 2) + '</td>';

              }).join('');

              var celsDose = anos.map(function (an) { return celDose(g, an); }).join('');

              var celsRegs = anos.map(function (an) {

                var a = g.porAno[an];

                return '<td class="cel-ano">' + (a ? a.registros : 0) + '</td>';

              }).join('');

              return '<tr class="fert-grupo"><td class="fert-nome" rowspan="4">' + esc(serie.rotulo) + '</td>' +

                  '<td class="fert-metrica">Total (kg)</td>' +

                  '<td class="cel-ano fert-geral">' + fmtNum(g.total, 0) + '</td>' + celsTotal + '</tr>' +

                '<tr><td class="fert-metrica">Área adubada (ha)</td>' +

                  '<td class="cel-ano fert-geral">' + fmtNum(g.area, 2) + '</td>' + celsArea + '</tr>' +

                '<tr><td class="fert-metrica">Dose média (kg/ha)</td>' +

                  '<td class="cel-ano fert-geral">' + (isNaN(doseGeral) ? '—' : fmtNum(doseGeral, 2)) + '</td>' + celsDose + '</tr>' +

                '<tr><td class="fert-metrica">Registros</td>' +

                  '<td class="cel-ano fert-geral">' + g.registros + '</td>' + celsRegs + '</tr>';

            }).join('');

            var headAnos = anos.map(function (an) { return '<th>' + esc(an) + '</th>'; }).join('');

            tablaNutri.innerHTML = '<table class="fert-pivot"><thead><tr>' +

              '<th>Nutriente</th><th></th><th>Geral</th>' + headAnos +

              '</tr></thead><tbody>' + linhas + '</tbody></table>';

          }

          // 6.5 — um subpainel por série de nutriente, no estilo do 5.5: cada nó
          // (OS → Fazenda → Talhão) é um grupo de 4 linhas — Total (kg), Área
          // adubada (ha), Dose média (kg/ha) e Registros — com uma coluna Geral
          // + uma por ano, expandindo/recolhendo (começa recolhido).
          function renderNutriPivot(regs, el, serie) {

            if (!el) return;

            if (!regs.length) {

              el.innerHTML = '';

              el.style.display = 'none';

              return;

            }

            el.style.display = 'block';

            var anos = anosNutri(regs);

            var METRICAS = [

              { chave: 'total', rotulo: 'Total (kg)', casas: 0 },

              { chave: 'area', rotulo: 'Área adubada (ha)', casas: 2 },

              { chave: 'dose', rotulo: 'Dose média (kg/ha)', casas: 2 },

              { chave: 'registros', rotulo: 'Registros', casas: 0 }

            ];

            var arv = {}, ordemOs = [], i, r, os, faz, tal;

            for (i = 0; i < regs.length; i++) {

              r = regs[i];

              os = r.os || '—';

              faz = r.fazenda || '—';

              tal = r.talhao || '—';

              if (!arv[os]) { arv[os] = {}; ordemOs.push(os); }

              if (!arv[os][faz]) arv[os][faz] = {};

              if (!arv[os][faz][tal]) arv[os][faz][tal] = [];

              arv[os][faz][tal].push(r);

            }

            ordemOs.sort(function (a, b) { return a.localeCompare(b, 'pt-BR', { numeric: true }); });

            function acc() { return { total: 0, registros: 0, area: 0, vistos: {} }; }

            function agregar(lista) {

              var porAno = {}, geral = acc(), j, rr, an, v, a, chave;

              for (j = 0; j < lista.length; j++) {

                rr = lista[j];

                an = anoNutri(rr);

                if (!porAno[an]) porAno[an] = acc();

                v = num(rr[serie.chave]);

                if (!isNaN(v) && v > 0) { porAno[an].total += v; geral.total += v; }

                porAno[an].registros++; geral.registros++;

                a = num(rr.area);

                chave = [rr.os || '', rr.fazenda || '', rr.talhao || '', an, String(rr.cenario || '')].join('|');

                if (!isNaN(a) && a > 0) {

                  if (!porAno[an].vistos[chave]) { porAno[an].vistos[chave] = 1; porAno[an].area += a; }

                  if (!geral.vistos[chave]) { geral.vistos[chave] = 1; geral.area += a; }

                }

              }

              return { porAno: porAno, geral: geral };

            }

            function valorMetrica(x, m) {

              if (!x) return null;

              if (m.chave === 'total') return x.total;

              if (m.chave === 'area') return x.area > 0 ? x.area : null;

              if (m.chave === 'dose') return x.area > 0 ? x.total / x.area : null;

              if (m.chave === 'registros') return x.registros > 0 ? x.registros : null;

              return null;

            }

            function celNutri(valor, casas) {

              return (valor === null || valor === undefined)

                ? '<td class="fert-cel fert-sem-valor">—</td>'

                : '<td class="fert-cel">' + fmtNum(valor, casas) + '</td>';

            }

            function coleccionarRegistros(osA, fazA, talA) {

              if (talA) return arv[osA][fazA][talA];

              var total = [];

              Object.keys(arv[osA] || {}).forEach(function (fz) {

                if (!fazA || fz === fazA) {

                  Object.keys(arv[osA][fz]).forEach(function (tl) {

                    total = total.concat(arv[osA][fz][tl]);

                  });

                }

              });

              return total;

            }

            function linhasNo(gid, nome, nivel, listaRegs, temFilhos) {

              var agg = agregar(listaRegs), html = '';

              METRICAS.forEach(function (m, idx) {

                var vGeral = valorMetrica(agg.geral, m);

                var celsAno = anos.map(function (an) {

                  return celNutri(valorMetrica(agg.porAno[an], m), m.casas);

                }).join('');

                var nomeTd = (idx === 0)

                  ? '<td class="fert-nome fert-nivel-' + nivel + (temFilhos ? ' fert-clicavel' : '') +

                    '" data-grupo="' + gid + '"' + (temFilhos ? ' data-toggle="1"' : '') +

                    ' rowspan="' + METRICAS.length + '">' +

                    (temFilhos ? '<span class="fert-seta">▶</span> ' : '') + esc(nome) + '</td>'

                  : '';

                var geralTd = (vGeral === null || vGeral === undefined)

                  ? '<td class="fert-cel fert-geral fert-sem-valor">—</td>'

                  : '<td class="fert-cel fert-geral">' + fmtNum(vGeral, m.casas) + '</td>';

                html += '<tr data-g="' + gid + '" class="fert-linha' + (idx === 0 ? ' fert-inicio-grupo' : '') + '">' +

                  nomeTd + '<td class="fert-metrica">' + esc(m.rotulo) + '</td>' + geralTd + celsAno + '</tr>';

              });

              return html;

            }

            var headAnos = anos.map(function (an) { return '<th>' + esc(an) + '</th>'; }).join('');

            el.innerHTML = '<table class="fert-pivot"><thead><tr>' +

              '<th>OS · Fazenda · Talhão</th><th>Métrica</th><th>Geral</th>' + headAnos +

              '</tr></thead><tbody></tbody></table>';

            // Hierarquia sob demanda: só as OS (e a linha do total) entram
            // agora; as fazendas nascem ao abrir a OS e os talhões ao abrir a
            // fazenda — mesmo mecanismo do 5.5.
            var piv = ObterDados.pivotLazy({

              prefixo: 'fert',

              corpo: el.querySelector('tbody'),

              linhas: linhasNo

            });

            ordemOs.forEach(function (osA) {

              piv.raiz({

                nome: osA, nivel: 'os',

                coletar: function () { return coleccionarRegistros(osA, null, null); },

                gerarFilhos: function () {

                  return Object.keys(arv[osA]).sort(function (a, b) { return a.localeCompare(b, 'pt-BR', { numeric: true }); })

                    .map(function (fazA) {

                      return {

                        nome: fazA, nivel: 'faz',

                        coletar: function () { return coleccionarRegistros(osA, fazA, null); },

                        gerarFilhos: function () {

                          return Object.keys(arv[osA][fazA]).sort(function (a, b) { return a.localeCompare(b, 'pt-BR', { numeric: true }); })

                            .map(function (talA) {

                              return { nome: talA, nivel: 'tal', coletar: arv[osA][fazA][talA] };

                            });

                        }

                      };

                    });

                }

              });

            });

            piv.raiz({ nome: 'Total geral', nivel: 'total', coletar: regs });

          }

          // Renderiza o 6.5: um `<details>` recolhido por série de nutriente
          // (só as séries com dado no recorte), montado na primeira abertura.
          function renderNutriPivotes(lista) {

            if (!wrapNutri) return;

            if (!lista.length) {

              wrapNutri.innerHTML = '';

              wrapNutri.style.display = 'none';

              if (vazioNutri) vazioNutri.classList.add('visivel');

              return;

            }

            if (vazioNutri) vazioNutri.classList.remove('visivel');

            var series = seriesComDados(lista);

            wrapNutri.innerHTML = '';

            series.forEach(function (serie, idx) {

              var regsSerie = lista.filter(function (r) { return valorNutri(r, serie) > 0; });

              var detalhe = document.createElement('details');

              detalhe.className = 'fert-detalhe';

              var resumo = document.createElement('summary');

              resumo.className = 'fert-detalhe-titulo';

              resumo.innerHTML = '<h4>6.5.' + (idx + 1) + ' · ' + esc(serie.rotulo) + '</h4>';

              var cont = document.createElement('div');

              cont.className = 'fert-pivot-cont';

              detalhe.appendChild(resumo);

              detalhe.appendChild(cont);

              wrapNutri.appendChild(detalhe);

              detalhe.addEventListener('toggle', function () {

                if (!detalhe.open || cont.getAttribute('data-montado') === '1') return;

                cont.setAttribute('data-montado', '1');

                renderNutriPivot(regsSerie, cont, serie);

              });

            });

            wrapNutri.style.display = 'block';

          }

          // Séries (uma por nutriente) para os gráficos 6.2–6.4.
          // metric: 'total' (kg) | 'area' (ha, deduplicada por talhão/ano) |
          // 'dose' (kg/ha = Σtotal ÷ Σárea). Só entram os registros em que o
          // nutriente veio da adubação (> 0).
          function serieNutriente(lista, serie, metric) {

            var tot = {}, area = {}, vistos = {}, valores = {}, tem = false, i, r, an, v, a, k, y;

            for (i = 0; i < lista.length; i++) {

              r = lista[i];

              v = num(r[serie.chave]);

              if (isNaN(v) || v <= 0) continue;

              an = anoNutri(r);

              tot[an] = (tot[an] || 0) + v;

              a = num(r.area);

              if (!isNaN(a) && a > 0) {

                k = [r.os || '', r.fazenda || '', r.talhao || '', an, String(r.cenario || '')].join('|');

                if (!vistos[k]) { vistos[k] = 1; area[an] = (area[an] || 0) + a; }

              }

            }

            if (metric === 'area') {

              valores = area;

            } else if (metric === 'dose') {

              for (y in tot) {

                if (Object.prototype.hasOwnProperty.call(tot, y) && area[y] > 0) {

                  valores[y] = tot[y] / area[y];

                }

              }

            } else {

              valores = tot;

            }

            for (y in valores) {

              if (Object.prototype.hasOwnProperty.call(valores, y)) {

                if (valores[y] > 0) tem = true;

              }

            }

            return tem ? { nome: serie.chave, rotulo: serie.rotulo, valores: valores } : null;

          }

          function seriesNutri(lista, metric) {

            var series = [], anosSet = {}, anos, y;

            NUTRI.forEach(function (serie) {

              var s = serieNutriente(lista, serie, metric);

              if (!s) return;

              series.push(s);

              for (y in s.valores) {

                if (Object.prototype.hasOwnProperty.call(s.valores, y)) anosSet[y] = 1;

              }

            });

            anos = Object.keys(anosSet).sort(function (a, b) {

              var x = Number(a), z = Number(b);

              if (isNaN(x)) return 1;

              if (isNaN(z)) return -1;

              return x - z;

            });

            return { series: series, anos: anos };

          }

          function renderNutriTotaisLinhas(lista) {

            if (!wrapNutriTotais || typeof ObterDados.montarGrafico !== 'function') return;

            var d = seriesNutri(lista, 'total');

            ObterDados.montarGrafico({

              container: wrapNutriTotais, leyenda: leyendaNutriTotais,

              series: d.series, anos: d.anos, ocultas: nutriTotaisOcultas,

              unidade: 'total de nutrientes (kg)', unidadeCurta: 'kg',

              vazio: 'Nenhum nutriente da adubação nos filtros selecionados.',

              aria: 'Total de cada nutriente da adubação por ano (kg)'

            });

          }

          function renderNutriAreaLinhas(lista) {

            if (!wrapNutriArea || typeof ObterDados.montarGrafico !== 'function') return;

            var d = seriesNutri(lista, 'area');

            ObterDados.montarGrafico({

              container: wrapNutriArea, leyenda: leyendaNutriArea,

              series: d.series, anos: d.anos, ocultas: nutriAreaOcultas,

              unidade: 'área adubada (ha)', unidadeCurta: 'ha',

              vazio: 'Nenhuma área adubada nos filtros selecionados.',

              aria: 'Área adubada com cada nutriente por ano (ha)'

            });

          }

          function renderNutriDoseLinhas(lista) {

            if (!wrapNutriDose || typeof ObterDados.montarGrafico !== 'function') return;

            var d = seriesNutri(lista, 'dose');

            ObterDados.montarGrafico({

              container: wrapNutriDose, leyenda: leyendaNutriDose,

              series: d.series, anos: d.anos, ocultas: nutriDoseOcultas,

              unidade: 'dose média (kg/ha)', unidadeCurta: 'kg/ha',

              vazio: 'Nenhuma dose calculável nos filtros selecionados.',

              aria: 'Dose média de cada nutriente por hectare e por ano (kg/ha)'

            });

          }

          // Etapas do painel: resumo → 6.1 (por nutriente) → gráficos 6.2–6.4
          // → subpainéis 6.5. Cada bloco entra num quadro.
          function renderNutriTudo() {

            var lista = filtrarNutrientes();

            return [

              function () { renderNutriResumo(lista); },

              function () { renderNutriTabla(lista); },

              function () { renderNutriTotaisLinhas(lista); },

              function () { renderNutriAreaLinhas(lista); },

              function () { renderNutriDoseLinhas(lista); },

              function () { renderNutriPivotes(lista); }

            ];

          }

          // Renderização sob demanda: o painel é montado na primeira abertura.
          // Recolhido, as tabelas e os subpainéis de nutrientes saem da memória.
          ObterDados.registrarPainel('nutrientes', renderNutriTudo, function () {

            [resumoNutri, tablaNutri, wrapNutri, wrapNutriTotais, leyendaNutriTotais,
              wrapNutriArea, leyendaNutriArea, wrapNutriDose, leyendaNutriDose]
              .forEach(function (el) { if (el) el.innerHTML = ''; });

          });

        })();


      })();



      // ----- Painel 07: combustíveis (L) e energia (kWh) -----
      // O JSON (`dadosCombustivel`) reúne as duas unidades e cada linha é
      // classificada pela unidade (`categoriaDe`). O painel (`montar(cfg)`) tem
      // as subdivisões: resumo → 7.1 (por combustível/fonte e ano) →
      // 7.2/7.3 (gráficos de consumo total e por hectare com DUAS escalas:
      // energia à esquerda e UMA LINHA POR COMBUSTÍVEL à direita) → 7.4–7.8
      // (uma tabela agrupada por combustível/fonte).
      (function () {

        // Classificação por unidade: energia elétrica (kWh) x combustíveis (L).
        function categoriaDe(r) {

          var u = normValor(r.unidade);

          if (u.indexOf('kwh') >= 0 || u.indexOf('energia') >= 0 || u.indexOf('eletric') >= 0) return 'energia';

          return 'combustivel';

        }

        // Cores das séries dos gráficos 7.2/7.3: a energia elétrica (kWh) tem a
        // SUA cor fixa (`ObterDados.COR_ENERGIA`) e cada combustível líquido (L)
        // recebe uma cor da PALETA PADRÃO — a lista começa DEPOIS da cor da
        // energia, então as duas séries nunca saem iguais e nenhum combustível
        // repete a cor do outro enquanto houver cor livre.
        var CORES_COMB_EVOL = {
          kwh: ObterDados.COR_ENERGIA,
          liquidos: ObterDados.coresDaPaleta(20, 1)
        };

        function montar(cfg) {

        var resumoComb = cfg.resumo;

        var painelComb = cfg.painel;

        var tablaAnoComb = cfg.tablaAno;

        var tablaComb = cfg.tabla;

        var wrapComb = cfg.wrap;

        var vazioComb = cfg.vazio;

        var pivotComb = cfg.pivot;

        var pivotDiesel = cfg.pivotDiesel;

        var pivotAlcool = cfg.pivotAlcool;

        var pivotGasolina = cfg.pivotGasolina;

        var pivotEnergia = cfg.pivotEnergia;

        var wrapCombEvol = cfg.evol;

        var leyendaCombEvol = cfg.evolLeyenda;

        var wrapCombHa = cfg.ha;

        var leyendaCombHa = cfg.haLeyenda;

        var ocultasCombEvol = {};

        var ocultasCombHa = {};

        function filtrarCombustiveis(categoria, fonte) {

          var f = ObterDados.filtros, busca = normValor(f.busca);

          var chaves = ['os', 'fazenda', 'ano', 'cenario', 'combustivel'];

          var cat = normValor(categoria), fnt = normValor(fonte);

          return ObterDados.dadosCombustivel.filter(function (r) {

            if (cat && categoriaDe(r) !== cat) return false;

            if (fnt && normValor(r.fonte) !== fnt) return false;

            for (var i = 0; i < chaves.length; i++) {

              if (!casaFiltro(r[chaves[i]], f[chaves[i]])) return false;

            }

            if (busca && normValor(JSON.stringify(r)).indexOf(busca) < 0) return false;

            return true;

          });

        }

        function anosComb(lista) {

          var mapa = {}, anos = [], i, r, an;

          for (i = 0; i < lista.length; i++) {

            r = lista[i];

            an = (r.ano === null || r.ano === undefined) ? '—' : String(r.ano).trim();

            if (!(an in mapa)) { mapa[an] = 1; anos.push(an); }

          }

          return anos.sort(function (a, b) {

            var x = Number(a), y = Number(b);

            if (isNaN(x)) return 1;

            if (isNaN(y)) return -1;

            return x - y;

          });

        }

        function unidadesComb(lista) {

          var mapa = {}, lista2 = [], i, u;

          for (i = 0; i < lista.length; i++) {

            u = String(lista[i].unidade || 'L').trim();

            if (!(u in mapa)) { mapa[u] = 1; lista2.push(u); }

          }

          lista2.sort(function (a, b) { return a.localeCompare(b, 'pt-BR', { numeric: true }); });

          return lista2;

        }

        function rotuloUnidade(u) {

          var norm = normValor(u);

          if (norm.indexOf('kwh') >= 0 || norm.indexOf('energia') >= 0) return 'Energia elétrica (kWh)';

          if (norm === 'l' || norm.indexOf('litro') >= 0) return 'Combustíveis líquidos (L)';

          return 'Consumo (' + u + ')';

        }

        function anoComb(r) {

          return (r.ano === null || r.ano === undefined) ? '—' : String(r.ano).trim();

        }

        function areaPorAno(lista) {

          // Cada par (OS, fazenda, cenário) conta a área UMA vez por ano, para

          // não repetir a mesma área em cada combustível/fonte.

          var vistos = {}, mapa = {}, i, r, an, chave, v;

          for (i = 0; i < lista.length; i++) {

            r = lista[i];

            an = anoComb(r);

            chave = an + '§' + [r.os || '', r.fazenda || '', r.talhao || '', String(r.cenario || '')].join('|');

            if (vistos[chave]) continue;

            v = num(r.area);

            if (isNaN(v) || v <= 0) continue;

            vistos[chave] = 1;

            mapa[an] = (mapa[an] || 0) + v;

          }

          return mapa;

        }

        function areaDistinta(lista) {

          var vistos = {}, total = 0, i, r, chave, v;

          for (i = 0; i < lista.length; i++) {

            r = lista[i];

            chave = [r.os || '', r.fazenda || '', r.talhao || '', anoComb(r), String(r.cenario || '')].join('|');

            if (vistos[chave]) continue;

            v = num(r.area);

            if (isNaN(v) || v <= 0) continue;

            vistos[chave] = 1;

            total += v;

          }

          return total;

        }

        function somarPorAno(lista, campo) {

          var mapa = {}, i, r, an, v;

          for (i = 0; i < lista.length; i++) {

            r = lista[i];

            an = (r.ano === null || r.ano === undefined) ? '—' : String(r.ano).trim();

            if (!mapa[an]) mapa[an] = 0;

            v = num(r[campo]);

            if (!isNaN(v) && v > 0) mapa[an] += v;

          }

          return mapa;

        }

        function barraComb(v, maxV, sufixo) {

          var largura = (maxV > 0) ? Math.max(3, Math.round(v / maxV * 90)) : 3;

          return '<span class="comb-evo-celda"><span class="comb-barra" style="width:' +

            largura + 'px"></span>' + fmtNum(v, 2) + ' ' + esc(sufixo) + '</span>';

        }

        function tabelaEvolucao(regs, unidade) {

          var anos = anosComb(regs);

          if (!anos.length) return '';

          var tots = somarPorAno(regs, 'total'), areas = areaPorAno(regs);

          var doses = anos.map(function (an) {

            return (areas[an] && areas[an] > 0) ? (tots[an] || 0) / areas[an] : null;

          });

          var maxD = 0, i2;

          for (i2 = 0; i2 < doses.length; i2++) { if (doses[i2] && doses[i2] > maxD) maxD = doses[i2]; }

          var filas = anos.map(function (an, i3) {

            var d = doses[i3];

            var cel = (d === null || d === undefined)

              ? '<td class="cel-ano pec-sem-valor">—</td>'

              : '<td class="cel-ano">' + barraComb(d, maxD, unidade + '/ha') + '</td>';

            return '<tr><td class="cel-ano">' + esc(an) + '</td>' +

              '<td class="cel-ano">' + fmtNum(tots[an] || 0, 2) + ' ' + esc(unidade) + '</td>' +

              '<td class="cel-ano">' + fmtNum(areas[an] || 0, 2) + '</td>' +

              cel + '</tr>';

          }).join('');

          return '<table><thead><tr><th>Ano</th><th>Consumo total (' + esc(unidade) + ')</th>' +

            '<th>Área (ha)</th><th>Consumo por hectare (' + esc(unidade) + '/ha)</th></tr></thead><tbody>' +

            filas + '</tbody></table>';

        }

        function renderCombPainel(lista) {

          if (!painelComb) return;

          if (!lista.length) {

            painelComb.innerHTML = '<p class="muted">Nenhum consumo registrado.</p>';

            return;

          }

          var blocos = unidadesComb(lista).map(function (u) {

            var regs = lista.filter(function (x) { return String(x.unidade || 'L').trim() === u; });

            var fazSet = {}, ordemF = [], i, r;

            for (i = 0; i < regs.length; i++) {

              r = regs[i];

              if (r.fazenda && !(String(r.fazenda) in fazSet)) {

                fazSet[String(r.fazenda)] = 1; ordemF.push(String(r.fazenda));

              }

            }

            ordemF.sort(function (a, b) { return a.localeCompare(b, 'pt-BR', { numeric: true }); });

            var blocoFazendas = ordemF.map(function (fz) {

              var regsF = regs.filter(function (x) { return String(x.fazenda) === fz; });

              return '<details class="talhoes"><summary>' + esc(fz) + ' — consumo por hectare por ano (' +

                esc(u) + '/ha)</summary>' + tabelaEvolucao(regsF, u) + '</details>';

            }).join('');

            return '<div class="prod-bloco-titulo"><h4 style="margin:14px 0 6px">' + esc(rotuloUnidade(u)) +

              '</h4><p class="muted">Consumo por hectare = Σ consumo total ÷ Σ área distinta (ha) do ano</p></div>' +

              tabelaEvolucao(regs, u) + blocoFazendas;

          }).join('');

          painelComb.innerHTML = blocos;

        }

        function resumirPorCombustivel(lista) {

          var mapa = {}, ordem = [], vistos = {}, i, r, nome, item, v, chave, an;

          for (i = 0; i < lista.length; i++) {

            r = lista[i];

            nome = String(r.combustivel || '—');

            if (!mapa[nome]) {

              mapa[nome] = { combustivel: nome, unidade: String(r.unidade || 'L').trim(),

                             total: 0, area: 0, registros: 0, porAno: {} };

              ordem.push(mapa[nome]);

            }

            item = mapa[nome];

            an = anoComb(r);

            v = num(r.total);

            if (!isNaN(v)) { item.total += v; item.porAno[an] = (item.porAno[an] || 0) + v; }

            chave = nome + '§' + [r.os || '', r.fazenda || '', r.talhao || '', anoComb(r), String(r.cenario || '')].join('|');

            v = num(r.area);

            if (!isNaN(v) && v > 0 && !vistos[chave]) { vistos[chave] = 1; item.area += v; }

            item.registros++;

          }

          ordem.sort(function (a, b) { return b.total - a.total; });

          return ordem;

        }

        function renderCombTabla(lista) {

          if (!tablaComb) return;

          if (!lista.length) {

            tablaComb.innerHTML = '<p class="muted">Nenhum registro nos filtros selecionados.</p>';

            return;

          }

          var anos = anosComb(lista);

          var filas = resumirPorCombustivel(lista).map(function (it) {

            var dose = it.area > 0 ? (it.total / it.area) : NaN;

            var celsAnos = anos.map(function (an) {

              return '<td class="cel-ano">' + fmtNum(it.porAno[an] || 0, 2) + '</td>';

            }).join('');

            return '<tr><td>' + esc(it.combustivel) + '</td>' +

              '<td class="cel-ano">' + esc(it.unidade) + '</td>' +

              celsAnos +

              '<td class="cel-ano"><strong>' + fmtNum(it.total, 2) + '</strong></td>' +

              '<td class="cel-ano">' + fmtNum(it.area, 2) + '</td>' +

              '<td class="cel-ano">' + (isNaN(dose) ? '—' : fmtNum(dose, 2)) + '</td>' +

              '<td class="cel-ano">' + it.registros + '</td></tr>';

          }).join('');

          var cabAnos = anos.map(function (an) { return '<th>' + esc(an) + '</th>'; }).join('');

          tablaComb.innerHTML = '<table><thead><tr><th>' + esc(cfg.coluna) + '</th><th>Unidade</th>' +

            cabAnos +

            '<th>Consumo total</th><th>Área (ha)</th><th>Consumo por hectare</th><th>Registros</th>' +

            '</tr></thead><tbody>' + filas + '</tbody></table>';

        }

        function renderCombHierarquia(lista) {

          if (!wrapComb) return;

          if (!lista.length) {

            wrapComb.style.display = 'none';

            if (vazioComb) vazioComb.classList.add('visivel');

            return;

          }

          if (vazioComb) vazioComb.classList.remove('visivel');

          var blocos = unidadesComb(lista).map(function (u) {

            var regsU = lista.filter(function (x) { return String(x.unidade || 'L').trim() === u; });

            var anos = anosComb(regsU);

            var arv = {}, ordemOs = [], i, r, os, faz;

            for (i = 0; i < regsU.length; i++) {

              r = regsU[i];

              os = r.os || '—';

              faz = r.fazenda || '—';

              if (!arv[os]) { arv[os] = {}; ordemOs.push(os); }

              if (!arv[os][faz]) arv[os][faz] = [];

              arv[os][faz].push(r);

            }

            ordemOs.sort(function (a, b) { return a.localeCompare(b, 'pt-BR', { numeric: true }); });

            function regsDaFazenda(osAtual, fazAtual) { return arv[osAtual][fazAtual]; }

            function regsDaOS(osAtual) {

              var total = [];

              Object.keys(arv[osAtual] || {}).forEach(function (fz) {

                total = total.concat(arv[osAtual][fz]);

              });

              return total;

            }

            function celdasDose(regs) {

              var areas = areaPorAno(regs), tots = somarPorAno(regs, 'total');

              return anos.map(function (an) {

                var area = areas[an], tot = tots[an];

                var v = (area && area > 0) ? (tot || 0) / area : null;

                return v === null ? '<span class="cel-ano pec-sem-valor">—</span>'

                                  : '<span class="cel-ano">' + fmtNum(v, 2) + ' ' + esc(u) + '/ha</span>';

              }).join('');

            }

            function fatiaLinha(expand, nome, regs) {

              return '<span class="toggle">' + (expand ? '▶' : '') + '</span>' +

                '<span class="cel-nome">' + esc(nome) + '</span>' + celdasDose(regs) +

                '<span class="cel-regs">' + regs.length + '</span>';

            }

            var head = '<div class="det-row det-head"><span class="toggle"></span>' +

              '<span class="cel-nome">OS · Fazenda</span>' +

              anos.map(function (an) { return '<span class="cel-cultura">' + esc(an) + '</span>'; }).join('') +

              '<span class="cel-regs">Registros</span></div>';


            var bloques = ordemOs.map(function (osA) {

              var fazes = Object.keys(arv[osA]).sort(function (a, b) {

                return a.localeCompare(b, 'pt-BR', { numeric: true });

              });

              var rowsFaz = fazes.map(function (fazA) {

                return '<div class="det-row">' + fatiaLinha(false, fazA, regsDaFazenda(osA, fazA)) + '</div>';

              }).join('');

              return '<details class="cons-os"' + '><summary class="det-row">' +

                fatiaLinha(true, osA, regsDaOS(osA)) + '</summary>' +

                (rowsFaz ? '<div class="cons-body">' + rowsFaz + '</div>' : '') + '</details>';

            }).join('');

            var totalGeral = '<div class="det-row det-total">' + fatiaLinha(false, 'Total geral', regsU) + '</div>';

            var cols = '1.7rem minmax(180px, auto) repeat(' + anos.length + ', minmax(96px, auto)) minmax(70px, auto)';

            return '<div class="prod-bloco-titulo"><h4 style="margin:14px 0 6px">' + esc(rotuloUnidade(u)) +

              '</h4><p class="muted">Consumo por hectare (' + esc(u) + '/ha) por ano — clique na OS para expandir as fazendas</p></div>' +

              '<div class="painel-consolidado prod-hierarquia" style="--cols:' + cols + '">' +

              head + bloques + totalGeral + '</div>';

          }).join('');

          wrapComb.innerHTML = blocos;

          wrapComb.style.display = 'block';

        }

        // ------------------------------------------------------------------
        // 7.1 — Consumo por combustível/fonte e por ano, com a EVIDÊNCIA (NF)
        // na LINHA DE BAIXO de cada item (mesma regra do painel 5.1).
        // ------------------------------------------------------------------
        // Tipo de evidência (NF) de um combustível/fonte: o rótulo do painel é o
        // do dado (`Diesel`, `Gasolina`, `Etanol`/`Álcool`) e o tipo é a FAMÍLIA
        // da nota fiscal (`diesel`, `gasolina`, `etanol` — `NfsProductFilter` da
        // API 7). A energia elétrica (kWh) NÃO tem evidência de NF e devolve ''.
        function tipoEvidenciaComb(nome) {

          var n = normValor(nome);

          if (!n) return '';

          if (n.indexOf('diesel') >= 0) return 'diesel';

          if (n.indexOf('gasolina') >= 0) return 'gasolina';

          if (n.indexOf('etanol') >= 0 || n.indexOf('alcool') >= 0) return 'etanol';

          return '';

        }

        // Evidência (NF) por TIPO — `{tipo: {unidade, anos}}` — a partir do
        // payload `dadosEvidenciasTipos` (API 3). O 7.1 usa o TOTAL do tipo: o
        // diesel, por exemplo, soma S10 + S500 num só volume ("diesel total"),
        // como o 9.1; gasolina e etanol são um produto só cada, sempre em litros.
        function evidenciasPorTipo() {

          var mapa = {}, tipos = ObterDados.dadosEvidenciasTipos || [], i, t, tipo, anos, y, v;

          for (i = 0; i < tipos.length; i++) {

            t = tipos[i];

            tipo = normValor(t.tipo);

            if (!tipo) continue;

            if (!mapa[tipo]) mapa[tipo] = { unidade: String(t.unidade || 'kg').trim(), anos: {} };

            anos = t.anos || {};

            for (y in anos) {

              if (!Object.prototype.hasOwnProperty.call(anos, y)) continue;

              v = num(anos[y]);

              if (!isNaN(v) && v > 0) mapa[tipo].anos[y] = (mapa[tipo].anos[y] || 0) + v;

            }

          }

          return mapa;

        }

        // Célula de UM ano da linha de evidência, na MESMA regra do 5.1: sem
        // consumo informado E sem evidência no ano → `—`; com consumo informado
        // → o volume evidenciado e o % de cobertura (evidenciado ÷ informado ×
        // 100) com a cor da faixa (`configCobertura`).
        function celEvidenciaComb(informado, evidAno) {

          if (!(informado > 0) && !(evidAno > 0)) return '<td class="cel-ano comb-sem-valor">—</td>';

          var pct = (informado > 0) ? Math.round(evidAno / informado * 100) : 0;

          return '<td class="cel-ano ' + corCobertura(pct) + '">' + fmtNum(evidAno, 0) + ' (' + pct + '%)</td>';

        }

        function renderCombTablaAno(lista) {

          if (!tablaAnoComb) return;

          var anos = anosComb(lista);

          if (!lista.length || !anos.length) {

            tablaAnoComb.innerHTML = '<p class="muted">Nenhum registro nos filtros selecionados.</p>';

            return;

          }

          var mapa = {}, ordem = [], i, r, nome, an, v;

          for (i = 0; i < lista.length; i++) {

            r = lista[i];

            nome = String(r.combustivel || '—');

            if (!mapa[nome]) {

              mapa[nome] = { nome: nome, unidade: String(r.unidade || 'L').trim(),
                             fonte: String(r.fonte || '').trim(), porAno: {}, total: 0 };

              ordem.push(mapa[nome]);

            }

            an = anoComb(r);

            v = num(r.total); if (isNaN(v)) v = 0;

            mapa[nome].porAno[an] = (mapa[nome].porAno[an] || 0) + v;

            mapa[nome].total += v;

          }

          ordem.sort(function (a, b) { return b.total - a.total; });

          var evidTipos = evidenciasPorTipo();

          var cab = '<tr><th>' + esc(cfg.coluna) + '</th>' +

            anos.map(function (x) { return '<th>' + esc(x) + '</th>'; }).join('') +

            '<th>Total</th></tr>';

          var filas = ordem.map(function (it) {

            // Linha de CIMA: o consumo INFORMADO (coleta), com a unidade.
            var cels = anos.map(function (x) { return '<td class="cel-ano">' + fmtNum(it.porAno[x] || 0, 2) + ' ' + esc(it.unidade) + '</td>'; }).join('');

            var html = '<tr class="comb-grupo"><td class="comb-nome">' + esc(it.nome) + '</td>' + cels +

              '<td class="cel-ano"><strong>' + fmtNum(it.total, 2) + ' ' + esc(it.unidade) + '</strong></td></tr>';

            // Linha de BAIXO: o Total Evidências do tipo, ano a ano, com o %.
            var tipoEv = tipoEvidenciaComb(it.nome) || tipoEvidenciaComb(it.fonte);

            var ev = tipoEv ? (evidTipos[tipoEv] || null) : null;

            var rotulo = 'Total Evidências (' + esc(it.unidade) + ')';

            // Sem tipo de evidência (a energia elétrica, por exemplo): a linha
            // sai com `—` em vez de "0 (0%)" — não existe NF desse
            // combustível/fonte e o zero sugeriria falta de comprovação onde não
            // há fonte de evidência.
            if (!ev) {

              html += '<tr class="comb-evid"><td class="comb-nome comb-evid-rotulo">' + rotulo + '</td>' +

                anos.map(function () { return '<td class="cel-ano comb-sem-valor">—</td>'; }).join('') +

                '<td class="cel-ano comb-sem-valor">—</td></tr>';

              return html;

            }

            var evidTotal = 0;

            var celsEvid = anos.map(function (x) {

              var evidAno = num(ev.anos[x]); if (isNaN(evidAno)) evidAno = 0;

              evidTotal += evidAno;

              return celEvidenciaComb(it.porAno[x] || 0, evidAno);

            }).join('');

            var pct = (it.total > 0) ? Math.round(evidTotal / it.total * 100) : 0;

            var cor = (evidTotal > 0) ? corCobertura(pct) : '';

            html += '<tr class="comb-evid"><td class="comb-nome comb-evid-rotulo">' + rotulo + '</td>' + celsEvid +

              '<td class="cel-ano ' + cor + '">' + fmtNum(evidTotal, 0) + ' (' + pct + '%)</td></tr>';

            return html;

          }).join('');

          tablaAnoComb.innerHTML = '<table><thead>' + cab + '</thead><tbody>' + filas + '</tbody></table>';

        }

        // ------------------------------------------------------------------
        // 7.2 / 7.3 — Consumo TOTAL e consumo POR HECTARE por ano, em duas
        // escalas: energia elétrica (kWh) na escala da ESQUERDA (eixo 0) e os
        // combustíveis líquidos (L) na escala da DIREITA (eixo 1).
        // ------------------------------------------------------------------
        // Rótulo do combustível: a `fonte` é o tipo (Diesel, Gasolina, Etanol,
        // ...) — o mesmo critério dos painéis 7.5–7.8. Sem `fonte`, cai no
        // rótulo `combustivel` do registo.
        function nomeFonteComb(r) {

          var f = String(r.fonte === null || r.fonte === undefined ? '' : r.fonte).trim();

          if (f) return f;

          var c = String(r.combustivel === null || r.combustivel === undefined ? '' : r.combustivel).trim();

          return c || '—';

        }

        // Valor de cada ano de uma lista de registos: consumo total (Σ `total`)
        // e, no 7.3, consumo por hectare (Σ `total` ÷ Σ área distinta do ano —
        // a área conta UMA vez por OS·Fazenda·Talhão·ano·cenário, como 7.4–7.8).
        function valoresCombPorAno(regs, porHectare, anos) {

          var totais = somarPorAno(regs, 'total');

          var areas = porHectare ? areaPorAno(regs) : {};

          var valores = {}, i, an, t, a;

          for (i = 0; i < anos.length; i++) {

            an = anos[i];

            t = totais[an];

            if (t === undefined || t === null || isNaN(t)) { valores[an] = null; continue; }

            if (!porHectare) { valores[an] = t; continue; }

            a = areas[an];

            valores[an] = (a && a > 0) ? t / a : null;

          }

          return valores;

        }

        // Devolve `{ series, eixos }`: a energia elétrica numa série única no
        // eixo da ESQUERDA e UMA SÉRIE POR COMBUSTÍVEL (Diesel, Gasolina,
        // Etanol, ...) no eixo da DIREITA — as fontes de uma mesma unidade
        // (L ou L/ha) dividem a mesma régua.
        function seriesCombEvol(lista, porHectare, anos) {

          var sufixo = porHectare ? '/ha' : '';

          var unidadeL = 'L' + sufixo;

          var regs = lista.filter(function (r) { return categoriaDe(r) !== 'energia'; });

          var porFonte = {}, ordem = [], i, r, nome;

          for (i = 0; i < regs.length; i++) {

            r = regs[i];

            nome = nomeFonteComb(r);

            if (!porFonte[nome]) { porFonte[nome] = []; ordem.push(nome); }

            porFonte[nome].push(r);

          }

          // Ordena pelo consumo total (maior primeiro), como o 7.1.
          function totalFonte(rs) {

            var t = somarPorAno(rs, 'total'), s = 0, k;

            for (k in t) { if (Object.prototype.hasOwnProperty.call(t, k)) s += t[k]; }

            return s;

          }

          var ordemF = ordem.slice().sort(function (a, b) {

            var d = totalFonte(porFonte[b]) - totalFonte(porFonte[a]);

            return d !== 0 ? d : a.localeCompare(b, 'pt-BR', { numeric: true });

          });

          var series = [{
            nome: 'kwh', rotulo: 'Energia elétrica (kWh' + sufixo + ')',
            curto: 'Energia', unidadeCurta: 'kWh' + sufixo, casas: 2,
            eixo: 0, cor: CORES_COMB_EVOL.kwh,
            valores: valoresCombPorAno(
              lista.filter(function (x) { return categoriaDe(x) === 'energia'; }),
              porHectare, anos)
          }];

          var nomesF = [];

          ordemF.forEach(function (fonte, idx) {

            nomesF.push(fonte);

            series.push({
              nome: fonte, rotulo: fonte, curto: fonte,
              unidadeCurta: unidadeL, casas: 2,
              eixo: 1, cor: CORES_COMB_EVOL.liquidos[idx % CORES_COMB_EVOL.liquidos.length],
              valores: valoresCombPorAno(porFonte[fonte], porHectare, anos)
            });

          });

          // A unidade só entra no título do eixo da direita quando há MAIS DE UM
          // combustível (com um só, o título da série já sai com "(L)").
          return {
            series: series,
            eixos: [{ series: ['kwh'] },
                    { series: nomesF, nota: nomesF.length > 1 ? unidadeL : null }]
          };

        }

        function renderCombEvolucao(lista, porHectare) {

          var wrap = porHectare ? wrapCombHa : wrapCombEvol;

          var leyenda = porHectare ? leyendaCombHa : leyendaCombEvol;

          if (!wrap) return;

          var anos = anosComb(lista);

          if (!lista.length || !anos.length) {

            wrap.innerHTML = '<p class="muted">Nenhum registro de combustível/energia corresponde aos filtros selecionados.</p>';

            if (leyenda) leyenda.innerHTML = '';

            return;

          }

          if (typeof ObterDados.montarGraficoEixos !== 'function') return;

          var dadosSeries = seriesCombEvol(lista, porHectare, anos);

          ObterDados.montarGraficoEixos({
            container: wrap, leyenda: leyenda,
            series: dadosSeries.series, anos: anos,
            eixos: dadosSeries.eixos,
            ocultas: porHectare ? ocultasCombHa : ocultasCombEvol,
            aria: porHectare
              ? 'Consumo de energia e de cada combustível por hectare e por ano'
              : 'Consumo total de energia e de cada combustível por ano',
            vazio: 'Sem dados de consumo para o gráfico.'
          });

        }

        function renderCombResumo(lista) {

          if (!resumoComb) return;

          var fazSet = {}, osSet = {}, combSet = {}, anosSet = {}, totais = {}, i, r, v, u;

          for (i = 0; i < lista.length; i++) {

            r = lista[i];

            u = String(r.unidade || 'L').trim();

            v = num(r.total);

            if (!isNaN(v)) totais[u] = (totais[u] || 0) + v;

            if (r.fazenda) fazSet[String(r.fazenda)] = 1;

            if (r.os) osSet[String(r.os)] = 1;

            if (r.combustivel) combSet[String(r.combustivel)] = 1;

            if (anoComb(r) !== '—') anosSet[anoComb(r)] = 1;

          }

          var chips = '<span class="prod-chip"><strong>' + lista.length + '</strong> registros de consumo</span>';

          unidadesComb(lista).forEach(function (u2) {

            chips += '<span class="prod-chip"><strong>' + fmtNum(totais[u2] || 0, 2) + ' ' + esc(u2) +

              '</strong> de consumo total</span>';

          });

          chips +=
            '<span class="prod-chip"><strong>' + fmtNum(areaDistinta(lista), 2) + '</strong> ha com consumo</span>' +
            '<span class="prod-chip"><strong>' + Object.keys(combSet).length + '</strong> ' + esc(cfg.singular) + '</span>' +
            '<span class="prod-chip"><strong>' + Object.keys(anosSet).length + '</strong> anos</span>' +
            '<span class="prod-chip"><strong>' + Object.keys(fazSet).length + '</strong> fazendas</span>' +
            '<span class="prod-chip"><strong>' + Object.keys(osSet).length + '</strong> OS</span>';

          resumoComb.innerHTML = chips;

        }

        function renderCombPivot(lista, el) {

          if (!el) return;

          if (!lista.length) {

            el.innerHTML = '';

            el.style.display = 'none';

            return;

          }

          el.style.display = 'block';

          var anos = anosComb(lista);

          var us = unidadesComb(lista);

          var u = (us.length === 1) ? us[0] : '';

          // Cada nó (OS · Fazenda · Talhão) vira um grupo de 4 linhas — uma por
          // métrica — com colunas Geral + uma por ano. O talhão só aparece
          // quando há consumo registrado por talhão; registros agregados
          // (TODAS/TODOS/RATEIO) ficam no nível da fazenda.
          var METRICAS = [

            { chave: 'total', rotulo: 'Consumo total' + (u ? ' (' + u + ')' : ''), casas: 2 },

            { chave: 'area', rotulo: 'Área (ha)', casas: 2 },

            { chave: 'dose', rotulo: 'Consumo por hectare' + (u ? ' (' + u + '/ha)' : ''), casas: 2 },

            { chave: 'registros', rotulo: 'Registros', casas: 0 }

          ];

          // Nome agregado de total/rateio (não é nível próprio): TODAS/TODOS/
          // RATEIO. Quando a fazenda (ou o talhão) é agregada, a linha sobe de
          // nível — discrimina por fazenda e, sem fazenda, por OS.
          function agregado(nome) {

            var t = normValor(nome);

            return t === 'todas' || t === 'todos' || t === 'rateio';

          }

          var arv = {}, ordemOs = [], i, r, os, faz, tal;

          for (i = 0; i < lista.length; i++) {

            r = lista[i];

            os = r.os || '—';

            faz = (r.fazenda && !agregado(r.fazenda)) ? String(r.fazenda).trim() : '';

            tal = (r.talhao && !agregado(r.talhao)) ? String(r.talhao).trim() : '';

            if (!arv[os]) { arv[os] = {}; ordemOs.push(os); }

            if (!arv[os][faz]) arv[os][faz] = {};

            if (!arv[os][faz][tal]) arv[os][faz][tal] = [];

            arv[os][faz][tal].push(r);

          }

          ordemOs.sort(function (a, b) { return a.localeCompare(b, 'pt-BR', { numeric: true }); });

          function acc() { return { total: 0, registros: 0, area: 0, vistos: {} }; }

          function agregar(regs) {

            var porAno = {}, geral = acc(), j, rr, an, v, a, chave;

            for (j = 0; j < regs.length; j++) {

              rr = regs[j];

              an = anoComb(rr);

              if (!porAno[an]) porAno[an] = acc();

              v = num(rr.total);

              if (!isNaN(v)) { porAno[an].total += v; geral.total += v; }

              porAno[an].registros++; geral.registros++;

              a = num(rr.area);

              chave = [rr.os || '', rr.fazenda || '', rr.talhao || '', anoComb(rr), String(rr.cenario || '')].join('|');

              if (!isNaN(a) && a > 0) {

                if (!porAno[an].vistos[chave]) { porAno[an].vistos[chave] = 1; porAno[an].area += a; }

                if (!geral.vistos[chave]) { geral.vistos[chave] = 1; geral.area += a; }

              }

            }

            return { porAno: porAno, geral: geral };

          }

          function valorMetrica(x, m) {

            if (!x) return null;

            if (m.chave === 'total') return x.total;

            if (m.chave === 'area') return x.area > 0 ? x.area : null;

            if (m.chave === 'dose') return x.area > 0 ? x.total / x.area : null;

            if (m.chave === 'registros') return x.registros > 0 ? x.registros : null;

            return null;

          }

          function celComb(valor, casas) {

            return (valor === null || valor === undefined)

              ? '<td class="comb-cel comb-sem-valor">—</td>'

              : '<td class="comb-cel">' + fmtNum(valor, casas) + '</td>';

          }

          // Linhas de um nó: escritas só quando o nó de cima é expandido.
          // `temFilhos` marca a existência de nível inferior (seta clicável).
          function linhasNo(gid, nome, nivel, regs, temFilhos) {

            var agg = agregar(regs), html = '';

            METRICAS.forEach(function (m, idx) {

              var vGeral = valorMetrica(agg.geral, m);

              var celsAno = anos.map(function (an) {

                return celComb(valorMetrica(agg.porAno[an], m), m.casas);

              }).join('');

              var nomeTd = (idx === 0)

                ? '<td class="comb-nome comb-nivel-' + nivel + (temFilhos ? ' comb-clicavel' : '') +

                  '" data-grupo="' + gid + '"' + (temFilhos ? ' data-toggle="1"' : '') +

                  ' rowspan="' + METRICAS.length + '">' +

                  (temFilhos ? '<span class="comb-seta">▶</span> ' : '') + esc(nome) + '</td>'

                : '';

              var geralTd = (vGeral === null || vGeral === undefined)

                ? '<td class="comb-cel comb-geral comb-sem-valor">—</td>'

                : '<td class="comb-cel comb-geral">' + fmtNum(vGeral, m.casas) + '</td>';

              html += '<tr data-g="' + gid + '" class="comb-linha' + (idx === 0 ? ' comb-inicio-grupo' : '') + '">' +

                nomeTd + '<td class="comb-metrica">' + esc(m.rotulo) + '</td>' + geralTd + celsAno + '</tr>';

            });

            return html;

          }

          function regsDaFazenda(fazMap, apenasTalhoes) {

            var total = [], chaves = Object.keys(fazMap || {}), k;

            for (k = 0; k < chaves.length; k++) {

              if (apenasTalhoes && chaves[k] === '') continue;

              total = total.concat(fazMap[chaves[k]]);

            }

            return total;

          }

          function regsDaOS(fazMapa) {

            var total = [], fzs = Object.keys(fazMapa || {}), k;

            for (k = 0; k < fzs.length; k++) {

              total = total.concat(regsDaFazenda(fazMapa[fzs[k]], false));

            }

            return total;

          }

          var headAnos = anos.map(function (an) { return '<th>' + esc(an) + '</th>'; }).join('');

          el.innerHTML = '<table class="comb-pivot"><thead><tr>' +

            '<th>OS · Fazenda · Talhão</th><th>Métrica</th><th>Geral</th>' + headAnos +

            '</tr></thead><tbody></tbody></table>';

          // Hierarquia sob demanda: só as OS (e a linha do total) entram agora;
          // as fazendas nascem ao abrir a OS e os talhões ao abrir a fazenda.
          // Fazendas/talhões agregados (TODAS/TODOS/RATEIO) não viram nó.
          var piv = ObterDados.pivotLazy({

            prefixo: 'comb',

            corpo: el.querySelector('tbody'),

            linhas: linhasNo

          });

          ordemOs.forEach(function (osA) {

            piv.raiz({

              nome: osA, nivel: 'os',

              coletar: function () { return regsDaOS(arv[osA]); },

              gerarFilhos: function () {

                var fazes = Object.keys(arv[osA]).filter(function (fz) { return fz !== ''; });

                fazes.sort(function (a, b) { return a.localeCompare(b, 'pt-BR', { numeric: true }); });

                return fazes.map(function (fazA) {

                  var talhoesReais = Object.keys(arv[osA][fazA]).filter(function (t) { return t !== ''; });

                  talhoesReais.sort(function (a, b) { return a.localeCompare(b, 'pt-BR', { numeric: true }); });

                  return {

                    nome: fazA, nivel: 'faz',

                    coletar: function () { return regsDaFazenda(arv[osA][fazA], false); },

                    gerarFilhos: talhoesReais.length ? function () {

                      return talhoesReais.map(function (talA) {

                        return { nome: talA, nivel: 'tal', coletar: arv[osA][fazA][talA] };

                      });

                    } : null

                  };

                });

              }

            });

          });

          piv.raiz({ nome: 'Total geral', nivel: 'total', coletar: lista });

        }

        // Etapas do painel: resumo → 7.1 (por combustível/fonte e ano) → os
        // gráficos 7.2/7.3 (duas escalas) → cada uma das tabelas agrupadas
        // (7.4–7.8) num bloco próprio.
        function renderCombTudo() {

          var todos = filtrarCombustiveis('', '');

          return [

            function () { renderCombResumo(todos); },

            function () { renderCombTablaAno(todos); },

            function () { renderCombEvolucao(todos, false); },

            function () { renderCombEvolucao(todos, true); },

            function () { renderCombPivot(filtrarCombustiveis('combustivel', ''), pivotComb); },

            function () { renderCombPivot(filtrarCombustiveis('combustivel', 'diesel'), pivotDiesel); },

            function () { renderCombPivot(filtrarCombustiveis('combustivel', 'etanol'), pivotAlcool); },

            function () { renderCombPivot(filtrarCombustiveis('combustivel', 'gasolina'), pivotGasolina); },

            function () { renderCombPivot(filtrarCombustiveis('energia', ''), pivotEnergia); }

          ];

        }

        // Renderização sob demanda: o painel é montado na primeira abertura.
        // Recolhido, as tabelas e as hierarquias saem da memória.
        ObterDados.registrarPainel('combustivel', renderCombTudo, function () {

          [resumoComb, tablaAnoComb, wrapCombEvol, leyendaCombEvol, wrapCombHa,
            leyendaCombHa, pivotComb, pivotDiesel, pivotAlcool,
            pivotGasolina, pivotEnergia].forEach(function (el) {

            if (!el) return;

            el.innerHTML = '';

            el.style.display = '';

          });

        });

        }

        montar({

          id: 'combustivel',

          coluna: 'Combustível/fonte',

          singular: 'combustíveis/fontes',

          resumo: document.getElementById('combResumo'),

          tablaAno: document.getElementById('combTablaAno'),

          evol: document.getElementById('combEvolLinhas'),

          evolLeyenda: document.getElementById('combEvolLeyenda'),

          ha: document.getElementById('combHaLinhas'),

          haLeyenda: document.getElementById('combHaLeyenda'),

          pivot: document.getElementById('combPivot'),

          pivotDiesel: document.getElementById('combPivotDiesel'),

          pivotAlcool: document.getElementById('combPivotAlcool'),

          pivotGasolina: document.getElementById('combPivotGasolina'),

          pivotEnergia: document.getElementById('enerPivot'),

          vazio: document.getElementById('combVazio')

        });

      })();

      // ----- Painel de práticas de solo: hectares por prática/fazenda/ano -----
      (function () {
        var scriptPrat = document.getElementById('dadosPraticas');
        var resumoPrat = document.getElementById('pratResumo');
        var tablaPrat = document.getElementById('pratTabla');
        var wrapPrat = document.getElementById('pratTabelaWrap');
        var vazioPrat = document.getElementById('pratVazio');
        var wrapLinhas = document.getElementById('pratLinhas');
        var leyendaPrat = document.getElementById('pratLeyenda');

        var crudosPrat = [];
        if (scriptPrat) {
          try { crudosPrat = JSON.parse(scriptPrat.textContent || '[]'); } catch (ign) { crudosPrat = []; }
        }
        ObterDados.dadosPraticas = Array.isArray(crudosPrat) ? crudosPrat : [];

        // Ordem canônica (comparação sem acentos) e depois A-Z. Vale para o 8.3
        // ("Preparo do solo") e para o select de filtro; o 8.1 e o 8.2 usam
        // `cmpPraticaAZ`.
        // Inclui as práticas que a V3 passou a registrar em campo único
        // (manejo de água, integração e cobertura — a coluna Sucessão fica de
        // fora do painel, ver `config.PRATICAS_CAMPOS_LISTA`).
        var ORDEM_PRATICAS = ['plantio direto', 'cultivo minimo', 'preparo convencional', 'gradagem',
          'coveamento/faixa (perenes)', 'ilp', 'ipf', 'ilpf', 'agricultura de precisao',
          'pasto rotacionado', 'ureia revestida', 'solubilizador de p', 'biologicos',
          'irrigacao pivo', 'irrigacao gotejamento', 'sequeiro', 'pastagem em bom estado',
          'pastagem degradada',
          'solo exposto', 'forrageira',
          'mix de plantas', 'outro'];
        function pesoPratica(nome) {
          var i = ORDEM_PRATICAS.indexOf(normValor(nome));
          return i < 0 ? ORDEM_PRATICAS.length : i;
        }
        function cmpPratica(a, b) {
          var pa = pesoPratica(a), pb = pesoPratica(b);
          if (pa !== pb) return pa - pb;
          return String(a).localeCompare(String(b), 'pt-BR', { numeric: true });
        }
        // 8.1 e 8.2 saem em ORDEM ALFABÉTICA (a ordem canônica acima fica só
        // para o 8.3 — "Preparo do solo" — e para o select de filtro).
        function cmpPraticaAZ(a, b) {
          return String(a).localeCompare(String(b), 'pt-BR', { numeric: true });
        }
        // Guarda contra a coluna "Sucessão" da V3: o backend já não a entrega no
        // `dadosPraticas` (`config.PRATICAS_CAMPOS_LISTA`), mas o 8.1 e o 8.2
        // seguem descartando rótulos "Sucessão ..." caso algum chegue. O 8.3 tem
        // regra própria (só Convencional e Plantio direto).
        function ehPraticaSucessao(nome) {
          return normValor(nome).indexOf('sucessao') === 0;
        }


        // Painel 8.3 ("Preparo do solo" por OS · Fazenda · Talhão): a hierarquia
        // exibe SOMENTE as duas práticas de preparo de interesse —
        // "Convencional"
        // (Preparo convencional) e "Plantio direto" (comparação sem acentos,
        // minúsculas). Os demais valores do campo de manejo
        // (Coveamento/faixa (perenes), Cultivo mínimo, Subsolagem, Outro, ...)
        // continuam contando em 8.1, 8.2 e na coluna de Registros do 8.3, mas
        // saem como "—" nas colunas de ano.
        var MANEJO_73 = ['preparo convencional', 'convencional', 'plantio direto'];
        function manejoDe73(nome) {
          return MANEJO_73.indexOf(normValor(nome)) >= 0;
        }

        // Preenche o select de práticas (canônicas primeiro).
        var pratSelect = document.getElementById('filtroPratica');
        if (pratSelect) {
          var mapaPrat = {}, listaPrat = [], iPrat, vPrat;
          for (iPrat = 0; iPrat < ObterDados.dadosPraticas.length; iPrat++) {
            vPrat = ObterDados.dadosPraticas[iPrat].pratica;
            if (vPrat !== null && vPrat !== undefined && String(vPrat).trim() !== '' && !(String(vPrat) in mapaPrat)) {
              mapaPrat[String(vPrat)] = 1; listaPrat.push(String(vPrat));
            }
          }
          listaPrat.sort(cmpPratica);
          preencherSelect(pratSelect, listaPrat);
        }

        function filtrarPraticas() {
          var f = ObterDados.filtros, busca = normValor(f.busca);
          var chaves = ['os', 'fazenda', 'talhao', 'ano', 'cenario', 'pratica'];
          return ObterDados.dadosPraticas.filter(function (r) {
            for (var i = 0; i < chaves.length; i++) {
              if (!casaFiltro(r[chaves[i]], f[chaves[i]])) return false;
            }
            if (busca && normValor(JSON.stringify(r)).indexOf(busca) < 0) return false;
            return true;
          });
        }

        function anosPrat(lista) {
          var mapa = {}, anos = [], i, r, an;
          for (i = 0; i < lista.length; i++) {
            r = lista[i];
            an = (r.ano === null || r.ano === undefined) ? '—' : String(r.ano).trim();
            if (!(an in mapa)) { mapa[an] = 1; anos.push(an); }
          }
          return anos.sort(function (a, b) {
            var x = Number(a), y = Number(b);
            if (isNaN(x)) return 1;
            if (isNaN(y)) return -1;
            return x - y;
          });
        }

        function areaTotal(regs) {
          var s = 0, i, v;
          for (i = 0; i < regs.length; i++) { v = num(regs[i].area); if (!isNaN(v) && v > 0) s += v; }
          return s;
        }

        function areaAno(regs, an) {
          var s = 0, i, anR, v;
          for (i = 0; i < regs.length; i++) {
            anR = (regs[i].ano === null || regs[i].ano === undefined) ? '—' : String(regs[i].ano).trim();
            if (anR !== an) continue;
            v = num(regs[i].area); if (!isNaN(v) && v > 0) s += v;
          }
          return s;
        }

        function manejoAno(regs, an) {
          var mapa = {}, i, anR, p, out = [];
          for (i = 0; i < regs.length; i++) {
            anR = (regs[i].ano === null || regs[i].ano === undefined) ? '—' : String(regs[i].ano).trim();
            if (anR !== an) continue;
            p = String(regs[i].pratica || '—');
            if (!(p in mapa)) { mapa[p] = 1; out.push(p); }
          }
          return out.sort(cmpPratica);
        }

        // Realce da prática no painel hierárquico (2 · Manejo por OS · Fazenda
        // · Talhão): "Preparo convencional" vira "Convencional"; os termos
        // "Convencional" e "Gradagem" saem em negrito + vermelho.
        function prepararManejo(texto) {
          var t = esc(String(texto === null || texto === undefined ? '—' : texto));
          t = t.replace(/Preparo\s+convencional/gi, 'Convencional');
          t = t.replace(/Convencional/gi, function (m) {
            return '<strong class="prat-destaque">' + m + '</strong>';
          });
          t = t.replace(/Gradagem/gi, function (m) {
            return '<strong class="prat-destaque">' + m + '</strong>';
          });
          return t;
        }

        function agrupar(lista, chave) {
          var porGrupo = {}, ordem = [], i, r, nome;
          for (i = 0; i < lista.length; i++) {
            r = lista[i]; nome = String(r[chave] || '—');
            if (!porGrupo[nome]) { porGrupo[nome] = []; ordem.push(nome); }
            porGrupo[nome].push(r);
          }
          return { porGrupo: porGrupo, ordem: ordem };
        }

        function renderPratResumo(lista) {
          if (!resumoPrat) return;
          var fazSet = {}, osSet = {}, pratSet = {}, total = 0, i, r, v;
          for (i = 0; i < lista.length; i++) {
            r = lista[i]; v = num(r.area); if (!isNaN(v)) total += v;
            if (r.fazenda) fazSet[String(r.fazenda)] = 1;
            if (r.os) osSet[String(r.os)] = 1;
            if (r.pratica) pratSet[String(r.pratica)] = 1;
          }
          resumoPrat.innerHTML =
            '<span class="prod-chip"><strong>' + lista.length + '</strong> registros de práticas</span>' +
            '<span class="prod-chip"><strong>' + fmtNum(total, 0) + '</strong> ha</span>' +
            '<span class="prod-chip"><strong>' + Object.keys(pratSet).length + '</strong> práticas</span>' +
            '<span class="prod-chip"><strong>' + Object.keys(fazSet).length + '</strong> fazendas</span>' +
            '<span class="prod-chip"><strong>' + Object.keys(osSet).length + '</strong> OS</span>' +
            '<span class="prod-chip"><strong>' + anosPrat(lista).join(' · ') + '</strong> anos</span>';
        }

        function renderPratTabla(lista) {
          if (!tablaPrat) return;
          if (!lista.length) {
            tablaPrat.innerHTML = '<p class="muted">Nenhuma prática registrada nos filtros selecionados.</p>';
            return;
          }
          var anos = anosPrat(lista);
          var g = agrupar(lista, 'pratica');
          // 8.1: ordem alfabética e sem as práticas de sucessão.
          g.ordem = g.ordem.filter(function (nome) { return !ehPraticaSucessao(nome); });
          g.ordem.sort(cmpPraticaAZ);
          if (!g.ordem.length) {
            tablaPrat.innerHTML = '<p class="muted">Nenhuma prática registrada nos filtros selecionados.</p>';
            return;
          }
          function talhoesGrupo(regs) {
            var mapa = {}, i;
            for (i = 0; i < regs.length; i++) {
              mapa[String(regs[i].os) + '|' + String(regs[i].fazenda) + '|' + String(regs[i].talhao)] = 1;
            }
            return Object.keys(mapa).length;
          }
          var linhas = g.ordem.map(function (nome) {
            var regs = g.porGrupo[nome];
            var celsAno = anos.map(function (an) { return '<td class="cel-ano">' + fmtNum(areaAno(regs, an)) + '</td>'; }).join('');
            return '<tr><td class="fert-nome">' + esc(nome) + '</td>' +
              '<td class="cel-ano fert-geral">' + fmtNum(areaTotal(regs)) + '</td>' + celsAno +
              '<td class="cel-ano">' + talhoesGrupo(regs) + '</td>' +
              '<td class="cel-ano">' + regs.length + '</td></tr>';
          }).join('');
          var headAnos = anos.map(function (an) { return '<th>' + esc(an) + '</th>'; }).join('');
          tablaPrat.innerHTML = '<table class="fert-pivot"><thead><tr>' +
            '<th>Prática</th><th>Total (ha)</th>' + headAnos + '<th>Talhões</th><th>Registros</th>' +
            '</tr></thead><tbody>' + linhas + '</tbody></table>';
        }

        function renderPratHierarquia(lista) {
          if (!wrapPrat) return;
          // 8.3 mostra SOMENTE o manejo do solo; dentro de cada célula de ano,
          // apenas "Convencional" e "Plantio direto" são exibidos (ver
          // `MANEJO_73`) — os demais valores viram "—", sem alterar a árvore
          // OS → Fazenda → Talhão nem a coluna de registros.
          lista = lista.filter(function (r) { return r.grupo !== 'extra'; });
          if (!lista.length) {
            wrapPrat.innerHTML = '<p class="muted">Nenhuma prática registrada nos filtros selecionados.</p>';
            wrapPrat.style.display = 'block';
            return;
          }
          var anos = anosPrat(lista);
          if (!anos.length) { wrapPrat.innerHTML = ''; wrapPrat.style.display = 'none'; return; }
          var arv = {}, ordemOs = [], i, r, os, faz, tal;
          for (i = 0; i < lista.length; i++) {
            r = lista[i];
            os = r.os || '—'; faz = r.fazenda || '—'; tal = r.talhao || '—';
            if (!arv[os]) { arv[os] = {}; ordemOs.push(os); }
            if (!arv[os][faz]) arv[os][faz] = {};
            if (!arv[os][faz][tal]) arv[os][faz][tal] = [];
            arv[os][faz][tal].push(r);
          }
          ordemOs.sort(function (a, b) { return a.localeCompare(b, 'pt-BR', { numeric: true }); });
          function coleccionarRegistros(osA, fazA) {
            var total = [];
            Object.keys(arv[osA] || {}).forEach(function (fz) {
              if (!fazA || fz === fazA) {
                Object.keys(arv[osA][fz]).forEach(function (tl) { total = total.concat(arv[osA][fz][tl]); });
              }
            });
            return total;
          }
          function celdasManejo(regs) {
            return anos.map(function (an) {
              // Só "Convencional" (Preparo convencional) e "Plantio direto"
              // aparecem: os demais valores do campo de manejo viram "—".
              var ms = manejoAno(regs, an).filter(manejoDe73);
              return ms.length ? '<span class="cel-ano">' + prepararManejo(ms.join(', ')) + '</span>'
                               : '<span class="cel-ano pec-sem-valor">—</span>';
            }).join('');
          }
          // Filas de agregação (OS, fazenda e total geral) mostram só os
          // registros; o manejo (prática) por ano fica apenas nas filas de
          // talhão (folhas).
          function linhaDet(expand, nome, regs, mostrarManejo) {
            var celdasAno = mostrarManejo
              ? celdasManejo(regs)
              : anos.map(function () { return '<span class="cel-ano"></span>'; }).join('');
            return '<span class="toggle">' + (expand ? '▶' : '') + '</span>' +
              '<span class="cel-nome">' + esc(nome) + '</span>' + celdasAno +
              '<span class="cel-regs">' + regs.length + '</span>';
          }
          var head = '<div class="det-row det-head"><span class="toggle"></span>' +
            '<span class="cel-nome">OS · Fazenda · Talhão</span>' +
            anos.map(function (an) { return '<span class="cel-cultura">' + esc(an) + '</span>'; }).join('') +
            '<span class="cel-regs">Registros</span></div>';
          var bloques = ordemOs.map(function (osA) {
            var fazes = Object.keys(arv[osA]).sort(function (a, b) { return a.localeCompare(b, 'pt-BR', { numeric: true }); });
            var cuerpoFaz = fazes.map(function (fazA) {
              var talhoes = Object.keys(arv[osA][fazA]).sort(function (a, b) { return a.localeCompare(b, 'pt-BR', { numeric: true }); });
              var rowsTal = talhoes.map(function (talA) {
                return '<div class="det-row">' + linhaDet(false, talA, arv[osA][fazA][talA], true) + '</div>';
              }).join('');
              return '<details class="cons-faz"><summary class="det-row">' +
                linhaDet(true, fazA, coleccionarRegistros(osA, fazA), false) + '</summary>' +
                (rowsTal ? '<div class="cons-body">' + rowsTal + '</div>' : '') + '</details>';
            }).join('');
            return '<details class="cons-os"' + '><summary class="det-row">' +
              linhaDet(true, osA, coleccionarRegistros(osA, null), false) + '</summary>' +
              (cuerpoFaz ? '<div class="cons-body">' + cuerpoFaz + '</div>' : '') + '</details>';
          }).join('');
          var totalGeral = '<div class="det-row det-total">' + linhaDet(false, 'Total geral', lista, false) + '</div>';
          var cols = '1.7rem minmax(200px, auto) repeat(' + anos.length + ', minmax(120px, auto)) minmax(70px, auto)';
          wrapPrat.innerHTML = '<div class="painel-consolidado prod-hierarquia" style="--cols:' + cols + '">' +
            head + bloques + totalGeral + '</div>';
          wrapPrat.style.display = 'block';
          // Corpo de cada OS/fazenda só entra no documento ao ser aberto.
          ObterDados.detailsSobDemanda(wrapPrat);
        }

        // Gráfico de linhas (8.2): hectares por prática ao longo dos anos.
        // As práticas usam a PALETA PADRÃO dos gráficos (`ObterDados.CORES`) por
        // `ObterDados.coresDasSeries`, que NÃO repete cor enquanto houver cor
        // livre (com mais práticas que cores, a paleta recomeça).
        // Linha de REFERÊNCIA do 8.2 (área total física): mesmo estilo da linha
        // de base "Área física (base)" do gráfico 3.2 — cinza tracejado — e o
        // rótulo que ela usa na legenda e na dica.
        var COR_BASE_PRAT = ObterDados.COR_REFERENCIA;
        var REF_PRAT = 'Área física (base)';
        var praticasOcultas = {};

        function praticasPresentes(lista) {
          var mapa = {}, ordem = [], i, p;
          for (i = 0; i < lista.length; i++) {
            p = String(lista[i].pratica || '');
            if (p && !ehPraticaSucessao(p) && !(p in mapa)) { mapa[p] = 1; ordem.push(p); }
          }
          // 8.2: ordem alfabética (o 8.3 mantém a ordem canônica).
          ordem.sort(cmpPraticaAZ);
          return ordem;
        }

        // Máximo "bonito" do eixo Y: arredonda para 1/2/5 × 10ⁿ.
        function escalaBonita(maxV) {
          if (!(maxV > 0)) return { max: 1, passo: 1, ticks: 5 };
          var bruto = maxV / 5;
          var mag = Math.pow(10, Math.floor(Math.log(bruto) / Math.LN10));
          var norm = bruto / mag, passo;
          if (norm <= 1) passo = 1; else if (norm <= 2) passo = 2;
          else if (norm <= 5) passo = 5; else passo = 10;
          passo *= mag;
          var max = Math.ceil(maxV / passo) * passo;
          return { max: max, passo: passo, ticks: Math.max(1, Math.round(max / passo)) };
        }

        // Curva suave (Catmull-Rom → Bézier) para um traçado profissional.
        function caminhoSuave(pts) {
          if (!pts.length) return '';
          if (pts.length === 1) return 'M' + pts[0].x + ',' + pts[0].y;
          var d = 'M' + pts[0].x + ',' + pts[0].y;
          for (var i = 0; i < pts.length - 1; i++) {
            var p0 = pts[i - 1] || pts[i], p1 = pts[i], p2 = pts[i + 1], p3 = pts[i + 2] || p2;
            d += 'C' + (p1.x + (p2.x - p0.x) / 6) + ',' + (p1.y + (p2.y - p0.y) / 6) + ' ' +
              (p2.x - (p3.x - p1.x) / 6) + ',' + (p2.y - (p3.y - p1.y) / 6) + ' ' +
              p2.x + ',' + p2.y;
          }
          return d;
        }

        function renderPratLinhas(lista) {
          if (!wrapLinhas) return;
          var anosNum = anosPrat(lista).filter(function (a) { return a !== '—'; });
          var praticas = praticasPresentes(lista);
          if (!anosNum.length || !praticas.length) {
            wrapLinhas.innerHTML = '<p class="muted">' + (lista.length
              ? 'Sem anos identificáveis para o gráfico.'
              : 'Nenhuma prática registrada nos filtros selecionados.') + '</p>';
            if (leyendaPrat) leyendaPrat.innerHTML = '';
            return;
          }
          // Cores: paleta padrão, sem repetir; o cinza da linha de REFERÊNCIA
          // (área física) fica reservado.
          var cor = ObterDados.coresDasSeries(praticas, [COR_BASE_PRAT]);

          // Área total FÍSICA do conjunto filtrado: é a linha de REFERÊNCIA do
          // gráfico. Cada talhão (os + fazenda + talhão) conta 1× pela MAIOR
          // área registrada entre as safras — mesma regra do painel de área e
          // da linha de base "Área física" do 3.2. Os hectares das práticas
          // podem ultrapassá-la porque o mesmo talhão recebe mais de uma
          // prática no mesmo ano e cada prática soma a área do talhão.
          var physicalAreaByField = {}, fk, fi, fr, fa, physicalArea = 0;
          for (fi = 0; fi < lista.length; fi++) {
            fr = lista[fi]; fa = num(fr.area);
            if (isNaN(fa) || fa <= 0) continue;
            fk = String(fr.os) + '|' + String(fr.fazenda) + '|' + String(fr.talhao);
            if (!(fk in physicalAreaByField) || fa > physicalAreaByField[fk]) {
              physicalAreaByField[fk] = fa;
            }
          }
          Object.keys(physicalAreaByField).forEach(function (kk) {
            physicalArea += physicalAreaByField[kk];
          });
          // A referência também entra no mapa de cores (legenda e dica).
          cor[REF_PRAT] = COR_BASE_PRAT;

          // Matriz prática × ano (hectares somados no ano).
          var matriz = {};
          praticas.forEach(function (p) { matriz[p] = {}; });
          lista.forEach(function (r) {
            var p = String(r.pratica || ''); if (!(p in matriz)) return;
            var an = (r.ano === null || r.ano === undefined) ? '—' : String(r.ano).trim();
            var v = num(r.area); if (isNaN(v) || v <= 0) return;
            matriz[p][an] = (matriz[p][an] || 0) + v;
          });

          // Legenda (clique mostra/oculta a linha da prática).
          if (leyendaPrat) {
            var itensLeyenda = praticas.map(function (p) {
              var oc = praticasOcultas[p] ? ' oculta' : '';
              return '<button type="button" class="prat-leyenda-item' + oc + '" data-prat="' + esc(p) + '">' +
                '<span class="prat-leyenda-cor" style="background:' + cor[p] + '"></span>' + esc(p) + '</button>';
            });
            // A área física entra por ÚLTIMO na legenda e alterna como as demais.
            if (physicalArea > 0) {
              itensLeyenda.push('<button type="button" class="prat-leyenda-item' +
                (praticasOcultas[REF_PRAT] ? ' oculta' : '') + '" data-prat="' + esc(REF_PRAT) + '">' +
                '<span class="prat-leyenda-cor" style="background:' + COR_BASE_PRAT + '"></span>' +
                esc(REF_PRAT) + '</button>');
            }
            leyendaPrat.innerHTML = itensLeyenda.join('');
            Array.prototype.forEach.call(leyendaPrat.querySelectorAll('[data-prat]'), function (b) {
              b.addEventListener('click', function () {
                var p = b.getAttribute('data-prat');
                if (praticasOcultas[p]) { delete praticasOcultas[p]; } else { praticasOcultas[p] = 1; }
                renderPratLinhas(lista);
              });
            });
          }

          var visiveis = praticas.filter(function (p) { return !praticasOcultas[p]; });
          // A referência só entra no desenho (e na régua) se estiver visível.
          var refVisivel = physicalArea > 0 && !praticasOcultas[REF_PRAT];
          var maxReal = 0;
          visiveis.forEach(function (p) {
            anosNum.forEach(function (an) { var v = matriz[p][an] || 0; if (v > maxReal) maxReal = v; });
          });
          // Sem isto a linha da referência sairia por cima do quadro.
          if (refVisivel && physicalArea > maxReal) maxReal = physicalArea;
          var escala = escalaBonita(maxReal);
          var maxY = escala.max, ticks = escala.ticks;

          var W = 1040, H = 460, mL = 84, mR = 104, mT = 30, mB = 56;
          var pw = W - mL - mR, ph = H - mT - mB;
          var passoX = anosNum.length > 1 ? pw / (anosNum.length - 1) : pw;
          function xi(an) {
            var i = anosNum.indexOf(an);
            return anosNum.length === 1 ? mL + pw / 2 : mL + i * passoX;
          }
          function yi(v) { return mT + ph - (v / maxY) * ph; }

          var partes = [], k, vv, yy;
          partes.push('<rect class="prat-fundo" x="' + mL + '" y="' + mT + '" width="' + pw + '" height="' + ph + '" rx="10"></rect>');
          for (k = 0; k <= ticks; k++) {
            vv = escala.passo * k; yy = yi(vv);
            partes.push('<line class="prat-grid" x1="' + mL + '" y1="' + yy + '" x2="' + (mL + pw) + '" y2="' + yy + '"></line>');
            partes.push('<text class="prat-eixo-txt" x="' + (mL - 12) + '" y="' + (yy + 4) + '" text-anchor="end">' + fmtNum(vv, 0) + '</text>');
          }
          partes.push('<line class="prat-eixo" x1="' + mL + '" y1="' + mT + '" x2="' + mL + '" y2="' + (mT + ph) + '"></line>');
          partes.push('<line class="prat-eixo" x1="' + mL + '" y1="' + (mT + ph) + '" x2="' + (mL + pw) + '" y2="' + (mT + ph) + '"></line>');
          partes.push('<text class="prat-unit" x="' + mL + '" y="' + (mT - 12) + '">hectares (ha)</text>');
          anosNum.forEach(function (an) {
            var xx = xi(an);
            if (anosNum.length > 1) {
              partes.push('<line class="prat-grid-vert" x1="' + xx + '" y1="' + mT + '" x2="' + xx + '" y2="' + (mT + ph) + '"></line>');
            }
            partes.push('<text class="prat-eixo-txt" x="' + xx + '" y="' + (H - mB + 24) + '" text-anchor="middle">' + esc(an) + '</text>');
          });
          partes.push('<line class="prat-guia" x1="0" y1="' + mT + '" x2="0" y2="' + (mT + ph) + '" opacity="0"></line>');

          visiveis.forEach(function (p) {
            var pts = anosNum.map(function (an) { return { x: xi(an), y: yi(matriz[p][an] || 0) }; });
            partes.push('<path class="prat-line" stroke="' + cor[p] + '" d="' + caminhoSuave(pts) + '"></path>');
            pts.forEach(function (pt, idx) {
              var v = matriz[p][anosNum[idx]] || 0;
              partes.push('<circle class="prat-dot" cx="' + pt.x + '" cy="' + pt.y + '" r="3.4" fill="' + cor[p] + '">' +
                '<title>' + esc(p) + ' · ' + esc(anosNum[idx]) + ': ' + fmtNum(v) + ' ha</title></circle>');
            });
          });

          // A REFERÊNCIA (área total física) entra DEPOIS das práticas: valor
          // constante no período, tracejado, para comparar com os hectares.
          if (refVisivel) {
            var ptsRef = anosNum.map(function (an) { return { x: xi(an), y: yi(physicalArea) }; });
            partes.push('<path class="prat-line" stroke="' + COR_BASE_PRAT +
              '" style="stroke-width:2.2" stroke-dasharray="7 5" d="' + caminhoSuave(ptsRef) + '"></path>');
            ptsRef.forEach(function (pt, idx) {
              partes.push('<circle class="prat-dot" cx="' + pt.x + '" cy="' + pt.y + '" r="3.4" fill="' + COR_BASE_PRAT + '">' +
                '<title>' + esc(REF_PRAT) + ' · ' + esc(anosNum[idx]) + ': ' + fmtNum(physicalArea) + ' ha</title></circle>');
            });
          }

          anosNum.forEach(function (an) {
            var xx = xi(an);
            var esq = Math.max(mL, xx - passoX / 2);
            var dir = Math.min(mL + pw, xx + passoX / 2);
            partes.push('<rect class="prat-hot" data-ano="' + esc(an) + '" data-x="' + xx + '" x="' + esq +
              '" y="' + mT + '" width="' + (dir - esq) + '" height="' + ph + '" fill="transparent"></rect>');
          });

          wrapLinhas.innerHTML = '<svg viewBox="0 0 ' + W + ' ' + H + '" preserveAspectRatio="xMidYMid meet" role="img" aria-label="Hectares por prática e por ano">' + partes.join('') + '</svg>';

          // Tooltip + linha-guia ao passar o mouse por um ano.
          var tip = document.createElement('div');
          tip.className = 'prat-tip';
          tip.hidden = true;
          wrapLinhas.appendChild(tip);
          var guia = wrapLinhas.querySelector('.prat-guia');
          Array.prototype.forEach.call(wrapLinhas.querySelectorAll('.prat-hot'), function (rc) {
            rc.addEventListener('mouseenter', function () {
              var an = rc.getAttribute('data-ano');
              if (guia) {
                guia.setAttribute('x1', rc.getAttribute('data-x'));
                guia.setAttribute('x2', rc.getAttribute('data-x'));
                guia.setAttribute('opacity', '1');
              }
              var filas = visiveis.map(function (p) { return { p: p, v: matriz[p][an] || 0 }; })
                .filter(function (o) { return o.v > 0; });
              // A dica mostra a área física (referência) junto das práticas.
              if (refVisivel) { filas.push({ p: REF_PRAT, v: physicalArea }); }
              filas.sort(function (a, b) { return b.v - a.v; });
              var html = '<div class="prat-tip-tit">' + esc(an) + '</div>';
              if (!filas.length) { html += '<div class="prat-tip-vazio">sem hectares</div>'; }
              filas.forEach(function (o) {
                html += '<div class="prat-tip-row"><span class="prat-tip-cor" style="background:' + cor[o.p] + '"></span>' +
                  '<span class="prat-tip-nome">' + esc(o.p) + '</span>' +
                  '<span class="prat-tip-val">' + fmtNum(o.v) + ' ha</span></div>';
              });
              tip.innerHTML = html;
              tip.hidden = false;
              var rr = rc.getBoundingClientRect(), wr = wrapLinhas.getBoundingClientRect();
              var cx = rr.left + rr.width / 2 - wr.left;
              cx = Math.max(110, Math.min(wr.width - 110, cx));
              tip.style.left = cx + 'px';
            });
            rc.addEventListener('mouseleave', function () {
              tip.hidden = true;
              if (guia) guia.setAttribute('opacity', '0');
            });
          });
        }

        // Etapas do painel: resumo → 8.1 (hectares por prática/ano) → gráfico 8.2
        // → hierarquia 8.3 (a parte pesada, que entra no fim).
        function renderPratTudo() {
          var lista = filtrarPraticas();
          return [
            function () { renderPratResumo(lista); },
            function () { renderPratTabla(lista); },
            function () { renderPratLinhas(lista); },
            function () { renderPratHierarquia(lista); },
            function () { if (vazioPrat) vazioPrat.style.display = lista.length ? 'none' : 'block'; }
          ];
        }

        // Renderização sob demanda: o painel é montado na primeira abertura.
        // Recolhido, as tabelas, o gráfico e a hierarquia saem da memória.
        ObterDados.registrarPainel('praticas', renderPratTudo, function () {
          [resumoPrat, tablaPrat, wrapPrat, wrapLinhas, leyendaPrat]
            .forEach(function (el) { if (el) el.innerHTML = ''; });
        });
      })();

      // ===================== PAINEL 09 · EVIDÊNCIAS =========================
      // Evidências das notas fiscais por TIPO e por ano: 9.1 tabela e 9.2
      // gráfico. O payload `dadosEvidenciasTipos` (API 3) já traz cada tipo com
      // a sua unidade (kg/L), total, anos e produtos.
      (function () {
        var resumoEvid = document.getElementById('evidResumo');
        var tablaEvid = document.getElementById('evidTabla');
        var wrapEvid = document.getElementById('evidLinhas');
        var leyendaEvid = document.getElementById('evidLeyenda');
        var vazioEvid = document.getElementById('evidVazio');
        var evidOcultas = {};

        var NOMES_TIPO = {
          fertilizantes: 'Fertilizantes',
          semente: 'Sementes',
          racao: 'Ração',
          diesel: 'Diesel',
          gasolina: 'Gasolina',
          etanol: 'Etanol',
          arla: 'ARLA',
          defensivo: 'Defensivos',
          outro: 'Outros'
        };

        function nomeTipo(tipo) {
          return NOMES_TIPO[String(tipo)] || String(tipo);
        }

        function anosEvid(tipos) {
          var set = {}, i, t, an;
          for (i = 0; i < tipos.length; i++) {
            t = tipos[i].anos || {};
            for (an in t) {
              if (Object.prototype.hasOwnProperty.call(t, an)) set[String(an).trim()] = 1;
            }
          }
          return Object.keys(set).sort(function (a, b) {
            var x = Number(a), y = Number(b);
            if (isNaN(x)) return 1;
            if (isNaN(y)) return -1;
            return x - y;
          });
        }

        function renderEvidResumo(tipos) {
          if (!resumoEvid) return;
          var anos = anosEvid(tipos);
          resumoEvid.innerHTML =
            '<span class="prod-chip"><strong>' + tipos.length + '</strong> tipos de evidência</span>' +
            '<span class="prod-chip"><strong>' + anos.length + '</strong> anos fiscais</span>';
        }

        function renderEvidTabla(tipos) {
          if (!tablaEvid) return;
          if (!tipos.length) {
            tablaEvid.innerHTML = '<p class="muted">Nenhuma evidência de nota fiscal nos filtros selecionados.</p>';
            return;
          }
          var anos = anosEvid(tipos);
          var celsAno = function (mapa) {
            return anos.map(function (an) {
              var v = (mapa || {})[an];
              return '<td class="cel-ano">' + (v ? fmtNum(v, 0) : '—') + '</td>';
            }).join('');
          };
          var linhas = tipos.map(function (t) {
            var unidade = ' <span class="muted">(' + esc(t.unidade || 'kg') + ')</span>';
            var produtos = t.produtos || [];
            // Tipo com UM produto: uma linha só (o próprio tipo), com a unidade.
            if (produtos.length <= 1) {
              return '<tr class="fert-grupo"><td class="fert-nome">' + esc(nomeTipo(t.tipo)) + unidade +
                '</td><td class="cel-ano fert-geral">' + fmtNum(t.total, 0) + '</td>' +
                celsAno(t.anos) + '</tr>';
            }
            // Tipo com VÁRIOS produtos: a linha de TOTAL do tipo + cada produto.
            var html = '<tr class="fert-grupo"><td class="fert-nome">' + esc(nomeTipo(t.tipo)) +
              ' Total' + unidade + '</td>' +
              '<td class="cel-ano fert-geral">' + fmtNum(t.total, 0) + '</td>' +
              celsAno(t.anos) + '</tr>';
            return html + produtos.map(function (p) {
              return '<tr><td class="fert-nome" style="padding-left:22px">' + esc(p.nome) + '</td>' +
                '<td class="cel-ano fert-geral">' + fmtNum(p.volume, 0) + '</td>' +
                celsAno(p.anos) + '</tr>';
            }).join('');
          }).join('');
          var headAnos = anos.map(function (an) { return '<th>' + esc(an) + '</th>'; }).join('');
          tablaEvid.innerHTML = '<table class="fert-pivot"><thead><tr>' +
            '<th>Tipo / Produto</th><th>Geral</th>' + headAnos +
            '</tr></thead><tbody>' + linhas + '</tbody></table>';
        }

        function renderEvidLinhas(tipos) {
          if (!wrapEvid || typeof ObterDados.montarGrafico !== 'function') return;
          var anos = anosEvid(tipos);
          var series = (tipos || []).map(function (t) {
            return { nome: t.tipo,
                     rotulo: nomeTipo(t.tipo) + ' (' + (t.unidade || 'kg') + ')',
                     valores: t.anos || {} };
          });
          ObterDados.montarGrafico({
            container: wrapEvid, leyenda: leyendaEvid,
            series: series, anos: anos, ocultas: evidOcultas,
            unidade: 'volume evidenciado', unidadeCurta: 'kg/L',
            vazio: 'Nenhuma evidência de nota fiscal nos filtros selecionados.',
            aria: 'Total evidenciado por tipo e por ano'
          });
        }

        function renderEvidTudo() {
          var tipos = ObterDados.dadosEvidenciasTipos || [];
          return [
            function () { renderEvidResumo(tipos); },
            function () { renderEvidTabla(tipos); },
            function () { renderEvidLinhas(tipos); },
            function () { if (vazioEvid) vazioEvid.style.display = tipos.length ? 'none' : 'block'; }
          ];
        }

        ObterDados.registrarPainel('evidencias', renderEvidTudo, function () {
          [resumoEvid, tablaEvid, wrapEvid, leyendaEvid]
            .forEach(function (el) { if (el) el.innerHTML = ''; });
        });
      })();

      // Animação leve de fundo (partículas lentas), respeita "reduzir movimento"



      var cv = document.getElementById('fundo'), ctx = cv.getContext('2d');



      var w, h, pts = [], reduz = window.matchMedia('(prefers-reduced-motion: reduce)').matches, rodando = false;



      function tamanho() {



        var d = Math.min(window.devicePixelRatio || 1, 2);



        w = cv.width = innerWidth * d; h = cv.height = innerHeight * d;



        var n = Math.round(Math.min(46, innerWidth / 26));



        pts = [];



        for (var i = 0; i < n; i++) pts.push({ x: Math.random() * w, y: Math.random() * h, vx: (Math.random() - .5) * .25 * d, vy: (Math.random() - .5) * .25 * d });



      }



      function quadro() {

        // No celular a animação de fundo fica desligada (o CSS esconde o
        // canvas): a rolagem ganha muito mais do que o efeito entrega.
        if (innerWidth <= 760) { rodando = false; return; }

        rodando = true;



        ctx.clearRect(0, 0, w, h);



        var lim = Math.min(w, h) * .2;



        for (var i = 0; i < pts.length; i++) {



          var p = pts[i];



          if (!reduz) { p.x += p.vx; p.y += p.vy; if (p.x < 0 || p.x > w) p.vx *= -1; if (p.y < 0 || p.y > h) p.vy *= -1; }



          ctx.fillStyle = 'rgba(96,165,250,.55)';



          ctx.beginPath(); ctx.arc(p.x, p.y, 1.8, 0, 6.283); ctx.fill();



          for (var j = i + 1; j < pts.length; j++) {



            var q = pts[j], dx = p.x - q.x, dy = p.y - q.y, d = Math.sqrt(dx * dx + dy * dy);



            if (d < lim) { ctx.strokeStyle = 'rgba(96,165,250,' + (.16 * (1 - d / lim)) + ')'; ctx.beginPath(); ctx.moveTo(p.x, p.y); ctx.lineTo(q.x, q.y); ctx.stroke(); }



          }



        }



        // Pausa em aba oculta e retoma ao voltar (economia real de bateria).
        if (!reduz && !document.hidden) requestAnimationFrame(quadro);

        else rodando = false;



      }



      tamanho(); quadro();



      addEventListener('resize', function () { tamanho(); if (!rodando) quadro(); });

      document.addEventListener('visibilitychange', function () { if (!document.hidden && !rodando) quadro(); });



    })();



      // ===== Celular: rótulos de coluna + tabelas em cartões =====
      /*
         O relatório tem muitas tabelas largas (uma coluna por ano). Em telas
         estreitas elas viram cartões no formato "COLUNA: valor" — sem rolagem
         horizontal. Os rótulos saem do próprio cabeçalho da tabela/grade
         (`thead th` / `.det-head`) e são copiados para `data-col` nas células;
         nas tabelas agrupadas por `rowspan`, as linhas de continuação recebem
         o nome do grupo em `data-no`. Nada é feito no desktop e apenas os
         trechos NOVOS da página são processados (MutationObserver), de modo
         que o custo é proporcional ao que acabou de ser montado.
         Linhas recolhidas (`hidden`) ficam sem rótulo até aparecerem: os pivôs
         que começam fechados não pagam por cartões que ninguém está vendo — o
         observador rotula o contêiner quando o `hidden` sai.
      */
      (function responsivo() {
        var LIMITE_CELULAR = 760;

        function telaEstreita() { return window.innerWidth <= LIMITE_CELULAR; }

        function rotuloDe(el) {
          return (el && el.textContent ? el.textContent : '').replace(/\s+/g, ' ').trim();
        }

        // Linha recolhida (`hidden` — os pivôs 4.1/5.1/5.5 e 7.4–7.8 começam
        // fechados) não é rotulada enquanto está escondida: menos escrita no
        // DOM ao abrir o painel. O rótulo entra quando a linha aparece.
        function recolhida(linha) {
          return linha.hasAttribute('hidden');
        }

        // Grades OS → Fazenda → Talhão: copia o cabeçalho em cada linha.
        function rotularGrade(grade) {
          if (!grade || grade.getAttribute('data-rotulado')) return;
          var cabecalho = grade.querySelector('.det-head');
          if (!cabecalho) return;
          var rotulos = [], linhas, i, c;
          for (i = 0; i < cabecalho.children.length; i++) {
            rotulos.push(rotuloDe(cabecalho.children[i]));
          }
          linhas = grade.querySelectorAll('.det-row');
          for (i = 0; i < linhas.length; i++) {
            var linha = linhas[i];
            if (linha.classList.contains('det-head')) continue;
            // Linha recolhida não vira cartão agora: o rótulo dela é aplicado
            // quando o observador vê a linha aparecer (menos escrita no DOM).
            if (recolhida(linha)) continue;
            for (c = 0; c < linha.children.length; c++) {
              var cel = linha.children[c], rotulo = rotulos[c];
              // Coluna 0 = selo de expandir/recolher; coluna 1 = nome do nó
              // (título do cartão). Nenhuma das duas é um valor rotulado — a
              // regra é por POSIÇÃO porque a linha "Total geral" (do
              // consolidado) usa um `<span>` sem a classe `cel-nome`.
              if (c < 2 || !rotulo || cel.classList.contains('toggle')) continue;
              cel.setAttribute('data-col', rotulo);
            }
          }
          grade.setAttribute('data-rotulado', '1');
        }

        // Tabelas: copia o `thead` para as células. Na primeira linha de um
        // grupo a coluna do nome é consumida pelo `rowspan`; o deslocamento
        // (nº de colunas do cabeçalho menos o nº de células da linha) devolve
        // o alinhamento correto dos rótulos nas linhas seguintes.
        function rotularTabela(tab) {
          if (!tab || tab.getAttribute('data-rotulado')) return;
          var ths = tab.querySelectorAll('thead th');
          if (!ths.length) return;
          var rotulos = [], linhas, nome = '', restantes = 0, i, c;
          for (i = 0; i < ths.length; i++) rotulos.push(rotuloDe(ths[i]));
          linhas = tab.querySelectorAll('tbody tr');
          for (i = 0; i < linhas.length; i++) {
            var linha = linhas[i], cels = linha.children;
            // Linhas recolhidas (`hidden`) ficam de fora: os pivôs 4.1/5.1/5.5
            // e 7.4–7.8 começam fechados e são rotulados quando abrem.
            if (recolhida(linha)) continue;
            var deslocamento = rotulos.length - cels.length;
            for (c = 0; c < cels.length; c++) {
              var cel = cels[c], posicao = c + deslocamento;
              if (cel.hasAttribute('rowspan')) continue;
              var rotulo = posicao >= 0 ? rotulos[posicao] : '';
              if (rotulo) cel.setAttribute('data-col', rotulo);
            }
            var primeira = cels.length ? cels[0] : null;
            if (primeira && primeira.hasAttribute('rowspan')) {
              nome = rotuloDe(primeira);
              restantes = (parseInt(primeira.getAttribute('rowspan'), 10) || 1) - 1;
            } else if (restantes > 0) {
              linha.setAttribute('data-no', nome);
              restantes--;
            }
          }
          tab.setAttribute('data-rotulado', '1');
        }

        function aplicar(raiz) {
          if (!raiz || raiz.nodeType !== 1) return;
          var alvos = [], grades, tabelas, i;
          if (raiz.classList && (raiz.classList.contains('painel-consolidado') ||
            raiz.classList.contains('prod-hierarquia'))) alvos.push(raiz);
          grades = raiz.querySelectorAll('.painel-consolidado, .prod-hierarquia');
          for (i = 0; i < grades.length; i++) alvos.push(grades[i]);
          for (i = 0; i < alvos.length; i++) rotularGrade(alvos[i]);
          if (raiz.tagName === 'TABLE') tabelas = [raiz];
          else tabelas = raiz.querySelectorAll('table');
          for (i = 0; i < tabelas.length; i++) rotularTabela(tabelas[i]);
        }

        function aplicarTudo() {
          if (telaEstreita()) aplicar(document.body);
        }

        // Gancho usado pelo template quando uma hierarquia sob demanda repõe o
        // corpo de um nó: o rótulo dos cartões (celular) é reaplicado à grade
        // dona daquele corpo — e só em tela estreita (no desktop é custo puro).
        ObterDados.rotular = function (raiz) {
          if (!telaEstreita() || !raiz) return;
          var caixa = raiz.closest('.painel-consolidado, .prod-hierarquia') || raiz;
          // As linhas que acabaram de entrar ainda não têm rótulo: a marca do
          // contêiner precisa cair para a grade ser rotulada de novo.
          if (caixa.removeAttribute) caixa.removeAttribute('data-rotulado');
          aplicar(caixa);
        };

        var pendentes = [], agendado = false;

        function agendar() {
          if (agendado) return;
          agendado = true;
          requestAnimationFrame(function () {
            agendado = false;
            var nos = pendentes;
            pendentes = [];
            if (!telaEstreita()) return;
            for (var i = 0; i < nos.length; i++) aplicar(nos[i]);
          });
        }

        // Pivô sob demanda: a tabela recebeu linhas novas e o rótulo dos
        // cartões precisa ser recalculado. A tabela entra na mesma fila do
        // `MutationObserver` (um recálculo por quadro, no máximo).
        ObterDados.reRotular = function (caixa) {
          if (!telaEstreita() || !caixa) return;
          var tab = caixa.tagName === 'TABLE' ? caixa : caixa.closest('table');
          if (!tab) return;
          tab.removeAttribute('data-rotulado');
          pendentes.push(tab);
          agendar();
        };

        if (typeof MutationObserver === 'function') {
          new MutationObserver(function (mudancas) {
            if (!telaEstreita()) return;
            for (var i = 0; i < mudancas.length; i++) {
              var mudanca = mudancas[i], novos = mudanca.addedNodes;
              for (var j = 0; j < novos.length; j++) {
                if (novos[j].nodeType === 1) pendentes.push(novos[j]);
              }
              // Linha revelada (`hidden` retirado ao expandir um nó): o
              // contêiner dela (tabela ou grade) volta a ser rotulado.
              if (mudanca.type === 'attributes') {
                var alvo = mudanca.target;
                if (!alvo || alvo.hasAttribute('hidden')) continue;
                var caixa = alvo.closest('table') ||
                  alvo.closest('.painel-consolidado, .prod-hierarquia');
                if (caixa) { caixa.removeAttribute('data-rotulado'); pendentes.push(caixa); }
              }
            }
            if (pendentes.length) agendar();
          }).observe(document.querySelector('main') || document.body,
            { childList: true, subtree: true, attributes: true, attributeFilter: ['hidden'] });
        }

        aplicarTudo();

        // Ao girar o telefone (ou redimensionar) os rótulos são recalculados.
        var larguraAnterior = window.innerWidth, temporizador = null;
        window.addEventListener('resize', function () {
          if (Math.abs(window.innerWidth - larguraAnterior) < 24) return;
          larguraAnterior = window.innerWidth;
          if (temporizador) clearTimeout(temporizador);
          temporizador = setTimeout(aplicarTudo, 180);
        }, { passive: true });
      })();

      // ===== Celular: botão "voltar ao topo" =====
      (function botaoTopo() {
        var btn = document.getElementById('btnTopo');
        if (!btn) return;
        var visivel = false;
        btn.addEventListener('click', function () {
          window.scrollTo({ top: 0, behavior: 'smooth' });
        });
        window.addEventListener('scroll', function () {
          var mostrar = window.innerWidth <= 760 && window.scrollY > 600;
          if (mostrar === visivel) return;
          visivel = mostrar;
          btn.classList.toggle('visivel', mostrar);
        }, { passive: true });
      })();

      // Selo de filtros: os painéis só são montados ao abrir, então o estado
      // inicial é calculado aqui.
      if (window.ObterDados && window.ObterDados.atualizarBadgeFiltros) {
        window.ObterDados.atualizarBadgeFiltros();
      }

      // Hierarquias que já vêm prontas do Python (painel 2.1 · consolidado e
      // por arquivo): o corpo de cada fazenda/talhão passa a entrar no
      // documento só quando o nó é aberto.
      if (window.ObterDados && window.ObterDados.detailsSobDemanda) {
        Array.prototype.forEach.call(
          document.querySelectorAll('main .painel-consolidado'),
          function (raiz) { window.ObterDados.detailsSobDemanda(raiz); }
        );
      }

      // ===== Painéis numerados: recolher/expandir =====
      (function configurarPaineis() {
        var paineis = document.querySelectorAll('main > section.painel');

        function definirExpandido(painel, expandido) {
          painel.classList.toggle('painel-recolhido', !expandido);
          var btn = painel.querySelector(':scope > .painel-topo .painel-toggle');
          if (btn) btn.setAttribute('aria-expanded', expandido ? 'true' : 'false');

          if (!window.ObterDados) return;

          // Primeira abertura do painel: monta o conteúdo sob demanda.
          if (expandido) {

            if (window.ObterDados.ativarPainel) window.ObterDados.ativarPainel(painel.id);

          } else if (window.ObterDados.agendarLiberacao) {

            // Recolhido: o conteúdo pesado do painel sai da memória depois de
            // um tempo (reabrir remonta). Vale só para os painéis montados em
            // JavaScript, que declaram como se liberar.
            window.ObterDados.agendarLiberacao(painel.id);

          }
        }

        Array.prototype.forEach.call(paineis, function (painel, idx) {
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
            definirExpandido(painel, painel.classList.contains('painel-recolhido'));
          }

          topo.addEventListener('click', function (ev) {
            var alvo = ev.target;
            if (alvo.closest('.painel-toggle')) { alternar(); return; }
            if (alvo.closest('a, button, select, input, textarea, .info-tooltip')) return;
            alternar();
          });

          btn.addEventListener('keydown', function (ev) {
            if (ev.key === 'Enter' || ev.key === ' ') {
              ev.preventDefault();
              alternar();
            }
          });

          // Painéis 1 a 8 começam recolhidos; o 9º (Qualidade dos dados) inicia aberto.
          definirExpandido(painel, idx >= 8);
        });

        // Ao navegar por um link interno, expande o painel de destino.
        Array.prototype.forEach.call(
          document.querySelectorAll('a[href^="#"]'),
          function (a) {
            a.addEventListener('click', function () {
              var alvo = document.getElementById(
                (a.getAttribute('href') || '').slice(1));
              if (alvo && alvo.classList.contains('painel')) {
                definirExpandido(alvo, true);
              }
            });
          });
      })();

  
      // ===== Painel 09 · laudos para download (PDF · DOCX) =====
      // O laudo de cada OS vem ANEXADO no próprio HTML (base64, gerado pela API
      // 3): aqui só se montam os botões — no corpo do 9.3 e no topo do painel,
      // ao lado do `i` e do expandir — e o download do arquivo escolhido.
      (function configurarLaudos() {
        var origem = document.getElementById('dadosLaudos');
        if (!origem) return;

        var laudos = [];
        try { laudos = JSON.parse(origem.textContent || '[]'); } catch (ign) { laudos = []; }
        if (!Array.isArray(laudos) || !laudos.length) return;

        // Os dois formatos do laudo: o rótulo do botão e o campo do payload.
        var TIPOS = [
          { chave: 'pdf', rotulo: 'PDF', dados: 'pdf', nome: 'pdfNome',
            descricao: 'Baixar o laudo em PDF',
            mime: 'application/pdf' },
          { chave: 'docx', rotulo: 'DOCX', dados: 'docx', nome: 'docxNome',
            descricao: 'Baixar o laudo em DOCX',
            mime: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' }
        ];

        // Base64 (do Python) → Blob: o download não depende de rede nem de
        // arquivo ao lado do relatório.
        function paraBlob(base64, mime) {
          var binario = window.atob(base64);
          var bytes = new Uint8Array(binario.length);
          for (var i = 0; i < binario.length; i++) {
            bytes[i] = binario.charCodeAt(i);
          }
          return new Blob([bytes], { type: mime });
        }

        function baixar(laudo, tipo) {
          var base64 = laudo[tipo.dados];
          if (!base64) return;
          var url = URL.createObjectURL(paraBlob(base64, tipo.mime));
          var a = document.createElement('a');
          a.href = url;
          a.download = laudo[tipo.nome] || ('laudo.' + tipo.chave);
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          window.setTimeout(function () { URL.revokeObjectURL(url); }, 5000);
        }

        // Botão de um formato; `null` quando o anexo daquele formato não veio
        // (ex.: o PDF não pôde ser gerado) — o botão simplesmente não aparece.
        function botao(laudo, tipo, classe) {
          if (!laudo[tipo.dados]) return null;
          var btn = document.createElement('button');
          btn.type = 'button';
          btn.className = classe;
          btn.textContent = tipo.rotulo;
          btn.setAttribute('title', tipo.descricao + ' — ' +
            (laudo[tipo.nome] || ''));
          btn.setAttribute('aria-label', tipo.descricao + ' (' +
            (laudo.os || 'sem OS') + ')');
          btn.addEventListener('click', function (ev) {
            ev.stopPropagation();
            baixar(laudo, tipo);
          });
          return btn;
        }

        function acoesDoLaudo(laudo, classe) {
          var acoes = document.createElement('span');
          acoes.className = 'laudo-item-acoes';
          TIPOS.forEach(function (tipo) {
            var btn = botao(laudo, tipo, classe);
            if (btn) acoes.appendChild(btn);
          });
          return acoes;
        }

        // 1) Corpo do 9.3: uma linha por laudo (OS + os botões dos formatos).
        var lista = document.getElementById('laudosLista');
        if (lista) {
          laudos.forEach(function (laudo) {
            var item = document.createElement('div');
            item.className = 'laudo-item';
            var nome = document.createElement('span');
            nome.className = 'laudo-item-os';
            nome.textContent = laudo.os || 'Sem OS';
            item.appendChild(nome);
            item.appendChild(acoesDoLaudo(laudo, 'laudo-btn'));
            lista.appendChild(item);
          });
        }

        // 2) Topo do painel 09: ao lado do `i` e do expandir. Com UM laudo saem
        //    os dois botões; com vários (consolidado), um menu por OS.
        var painel = document.getElementById('alertas');
        var acoes = painel
          ? painel.querySelector(':scope > .painel-topo > .painel-acoes') : null;
        if (!acoes) return;

        var caixa = document.createElement('div');
        caixa.className = 'painel-laudos';
        if (laudos.length === 1) {
          TIPOS.forEach(function (tipo) {
            var btn = botao(laudos[0], tipo, 'laudo-btn');
            if (btn) caixa.appendChild(btn);
          });
        } else {
          var menu = document.createElement('details');
          menu.className = 'laudos-menu';
          var resumo = document.createElement('summary');
          resumo.className = 'laudo-btn laudos-menu-resumo';
          resumo.textContent = 'Laudos (' + laudos.length + ')';
          menu.appendChild(resumo);
          var corpo = document.createElement('div');
          corpo.className = 'laudos-menu-lista';
          laudos.forEach(function (laudo) {
            var item = document.createElement('div');
            item.className = 'laudo-item';
            var nome = document.createElement('span');
            nome.className = 'laudo-item-os';
            nome.textContent = laudo.os || 'Sem OS';
            item.appendChild(nome);
            item.appendChild(acoesDoLaudo(laudo, 'laudo-btn'));
            corpo.appendChild(item);
          });
          menu.appendChild(corpo);
          caixa.appendChild(menu);
        }
        if (caixa.childNodes.length) {
          acoes.insertBefore(caixa, acoes.querySelector('.painel-toggle'));
        }
      })();

/* One article template. Dates select immutable Markdown, never another HTML page. */
(() => {
  const base = document.body.dataset.baseUrl;
  const siteTitle = document.body.dataset.siteTitle;
  const datePattern = /^\d{4}-\d{2}-\d{2}$/;
  const reportURL = date => `${base}/reader/?date=${encodeURIComponent(date)}`;
  if (document.body.classList.contains('page-not-found')) {
    const relative = location.pathname.startsWith(`${base}/`) ? location.pathname.slice(base.length) : '';
    const legacy = relative.match(/^\/daily\/(\d{4}-\d{2}-\d{2})(?:\/(?:index\.html)?)?$/);
    if (legacy) location.replace(reportURL(legacy[1]) + location.hash);
    return;
  }

  const status = document.querySelector('#reader-status');
  const content = document.querySelector('#reader-content');
  const chooser = document.querySelector('#report-date');
  const escape = value => String(value).replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
  function localLink(url) {
    if (!url.startsWith('/') || url.startsWith('//')) return url;
    return base + url;
  }

  // Match the archive parser's Markdown dialect and figure/caption treatment.
  function renderMarkdown(text) {
    const md = window.markdownit('commonmark', {html: false}).enable(['table', 'strikethrough']);
    const tokens = md.parse(text, {});
    function rewrite(items) {
      items.forEach(token => {
        ['href', 'src'].forEach(attr => {
          const value = token.attrGet(attr);
          if (value) token.attrSet(attr, localLink(value));
        });
        if (token.type === 'image') {
          token.attrSet('loading', 'lazy');
          token.attrSet('decoding', 'async');
        }
        if (token.children) rewrite(token.children);
      });
    }
    rewrite(tokens);
    tokens.forEach((token, index) => {
      if (token.type !== 'paragraph_open') return;
      const children = tokens[index + 1]?.children || [];
      if (children.length === 1 && children[0].type === 'image') {
        token.attrSet('class', 'figure');
        if (tokens[index + 3]?.type === 'paragraph_open') {
          const caption = tokens[index + 4]?.children || [];
          if (caption[0]?.type === 'em_open' && caption.at(-1)?.type === 'em_close') {
            tokens[index + 3].attrSet('class', 'figure-caption');
          }
        }
      }
    });
    return md.renderer.render(tokens, md.options, {});
  }

  function display(report, markdown, reports) {
    const spans = report.source_spans;
    const lines = markdown.split(/\r?\n/).slice(spans.body_line);
    const ignored = new Set(spans.ignored_lines);
    const section = ([start, end]) => lines.slice(start, end).filter((_, i) => !ignored.has(start + i))
      .join('\n').trim().replace(/(?:\n\s*---\s*)+$/, '').trim();
    const toc = [], papers = [];
    report.papers.forEach((paper, index) => {
      const number = String(index + 1).padStart(2, '0');
      toc.push(`<li><a href="#${escape(paper.anchor)}"><span>${number}</span>${escape(paper.short_title)}</a></li>`);
      papers.push(`<section class="paper-section" id="${escape(paper.anchor)}">
        <header class="paper-heading"><div class="paper-kicker"><span class="paper-number">${number}</span>
        <span class="badge ${paper.category === 'Classic' ? 'badge-classic' : ''}">${escape(paper.category)}</span></div><h2>${escape(paper.title)}</h2></header>
        <div class="prose">${renderMarkdown(section(spans.papers[index]))}</div></section>`);
    });
    const trends = section(spans.trends);
    if (trends) {
      toc.push('<li><a href="#research-trends"><span>↳</span>Research trends</a></li>');
      papers.push(`<section class="trends-section" id="research-trends"><p class="eyebrow">CONNECTING THE PAPERS</p><h2>${escape(report.trends_title)}</h2><div class="prose">${renderMarkdown(trends)}</div></section>`);
    }
    const introText = section(spans.intro);
    const intro = !introText ? '' : /Run ID|Permanent history|执行日期|归档位置/.test(introText)
      ? `<details class="report-notes"><summary>Publication &amp; verification notes <span aria-hidden="true">+</span></summary><div class="prose">${renderMarkdown(introText)}</div></details>`
      : `<div class="report-intro prose">${renderMarkdown(introText)}</div>`;
    const index = reports.indexOf(report);
    const neighbors = [[reports[index + 1], 'Older report', '←'], [reports[index - 1], 'Newer report', '→']]
      .filter(([neighbor]) => neighbor).map(([neighbor, label, arrow]) =>
        `<a class="issue-neighbor" href="${reportURL(neighbor.date)}"><span>${label} ${arrow}</span><strong>${escape(neighbor.formatted_date)}</strong></a>`).join('');
    const contents = toc.length ? `<aside class="toc"><details open><summary>In this report <span>${String(report.papers.length).padStart(2, '0')}</span></summary><nav aria-label="Report contents"><ol>${toc.join('')}</ol></nav></details><a class="back-top" href="#top">Back to top ↑</a></aside>` : '';
    content.innerHTML = `<header class="report-header"><p class="eyebrow">DAILY BRIEFING <span>/</span> ${escape(report.weekday)}</p><h1>${escape(report.formatted_date)}</h1><div class="report-meta"><span>${report.papers.length} ${report.papers.length === 1 ? 'paper' : 'papers'}</span><span>~${escape(report.reading_minutes)} min read</span></div></header>
      <div class="reader-layout">${contents}<article id="report-body">${intro}${papers.join('')}<nav class="issue-pagination" aria-label="Adjacent reports">${neighbors}</nav></article></div>`;
    document.title = `${report.title} - ${siteTitle}`;
    status.hidden = true;
    content.setAttribute('aria-busy', 'false');
    window.DailyPaperEnhance();
    if (location.hash) {
      // A malformed fragment must not discard a successfully loaded article.
      let anchor = location.hash.slice(1);
      try { anchor = decodeURIComponent(anchor); } catch { /* Keep the literal fragment. */ }
      document.getElementById(anchor)?.scrollIntoView();
    }
  }

  async function fetchFile(path) {
    const response = await fetch(`${base}${path}`, {cache: 'no-cache', credentials: 'same-origin'});
    if (!response.ok) throw new Error('Could not load the report. Please try again.');
    return response;
  }
  async function load() {
    try {
      const reports = await (await fetchFile('/reports/index.json')).json();
      if (!Array.isArray(reports) || reports.some(report => !datePattern.test(report.date))) {
        throw new Error('The report index could not be read. Please try again.');
      }
      if (!reports.length) throw new Error('No reports have been published yet.');
      chooser.replaceChildren(...reports.map(report => new Option(report.formatted_date, report.date)));
      chooser.disabled = false;
      chooser.addEventListener('change', () => location.assign(reportURL(chooser.value)));
      const requested = new URLSearchParams(location.search).get('date') ?? reports[0].date;
      const report = reports.find(item => item.date === requested);
      if (!report) throw new Error('No report was published for this date. Choose another date or browse the archive.');
      chooser.value = requested;
      const response = await fetchFile(`/reports/${report.date}.md?v=${report.sha256}`);
      const raw = await response.arrayBuffer();
      const digest = [...new Uint8Array(await crypto.subtle.digest('SHA-256', raw))]
        .map(byte => byte.toString(16).padStart(2, '0')).join('');
      if (digest !== report.sha256) throw new Error('This report is being updated. Please reload in a moment.');
      display(report, new TextDecoder().decode(raw), reports);
    } catch (error) {
      content.replaceChildren();
      content.setAttribute('aria-busy', 'false');
      status.hidden = false;
      status.innerHTML = `<h1>Report unavailable</h1><p>${escape(error.message)}</p><div class="reader-recovery"><button class="button button-primary" type="button" id="reader-retry">Try again</button><a class="button" href="${base}/archive/">Browse archive →</a></div>`;
      document.querySelector('#reader-retry').addEventListener('click', () => location.reload());
    }
  }
  load();
})();

/* Archive filters and reading controls shared by every selected report. */
(() => {
  const search = document.querySelector('#archive-search');
  const month = document.querySelector('#archive-month');
  if (search && month) {
    const rows = [...document.querySelectorAll('[data-report]')];
    const groups = [...document.querySelectorAll('[data-month-group]')];
    const reset = document.querySelector('#reset-filters');
    const parameters = new URLSearchParams(location.search);
    search.value = parameters.get('q') || '';
    const requestedMonth = parameters.get('month') || '';
    month.value = [...month.options].some(option => option.value === requestedMonth) ? requestedMonth : '';
    function filter() {
      const terms = search.value.trim().toLowerCase().split(/\s+/).filter(Boolean);
      let count = 0;
      rows.forEach(row => {
        const matches = (!month.value || row.dataset.month === month.value) && terms.every(term => row.dataset.search.includes(term));
        row.hidden = !matches;
        if (matches) count += 1;
      });
      groups.forEach(group => { group.hidden = !group.querySelector('[data-report]:not([hidden])'); });
      document.querySelector('#result-count').textContent = `${count} ${count === 1 ? 'report' : 'reports'}`;
      document.querySelector('#no-results').hidden = count !== 0;
      reset.hidden = !search.value && !month.value;
      const url = new URL(location.href);
      if (search.value) url.searchParams.set('q', search.value); else url.searchParams.delete('q');
      if (month.value) url.searchParams.set('month', month.value); else url.searchParams.delete('month');
      history.replaceState(null, '', url);
    }
    document.querySelector('[data-enhanced]').hidden = false;
    search.addEventListener('input', filter);
    month.addEventListener('change', filter);
    reset.addEventListener('click', () => { search.value = ''; month.value = ''; filter(); search.focus(); });
    filter();
  }

  window.DailyPaperEnhance = () => {
    const contents = document.querySelector('.toc details');
    if (contents && matchMedia('(max-width: 900px)').matches) contents.open = false;
    const report = document.querySelector('#report-body');
    if (report) {
      const links = [...document.querySelectorAll('.toc a[href^="#paper-"], .toc a[href="#research-trends"]')];
      const sections = links.map(link => document.querySelector(link.getAttribute('href')));
      let scheduled = false;
      function updateReadingPosition() {
        const start = report.getBoundingClientRect().top + scrollY;
        const distance = report.offsetHeight - innerHeight + 110;
        const fraction = Math.min(1, Math.max(0, (scrollY - start + 110) / Math.max(1, distance)));
        document.querySelector('.reading-progress span').style.transform = `scaleX(${fraction})`;
        let active = 0;
        sections.forEach((section, index) => { if (section && section.getBoundingClientRect().top <= 160) active = index; });
        links.forEach((link, index) => { if (index === active) link.setAttribute('aria-current', 'location'); else link.removeAttribute('aria-current'); });
        scheduled = false;
      }
      function scheduleUpdate() {
        if (!scheduled) { scheduled = true; requestAnimationFrame(updateReadingPosition); }
      }
      addEventListener('scroll', scheduleUpdate, { passive: true });
      addEventListener('resize', scheduleUpdate);
      addEventListener('load', scheduleUpdate);
      document.querySelector('.report-notes')?.addEventListener('toggle', scheduleUpdate);
      scheduleUpdate();
    }

    const dialog = document.querySelector('#figure-dialog');
    if (dialog && typeof dialog.showModal === 'function') {
      const enlarged = dialog.querySelector('img');
      const viewport = dialog.querySelector('.figure-viewport');
      let scale = 1;
      function setScale(value) {
        if (!enlarged.naturalWidth) return;
        scale = Math.min(4, Math.max(.125, value));
        enlarged.style.width = `${Math.round(enlarged.naturalWidth * scale)}px`;
        dialog.querySelector('.dialog-scale').textContent = `${Math.round(scale * 100)}%`;
        dialog.querySelector('.dialog-smaller').disabled = scale <= .125;
        dialog.querySelector('.dialog-larger').disabled = scale >= 4;
      }
      function originalSize() { setScale(1); viewport.scrollTo(0, 0); }
      enlarged.addEventListener('load', originalSize);
      dialog.querySelector('.dialog-fit').addEventListener('click', () => {
        setScale(Math.min(1, viewport.clientWidth / enlarged.naturalWidth, innerHeight * .7 / enlarged.naturalHeight));
        viewport.scrollTo(0, 0);
      });
      dialog.querySelector('.dialog-actual').addEventListener('click', originalSize);
      dialog.querySelector('.dialog-larger').addEventListener('click', () => setScale(scale * 1.5));
      dialog.querySelector('.dialog-smaller').addEventListener('click', () => setScale(scale / 1.5));
      document.querySelectorAll('.figure img').forEach(img => {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'figure-zoom';
        button.setAttribute('aria-label', `Enlarge figure: ${img.alt || 'paper figure'}`);
        img.replaceWith(button);
        button.append(img);
        const hint = document.createElement('span');
        hint.className = 'figure-hint';
        hint.textContent = 'Expand ↗';
        button.append(hint);
        button.addEventListener('click', () => {
          enlarged.src = img.currentSrc || img.src;
          enlarged.alt = img.alt;
          dialog.querySelector('.dialog-caption').textContent = img.alt;
          dialog.showModal();
          if (enlarged.complete) originalSize();
        });
      });
      dialog.querySelector('.dialog-close').addEventListener('click', () => dialog.close());
      dialog.addEventListener('click', event => { if (event.target === dialog) dialog.close(); });
    }
  };
  // Keep figure controls working on dated HTML still in a reader's browser cache.
  if (document.querySelector('#report-body')) window.DailyPaperEnhance();
})();

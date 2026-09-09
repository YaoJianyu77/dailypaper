"""Controller-owned, local-only website screenshots for the final visual review."""

import mimetypes
from pathlib import Path
from urllib.parse import unquote, urlparse

from recommendation_history import sha256
from report_validation import require


def inspect_site(site, article, output, expected_images, expected_tables):
    """Render fixed local build files; no arbitrary URLs, commands, or live network."""
    try:
        from playwright.sync_api import sync_playwright, Error
    except ImportError as error:
        raise RuntimeError('Website browser dependency missing; run bash scripts/install_local_cron.sh') from error
    site, output = Path(site).resolve(), Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    screenshots, views, failures = [], [], []
    origin, prefix = 'https://dailypaper.invalid', '/dailypaper/'

    def local_resource(route):
        url = urlparse(route.request.url)
        if url.scheme != 'https' or url.netloc != 'dailypaper.invalid' or not url.path.startswith(prefix):
            failures.append('Blocked non-local website resource')
            route.abort()
            return
        path = (site / unquote(url.path[len(prefix):])).resolve()
        if path.is_dir():
            path = path / 'index.html'
        if not path.is_relative_to(site) or not path.is_file():
            failures.append('Missing or unsafe local website resource: ' + url.path)
            route.abort()
            return
        route.fulfill(path=str(path), content_type=mimetypes.guess_type(str(path))[0] or 'application/octet-stream',
                      headers={'Content-Security-Policy': "default-src 'self' data:; script-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'none'; object-src 'none'"})

    def capture(target, name, width):
        path = output / f'{width}-{name}.png'
        target.screenshot(path=str(path), animations='disabled')
        screenshots.append({'path': str(path), 'sha256': sha256(path.read_bytes()), 'viewport_width': width, 'item': name})

    try:
        with sync_playwright() as playwright:
            # Keep Chromium's own OS sandbox enabled. Codex never receives a
            # broader execution profile or a host-browser command interface.
            with playwright.chromium.launch(headless=True, chromium_sandbox=True) as browser:
                version = browser.version
                for width in (1440, 390):
                    context = browser.new_context(viewport={'width': width, 'height': 1000},
                                                  service_workers='block', accept_downloads=False)
                    context.set_offline(True)
                    context.route('**/*', local_resource)
                    page = context.new_page()
                    page.on('pageerror', lambda error: failures.append('Website JavaScript error: ' + str(error)))
                    page.goto(origin + prefix + article.lstrip('/'), wait_until='networkidle')
                    page.locator('#report-body').wait_for()
                    require(not failures, '; '.join(failures))
                    images, tables = page.locator('#report-body img'), page.locator('#report-body table')
                    require(images.count() == expected_images, 'Browser did not display every report figure')
                    require(tables.count() == expected_tables, 'Browser did not display every report table')
                    require(page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'), 'Rendered article overflows the viewport')
                    capture(page, 'article-top', width)
                    for index in range(images.count()):
                        element = images.nth(index)
                        element.scroll_into_view_if_needed()
                        page.wait_for_function('img => img.complete', arg=element.element_handle())
                        require(element.is_visible() and element.evaluate('e => e.complete && e.naturalWidth > 0 && e.getBoundingClientRect().width > 32'),
                                'Website figure is hidden, broken, or too small')
                        capture(element, f'figure-{index + 1}', width)
                    for index in range(tables.count()):
                        element = tables.nth(index)
                        element.scroll_into_view_if_needed()
                        require(element.is_visible() and element.locator('th,td').count() > 0, 'Website table is hidden or empty')
                        capture(element, f'table-{index + 1}', width)
                    zoom = page.locator('.figure-zoom')
                    require(zoom.count() == expected_images, 'Figure enlargement controls are missing')
                    expanded = []
                    for index in range(expected_images):
                        zoom.nth(index).click()
                        dialog = page.locator('#figure-dialog')
                        require(dialog.is_visible(), 'Figure enlargement did not open')
                        enlarged = dialog.locator('img')
                        page.wait_for_function('img => img.complete && img.naturalWidth > 0', arg=enlarged.element_handle())
                        frame = dialog.locator('.figure-viewport')
                        dialog.locator('.dialog-fit').click()
                        require(enlarged.evaluate('e => e.getBoundingClientRect().width <= e.parentElement.clientWidth + 1'),
                                'Fit control does not fit the enlarged figure')
                        dialog.locator('.dialog-actual').click()
                        require(enlarged.evaluate('e => Math.abs(e.getBoundingClientRect().width - e.naturalWidth) <= 1'),
                                'Original-size figure control does not preserve readable pixels')
                        if index == 0:
                            dialog.locator('.dialog-larger').click()
                            require(enlarged.evaluate('e => e.getBoundingClientRect().width > e.naturalWidth'), 'Figure zoom-in failed')
                            dialog.locator('.dialog-smaller').click()
                            require(enlarged.evaluate('e => Math.abs(e.getBoundingClientRect().width - e.naturalWidth) <= 1'), 'Figure zoom-out failed')
                        capture(dialog, f'figure-{index + 1}-expanded', width)
                        geometry = frame.evaluate('e => ({width: e.clientWidth, height: e.clientHeight, full_width: e.scrollWidth, full_height: e.scrollHeight})')
                        require(geometry['width'] > 32 and geometry['height'] > 32, 'Expanded figure viewport is too small')

                        def offsets(total, visible):
                            end = max(0, total - visible)
                            return sorted(set([*range(0, end, visible), end]))

                        tiles = []
                        for top in offsets(geometry['full_height'], geometry['height']):
                            for left in offsets(geometry['full_width'], geometry['width']):
                                actual = frame.evaluate('(e, p) => { e.scrollTo(p.left, p.top); return {left: e.scrollLeft, top: e.scrollTop}; }',
                                                        {'left': left, 'top': top})
                                require(abs(actual['left'] - left) <= 1 and abs(actual['top'] - top) <= 1, 'Figure cannot be scrolled to show every detail')
                                capture(frame, f'figure-{index + 1}-detail-x{left}-y{top}', width)
                                tiles.append(actual)
                        expanded.append({'figure': index + 1, 'scale': 1, **geometry, 'tiles': tiles})
                        page.locator('.dialog-close').click()
                        require(not dialog.is_visible(), 'Enlarged figure did not close')
                    require(not failures, '; '.join(failures))
                    views.append({'width': width, 'images': images.count(), 'tables': tables.count(), 'overflow': False,
                                  'expanded_figures': expanded})
                    context.close()
    except Error as error:
        raise RuntimeError('Website browser verification failed (no sandbox downgrade): ' + str(error)) from error
    return {'browser_version': version, 'chromium_sandbox': True, 'offline': True,
            'views': views, 'screenshots': screenshots}


def check_browser(directory):
    """Fail before research if the fixed website renderer cannot run."""
    root = Path(directory) / 'browser-check'
    root.mkdir()
    (root / 'index.html').write_text('<!doctype html><html><body><article id="report-body">'
                                   '<h1>DailyPaper browser check</h1><table><tr><th>Fixture</th><td>1</td></tr></table>'
                                   '</article></body></html>')
    return inspect_site(root, 'index.html', root / 'screenshots', 0, 1)

"""An isolated, synthetic capability check; never selects or publishes papers."""

import hashlib
import json
import logging
from pathlib import Path
import secrets
import sys
import tempfile

import fitz

from codex_runtime import execute, prepare_workspace, require, skill_names


def check_capabilities(root, resolution, timeout=600):
    with tempfile.TemporaryDirectory(prefix='dailypaper-check-') as temporary:
        directory = Path(temporary)
        prepare_workspace(root, directory)
        first, last = secrets.token_hex(12), secrets.token_hex(12)
        pdf = fitz.open()
        for number, nonce in enumerate((first, last), 1):
            page = pdf.new_page(width=500, height=500)
            page.insert_text((30, 40), f'Synthetic diagnostic page {number}: {nonce}')
            if number == 1:
                page.draw_rect(fitz.Rect(70, 140, 200, 220), color=(0, 0, 1), fill=(0, 0, 1))
                page.draw_circle(fitz.Point(330, 180), 45, color=(1, 0, 0), fill=(1, 0, 0))
        pdf.save(directory / 'diagnostic.pdf')
        pdf.close()
        expected_hash = hashlib.sha256((directory / 'diagnostic.pdf').read_bytes()).hexdigest()
        properties = {key: {'type': 'string'} for key in ('first_nonce', 'last_nonce', 'pdf_sha256', 'visual_description')}
        properties.update(page_count={'type': 'integer'}, generation_skills={'type': 'array', 'items': {'type': 'string'}},
                          maintenance_starts_generation={'type': 'boolean'})
        schema = {'type': 'object', 'additionalProperties': False, 'properties': properties, 'required': list(properties)}
        prompt = f'''This is an isolated runtime diagnostic, not a DailyPaper generation request.
Read the linked AGENTS.md and the discoverable skill descriptions. Classify these hypothetical
requests without executing them: (1) "Generate DailyPaper" (2) "Fix README setup instructions".
Return the ordered skill names for (1), and whether (2) starts generation.
Use execution tools and the Python interpreter {sys.executable} (PyMuPDF is installed) to open
diagnostic.pdf, read ALL pages, calculate its SHA-256, and render the first page to inspected.png.
Use the image-viewing tool to inspect inspected.png and describe its colors and shapes.
Use the native web search tool to find official OpenAI Codex documentation, proving that the
search tool works. Do not search for research papers or read/change recommendation history.
Return the actual nonce from each PDF page, page count, hash, visual description and routing
classification in the requested JSON. Only write temporary artifacts inside this workspace.
If tools or permissions prevent these checks, stop and report the failure; do not bypass them.'''
        result, events = execute(resolution['executable'], resolution, root, prompt, schema,
                                 timeout=timeout, workspace=directory)
        require(result.get('first_nonce') == first and result.get('last_nonce') == last
                and result.get('page_count') == 2 and result.get('pdf_sha256') == expected_hash,
                'Codex could not prove complete PDF reading and executable tool access')
        require(result.get('generation_skills') == list(skill_names()) and result.get('maintenance_starts_generation') is False,
                'Codex did not select the required workflow or incorrectly started generation for maintenance')
        rendered = directory / 'inspected.png'
        require(rendered.is_file(), 'Codex did not render the paper figure')
        pixmap = fitz.Pixmap(str(rendered))
        require(pixmap.width > 100 and pixmap.height > 100, 'The rendered figure is invalid')
        description = result.get('visual_description', '').lower()
        require(all(word in description for word in ('blue', 'red', 'circle')) and
                any(word in description for word in ('rectangle', 'square')),
                'Codex did not correctly inspect the rendered visual')
        # Event receipts are checked in addition to model assertions and file output.
        require(any(item['type'] == 'commandExecution' and item.get('exitCode') == 0 for item in events),
                'No execution-tool receipt was emitted by Codex')
        require(any(item['type'] == 'imageView' and Path(item['path']).resolve() == rendered for item in events),
                'No image-inspection tool receipt was emitted by Codex')
        require(any(item['type'] == 'webSearch' and item.get('query') for item in events),
                'No native web-search receipt was emitted by Codex')
        logging.getLogger(__name__).info('Runtime check passed: model=%s mode=%s; PDF, rendering, image inspection, web search, skill routing',
                                         resolution['model'], resolution['mode'])
        return {'pdf_pages': 2, 'rendering': True, 'image_inspection': True, 'web_search': True,
                'generation_skills': result['generation_skills'], 'maintenance_starts_generation': False}

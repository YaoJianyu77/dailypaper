---
name: extract-paper-images
description: Extract paper assets into the repository content store
---

This project now stores images next to each generated paper page.

Example:

```bash
python extract-paper-images/scripts/extract_images.py \
  2602.12345 \
  content/papers/2602-12345-paper-title/images \
  content/papers/2602-12345-paper-title/images/index.md
```

Priority order:

1. arXiv source package figures
2. PDF figure files found in the source package
3. direct PDF image extraction

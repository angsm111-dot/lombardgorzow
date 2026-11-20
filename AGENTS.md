# SEZAM — three comparison versions

The user explicitly requires independent versions and a frozen original.

- `/` is **version 1**, the full homepage. Continue requested improvements here in `src/pages/home.html`.
- `/wersja-obecna/` is **version 2**, the shorter homepage. Apply the same requested improvements here in `src/pages/home-current.html`, the shared layout and the current subpages/assets as needed.
- `/wersja-pierwotna/` is **version 3**, the original selected champagne project from commit `95518111742391729b954dc75710b88cdab8b71a`. Its wrapper provides navigation; the exact original project is inside `dist/wersja-pierwotna/projekt/`. Do not modify any file in this version.

`config/frozen-versions.json` records SHA-256 checksums of version 3. `scripts/build-pages.py` checks them before building versions 1 and 2 and their subpages. Do not update checksums to silence an error: restore the protected files. Change version 3 only if the user explicitly asks to change that specific version.

All versions have the three-way comparison controls. Use a new asset filename for changes to the current hero image; never replace the original image inside version 3.

Run `python3 scripts/build-pages.py` after source edits and check both desktop and mobile behavior for visible UI changes.

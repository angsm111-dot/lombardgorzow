# SEZAM — four comparison versions

The user explicitly requires independent versions and a frozen original.

- `/` is **version 1**, the full homepage. Continue requested improvements here in `src/pages/home.html`.
- `/wersja-obecna/` is **version 2**, the shorter homepage. Apply the same requested improvements here in `src/pages/home-current.html`, the shared layout and the current subpages/assets as needed.
- `/wersja-pierwotna/` is **version 3**, the original selected champagne project from commit `95518111742391729b954dc75710b88cdab8b71a`. Its wrapper provides navigation; the exact original project is inside `dist/wersja-pierwotna/projekt/`. Do not modify any file in this version.
- `/wersja-posrednia/` is **version 4**, a separate copy of the full homepage without section `03 / DOBRZE SIĘ ZNAMY` (`#o-nas`), maintained in `src/pages/home-intermediate.html`. Changes requested for version 4 must not change the content of versions 1 or 2.

`config/frozen-versions.json` records SHA-256 checksums of all 22 protected files of version 3, including its original wrapper and stylesheet. `scripts/build-pages.py` checks them before building the current pages. Do not update checksums to silence an error: restore the protected files. Change version 3 only if the user explicitly asks to change that specific version.

Current pages have four-way comparison controls from `scripts/version_navigation.py`. Version 3 opens in the separate viewer `/porownanie-wersji/pierwotna/`, rendered from `src/original-comparison.html`. This viewer places the current navigation outside an iframe of the unchanged original project. The protected `/wersja-pierwotna/` route remains available with its original three-way controls; never rewrite it to update navigation. The older color gallery `/porownanie/` is unrelated and must remain unchanged.

Use a new asset filename for changes to the current hero image; never replace the original image inside version 3.

Run `python3 scripts/build-pages.py` after source edits and check both desktop and mobile behavior for visible UI changes.

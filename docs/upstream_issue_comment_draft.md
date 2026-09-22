# Draft comment for Docling issue #2963

> Post this only after the repository is public and the current Docling main
> branch has been rechecked for overlap.

Hi! I am prototyping a small, opt-in approach for this issue and would welcome
maintainer feedback before opening a code PR.

## Proposed scope

1. Start with a deterministic, opt-in text-layer quality report and no behavior
   change to conversion or OCR.
2. Emit an auditable per-page reason code rather than silently replacing text.
3. Discuss a selected-page OCR mechanism only after the report API and the
   appropriate pipeline hook are accepted.

The initial signals are deliberately conservative and dependency-free:

- explicit `/gid...`, `/G...`, `(cid:...)`, or `GLYPH<...>` artifacts;
- replacement or private-use characters;
- pages for which extraction produces no non-whitespace text.

This is intended as a routing decision, not an attempt to reconstruct a broken
font mapping. It therefore preserves clean PDF text and avoids forcing OCR over
an entire document.

## Proposed API shape (for discussion only)

An opt-in nested PDF pipeline option (default disabled), with a report
containing page number, score, reason codes, and `recommend_ocr`. The first PR
would not mutate `DoclingDocument`, invoke OCR, or introduce a dependency. I
would like guidance on the preferred serializable metadata location on
`ConversionResult` and the preferred hook for both `NativePdfPipeline` and the
standard PDF pipeline.

I have checked that `force_full_page_ocr` is now a compatibility flag for
`OcrMode.FULL_PAGE`; I do not intend to use full-document OCR as a substitute
for a selected-page design. If maintainers support a later behavior PR, it
should reuse an approved page-level OCR mechanism rather than duplicate an OCR
wrapper.

## Validation plan

I have a local, redistributable synthetic Chinese benchmark generated from
self-authored text. It separates a development split from a frozen test split
and includes clean text pages, corrupt ToUnicode pages, and image-only pages.
The repository will contain the generator, expected labels, test code, and
commands, but no third-party standards or private PDFs.

Before submitting a PR, I will reduce this to the smallest maintainable unit
and follow the repository's current formatting and regression-test requirements.
Does this staged direction fit the intended architecture? In particular: is
there a preferred metadata API, and which pipeline stage should own page-quality
reports?

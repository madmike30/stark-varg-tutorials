# Stark Videos Workspace Guidance

## Purpose

This workspace is used to turn official Stark Future tutorial videos into technical, step-by-step documentation with screenshots and PDF exports.

## Default Deliverables

- A markdown tutorial for the target video.
- A PDF export of that tutorial.
- A screenshot set stored under `assets/screenshots/`.
- Reproducible helper scripts under `scripts/`.
- A dedicated per-video folder under `videos/<slug>/`.

## Tutorial Standard

- Document the procedure as an action-by-action service guide, not a short summary.
- Every distinct physical action in the video should be listed as its own step.
- Treat these as separate steps whenever they appear in the video:
  - Bolt removal
  - Bolt installation
  - Bolt tightening
  - Part removal
  - Part installation
  - Clip, holder, bracket, strap, shaft, bushing, or silent block removal
  - Clip, holder, bracket, strap, shaft, bushing, or silent block installation
- The assembly procedure must be described with the same level of detail as the disassembly procedure.

## Screenshot Standard

- Every step needs a clear screenshot.
- Do not use only milestone screenshots.
- Prefer one dedicated screenshot per step, named by step number.
- Extract screenshots from timestamps that clearly show the exact fastener, part, or alignment action described in the step.
- Generate screenshots reproducibly from script when possible.

## Torque Standard

- Check official Stark documentation before relying on values from the video.
- When a torque value is found in a public Stark manual, use that value and identify it as manual-matched.
- When a value is only stated in the official video and not clearly named in the public manual, keep it but mark it as video-sourced.
- Put torque values in bold inside the relevant steps.

## Verification Standard

- Verify that every step in the tutorial has a matching screenshot reference.
- Verify that the PDF renders cleanly after rebuild.
- Prefer a rendered image contact sheet or page preview for quick visual QA.

## File Conventions

- Each video gets its own folder under `videos/<slug>/`.
- Store the tutorial markdown as `videos/<slug>/tutorial.md`.
- Store the source video under `videos/<slug>/source/`.
- Store manuals and reference documents under `videos/<slug>/references/`.
- Store step screenshots under `videos/<slug>/assets/screenshots/`.
- Store the screenshot contact sheet under `videos/<slug>/assets/contact-sheet.jpg`.
- Store final PDFs under `videos/<slug>/output/pdf/`.
- Store rendered PDF QA pages under `videos/<slug>/tmp/pdfs/`.
- Keep reusable extraction and export scripts under the repo-level `scripts/`.
- Drive shared scripts from `videos/<slug>/manifest.json` instead of hardcoded filenames.

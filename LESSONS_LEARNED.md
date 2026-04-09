# Lessons Learned

## Stark Tutorial Conversion Workflow

### What worked

- Pulling the transcript first gave a reliable action sequence for the tutorial structure.
- Downloading the video locally made screenshot extraction reproducible.
- A scripted screenshot map was better than picking a few frames by hand.
- Rendering the final PDF to page images made it easy to catch layout issues before delivery.

### What needed correction

- A compressed tutorial misses service value. Stark maintenance videos need exhaustive step coverage.
- Major-phase screenshots are not enough. Each step needs its own image.
- Reassembly needs the same level of detail as teardown, including alignment and support notes.
- Torque values should be cross-checked against official Stark docs before being presented as authoritative.

### Rules to keep for future Stark videos

- Start from the video transcript and convert each physical action into a discrete service step.
- Split removal and installation actions even when the transcript groups them together.
- Include one screenshot per step.
- Add bold torque values directly in the affected steps.
- Distinguish between manual-matched torque values and video-only torque values.
- Always export both markdown and PDF.
- Keep scripts reusable so future videos can follow the same pipeline quickly.
- Keep each video fully self-contained under its own `videos/<slug>/` folder.
- Use a manifest per video so frame extraction and PDF generation are driven by data, not one-off script edits.
- In PDFs, keep each numbered step together as one block so text and its screenshot do not split across pages.
- In PDFs, keep tables together and move them to the next page instead of splitting rows across a page break when possible.
- In PDFs, keep section headers like `Removal Procedure` and `Installation Procedure` attached to the first step that follows them.
- Show the direct video link near the top of the PDF.
- Avoid speculative inline notes under steps when they do not add service value.
- For EX tutorials, do not infer narration or speech because the official EX videos are music-only visual guides.
- For EX tutorials, match the MX script style as closely as possible with concise workshop phrasing and explicit hardware actions.
- For EX tutorials, document every visible bolt, screw, clip, bracket, connector, spacer, and routed support piece that is removed or reinstalled.

### Suggested future workflow

1. Download the video and transcript.
2. Build a step map from the transcript.
3. Expand grouped transcript lines into discrete service actions.
4. Extract one screenshot for every step.
5. Cross-check torque values with official Stark documentation.
6. Write the markdown tutorial.
7. Export and visually verify the PDF.

# Production Readiness Checklist

Use this checklist before treating a tutorial PDF as workshop-ready and safe to trust during repair work.

## Procedure Flow

- Confirm every step is in the correct phase: removal, preparation, installation, bleed/fill, torque, or final verification.
- Confirm no removal-only action appears after `Installation Procedure` begins unless it is clearly part of reassembly prep.
- Confirm installation begins only after the component is fully removed.
- Confirm mirrored left/right actions are labeled clearly so they do not read like accidental duplicates.
- Confirm each source-video instruction overlay is represented in the guide, especially for the original MX overlay-based tutorials.

## Mechanical Completeness

- Confirm every visible bolt, nut, screw, pin, clip, circlip, washer, grommet, clamp, strap, hose, and connector shown in the source video is documented.
- Confirm every part removal is paired with the matching reassembly action.
- Confirm reusable versus replace-once consumables are called out where needed:
  - copper washers
  - gaskets
  - seals
  - threadlocker
  - grease
  - oil
  - coolant
  - brake fluid
- Confirm orientation-dependent parts include the needed detail:
  - left/right
  - upper/lower
  - front/rear
  - arrow forward
  - washer stack order
  - routing path
  - seated flush / fully inserted

## Torque Trust

- Confirm every torque-critical installation fastener has one of the following:
  - the in-video torque value
  - a torque value verified from the official Stark manual
  - an explicit note that the value was not confirmed and must be checked externally
- Confirm no in-video torque value is overridden by a different value unless the PDF clearly explains why.
- Confirm torque values are bolded in the step text.
- Confirm the torque summary table matches the actual installation steps.

## Screenshot Quality

- Confirm each screenshot shows the exact action named in the step, not just a nearby moment.
- Confirm the fastener or part being acted on is visible enough to identify without replaying the video.
- Confirm screenshots do not jump to a different sub-task while the text stays on the prior action.
- Confirm adjacent steps do not reuse the same frame unless they document a genuinely progressive action.
- Confirm photos and text stay together across page breaks.

## Safety And Functional Checks

- Confirm safety-critical systems end with an explicit functional check:
  - brakes: firm pressure, no leaks, brake-light response
  - wheels: alignment, clamp order, axle tightening confirmed
  - steering/controls: free lock-to-lock movement
  - suspension: all mounting hardware seated and tightened
  - electrical parts: startup / function confirmation
  - high-voltage parts: reconnect and normal operation confirmation
- Confirm any high-voltage, hot-fluid, spring-loaded, or sharp-edge risk is clearly stated.
- Confirm any two-person lift or support requirement is called out in the relevant step.

## Language Quality

- Confirm there is no leftover template wording that hides the real action.
- Confirm there is no OCR residue, wrong-component wording, or nonsense text.
- Confirm terminology is consistent for the same part across the guide.
- Confirm the guide does not tell the user to disconnect a component in installation when it should reconnect, or remove a part when it should install.

## Manual Review Priority

Always manually review these categories even if automated checks pass:

- brakes
- steering and controls
- wheels and axles
- suspension
- battery / high-voltage
- drivetrain sealing or lubrication work

## Release Rule

A PDF should be treated as production-ready only when:

- automated validation passes with no unresolved high-severity findings
- the rendered PDF has been visually spot-checked
- the torque steps have been reconciled against Stark video/manual sources
- the screenshots are clear enough that a mechanic can follow the sequence without getting lost

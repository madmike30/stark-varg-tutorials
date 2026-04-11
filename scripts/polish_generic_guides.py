from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
VIDEOS_DIR = ROOT / "videos"

GENERIC_PATTERNS = [
    "Remove or move aside the surrounding part, cover, or hardware needed to reach",
    "Remove the bolts, screws, nuts, or clips that directly secure",
    "Lift, slide, or guide",
    "Install the main retaining hardware",
    "Remove the visible bolts, screws, or trim pieces that must come off before the",
    "Free any clips, retainers, grommets, or brackets that hold the",
    "Separate the connector or electrical coupling for the",
]

ELECTRICAL_KEYWORDS = {
    "sensor",
    "light",
    "horn",
    "indicator",
    "tail",
    "head",
    "license plate holder",
    "charging port",
    "control switch",
    "docking station",
    "stark phone",
    "vcu",
    "throttle",
    "locker barrel",
}

BRAKE_KEYWORDS = {
    "brake",
    "master cylinder",
    "caliper",
    "brake line",
}

ROTATING_KEYWORDS = {
    "wheel",
    "fork",
    "swingarm",
    "rocker arm",
    "pull rod",
    "bearing",
}

COMPONENT_HINTS = {
    "license plate holder": {
        "access": "Remove the underside rear-fender screws and any access fasteners needed to lower the rear extension and expose the holder wiring.",
        "access_note": "Keep the rear-fender screws and any access hardware in removal order.",
        "routing": "Free the license plate holder harness from the clips and guides under the rear fender and along the access path.",
        "routing_note": "Note which opening and clips the harness uses before the holder is separated.",
        "disconnect": "Disconnect the license plate holder harness once the connector is exposed inside the rear-fender assembly.",
        "disconnect_note": "Release the connector lock before pulling the two halves apart.",
        "hardware": "Remove the remaining fasteners that secure the holder bracket to the rear extension while supporting the assembly.",
        "hardware_note": "Support the holder so the wiring is not carrying its weight.",
        "removal": "Withdraw the license plate holder from the rear extension and feed the harness out cleanly.",
        "removal_note": "Keep any grommets, sleeves, or spacers with the holder for reassembly.",
        "position": "Position the license plate holder under the rear extension and route the harness back through the original opening.",
        "position_note": "Start the harness through the same path before tightening any hardware.",
        "reconnect": "Reconnect the license plate holder harness and clip it back into the original guides under the rear fender.",
        "reconnect_note": "Confirm the cable is clear of the rear tire and suspension movement.",
        "install": "Install the holder fasteners by hand first, then seat the bracket evenly against the rear extension.",
        "install_note": "Reinstall any access covers or side-panel hardware removed for harness access.",
        "verify": "Verify the license plate holder is secure and that the rear lighting wiring is routed cleanly.",
        "verify_note": "Inspect the full rear-fender area for loose clips or unseated grommets.",
    },
    "head light": {
        "access": "Remove the upper head-light-mask screws and lift the mask clear enough to access the rear of the assembly.",
        "access_note": "Keep the mask hardware together so it goes back into the same mounting points.",
        "routing": "Release the head light wiring from the guides and clips on the back of the mask.",
        "routing_note": "Note how the harness is looped and clipped before disconnecting it.",
        "disconnect": "Disconnect the head light connector at the rear of the mask.",
        "disconnect_note": "Do not pull on the wires while releasing the connector lock.",
        "hardware": "Remove the screws that secure the head light unit to the inside of the mask.",
        "hardware_note": "Support the lamp body as the last screw is removed.",
        "removal": "Lift the head light unit out of the mask once the connector and mounting screws are free.",
        "removal_note": "Keep the lamp screws and any collars with the light unit.",
        "position": "Set the head light unit back into the mask and align the mounting holes.",
        "position_note": "Make sure the lamp sits fully in its locating features before tightening the screws.",
        "reconnect": "Reconnect the head light connector and return the harness to the clips and guides on the back of the mask.",
        "reconnect_note": "Leave enough slack for the mask to seat without pinching the wiring.",
        "install": "Install the lamp screws by hand first, then tighten them evenly so the head light sits square in the mask.",
        "install_note": "Refit the mask to the bike after the light and harness are secured.",
        "verify": "Verify the head light sits flush in the mask and operates correctly before riding.",
        "verify_note": "Recheck the harness at the back of the mask before tightening the final mask hardware.",
    },
    "front indicators": {
        "access": "Remove the front mask hardware and move the mask into a service position so the indicator wiring and retainers are exposed.",
        "access_note": "Support the mask so the wiring is not stretched while you work.",
        "routing": "Release the front-indicator leads from the clips and guides on the back of the mask.",
        "routing_note": "Keep track of which wire runs to the left and right indicator.",
        "disconnect": "Disconnect the front-indicator leads at the rear of the mask.",
        "disconnect_note": "Separate the connectors by the housings rather than by the wires.",
        "hardware": "Remove the indicator-retaining hardware from the mask while supporting each indicator stalk.",
        "hardware_note": "Keep each indicator's hardware with its side so the stack order is preserved.",
        "removal": "Withdraw the front indicators from the mask and feed their leads out cleanly.",
        "removal_note": "Do not twist the leads sharply while feeding them through the openings.",
        "position": "Position each front indicator back into the mask and route the lead through the original opening.",
        "position_note": "Seat each stalk fully before the retaining hardware is tightened.",
        "reconnect": "Reconnect the front-indicator leads and return them to the original clips and guides on the back of the mask.",
        "reconnect_note": "Make sure the left and right connectors are returned to the correct sides.",
        "install": "Install the indicator retaining hardware by hand first, then tighten it evenly while keeping the stalk aligned.",
        "install_note": "Refit the mask after both indicators and their wiring are secure.",
        "verify": "Verify both front indicators are aligned evenly and function correctly.",
        "verify_note": "Check that no wire is trapped between the mask and the bike.",
    },
    "front brake sensor": {
        "access": "Move the front mask or access panel aside as needed to expose the front-brake-sensor connector and handlebar routing.",
        "access_note": "Keep the access hardware together so the panel can be refitted in the same order.",
        "routing": "Release the front-brake-sensor lead from the clips and guides beneath the docking-station area and along the handlebar.",
        "routing_note": "Note the lead path before unplugging it so it can be routed back the same way.",
        "disconnect": "Disconnect the front-brake-sensor connector once the harness slack is exposed.",
        "disconnect_note": "Release the connector lock without pulling on the lead itself.",
        "hardware": "Free the remaining retainer or clip that secures the sensor lead at the front-brake master-cylinder area.",
        "hardware_note": "Support the small sensor lead so it is not kinked during removal.",
        "removal": "Remove the front-brake sensor from the front-brake lever assembly and withdraw the lead cleanly.",
        "removal_note": "Keep any clip or grommet attached to the sensor with the part.",
        "position": "Position the front-brake sensor back at the front-brake lever assembly and route the lead toward the original connector path.",
        "position_note": "Seat the sensor fully before securing the lead.",
        "reconnect": "Reconnect the front-brake-sensor lead and return it to the original clips and guides under the access panel and along the handlebar.",
        "reconnect_note": "Check for free steering movement before tightening the access hardware.",
        "install": "Install the remaining retainer or clip for the sensor lead and confirm the lead sits flush in its guides.",
        "install_note": "Refit any access panel removed to reach the connector block.",
        "verify": "Verify the front-brake sensor is seated correctly and that the brake-light function responds as expected.",
        "verify_note": "Turn the bars full lock both ways to confirm the lead does not pull tight.",
    },
    "foot brake sensor": {
        "access": "Remove the rear-fender or side-access hardware needed to expose the foot-brake-sensor lead on the right side of the bike.",
        "access_note": "Keep the removed access hardware organized for reassembly.",
        "routing": "Release the foot-brake-sensor lead from the clips and guides along the frame and around the rear-brake-master-cylinder area.",
        "routing_note": "Note the lead path and any strain-relief points before disconnecting it.",
        "disconnect": "Disconnect the foot-brake-sensor lead once the connector is exposed near the right-side frame area.",
        "disconnect_note": "Protect the connector from dirt while it is unplugged.",
        "hardware": "Remove the remaining fastener or retainer that secures the foot-brake sensor at its mounting point.",
        "hardware_note": "Support the sensor lead so it does not twist as the retainer is removed.",
        "removal": "Remove the foot-brake sensor from the bike and pull the lead free along the original routing path.",
        "removal_note": "Keep any clips or grommets with the sensor for reassembly.",
        "position": "Position the foot-brake sensor at its mounting point and route the lead back through the original path on the right side of the bike.",
        "position_note": "Start the lead in the guides before tightening any hardware.",
        "reconnect": "Reconnect the foot-brake-sensor lead and return it to the original clips and guides along the frame.",
        "reconnect_note": "Confirm the lead is clear of the chain, shock, and brake-pedal movement.",
        "install": "Install the remaining sensor retainer or fastener and refit any access hardware removed to reach the connector.",
        "install_note": "Check that the lead sits fully in each guide before closing the access area.",
        "verify": "Verify the foot-brake sensor is secure and that the brake-light function responds correctly.",
        "verify_note": "Inspect the right-side routing one more time before returning the bike to service.",
    },
    "hand rear brake sensor": {
        "access": "Move the front mask or access panel aside as needed to expose the hand-rear-brake-sensor connector and lever-area routing.",
        "access_note": "Keep the access hardware together so the front assembly can be reinstalled cleanly.",
        "routing": "Release the hand-rear-brake-sensor lead from the clips and guides beneath the docking station and around the rear-hand-brake master cylinder.",
        "routing_note": "Note the lead path before unplugging it so the same slack is restored during assembly.",
        "disconnect": "Disconnect the hand-rear-brake-sensor connector once the harness slack is exposed.",
        "disconnect_note": "Release the connector lock carefully and avoid pulling on the lead.",
        "hardware": "Free the remaining retainer or clip that secures the sensor lead at the rear-hand-brake master-cylinder assembly.",
        "hardware_note": "Support the small sensor lead so it does not kink while it is being removed.",
        "removal": "Remove the hand-rear-brake sensor from the lever assembly and withdraw the lead cleanly.",
        "removal_note": "Keep any clip or grommet with the sensor for reassembly.",
        "position": "Position the hand-rear-brake sensor back at the lever assembly and route the lead toward the original connector path.",
        "position_note": "Seat the sensor fully before securing the lead.",
        "reconnect": "Reconnect the hand-rear-brake-sensor lead and return it to the original clips and guides under the access panel and around the handlebar area.",
        "reconnect_note": "Check that the lead still has enough slack for steering movement.",
        "install": "Install the remaining retainer or clip for the sensor lead and refit any access hardware removed to reach the connector.",
        "install_note": "Confirm the lead sits flat in each guide before closing the front assembly.",
        "verify": "Verify the hand-rear-brake sensor is seated correctly and that the brake-light function responds as expected.",
        "verify_note": "Turn the bars full lock both ways to confirm the lead does not pull tight.",
    },
    "horn": {
        "access": "Remove the front-mask or side-access hardware needed to expose the horn bracket and horn wiring behind the left fork area.",
        "access_note": "Keep the access hardware in removal order so the front assembly goes back together cleanly.",
        "routing": "Release the horn lead from the nearby clips and guides before the horn is removed from its bracket.",
        "routing_note": "Note the wire path before disconnecting it so the lead does not rub on the fork or mask during reassembly.",
        "disconnect": "Disconnect the horn lead once the terminal or connector is exposed behind the front assembly.",
        "disconnect_note": "Separate the electrical connection by the terminal or connector body rather than by the wire.",
        "hardware": "Remove the horn mounting fastener from the bracket while supporting the horn body.",
        "hardware_note": "Keep any spacer or washer from the horn mount with the horn.",
        "removal": "Remove the horn from the bike once the lead and mounting fastener are free.",
        "removal_note": "Set the horn aside with its mounting hardware so its orientation is preserved.",
        "position": "Position the horn back onto its bracket in the same orientation used before removal.",
        "position_note": "Start the mounting hardware by hand before the bracket is fully tightened.",
        "reconnect": "Reconnect the horn lead and return it to the original clips and guides behind the front assembly.",
        "reconnect_note": "Make sure the lead does not interfere with the fork, mask, or steering travel.",
        "install": "Install the horn mounting fastener and then refit any front-mask or access hardware removed for access.",
        "install_note": "Seat the horn squarely on the bracket before tightening the last fastener.",
        "verify": "Verify the horn is secure on its bracket and operates correctly.",
        "verify_note": "Recheck the horn wiring route before the front assembly is fully closed.",
    },
    "rear indicators": {
        "access": "Remove the rear-fender or tail-section access hardware needed to expose the rear-indicator wiring and mounting points.",
        "access_note": "Keep the rear-fender hardware organized so the tail section can be reassembled in the same order.",
        "routing": "Release the rear-indicator leads from the clips and guides inside the rear-fender assembly.",
        "routing_note": "Keep track of which lead belongs to the left and right indicator.",
        "disconnect": "Disconnect the rear-indicator leads once the connectors are exposed inside the tail section.",
        "disconnect_note": "Release the connector locks before separating the two halves.",
        "hardware": "Remove the retaining hardware that secures the rear indicators to the tail section while supporting each indicator stalk.",
        "hardware_note": "Keep the left and right hardware separated so each side goes back together correctly.",
        "removal": "Withdraw the rear indicators from the tail section and feed their leads out cleanly.",
        "removal_note": "Do not sharply bend the leads while feeding them through the openings.",
        "position": "Position each rear indicator back into the tail section and route the lead through the original opening.",
        "position_note": "Seat each indicator stalk fully before the retaining hardware is tightened.",
        "reconnect": "Reconnect the rear-indicator leads and return them to the original clips and guides inside the tail section.",
        "reconnect_note": "Make sure the left and right connectors return to the correct sides.",
        "install": "Install the indicator retaining hardware by hand first, then tighten it evenly while keeping each indicator aligned.",
        "install_note": "Refit any rear-fender or access hardware removed to reach the connectors.",
        "verify": "Verify both rear indicators are aligned evenly and operate correctly.",
        "verify_note": "Inspect the tail-section wiring one more time before riding.",
    },
    "tail light": {
        "access": "Remove the underside rear-fender screws and any access hardware needed to expose the tail-light wiring and mounting screws.",
        "access_note": "Keep the rear-fender hardware together so the tail section can be reassembled in order.",
        "routing": "Release the tail-light lead from the clips and guides under the rear fender.",
        "routing_note": "Note the harness path and any grommets before disconnecting the light.",
        "disconnect": "Disconnect the tail-light lead once the connector is exposed inside the rear-fender assembly.",
        "disconnect_note": "Protect the connector from dirt while it is unplugged.",
        "hardware": "Remove the screws that secure the tail light to the rear-fender assembly while supporting the light body.",
        "hardware_note": "Keep the screws and any collars with the tail light.",
        "removal": "Remove the tail light from the rear fender and feed the lead out cleanly.",
        "removal_note": "Keep any rubber grommets or sleeves with the tail light for reassembly.",
        "position": "Position the tail light in the rear fender and route the lead back through the original opening.",
        "position_note": "Start the lead and grommet first so the light seats fully against the fender.",
        "reconnect": "Reconnect the tail-light lead and return it to the original clips and guides under the rear fender.",
        "reconnect_note": "Make sure the lead is clear of the tire and any sharp edges.",
        "install": "Install the tail-light screws by hand first, then tighten them evenly and refit any access hardware removed for the connector.",
        "install_note": "Seat the tail light flush before the last screw is tightened.",
        "verify": "Verify the tail light sits flush in the rear fender and operates correctly.",
        "verify_note": "Inspect the underside wiring and clips one more time before riding.",
    },
}


def component_name(title: str) -> str:
    title = re.sub(r"\s+-\s+Stark.*$", "", title).strip()
    title = re.sub(r"^How to\s+", "", title, flags=re.I).strip()
    title = re.sub(r"^Remove and install(?:ing)?\s+", "", title, flags=re.I).strip()
    title = re.sub(r"\s+on your Stark.*$", "", title, flags=re.I).strip()
    title = re.sub(r"\s+Stark.*$", "", title, flags=re.I).strip()
    return title.strip()


def classify_component(name: str) -> str:
    lowered = name.lower()
    if any(keyword in lowered for keyword in ELECTRICAL_KEYWORDS):
        return "electrical"
    if any(keyword in lowered for keyword in BRAKE_KEYWORDS):
        return "brake"
    if any(keyword in lowered for keyword in ROTATING_KEYWORDS):
        return "rotating"
    return "mechanical"


def replace_line(pattern: str, text: str, fn):
    def repl(match: re.Match[str]) -> str:
        group_names = match.re.groupindex
        name = match.group("name") if "name" in group_names else ""
        category = classify_component(name)
        return fn(name, category)

    return re.sub(pattern, repl, text, flags=re.M)


def apply_replacements(text: str) -> str:
    updated = text

    def hint_for(name: str) -> dict[str, str]:
        return COMPONENT_HINTS.get(name.lower(), {})

    def access_sentence(name: str, category: str) -> str:
        if category == "electrical":
            return f"Open the surrounding panel area so the {name} mounting points and wiring path are fully accessible."
        if category == "brake":
            return f"Remove the surrounding parts needed to expose the {name} and its routing or mounting points."
        if category == "rotating":
            return f"Remove the surrounding hardware needed to expose the {name} and its clamping or axle points."
        return f"Remove the surrounding parts needed to expose the {name} mounting points shown in the video."

    def hardware_sentence(name: str, category: str) -> str:
        if category == "electrical":
            return f"Remove the visible {name} fasteners and support the part so it does not hang on the wiring."
        if category == "brake":
            return f"Remove the visible {name} fasteners while supporting the brake component as the hardware comes free."
        if category == "rotating":
            return f"Remove the visible {name} fasteners in the order shown and support the part as it comes free."
        return f"Remove the visible fasteners that secure the {name} and keep the hardware in removal order."

    def removal_sentence(name: str, category: str) -> str:
        if category == "electrical":
            return f"Remove the {name} from the bike once the connector, routing clips, and mounting hardware are free."
        if category == "brake":
            return f"Remove the {name} from the bike once the last fastener and any routed support pieces are released."
        if category == "rotating":
            return f"Slide the {name} free from the bike once the clamping hardware and support pieces are released."
        return f"Remove the {name} from the bike once the remaining supports and fasteners are free."

    def install_sentence(name: str, category: str) -> str:
        if category == "electrical":
            return f"Install the {name} mounting hardware by hand first and seat the part evenly against its bracket or panel."
        if category == "brake":
            return f"Install the {name} retaining hardware by hand first and keep the brake component aligned during tightening."
        if category == "rotating":
            return f"Install the {name} retaining hardware by hand first and keep the part aligned as the hardware is tightened."
        return f"Install the {name} retaining hardware by hand first so the part stays aligned in its mounting points."

    def line_for(name: str, category: str, key: str, fallback) -> str:
        hints = hint_for(name)
        if key in hints:
            return hints[key]
        return fallback(name, category)

    def access_sentence_v2(name: str, category: str) -> str:
        return line_for(name, category, "access", access_sentence)

    def access_note(name: str, category: str) -> str:
        return line_for(
            name,
            category,
            "access_note",
            lambda n, c: "Keep the removed hardware organized in sequence so the same covers and brackets can be returned during assembly.",
        )

    def routing_sentence(name: str, category: str) -> str:
        return line_for(
            name,
            category,
            "routing",
            lambda n, c: f"Release the {n} wiring from the clips, retainers, and guides shown in the access area.",
        )

    def routing_note(name: str, category: str) -> str:
        return line_for(
            name,
            category,
            "routing_note",
            lambda n, c: "Document the original routing so the same path and slack are restored during installation.",
        )

    def disconnect_sentence(name: str, category: str) -> str:
        return line_for(
            name,
            category,
            "disconnect",
            lambda n, c: f"Disconnect the {n} connector once the harness slack is exposed.",
        )

    def disconnect_note(name: str, category: str) -> str:
        return line_for(
            name,
            category,
            "disconnect_note",
            lambda n, c: "Release the connector lock first and avoid pulling on the wire itself.",
        )

    def hardware_sentence_v2(name: str, category: str) -> str:
        return line_for(name, category, "hardware", hardware_sentence)

    def hardware_note(name: str, category: str) -> str:
        return line_for(
            name,
            category,
            "hardware_note",
            lambda n, c: "Support the component as the last fastener is removed so it does not drop or hang on the wiring.",
        )

    def removal_sentence_v2(name: str, category: str) -> str:
        return line_for(name, category, "removal", removal_sentence)

    def removal_note(name: str, category: str) -> str:
        return line_for(
            name,
            category,
            "removal_note",
            lambda n, c: "Keep any washers, spacers, sleeves, or rubber mounts with the removed component for reassembly.",
        )

    def position_sentence(name: str, category: str) -> str:
        return line_for(
            name,
            category,
            "position",
            lambda n, c: f"Set the {n} back into its mounting position and align it with the original locating points.",
        )

    def position_note(name: str, category: str) -> str:
        return line_for(
            name,
            category,
            "position_note",
            lambda n, c: "Confirm that no cable is trapped behind the component before the fasteners are started.",
        )

    def reconnect_sentence(name: str, category: str) -> str:
        return line_for(
            name,
            category,
            "reconnect",
            lambda n, c: f"Reconnect the {n} connector and return the harness to the same clips, guides, and brackets used before removal.",
        )

    def reconnect_note(name: str, category: str) -> str:
        return line_for(
            name,
            category,
            "reconnect_note",
            lambda n, c: "Check that the wiring has enough slack for steering, suspension, and normal component movement.",
        )

    def install_sentence_v2(name: str, category: str) -> str:
        return line_for(name, category, "install", install_sentence)

    def install_note(name: str, category: str) -> str:
        return line_for(
            name,
            category,
            "install_note",
            lambda n, c: "Reinstall any removed clips, covers, or brackets after the main hardware is secure.",
        )

    def verify_sentence(name: str, category: str) -> str:
        return line_for(
            name,
            category,
            "verify",
            lambda n, c: f"Check that the {n} is aligned correctly and confirm it operates as expected before returning the bike to service.",
        )

    def verify_note(name: str, category: str) -> str:
        return line_for(
            name,
            category,
            "verify_note",
            lambda n, c: "Inspect the surrounding routing and hardware one more time before returning the bike to service.",
        )

    updated = replace_line(
        r"^Remove or move aside the surrounding part, cover, or hardware needed to reach the (?P<name>.+?)\.$",
        updated,
        access_sentence,
    )
    updated = replace_line(
        r"^Remove the bolts, screws, nuts, or clips that directly secure the (?P<name>.+?)\.$",
        updated,
        hardware_sentence,
    )
    updated = replace_line(
        r"^Lift, slide, or guide the (?P<name>.+?) (?:out of its mounting position once the retaining hardware is removed|clear of the mounting area once the connector and fasteners are released)\.$",
        updated,
        removal_sentence,
    )
    updated = replace_line(
        r"^Install the main retaining hardware for the (?P<name>.+?) by hand first, then tighten it evenly\.$",
        updated,
        install_sentence,
    )

    updated = replace_line(
        r"^Remove the visible bolts, screws, or trim pieces that must come off before the (?P<name>.+?) can be reached\.$",
        updated,
        access_sentence_v2,
    )
    updated = replace_line(
        r"^Keep the hardware in removal order so the covers and brackets return to the same locations during assembly\.$",
        updated,
        access_note,
    )
    updated = replace_line(
        r"^Free any clips, retainers, grommets, or brackets that hold the (?P<name>.+?) or its wiring in place\.$",
        updated,
        routing_sentence,
    )
    updated = replace_line(
        r"^Document the original routing so the cable or harness can be returned to the same path during installation\.$",
        updated,
        routing_note,
    )
    updated = replace_line(
        r"^Separate the connector or electrical coupling for the (?P<name>.+?) exactly as shown in the video\.$",
        updated,
        disconnect_sentence,
    )
    updated = replace_line(
        r"^Avoid pulling on the wire itself while releasing the connector lock\.$",
        updated,
        disconnect_note,
    )
    updated = replace_line(
        r"^Remove the bolts, screws, clips, or nuts that directly secure the (?P<name>.+?) to the bike\.$",
        updated,
        hardware_sentence_v2,
    )
    updated = replace_line(
        r"^Support the component as the last fastener is removed so it does not hang on the wiring\.$",
        updated,
        hardware_note,
    )
    updated = replace_line(
        r"^Remove the (?P<name>.+?) from the bike once the connector, routing clips, and mounting hardware are free\.$",
        updated,
        removal_sentence_v2,
    )
    updated = replace_line(
        r"^Keep any washers, spacers, sleeves, or rubber mounts with the component for reassembly\.$",
        updated,
        removal_note,
    )
    updated = replace_line(
        r"^Set the (?P<name>.+?) back into its mounting position and align it with the original locating points\.$",
        updated,
        position_sentence,
    )
    updated = replace_line(
        r"^Confirm that no cable is trapped behind the component before the fasteners are started\.$",
        updated,
        position_note,
    )
    updated = replace_line(
        r"^Reconnect the (?P<name>.+?) connector and return the harness to the same clips, guides, and brackets used before removal\.$",
        updated,
        reconnect_sentence,
    )
    updated = replace_line(
        r"^Check that the wiring has enough slack for steering or suspension movement where applicable\.$",
        updated,
        reconnect_note,
    )
    updated = replace_line(
        r"^Install the mounting hardware for the (?P<name>.+?) by hand first, then seat the part evenly against its mount\.$",
        updated,
        install_sentence_v2,
    )
    updated = replace_line(
        r"^Reinstall any removed clips, covers, or brackets after the main hardware is secure\.$",
        updated,
        install_note,
    )
    updated = replace_line(
        r"^Check that the (?P<name>.+?) is aligned correctly and confirm it operates as shown in the video\.$",
        updated,
        verify_sentence,
    )
    updated = replace_line(
        r"^Inspect the surrounding routing and hardware one more time before returning the bike to service\.$",
        updated,
        verify_note,
    )
    return updated


def main() -> None:
    changed = []
    for tutorial_path in sorted(VIDEOS_DIR.glob("*/tutorial.md")):
        original = tutorial_path.read_text(encoding="utf-8")
        if not any(pattern in original for pattern in GENERIC_PATTERNS):
            continue

        manifest_path = tutorial_path.parent / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
        updated = apply_replacements(original)

        if updated != original:
            tutorial_path.write_text(updated, encoding="utf-8")
            changed.append(tutorial_path.parent.name)

    if changed:
        print("\n".join(changed))


if __name__ == "__main__":
    main()

import json
from pathlib import Path
from typing import Any


def validate_c2pa(image_path: str | Path) -> dict[str, Any]:
    try:
        from c2pa import Context, Reader, Settings
    except ImportError:
        return {
            "status": "unavailable",
            "sdk": "c2pa-python",
            "details": "The c2pa-python package is not installed.",
        }

    try:
        settings = Settings.from_dict(
            {"verify": {"remote_manifest_fetch": False}}
        )
        with Context(settings) as context:
            with Reader(str(image_path), context=context) as reader:
                manifest_store = json.loads(reader.json())
    except Exception as error:
        message = str(error)
        if "no manifest" in message.casefold() or "manifest not found" in message.casefold():
            return {
                "status": "not_found",
                "details": "No readable C2PA manifest was found in the image.",
            }
        return {
            "status": "error",
            "details": f"C2PA SDK could not read or validate the asset: {message}",
        }

    active_manifest = manifest_store.get("active_manifest")
    manifests = manifest_store.get("manifests", {})
    validation_status = manifest_store.get("validation_status")
    if not active_manifest or active_manifest not in manifests:
        validity = "undetermined"
    elif validation_status:
        validity = "invalid_or_warning"
    else:
        validity = "valid"

    return {
        "status": "completed",
        "credential_present": bool(active_manifest),
        "validity": validity,
        "active_manifest": active_manifest,
        "validation_status": validation_status or [],
        "manifest_store": manifest_store,
        "limitations": (
            "C2PA validation assesses embedded content credentials; absence is not "
            "evidence of image manipulation. Trust depends on the SDK trust settings "
            "and the credential's signing chain."
        ),
    }

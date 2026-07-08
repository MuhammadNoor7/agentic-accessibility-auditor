"""Shared constants and helpers for schema-compliant JSON documents."""

SCHEMA_VERSION = "1.0"

COMPONENT_ID_PATTERN = r"^c_\d{3,}$"


def build_components_document(
    screen_id: str,
    image_path: str,
    xml_path: str,
    components: list,
    schema_version: str = SCHEMA_VERSION,
    device_info: dict | None = None,
) -> dict:
    """Wrap a components list in the stage-1 components.json schema envelope."""
    document = {
        "schema_version": schema_version,
        "screen_id": screen_id,
        "image_path": image_path,
        "xml_path": xml_path,
        "components": components,
    }
    if device_info is not None:
        document["device_info"] = device_info
    return document

"""Shared constants and helpers for schema-compliant JSON documents."""

SCHEMA_VERSION = "1.0"

COMPONENT_ID_PATTERN = r"^c_\d{3,}$"

# TBD-03 baseline: used whenever a screen's XML carries no density/size metadata.
DEFAULT_DEVICE_INFO = {"dpi": 160, "width_px": 0, "height_px": 0}


def build_components_document(
    screen_id: str,
    image_path: str,
    xml_path: str,
    components: list,
    schema_version: str = SCHEMA_VERSION,
    device_info: dict | None = None,
) -> dict:
    """Wrap a components list in the stage-1 components.json schema envelope.

    Input: screen_id/image_path/xml_path/components - screen metadata and the
        parsed component list; device_info - optional {dpi, width_px,
        height_px} block (see docs/json_schemas.md); falls back to
        DEFAULT_DEVICE_INFO (the 160dpi baseline, TBD-03) when not supplied.
    Output: dict matching the components.json schema, including device_info.
    """
    return {
        "schema_version": schema_version,
        "screen_id": screen_id,
        "image_path": image_path,
        "xml_path": xml_path,
        "device_info": device_info or dict(DEFAULT_DEVICE_INFO),
        "components": components,
    }

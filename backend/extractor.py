
import re


def find_label_value(text, labels):
    """Find a value written on the line immediately after a label."""

    for label in labels:
        pattern = rf"(?:^|\n)\s*{label}\s*\n\s*([^\n]+)"
        match = re.search(pattern, text, re.IGNORECASE)

        if match:
            return match.group(1).strip()

    return None


def extract_document(text, document_type):
    """Extract structured shipment fields from PDF text."""

    data = {}

    # Common fields
    data["shipment_number"] = find_label_value(
        text, ["Shipment Number"]
    )

    data["supplier_name"] = find_label_value(
        text, ["Exporter / Supplier", "Shipper"]
    )

    data["origin_country"] = find_label_value(
        text, ["Origin Country"]
    )

    data["consignee"] = find_label_value(
        text, ["Consignee"]
    )

    data["goods_description"] = find_label_value(
        text, ["Description of Goods"]
    )

    # Document number
    number_patterns = {
        "invoice": r"Invoice No:\s*([^|\n]+)",
        "packing_list": r"Packing List No:\s*([^|\n]+)",
        "bill_of_lading": r"B/L No:\s*([^|\n]+)"
    }

    number_pattern = number_patterns.get(document_type)

    match = re.search(number_pattern, text, re.IGNORECASE) if number_pattern else None

    data["document_number"] = (
        match.group(1).strip() if match else None
    )

    # Quantity
    quantity_text = find_label_value(text, ["Quantity"])

    quantity_match = re.search(
        r"([\d,]+)\s*(\w+)?",
        quantity_text or ""
    )

    data["quantity"] = (
        int(quantity_match.group(1).replace(",", ""))
        if quantity_match else None
    )

    data["quantity_unit"] = (
        quantity_match.group(2)
        if quantity_match else None
    )

    # Weights
    for field, label in [
        ("gross_weight_kg", "Gross Weight"),
        ("net_weight_kg", "Net Weight")
    ]:
        value = find_label_value(text, [label])
        match = re.search(r"([\d,.]+)\s*kg", value or "", re.IGNORECASE)

        data[field] = (
            float(match.group(1).replace(",", ""))
            if match else None
        )

    # Invoice-specific values
    unit_price = find_label_value(text, ["Unit Price"])
    total_value = find_label_value(text, ["Total Invoice Value"])

    price_match = re.search(
        r"([A-Z]{3})\s*([\d,.]+)",
        unit_price or "",
        re.IGNORECASE
    )

    total_match = re.search(
        r"([A-Z]{3})\s*([\d,.]+)",
        total_value or "",
        re.IGNORECASE
    )

    data["unit_price"] = (
        float(price_match.group(2).replace(",", ""))
        if price_match else None
    )

    data["total_value"] = (
        float(total_match.group(2).replace(",", ""))
        if total_match else None
    )

    data["currency"] = (
        price_match.group(1).upper()
        if price_match else (
            total_match.group(1).upper() if total_match else None
        )
    )

    # Package count
    packages_text = find_label_value(
        text, ["Number of Packages", "Packages"]
    )

    packages_match = re.search(
        r"([\d,]+)\s*(\w+)?",
        packages_text or ""
    )

    data["package_count"] = (
        int(packages_match.group(1).replace(",", ""))
        if packages_match else None
    )

    data["package_type"] = (
        packages_match.group(2)
        if packages_match else None
    )

    # Transport details from bill of lading
    data["port_of_loading"] = find_label_value(
        text, ["Port of Loading"]
    )

    data["port_of_discharge"] = find_label_value(
        text, ["Port of Discharge"]
    )

    # Confidence: exact pattern matches receive 0.95.
    confidence = {
        field: 0.95 if value is not None else 0.0
        for field, value in data.items()
    }

    available = sum(value is not None for value in data.values())
    overall_confidence = round(
        available / len(data), 2
    ) if data else 0.0

    return {
        "document_type": document_type,
        "fields": data,
        "field_confidence": confidence,
        "overall_confidence": overall_confidence
    }

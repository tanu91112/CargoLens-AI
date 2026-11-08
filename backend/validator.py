
def validate_documents(extracted_documents):
    fields_to_compare = {
        "shipment_number": "Shipment Number",
        "supplier_name": "Supplier / Shipper",
        "consignee": "Consignee",
        "goods_description": "Goods Description",
        "quantity": "Quantity",
        "gross_weight_kg": "Gross Weight",
        "package_count": "Package Count",
        "origin_country": "Origin Country"
    }

    results = []

    for field, label in fields_to_compare.items():
        values = []

        for document in extracted_documents:
            value = document["fields"].get(field)

            if value is not None:
                values.append({
                    "document_type": document["document_type"],
                    "value": value
                })

        # Compare only when at least two documents contain the field.
        if len(values) < 2:
            continue

        first_value = str(values[0]["value"]).strip().lower()

        is_match = all(
            str(item["value"]).strip().lower() == first_value
            for item in values[1:]
        )

        results.append({
            "field": field,
            "label": label,
            "status": "match" if is_match else "mismatch",
            "values": values
        })

    mismatch_count = sum(
        1 for item in results
        if item["status"] == "mismatch"
    )

    return {
        "overall_status": "needs_review" if mismatch_count else "consistent",
        "total_fields_checked": len(results),
        "mismatch_count": mismatch_count,
        "checks": results
    }

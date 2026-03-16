import uuid
from iso20022 import generate_pacs008_xml, parse_pacs008_xml

def test_roundtrip():
    message_id = str(uuid.uuid4())
    tx_id = str(uuid.uuid4())
    amount = 125.50
    currency = "TRY"
    from_iban = "TR123456789012345678901234"
    to_iban = "TR987654321098765432109876"
    from_bank_bic = "MODERN_BANK"
    to_bank_bic = "OTHER_BANK"
    
    xml_str = generate_pacs008_xml(
        message_id,
        tx_id,
        amount,
        currency,
        from_iban,
        to_iban,
        from_bank_bic,
        to_bank_bic
    )
    print("Generated XML:")
    print(xml_str)
    
    parsed = parse_pacs008_xml(xml_str)
    print("\nParsed Data:")
    print(parsed)
    
    assert parsed["tx_id"] == tx_id
    assert parsed["amount"] == amount
    assert parsed["currency"] == currency
    assert parsed["from_iban"] == from_iban
    assert parsed["to_iban"] == to_iban
    assert parsed["from_bank_bic"] == from_bank_bic
    assert parsed["to_bank_bic"] == to_bank_bic
    print("\nAll tests passed!")

if __name__ == "__main__":
    test_roundtrip()

import xml.etree.ElementTree as ET
import datetime
import uuid

# Namespaces
PACS008_NS = "urn:iso:std:iso:20022:tech:xsd:pacs.008.001.02"
PACS002_NS = "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.03"

ET.register_namespace("p008", PACS008_NS)
ET.register_namespace("p002", PACS002_NS)

def generate_pacs008_xml(
    message_id: str,
    tx_id: str,
    amount: float,
    currency: str,
    from_iban: str,
    to_iban: str,
    from_bank_bic: str,
    to_bank_bic: str,
    debtor_name: str = "Customer",
    creditor_name: str = "Customer"
) -> str:
    """
    Generate an ISO 20022 PACS.008 XML string for a customer credit transfer.
    """
    # Create the root Document element
    document = ET.Element(f"{{{PACS008_NS}}}Document", xmlns=PACS008_NS)
    
    # Main FIToFICstmrCdtTrf element
    fi_to_fi = ET.SubElement(document, f"{{{PACS008_NS}}}FIToFICstmrCdtTrf")
    
    # --- Group Header ---
    grp_hdr = ET.SubElement(fi_to_fi, f"{{{PACS008_NS}}}GrpHdr")
    ET.SubElement(grp_hdr, f"{{{PACS008_NS}}}MsgId").text = message_id
    ET.SubElement(grp_hdr, f"{{{PACS008_NS}}}CreDtTm").text = datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    ET.SubElement(grp_hdr, f"{{{PACS008_NS}}}NbOfTxs").text = "1"
    
    sttlm_inf = ET.SubElement(grp_hdr, f"{{{PACS008_NS}}}SttlmInf")
    ET.SubElement(sttlm_inf, f"{{{PACS008_NS}}}SttlmMtd").text = "CLRG" 
    
    # --- Credit Transfer Transaction Information ---
    tx_inf = ET.SubElement(fi_to_fi, f"{{{PACS008_NS}}}CdtTrfTxInf")
    
    # Payment Identification
    pmt_id = ET.SubElement(tx_inf, f"{{{PACS008_NS}}}PmtId")
    ET.SubElement(pmt_id, f"{{{PACS008_NS}}}EndToEndId").text = tx_id
    
    # Amount
    amt = ET.SubElement(tx_inf, f"{{{PACS008_NS}}}IntrBkSttlmAmt", Ccy=currency)
    amt.text = f"{amount:.2f}"
    
    # Debtor Account
    dbtr_acct = ET.SubElement(tx_inf, f"{{{PACS008_NS}}}DbtrAcct")
    dbtr_id = ET.SubElement(dbtr_acct, f"{{{PACS008_NS}}}Id")
    ET.SubElement(dbtr_id, f"{{{PACS008_NS}}}IBAN").text = from_iban
    
    # Creditor Account
    cdtr_acct = ET.SubElement(tx_inf, f"{{{PACS008_NS}}}CdtrAcct")
    cdtr_id = ET.SubElement(cdtr_acct, f"{{{PACS008_NS}}}Id")
    ET.SubElement(cdtr_id, f"{{{PACS008_NS}}}IBAN").text = to_iban
    
    # Convert to string
    xml_str = ET.tostring(document, encoding="utf-8", method="xml").decode("utf-8")
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_str

def parse_pacs008_xml(xml_string: str) -> dict:
    """
    Parse an ISO 20022 PACS.008 XML string and extract relevant transaction details.
    """
    # Remove encoding declaration if present to easily parse
    try:
        root = ET.fromstring(xml_string)
    except ET.ParseError as e:
        raise ValueError(f"Invalid XML: {e}")
        
    
    # Many elements in the actual XML might not have the namespace if the root lacks it.
    # However, ElementTree honors the default namespace, so we must prefix queries.
    # To be robust, let's find elements ignoring namespaces.
    
    def find_text_ignore_ns(element, tag_name):
        for child in element.iter():
            if child.tag.endswith(f"}}{tag_name}") or child.tag == tag_name:
                return child.text
        return None
        
    def find_elem_ignore_ns(element, tag_name):
        for child in element.iter():
            if child.tag.endswith(f"}}{tag_name}") or child.tag == tag_name:
                return child
        return None

    tx_inf = find_elem_ignore_ns(root, "CdtTrfTxInf")
    if tx_inf is None:
        raise ValueError("CdtTrfTxInf element not found in XML")
        
    pmt_id = find_elem_ignore_ns(tx_inf, "PmtId")
    tx_id = find_text_ignore_ns(pmt_id, "EndToEndId") if pmt_id else None
    
    amt_elem = find_elem_ignore_ns(tx_inf, "IntrBkSttlmAmt")
    amount = float(amt_elem.text) if amt_elem is not None else 0.0
    currency = amt_elem.attrib.get('Ccy') if amt_elem is not None else None
    
    dbtr_acct = find_elem_ignore_ns(tx_inf, "DbtrAcct")
    from_iban = find_text_ignore_ns(dbtr_acct, "IBAN") if dbtr_acct else None
    
    cdtr_acct = find_elem_ignore_ns(tx_inf, "CdtrAcct")
    to_iban = find_text_ignore_ns(cdtr_acct, "IBAN") if cdtr_acct else None
    
    
    return {
        "tx_id": tx_id,
        "amount": amount,
        "currency": currency,
        "from_iban": from_iban,
        "to_iban": to_iban
    }

def generate_pacs002_xml(msg_id: str, original_tx_id: str, status: str = "ACCP") -> str:
    """
    Generate an ISO 20022 PACS.002 XML response (Acknowledgment).
    status: ACCP (Accepted), RJCT (Rejected)
    """
    document = ET.Element(f"{{{PACS002_NS}}}Document", xmlns=PACS002_NS)
    fi_to_fi = ET.SubElement(document, f"{{{PACS002_NS}}}FIToFIPmtStsRpt")
    
    grp_hdr = ET.SubElement(fi_to_fi, f"{{{PACS002_NS}}}GrpHdr")
    ET.SubElement(grp_hdr, f"{{{PACS002_NS}}}MsgId").text = msg_id
    ET.SubElement(grp_hdr, f"{{{PACS002_NS}}}CreDtTm").text = datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    
    tx_inf = ET.SubElement(fi_to_fi, f"{{{PACS002_NS}}}TxInfAndSts")
    ET.SubElement(tx_inf, f"{{{PACS002_NS}}}OrgnlEndToEndId").text = original_tx_id
    ET.SubElement(tx_inf, f"{{{PACS002_NS}}}TxSts").text = status
    
    xml_str = ET.tostring(document, encoding="utf-8", method="xml").decode("utf-8")
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_str

def parse_pacs002_xml(xml_string: str) -> dict:
    """
    Parse an ISO 20022 PACS.002 XML status report.
    """
    try:
        root = ET.fromstring(xml_string)
    except ET.ParseError as e:
        raise ValueError(f"Invalid XML: {e}")
        
    def find_text(tag):
        for child in root.iter():
            if child.tag.endswith(f"}}{tag}") or child.tag == tag:
                return child.text
        return None

    return {
        "original_tx_id": find_text("OrgnlEndToEndId"),
        "status": find_text("TxSts")
    }

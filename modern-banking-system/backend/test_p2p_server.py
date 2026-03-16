import asyncio
import websockets
import uuid

async def test_p2p_incoming():
    uri = "ws://localhost:8001/ws/inter-bank/FINB"
    
    # pacs.008 XML logic (Simplified for testing)
    pacs008 = """<?xml version="1.0" encoding="UTF-8"?>
<Document xmlns="urn:iso:std:iso:20022:tech:xsd:pacs.008.001.02">
    <FIToFICstmrCdtTrf>
        <GrpHdr>
            <MsgId>TEST-MSG-001</MsgId>
            <CreDtTm>2026-03-16T12:00:00Z</CreDtTm>
        </GrpHdr>
        <CdtTrfTxInf>
            <PmtId>
                <EndToEndId>TEST-TX-001</EndToEndId>
            </PmtId>
            <IntrBkSttlmAmt Ccy="TRY">10.00</IntrBkSttlmAmt>
            <DbtrAcct>
                <Id><IBAN>FINB0000000001</IBAN></Id>
            </DbtrAcct>
            <CdtrAcct>
                <Id><IBAN>TR000006100000000000000001</IBAN></Id>
            </CdtrAcct>
        </CdtTrfTxInf>
    </FIToFICstmrCdtTrf>
</Document>"""

    try:
        async with websockets.connect(uri) as websocket:
            print("Connected to P2P Server.")
            await websocket.send(pacs008)
            print("Sent pacs.008.")
            
            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            print(f"Received Response:\n{response}")
            
            if "pacs.002" in response and "ACCP" in response:
                print("SUCCESS: Received ACCP acknowledgment.")
            else:
                print("FAILURE: Did not receive expected ACCP acknowledgment.")
                
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_p2p_incoming())

# Security & Protocol Analysis Notes

## 1. Authentication & Authorization
The application implements **JWT (JSON Web Token)** based authentication. 
- Passwords are never stored in plain text; they are hashed using `bcrypt`.
- All secured endpoints utilize FastAPI's internal `Depends(get_current_user)` pipeline which forces an invalidation for unauthorized requests (HTTP 401).
- **Role-Based Access Control (RBAC):** We implemented two roles: `Admin` and `Customer`. Read-only audit features are tightly bounded to `Admin` verification (`get_current_admin`), throwing a 403 Forbidden payload against regular user access.

## 2. API Security Best Practices
- **Input Validation:** Accomplished directly via `Pydantic` schemas. Amounts are validated to be strictly `> 0` natively, averting logic manipulation bypasses.
- **CORS Handling:** Enforced through middleware `CORSMiddleware` directly on the FastAPI instantiation application layer.
- **Secrets Management:** The repository relies purely on Environment Variables `.env`. An example `.env.example` handles structural guidelines, prohibiting `SECRET_KEY` credentials from bleeding into Version Control environments.
- **Rate Limiting (Future Step):** Ready to be attached to ASGI middleware, out of testing scope at present scale.

## 3. Financial Protocol Awareness (Conceptual Mapping)
Real financial systems do not solely rely on typical REST standards—they operate through rigorous structured networks. However, our internal REST infrastructure loosely concepts these systems:

- **ISO 20022:** The universal financial messaging standard uses heavy XMLs. Our JSON representation conceptually acts as a simpler surrogate mapping. For example, our `LedgerResponse` schema structurally equates to the payload fields needed inside a `pacs.008` (Customer Credit Transfer).
- **SWIFT:** Conceptually, inter-account transfers acting through our `Ledger` approximate the confirmation process of a localized SWIFT clearing node.
- **Open Banking APIs:** Our entire modular monolith exposes standard HTTP protocols, making it very straightforward to later wrap these internal endpoints under OAuth 2.0 Open Banking mandates (like PSD2 in Europe).

## 4. Audit Logging Mechanism
The central structure is deeply tied to the **append-only `Ledger` table**. 
- Actions are instantly recorded.
- Modification attempts return validation errors (the table is immutable).
- It binds the transaction UUID, from-address, to-address, type, timestamp, and amount cleanly, effectively offering a complete footprint tracking what action was performed and when.

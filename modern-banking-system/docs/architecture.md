# Modern Banking Architecture

```mermaid
graph TD
    Client((Client/Browser)) -->|REST API over HTTP| FastAPI[FastAPI Backend - Moduler Monolith]
    
    subgraph FastAPI_Backend [Backend: Python/FastAPI]
        AuthRouter[Auth Router: JWT]
        CustomerRouter[Customer Router]
        AccountRouter[Account Router]
        LedgerRouter[Ledger Router]
        
        AuthRouter -.-> Security[Security / Passlib]
        LedgerRouter -.-> CoreLogic[Double-entry Validation]
        
        Security -.-> SQLAlchemy[SQLAlchemy ORM]
        CoreLogic -.-> SQLAlchemy
        CustomerRouter -.-> SQLAlchemy
        AccountRouter -.-> SQLAlchemy
    end
    
    FastAPI -->|psycopg2: TCP 5432| Postgres[(PostgreSQL DB)]
    
    subgraph Database [Postgres Database]
        Customers[Customers Table]
        Accounts[Accounts Table]
        Ledger[Ledger Table - Append Only]
        
        Customers -.- Accounts
        Accounts -.- Ledger
    end
```

> **Note to user:** You can copy this Markdown code into any Mermaid Live Editor (or GitHub) to view the graph, and screenshot it to save as `architecture.png` for your assignment!

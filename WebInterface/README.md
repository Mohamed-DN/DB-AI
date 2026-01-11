# WebInterface

> Frontend (React) and Backend (FastAPI) for the dashboard.

## Structure

```
WebInterface/
├── backend/           # FastAPI API (Python)
│   ├── main.py        # Main application (~1000 lines)
│   └── requirements.txt
└── frontend-react/    # React Dashboard
    ├── src/
    │   ├── components/  # UI components
    │   ├── hooks/       # React Query hooks
    │   └── services/    # API client
    └── package.json
```

## Running

```powershell
# Backend (port 9000)
cd WebInterface/backend
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 9000

# Frontend (port 4002)
cd WebInterface/frontend-react
npm install
npm run dev:v2
```

Or use `.\scripts\setup_v2.ps1` to start both automatically.

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/inventory` | GET | List databases |
| `/api/alerts` | GET | List alerts |
| `/api/agents/status` | GET | Agent status |
| `/api/auto-discovery` | POST | Trigger scan |
| `/api/chat` | POST | AI chat |

Full docs: http://localhost:9000/docs

## See Also
- [ARCHITECTURE.md](../ARCHITECTURE.md) - System design


# Backend

يشرح ملف [`README.md`](../README.md) في جذر المشروع إعداد Python وتشغيل API والاختبارات.

نقطة تشغيل التطبيق:

```powershell
python -m uvicorn backend.app.main:app --host localhost --port 8000
```

نقاط API الحالية:

- `POST /analyze`
- `GET /session/{session_id}`

"""
Emails Router - Email archive management endpoints
"""
import os
from fastapi import APIRouter, HTTPException

router = APIRouter()

# Email directory path
EMAIL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../emails'))


@router.get("/emails")
def get_emails():
    """List archived emails"""
    try:
        if not os.path.exists(EMAIL_DIR):
            return []
        
        files = [f for f in os.listdir(EMAIL_DIR) if f.endswith('.html')]
        files.sort(reverse=True)  # Newest first
        return files
    except Exception as e:
        return []


@router.get("/emails/content")
def get_email_content(filename: str):
    """Get email content"""
    try:
        # Security check: filename only, no path traversal
        if "/" in filename or "\\" in filename:
            raise HTTPException(status_code=400, detail="Invalid filename")
        
        path = os.path.join(EMAIL_DIR, filename)
        
        if not os.path.exists(path):
            raise HTTPException(status_code=404, detail="File not found")
        
        with open(path, "r", encoding="utf-8") as f:
            return {"content": f.read()}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/emails/{filename}")
def delete_email(filename: str):
    """Delete a single email"""
    try:
        # Security check: filename only
        if "/" in filename or "\\" in filename:
            raise HTTPException(status_code=400, detail="Invalid filename")
        
        path = os.path.join(EMAIL_DIR, filename)
        
        if not os.path.exists(path):
            raise HTTPException(status_code=404, detail="File not found")
        
        os.remove(path)
        return {"status": "deleted", "filename": filename}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/emails/all")
def delete_all_emails():
    """Delete all emails from the inbox"""
    try:
        if not os.path.exists(EMAIL_DIR):
            return {"status": "no emails to delete", "count": 0}
        
        count = 0
        for f in os.listdir(EMAIL_DIR):
            if f.endswith('.html'):
                os.remove(os.path.join(EMAIL_DIR, f))
                count += 1
        
        return {"status": "deleted", "count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

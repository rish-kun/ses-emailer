from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Any, Dict
import os
import secrets
import asyncio
import uuid

from api.config_manager import ConfigProfileManager, Profile
from config.settings import AppConfig, AWSConfig, SenderConfig, BatchConfig
from sending.db import Database
from sending.senders import MassEmailSender
from sending.emails import Email

# To securely communicate, we generate a random token when the API starts
# In a real scenario, this might be saved or passed via env to the TUI
API_TOKEN = os.getenv("API_TOKEN", secrets.token_hex(32))

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_token(token: str = Depends(oauth2_scheme)):
    if token != API_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token

app = FastAPI(title="SES Email API")

# Add CORS middleware for local frontend development if needed
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

config_manager = ConfigProfileManager()
db = Database()

# --- Pydantic Models for Config ---

class AWSConfigModel(BaseModel):
    access_key_id: str
    secret_access_key: str
    region: str
    source_email: str

class SenderConfigModel(BaseModel):
    sender_name: str
    reply_to: str
    default_to: str

class BatchConfigModel(BaseModel):
    batch_size: int
    delay_seconds: float
    use_bcc: bool

class AppConfigModel(BaseModel):
    aws: AWSConfigModel
    sender: SenderConfigModel
    batch: BatchConfigModel
    files_directory: str
    data_directory: str
    last_excel_path: str
    last_excel_column: int
    theme: str
    test_recipients: List[str]

class ProfileModel(BaseModel):
    id: str
    name: str
    config: AppConfigModel

# --- Configuration Endpoints ---

@app.get("/profiles", response_model=List[ProfileModel], dependencies=[Depends(verify_token)])
def get_profiles():
    return [
        ProfileModel(
            id=p.id,
            name=p.name,
            config=AppConfigModel(
                aws=AWSConfigModel(**p.config.aws.__dict__),
                sender=SenderConfigModel(**p.config.sender.__dict__),
                batch=BatchConfigModel(**p.config.batch.__dict__),
                files_directory=p.config.files_directory,
                data_directory=p.config.data_directory,
                last_excel_path=p.config.last_excel_path,
                last_excel_column=p.config.last_excel_column,
                theme=p.config.theme,
                test_recipients=p.config.test_recipients,
            )
        ) for p in config_manager.get_all_profiles()
    ]

@app.get("/profiles/active", response_model=ProfileModel, dependencies=[Depends(verify_token)])
def get_active_profile():
    p = config_manager.get_active_profile()
    return ProfileModel(
        id=p.id,
        name=p.name,
        config=AppConfigModel(
            aws=AWSConfigModel(**p.config.aws.__dict__),
            sender=SenderConfigModel(**p.config.sender.__dict__),
            batch=BatchConfigModel(**p.config.batch.__dict__),
            files_directory=p.config.files_directory,
            data_directory=p.config.data_directory,
            last_excel_path=p.config.last_excel_path,
            last_excel_column=p.config.last_excel_column,
            theme=p.config.theme,
            test_recipients=p.config.test_recipients,
        )
    )

@app.post("/profiles/active/{profile_id}", dependencies=[Depends(verify_token)])
def set_active_profile(profile_id: str):
    if config_manager.set_active_profile(profile_id):
        return {"message": "Profile set as active"}
    raise HTTPException(status_code=404, detail="Profile not found")

@app.post("/profiles", response_model=ProfileModel, dependencies=[Depends(verify_token)])
def create_profile(name: str, config: Optional[AppConfigModel] = None):
    app_config = None
    if config:
        app_config = AppConfig(
            aws=AWSConfig(**config.aws.dict()),
            sender=SenderConfig(**config.sender.dict()),
            batch=BatchConfig(**config.batch.dict()),
            files_directory=config.files_directory,
            data_directory=config.data_directory,
            last_excel_path=config.last_excel_path,
            last_excel_column=config.last_excel_column,
            theme=config.theme,
            test_recipients=config.test_recipients,
        )

    p = config_manager.create_profile(name, app_config)
    return ProfileModel(
        id=p.id,
        name=p.name,
        config=AppConfigModel(
            aws=AWSConfigModel(**p.config.aws.__dict__),
            sender=SenderConfigModel(**p.config.sender.__dict__),
            batch=BatchConfigModel(**p.config.batch.__dict__),
            files_directory=p.config.files_directory,
            data_directory=p.config.data_directory,
            last_excel_path=p.config.last_excel_path,
            last_excel_column=p.config.last_excel_column,
            theme=p.config.theme,
            test_recipients=p.config.test_recipients,
        )
    )

@app.put("/profiles/{profile_id}", response_model=ProfileModel, dependencies=[Depends(verify_token)])
def update_profile(profile_id: str, name: Optional[str] = None, config: Optional[AppConfigModel] = None):
    app_config = None
    if config:
        app_config = AppConfig(
            aws=AWSConfig(**config.aws.dict()),
            sender=SenderConfig(**config.sender.dict()),
            batch=BatchConfig(**config.batch.dict()),
            files_directory=config.files_directory,
            data_directory=config.data_directory,
            last_excel_path=config.last_excel_path,
            last_excel_column=config.last_excel_column,
            theme=config.theme,
            test_recipients=config.test_recipients,
        )

    if config_manager.update_profile(profile_id, name, app_config):
        p = config_manager.profiles[profile_id]
        return ProfileModel(
            id=p.id,
            name=p.name,
            config=AppConfigModel(
                aws=AWSConfigModel(**p.config.aws.__dict__),
                sender=SenderConfigModel(**p.config.sender.__dict__),
                batch=BatchConfigModel(**p.config.batch.__dict__),
                files_directory=p.config.files_directory,
                data_directory=p.config.data_directory,
                last_excel_path=p.config.last_excel_path,
                last_excel_column=p.config.last_excel_column,
                theme=p.config.theme,
                test_recipients=p.config.test_recipients,
            )
        )
    raise HTTPException(status_code=404, detail="Profile not found")

@app.delete("/profiles/{profile_id}", dependencies=[Depends(verify_token)])
def delete_profile(profile_id: str):
    if config_manager.delete_profile(profile_id):
        return {"message": "Profile deleted"}
    raise HTTPException(status_code=400, detail="Cannot delete profile (may be the last one or not found)")

# --- Sending and History Endpoints ---

class SendEmailRequest(BaseModel):
    subject: str
    body: str
    recipients: List[str]
    files: List[str] = []
    email_type: str = "html"  # 'html' or 'plain'

class SendResponse(BaseModel):
    message: str
    total_recipients: int

class DraftRequest(BaseModel):
    name: str
    subject: str = ""
    body: str = ""
    recipients: List[str] = []
    attachments: List[str] = []
    email_type: str = "html"

# Global task storage for background sending progress
SEND_TASKS: Dict[str, Dict[str, Any]] = {}

import threading
import time

def background_send_task(task_id: str, req: SendEmailRequest, profile: Profile):
    task = SEND_TASKS[task_id]

    try:
        sender_cfg = profile.config.sender
        aws_cfg = profile.config.aws
        batch_cfg = profile.config.batch

        email = Email(
            body=req.body,
            subject=req.subject,
            sender=sender_cfg.sender_name,
            recipient=sender_cfg.default_to or aws_cfg.source_email,
            files=req.files
        )
        db.add_email(email)

        sender = MassEmailSender(
            sender=sender_cfg.sender_name,
            id=email.id,
            reply_to=sender_cfg.reply_to or aws_cfg.source_email,
            delay=batch_cfg.delay_seconds,
            aws_creds={
                "access_key_id": aws_cfg.access_key_id,
                "secret_access_key": aws_cfg.secret_access_key,
                "region": aws_cfg.region,
                "source_email": aws_cfg.source_email
            }
        )

        recipients = req.recipients
        batch_size = batch_cfg.batch_size
        delay = batch_cfg.delay_seconds

        task["total_batches"] = len(recipients) // batch_size + (1 if len(recipients) % batch_size else 0)

        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        from email.mime.application import MIMEApplication

        for i in range(0, len(recipients), batch_size):
            if task["status"] == "cancelled":
                break

            batch = recipients[i:i+batch_size]
            batch_num = (i // batch_size) + 1

            task["current_batch"] = batch_num
            task["status"] = f"Sending batch {batch_num}/{task['total_batches']}"

            msg = MIMEMultipart()
            msg["Subject"] = req.subject
            msg["From"] = sender.sender
            msg["To"] = sender.to
            msg["Reply-To"] = sender.reply_to

            if batch_cfg.use_bcc:
                msg["Bcc"] = ", ".join(batch)
            else:
                # CC or individual (for now CC)
                msg["Cc"] = ", ".join(batch)

            if req.email_type == "html":
                msg_body = MIMEMultipart("alternative")
                msg_body.attach(MIMEText(req.body, "html"))
                msg.attach(msg_body)
            else:
                msg.attach(MIMEText(req.body, "plain"))

            if req.files:
                for file in req.files:
                    try:
                        with open(os.path.join(profile.config.files_directory, file), "rb") as f:
                            part = MIMEApplication(f.read(), Name=file)
                            part.add_header("Content-Disposition", "attachment", filename=os.path.basename(file))
                            msg.attach(part)
                    except Exception as e:
                        print(f"File error: {e}")

            try:
                # Actual sending
                sender.send_bcc_plain_mail(batch, msg)

                # Log to DB
                for rec in batch:
                    db.add_sent(email.id, rec, "bcc" if batch_cfg.use_bcc else "cc")

                task["sent_emails"] += len(batch)

                if i + batch_size < len(recipients) and task["status"] != "cancelled":
                    task["status"] = f"Waiting {delay}s"
                    time.sleep(delay)
            except Exception as e:
                task["errors"].append(f"Batch {batch_num} error: {str(e)}")
                for rec in batch:
                    db.add_failed_email(email.id, rec, str(e))
                print(f"Error in batch {batch_num}: {str(e)}")

        if task["status"] != "cancelled":
            task["status"] = "completed"

    except Exception as e:
        task["status"] = "failed"
        task["errors"].append(str(e))
        print(f"Global send task error: {e}")

@app.post("/send", response_model=Dict[str, str], dependencies=[Depends(verify_token)])
def send_email(req: SendEmailRequest):
    profile = config_manager.get_active_profile()
    if not profile.config.aws.access_key_id:
        raise HTTPException(status_code=400, detail="AWS credentials not configured")

    task_id = uuid.uuid4().hex
    SEND_TASKS[task_id] = {
        "status": "starting",
        "total_emails": len(req.recipients),
        "sent_emails": 0,
        "current_batch": 0,
        "total_batches": 0,
        "errors": []
    }

    # Run sending in background thread
    t = threading.Thread(target=background_send_task, args=(task_id, req, profile))
    t.start()

    return {"task_id": task_id, "message": "Sending started"}

@app.get("/send/status/{task_id}", dependencies=[Depends(verify_token)])
def get_send_status(task_id: str):
    if task_id not in SEND_TASKS:
        raise HTTPException(status_code=404, detail="Task not found")
    return SEND_TASKS[task_id]

@app.post("/send/cancel/{task_id}", dependencies=[Depends(verify_token)])
def cancel_send(task_id: str):
    if task_id in SEND_TASKS:
        if SEND_TASKS[task_id]["status"] not in ["completed", "failed", "cancelled"]:
            SEND_TASKS[task_id]["status"] = "cancelled"
            return {"message": "Task cancelled"}
    raise HTTPException(status_code=404, detail="Task not active or found")

@app.get("/history", dependencies=[Depends(verify_token)])
def get_history():
    return db.get_grouped_emails_summary()

@app.get("/history/{email_id}", dependencies=[Depends(verify_token)])
def get_history_detail(email_id: str):
    email = db.get_email(email_id)
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    sent = db.get_sent_emails_by_email_id(email_id)
    failed = db.get_failed_emails_by_email_id(email_id)

    return {
        "email": {
            "id": email[0],
            "subject": email[1],
            "body": email[2],
            "sender": email[3],
            "files": email[4]
        },
        "sent": [
            {"id": s[0], "email_id": s[1], "sent_to": s[2], "sent_type": s[3], "sent_at": s[4]}
            for s in sent
        ],
        "failed": [
            {"id": f[0], "email_id": f[1], "recipient": f[2], "error": f[3], "failed_at": f[4], "retried": f[5]}
            for f in failed
        ]
    }

@app.get("/drafts", dependencies=[Depends(verify_token)])
def get_drafts():
    return db.get_all_drafts()

@app.post("/drafts", dependencies=[Depends(verify_token)])
def create_draft(draft: DraftRequest):
    draft_id = db.add_draft(
        name=draft.name,
        subject=draft.subject,
        body=draft.body,
        recipients=draft.recipients,
        attachments=draft.attachments,
        email_type=draft.email_type
    )
    return {"id": draft_id, "message": "Draft created"}

@app.put("/drafts/{draft_id}", dependencies=[Depends(verify_token)])
def update_draft(draft_id: int, draft: DraftRequest):
    success = db.update_draft(
        draft_id=draft_id,
        name=draft.name,
        subject=draft.subject,
        body=draft.body,
        recipients=draft.recipients,
        attachments=draft.attachments,
        email_type=draft.email_type
    )
    if success:
        return {"message": "Draft updated"}
    raise HTTPException(status_code=404, detail="Draft not found")

@app.delete("/drafts/{draft_id}", dependencies=[Depends(verify_token)])
def delete_draft(draft_id: int):
    if db.delete_draft(draft_id):
        return {"message": "Draft deleted"}
    raise HTTPException(status_code=404, detail="Draft not found")

@app.get("/files", dependencies=[Depends(verify_token)])
def list_files():
    profile = config_manager.get_active_profile()
    files_dir = profile.config.files_directory
    if not os.path.exists(files_dir):
        os.makedirs(files_dir)
    return {"files": os.listdir(files_dir)}

"""
ML ingestion router.

Ref: docs/plans/03-routes.md section 5.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Header, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.controllers import ml_controller
from app.middleware.auth import get_api_key_device
from app.middleware.db import get_db_session
from app.models.device import DeviceModel
from app.schemas.common import LogoUrlSchema, MessageSchema
from app.schemas.waste import BulkWasteIngestSchema, DetectionPayload, HeartbeatPayload, SyncResultSchema, WasteEntrySchema

router = APIRouter(prefix="/ml", tags=["ML Ingestion"])


@router.post("/detect", response_model=WasteEntrySchema, status_code=201)
async def ingest_detection(
    body: DetectionPayload,
    device: DeviceModel = Depends(get_api_key_device),
    db: AsyncSession = Depends(get_db_session),
):
    return await ml_controller.ingest_detection(db, body, device=device)


@router.post("/sync", response_model=SyncResultSchema)
async def bulk_ingest(
    body: BulkWasteIngestSchema,
    device: DeviceModel = Depends(get_api_key_device),
    db: AsyncSession = Depends(get_db_session),
):
    return await ml_controller.bulk_ingest(db, body, device=device)


@router.post("/heartbeat", response_model=MessageSchema)
async def ml_heartbeat(
    body: HeartbeatPayload,
    device: DeviceModel = Depends(get_api_key_device),
    db: AsyncSession = Depends(get_db_session),
):
    return await ml_controller.ml_heartbeat(db, body, device=device)


@router.post("/upload-image", response_model=LogoUrlSchema)
async def upload_image(
    image_file: UploadFile = File(...),
    content_length: int | None = Header(default=None, alias="Content-Length"),
    device: DeviceModel = Depends(get_api_key_device),  # noqa: ARG001
):
    return await ml_controller.upload_image(image_file, content_length=content_length)

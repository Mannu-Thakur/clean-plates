"""
Handles ML/edge-device requests for sending waste data to the backend.

The controller receives data from authenticated devices and passes it
to waste_service for processing. It handles waste detection ingestion,
bulk syncing, device heartbeats, and image uploads.

Router → Controller → waste_service
"""
from __future__ import annotations

from arq.connections import ArqRedis
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.device import DeviceModel
from app.schemas.common import LogoUrlSchema, MessageSchema
from app.schemas.waste import (
    BulkWasteIngestSchema,
    DetectionPayload,
    HeartbeatPayload,
    SyncResultSchema,
    WasteEntrySchema,
)
from app.services import waste_service


 # This is an asynchronous controller function used by our ML edge devices to submit waste detection data. It receives the database session, the detection payload, and the authenticated device. The controller itself doesn't contain business logic; it delegates the request to waste_service.create_waste_entry(). I also pass source='ml' so the service knows the origin of the waste data.
 # An optional ARQ pool is passed in case background processing is required
async def ingest_detection(
    db: AsyncSession,
    body: DetectionPayload,
    *,
    device: DeviceModel,
    arq_pool: ArqRedis | None = None,
) -> WasteEntrySchema:
    return await waste_service.create_waste_entry(db, body, authenticated_device=device, source="ml", arq_pool=arq_pool)


async def bulk_ingest(
    db: AsyncSession,
    body: BulkWasteIngestSchema,
    *,
    device: DeviceModel,
    arq_pool: ArqRedis | None = None,
) -> SyncResultSchema:
    return await waste_service.bulk_sync(db, body, authenticated_device=device, arq_pool=arq_pool)

# this is an asynchronous controller endpoint that handles heartbeat messages from authenticated ML devices. It receives the database session, heartbeat payload, authenticated device, and an optional ARQ pool, then delegates the actual processing to waste_service.ml_heartbeat(). Once the service completes successfully, it returns a confirmation message. The controller itself doesn't contain the business logic.
async def ml_heartbeat(
    db: AsyncSession,
    body: HeartbeatPayload,
    *,
    device: DeviceModel,
    arq_pool: ArqRedis | None = None,
) -> MessageSchema:
    await waste_service.ml_heartbeat(db, body, device=device, arq_pool=arq_pool)
    return MessageSchema(message="Heartbeat recorded")


async def upload_image(
    image_file: UploadFile,
    *,
    content_length: int | None = None,
) -> LogoUrlSchema:
    return await waste_service.upload_image(image_file, content_length=content_length)

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import settings
from backend.app.dependencies import get_db
from backend.app.models.active_client import ActiveClient
from backend.app.schemas.usage import (
    ActiveClientItem,
    ActiveUsersResponse,
    AdminUsageClientsResponse,
    AdminUsageSummaryResponse,
    HeartbeatRequest,
)

ACTIVE_WINDOW_SECONDS = 180

router = APIRouter(prefix="/usage", tags=["usage"])


def _normalize_bearer_token(auth_header: str | None) -> str | None:
    if not auth_header:
        return None
    if auth_header.lower().startswith("bearer "):
        return auth_header[7:].strip()
    return auth_header.strip()


def _require_admin_token(
    authorization: str | None = Header(default=None),
    x_admin_token: str | None = Header(default=None),
) -> None:
    expected = settings.usage_admin_token.strip()
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="USAGE_ADMIN_TOKEN is not configured",
        )
    provided = _normalize_bearer_token(authorization) or (x_admin_token.strip() if x_admin_token else None)
    if provided != expected:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin token")


@router.post("/heartbeat", response_model=ActiveUsersResponse)
async def heartbeat(
    req: HeartbeatRequest, request: Request, db: AsyncSession = Depends(get_db)
):
    now = datetime.now(timezone.utc)
    forwarded_for = request.headers.get("x-forwarded-for", "")
    ip_address = (
        forwarded_for.split(",")[0].strip()
        if forwarded_for
        else (request.client.host if request.client else "")
    )

    browser_info = req.browser_info
    stmt = insert(ActiveClient).values(
        client_id=req.client_id,
        first_seen_at=now,
        last_seen_at=now,
        user_agent=browser_info.user_agent,
        browser_language=browser_info.browser_language,
        platform=browser_info.platform,
        timezone=browser_info.timezone,
        screen_width=browser_info.screen_width,
        screen_height=browser_info.screen_height,
        viewport_width=browser_info.viewport_width,
        viewport_height=browser_info.viewport_height,
        current_path=browser_info.current_path,
        referrer=browser_info.referrer,
        ip_address=ip_address,
    )
    stmt = stmt.on_conflict_do_update(
        index_elements=[ActiveClient.client_id],
        set_={
            "last_seen_at": now,
            "user_agent": browser_info.user_agent,
            "browser_language": browser_info.browser_language,
            "platform": browser_info.platform,
            "timezone": browser_info.timezone,
            "screen_width": browser_info.screen_width,
            "screen_height": browser_info.screen_height,
            "viewport_width": browser_info.viewport_width,
            "viewport_height": browser_info.viewport_height,
            "current_path": browser_info.current_path,
            "referrer": browser_info.referrer,
            "ip_address": ip_address,
        },
    )
    await db.execute(stmt)
    await db.commit()

    active_from = now - timedelta(seconds=ACTIVE_WINDOW_SECONDS)
    active_result = await db.execute(
        select(func.count(ActiveClient.id)).where(ActiveClient.last_seen_at >= active_from)
    )
    active_users = int(active_result.scalar_one())
    historical_result = await db.execute(select(func.count(ActiveClient.id)))
    historical_users = int(historical_result.scalar_one())
    return ActiveUsersResponse(
        active_users=active_users,
        historical_users=historical_users,
        window_seconds=ACTIVE_WINDOW_SECONDS,
    )


@router.get("/admin/summary", response_model=AdminUsageSummaryResponse)
async def admin_summary(
    _: None = Depends(_require_admin_token), db: AsyncSession = Depends(get_db)
):
    now = datetime.now(timezone.utc)
    active_from = now - timedelta(seconds=ACTIVE_WINDOW_SECONDS)
    active_result = await db.execute(
        select(func.count(ActiveClient.id)).where(ActiveClient.last_seen_at >= active_from)
    )
    active_users = int(active_result.scalar_one())
    historical_result = await db.execute(select(func.count(ActiveClient.id)))
    historical_users = int(historical_result.scalar_one())
    return AdminUsageSummaryResponse(
        active_users=active_users,
        historical_users=historical_users,
        window_seconds=ACTIVE_WINDOW_SECONDS,
    )


@router.get("/admin/clients", response_model=AdminUsageClientsResponse)
async def admin_clients(
    _: None = Depends(_require_admin_token), db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(ActiveClient)
        .order_by(ActiveClient.last_seen_at.desc())
        .limit(settings.usage_admin_clients_limit)
    )
    rows = list(result.scalars().all())
    clients = [
        ActiveClientItem(
            client_id=row.client_id,
            first_seen_at=row.first_seen_at.isoformat(),
            last_seen_at=row.last_seen_at.isoformat(),
            user_agent=row.user_agent,
            browser_language=row.browser_language,
            platform=row.platform,
            timezone=row.timezone,
            screen_width=row.screen_width,
            screen_height=row.screen_height,
            viewport_width=row.viewport_width,
            viewport_height=row.viewport_height,
            current_path=row.current_path,
            referrer=row.referrer,
            ip_address=row.ip_address,
        )
        for row in rows
    ]
    return AdminUsageClientsResponse(clients=clients)

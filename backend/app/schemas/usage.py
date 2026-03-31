from pydantic import BaseModel, Field


class BrowserInfo(BaseModel):
    user_agent: str = Field(min_length=1, max_length=512)
    browser_language: str = Field(min_length=1, max_length=32)
    platform: str = Field(min_length=1, max_length=64)
    timezone: str = Field(min_length=1, max_length=64)
    screen_width: int = Field(ge=0)
    screen_height: int = Field(ge=0)
    viewport_width: int = Field(ge=0)
    viewport_height: int = Field(ge=0)
    current_path: str = Field(min_length=1, max_length=255)
    referrer: str = Field(default="", max_length=512)


class HeartbeatRequest(BaseModel):
    client_id: str = Field(min_length=8, max_length=64)
    browser_info: BrowserInfo


class ActiveUsersResponse(BaseModel):
    active_users: int
    historical_users: int
    window_seconds: int


class ActiveClientItem(BaseModel):
    client_id: str
    first_seen_at: str
    last_seen_at: str
    user_agent: str | None
    browser_language: str | None
    platform: str | None
    timezone: str | None
    screen_width: int | None
    screen_height: int | None
    viewport_width: int | None
    viewport_height: int | None
    current_path: str | None
    referrer: str | None
    ip_address: str | None


class AdminUsageSummaryResponse(BaseModel):
    active_users: int
    historical_users: int
    window_seconds: int


class AdminUsageClientsResponse(BaseModel):
    clients: list[ActiveClientItem]

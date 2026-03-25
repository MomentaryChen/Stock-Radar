from pydantic import BaseModel


class WatchlistCreate(BaseModel):
    name: str
    tickers: list[str] = []


class WatchlistUpdate(BaseModel):
    name: str | None = None
    tickers: list[str] | None = None


class WatchlistResponse(BaseModel):
    id: int
    name: str
    tickers: list[str]

    model_config = {"from_attributes": True}

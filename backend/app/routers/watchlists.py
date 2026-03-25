from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.dependencies import get_db
from backend.app.repositories.watchlist_repo import WatchlistRepo
from backend.app.schemas.watchlist import WatchlistCreate, WatchlistResponse, WatchlistUpdate

router = APIRouter(prefix="/watchlists", tags=["watchlists"])

DEFAULT_USER_ID = 1


@router.get("", response_model=list[WatchlistResponse])
async def list_watchlists(db: AsyncSession = Depends(get_db)):
    repo = WatchlistRepo(db)
    return await repo.get_all(DEFAULT_USER_ID)


@router.post("", response_model=WatchlistResponse, status_code=201)
async def create_watchlist(body: WatchlistCreate, db: AsyncSession = Depends(get_db)):
    repo = WatchlistRepo(db)
    return await repo.create(DEFAULT_USER_ID, body.name, body.tickers)


@router.put("/{watchlist_id}", response_model=WatchlistResponse)
async def update_watchlist(watchlist_id: int, body: WatchlistUpdate, db: AsyncSession = Depends(get_db)):
    repo = WatchlistRepo(db)
    wl = await repo.get_by_id(watchlist_id)
    if not wl or wl.user_id != DEFAULT_USER_ID:
        raise HTTPException(404, "Watchlist not found")
    return await repo.update(wl, name=body.name, tickers=body.tickers)


@router.delete("/{watchlist_id}", status_code=204)
async def delete_watchlist(watchlist_id: int, db: AsyncSession = Depends(get_db)):
    repo = WatchlistRepo(db)
    wl = await repo.get_by_id(watchlist_id)
    if not wl or wl.user_id != DEFAULT_USER_ID:
        raise HTTPException(404, "Watchlist not found")
    await repo.delete(wl)

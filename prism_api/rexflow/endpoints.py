"""Endpoints for communication with REXFlow bridge"""
from fastapi import APIRouter


router = APIRouter(tags=['rexflow'])


@router.post('/workflow/finish')
async def finish_workflow():
    ...


@router.post('/task/init')
async def start_task():
    ...

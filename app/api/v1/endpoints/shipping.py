"""
Shipping API Endpoints

Endpoints for managing saved shipper/recipient addresses and logistics providers.
"""

from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from app.database import get_database
from app.schemas.shipping import (
    SavedAddressCreate,
    SavedAddressUpdate,
    SavedAddressResponse,
    SavedAddressListResponse,
    LogisticsProviderResponse,
    LogisticsProviderListResponse,
)

router = APIRouter()


def build_address_response(address: dict) -> dict:
    """Build address response with string _id"""
    return {
        **address,
        "_id": str(address["_id"]),
    }


# ============================================
# Saved Shipper Addresses
# ============================================

@router.get("/shippers", response_model=SavedAddressListResponse)
async def list_shippers(
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """List all saved shipper addresses"""
    cursor = db.saved_addresses.find({"address_type": "shipper"}).sort("created_at", -1)
    addresses = await cursor.to_list(length=100)

    return SavedAddressListResponse(
        items=[build_address_response(addr) for addr in addresses],
        total=len(addresses)
    )


@router.post("/shippers", response_model=SavedAddressResponse)
async def create_shipper(
    address: SavedAddressCreate,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Create a new saved shipper address"""
    now = datetime.utcnow()

    # If this is default, unset other defaults
    if address.is_default:
        await db.saved_addresses.update_many(
            {"address_type": "shipper", "is_default": True},
            {"$set": {"is_default": False, "updated_at": now}}
        )

    address_doc = {
        **address.model_dump(),
        "address_type": "shipper",
        "created_at": now,
        "updated_at": now,
    }

    result = await db.saved_addresses.insert_one(address_doc)
    address_doc["_id"] = result.inserted_id

    return build_address_response(address_doc)


@router.get("/shippers/{address_id}", response_model=SavedAddressResponse)
async def get_shipper(
    address_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get a specific shipper address"""
    if not ObjectId.is_valid(address_id):
        raise HTTPException(status_code=400, detail="Invalid address ID")

    address = await db.saved_addresses.find_one({
        "_id": ObjectId(address_id),
        "address_type": "shipper"
    })

    if not address:
        raise HTTPException(status_code=404, detail="Shipper address not found")

    return build_address_response(address)


@router.put("/shippers/{address_id}", response_model=SavedAddressResponse)
async def update_shipper(
    address_id: str,
    update_data: SavedAddressUpdate,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Update a shipper address"""
    if not ObjectId.is_valid(address_id):
        raise HTTPException(status_code=400, detail="Invalid address ID")

    now = datetime.utcnow()

    # If setting as default, unset other defaults
    if update_data.is_default:
        await db.saved_addresses.update_many(
            {"address_type": "shipper", "is_default": True, "_id": {"$ne": ObjectId(address_id)}},
            {"$set": {"is_default": False, "updated_at": now}}
        )

    update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
    update_dict["updated_at"] = now

    result = await db.saved_addresses.find_one_and_update(
        {"_id": ObjectId(address_id), "address_type": "shipper"},
        {"$set": update_dict},
        return_document=True
    )

    if not result:
        raise HTTPException(status_code=404, detail="Shipper address not found")

    return build_address_response(result)


@router.delete("/shippers/{address_id}")
async def delete_shipper(
    address_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Delete a shipper address"""
    if not ObjectId.is_valid(address_id):
        raise HTTPException(status_code=400, detail="Invalid address ID")

    result = await db.saved_addresses.delete_one({
        "_id": ObjectId(address_id),
        "address_type": "shipper"
    })

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Shipper address not found")

    return {"message": "Shipper address deleted"}


# ============================================
# Saved Recipient Addresses
# ============================================

@router.get("/recipients", response_model=SavedAddressListResponse)
async def list_recipients(
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """List all saved recipient addresses"""
    cursor = db.saved_addresses.find({"address_type": "recipient"}).sort("created_at", -1)
    addresses = await cursor.to_list(length=100)

    return SavedAddressListResponse(
        items=[build_address_response(addr) for addr in addresses],
        total=len(addresses)
    )


@router.post("/recipients", response_model=SavedAddressResponse)
async def create_recipient(
    address: SavedAddressCreate,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Create a new saved recipient address"""
    now = datetime.utcnow()

    # If this is default, unset other defaults
    if address.is_default:
        await db.saved_addresses.update_many(
            {"address_type": "recipient", "is_default": True},
            {"$set": {"is_default": False, "updated_at": now}}
        )

    address_doc = {
        **address.model_dump(),
        "address_type": "recipient",
        "created_at": now,
        "updated_at": now,
    }

    result = await db.saved_addresses.insert_one(address_doc)
    address_doc["_id"] = result.inserted_id

    return build_address_response(address_doc)


@router.get("/recipients/{address_id}", response_model=SavedAddressResponse)
async def get_recipient(
    address_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get a specific recipient address"""
    if not ObjectId.is_valid(address_id):
        raise HTTPException(status_code=400, detail="Invalid address ID")

    address = await db.saved_addresses.find_one({
        "_id": ObjectId(address_id),
        "address_type": "recipient"
    })

    if not address:
        raise HTTPException(status_code=404, detail="Recipient address not found")

    return build_address_response(address)


@router.put("/recipients/{address_id}", response_model=SavedAddressResponse)
async def update_recipient(
    address_id: str,
    update_data: SavedAddressUpdate,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Update a recipient address"""
    if not ObjectId.is_valid(address_id):
        raise HTTPException(status_code=400, detail="Invalid address ID")

    now = datetime.utcnow()

    # If setting as default, unset other defaults
    if update_data.is_default:
        await db.saved_addresses.update_many(
            {"address_type": "recipient", "is_default": True, "_id": {"$ne": ObjectId(address_id)}},
            {"$set": {"is_default": False, "updated_at": now}}
        )

    update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
    update_dict["updated_at"] = now

    result = await db.saved_addresses.find_one_and_update(
        {"_id": ObjectId(address_id), "address_type": "recipient"},
        {"$set": update_dict},
        return_document=True
    )

    if not result:
        raise HTTPException(status_code=404, detail="Recipient address not found")

    return build_address_response(result)


@router.delete("/recipients/{address_id}")
async def delete_recipient(
    address_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Delete a recipient address"""
    if not ObjectId.is_valid(address_id):
        raise HTTPException(status_code=400, detail="Invalid address ID")

    result = await db.saved_addresses.delete_one({
        "_id": ObjectId(address_id),
        "address_type": "recipient"
    })

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Recipient address not found")

    return {"message": "Recipient address deleted"}


# ============================================
# Logistics Providers
# ============================================

@router.get("/providers", response_model=LogisticsProviderListResponse)
async def list_logistics_providers(
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """List all active logistics providers"""
    cursor = db.logistics_providers.find({"is_active": True}).sort("name", 1)
    providers = await cursor.to_list(length=50)

    # If no providers exist, seed some defaults
    if len(providers) == 0:
        default_providers = [
            {
                "code": "sf",
                "name": "SF Express",
                "name_zh": "顺丰速运",
                "service_types": ["standard", "express", "same-day"],
                "is_active": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            },
            {
                "code": "yto",
                "name": "YTO Express",
                "name_zh": "圆通速递",
                "service_types": ["standard", "economy"],
                "is_active": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            },
            {
                "code": "sto",
                "name": "STO Express",
                "name_zh": "申通快递",
                "service_types": ["standard", "economy"],
                "is_active": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            },
            {
                "code": "zto",
                "name": "ZTO Express",
                "name_zh": "中通快递",
                "service_types": ["standard", "economy"],
                "is_active": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            },
            {
                "code": "yunda",
                "name": "Yunda Express",
                "name_zh": "韵达快递",
                "service_types": ["standard", "economy"],
                "is_active": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            },
            {
                "code": "jd",
                "name": "JD Logistics",
                "name_zh": "京东物流",
                "service_types": ["standard", "express", "same-day"],
                "is_active": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            },
            {
                "code": "ems",
                "name": "China Post EMS",
                "name_zh": "中国邮政EMS",
                "service_types": ["standard", "international"],
                "is_active": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            },
        ]
        await db.logistics_providers.insert_many(default_providers)
        providers = default_providers

    return LogisticsProviderListResponse(
        providers=[
            {
                **p,
                "_id": str(p["_id"]) if "_id" in p else str(ObjectId()),
            }
            for p in providers
        ]
    )


# ============================================
# Seed Saved Addresses (for testing)
# ============================================

@router.post("/seed")
async def seed_addresses(
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Seed sample shipper and recipient addresses for testing"""
    now = datetime.utcnow()

    # Clear existing
    await db.saved_addresses.delete_many({})

    # Sample shippers (Korean warehouses/offices)
    shippers = [
        {
            "address_type": "shipper",
            "label": "Seoul Main Warehouse",
            "name": "김물류",
            "contact_number": "+82-2-1234-5678",
            "email": "warehouse@snaplive.kr",
            "address_line1": "123 Gangnam-daero",
            "address_line2": "Building A, 5F",
            "city": "Seoul",
            "province": "Seoul",
            "postal_code": "06000",
            "country": "South Korea",
            "is_default": True,
            "created_at": now,
            "updated_at": now,
        },
        {
            "address_type": "shipper",
            "label": "Busan Distribution Center",
            "name": "박배송",
            "contact_number": "+82-51-987-6543",
            "email": "busan@snaplive.kr",
            "address_line1": "456 Haeundae-ro",
            "city": "Busan",
            "province": "Busan",
            "postal_code": "48000",
            "country": "South Korea",
            "is_default": False,
            "created_at": now,
            "updated_at": now,
        },
        {
            "address_type": "shipper",
            "label": "Incheon Airport Hub",
            "name": "이국제",
            "contact_number": "+82-32-555-1234",
            "email": "airport@snaplive.kr",
            "address_line1": "789 Airport-ro",
            "city": "Incheon",
            "province": "Incheon",
            "postal_code": "22382",
            "country": "South Korea",
            "is_default": False,
            "created_at": now,
            "updated_at": now,
        },
    ]

    # Sample recipients (Chinese customers)
    recipients = [
        {
            "address_type": "recipient",
            "label": "VIP Customer - Beijing",
            "name": "王小明",
            "contact_number": "+86-10-8888-9999",
            "email": "xiaoming@example.com",
            "address_line1": "朝阳区建国路88号",
            "address_line2": "中海国际中心A座1201室",
            "city": "Beijing",
            "province": "Beijing",
            "postal_code": "100022",
            "country": "China",
            "is_default": True,
            "created_at": now,
            "updated_at": now,
        },
        {
            "address_type": "recipient",
            "label": "Regular Customer - Shanghai",
            "name": "李婷婷",
            "contact_number": "+86-21-5555-6666",
            "email": "tingting@example.com",
            "address_line1": "浦东新区陆家嘴环路1000号",
            "address_line2": "恒生银行大厦28层",
            "city": "Shanghai",
            "province": "Shanghai",
            "postal_code": "200120",
            "country": "China",
            "is_default": False,
            "created_at": now,
            "updated_at": now,
        },
        {
            "address_type": "recipient",
            "label": "Business Partner - Guangzhou",
            "name": "张伟",
            "contact_number": "+86-20-3333-4444",
            "email": "zhangwei@partner.com",
            "address_line1": "天河区珠江新城华夏路30号",
            "address_line2": "富力盈通大厦15楼",
            "city": "Guangzhou",
            "province": "Guangdong",
            "postal_code": "510623",
            "country": "China",
            "is_default": False,
            "created_at": now,
            "updated_at": now,
        },
    ]

    await db.saved_addresses.insert_many(shippers + recipients)

    return {
        "message": "Addresses seeded successfully",
        "shippers_created": len(shippers),
        "recipients_created": len(recipients),
    }

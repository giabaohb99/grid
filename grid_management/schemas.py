from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime

# Product Input Schema (from FE)
class ProductInput(BaseModel):
    productCode: str = Field(..., description="Product code: VA-M-000126-2")
    size: str = Field(..., description="Size")
    color: str = Field(..., description="Color")
    qrData: str = Field(..., description="QR data: 101725-VA-M-000126-2")
    number: str = Field(..., description="Product sequence number")
    total: str = Field(..., description="Total products")

# Grid Schemas
class GridCreate(BaseModel):
    name: str = Field(..., description="Grid name")
    width: int = Field(..., gt=0, le=20, description="Grid width (1-20)")
    height: int = Field(..., gt=0, le=20, description="Grid height (1-20)")

class GridUpdate(BaseModel):
    name: Optional[str] = Field(None, description="New grid name")
    width: Optional[int] = Field(None, gt=0, le=20, description="New width (1-20)")
    height: Optional[int] = Field(None, gt=0, le=20, description="New height (1-20)")

class GridResponse(BaseModel):
    id: int
    name: str
    width: int
    height: int
    total_cells: int
    created_at: datetime
    is_active: bool
    
    class Config:
        from_attributes = True

# Product Schemas
class ProductResponse(BaseModel):
    id: int
    product_code: str
    size: str
    color: str
    qr_data: str
    number: int
    total: int
    production_area: str
    size_code: str
    order_number: str
    product_number: int
    order_date: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# Cell Schemas
class GridCellResponse(BaseModel):
    id: int
    position_x: int
    position_y: int
    cell_name: str
    current_order_code: Optional[str]
    current_order_date: Optional[str]
    current_full_order_key: Optional[str]
    current_product_count: int
    target_product_count: Optional[int]
    status: str
    note: Optional[str]
    created_at: datetime
    updated_at: datetime
    filled_at: Optional[datetime]
    cleared_at: Optional[datetime]
    products: List[ProductResponse] = []
    
    class Config:
        from_attributes = True

class GridWithCellsResponse(BaseModel):
    id: int
    name: str
    width: int
    height: int
    total_cells: int
    created_at: datetime
    is_active: bool
    cells: List[GridCellResponse] = []
    
    class Config:
        from_attributes = True

# Cell Update Schemas
class CellNoteUpdate(BaseModel):
    note: Optional[str] = Field(None, description="Cell note")

class CellStatusUpdate(BaseModel):
    status: str = Field(..., description="Status: empty, filling, full")

# Order Tracking Schemas
class OrderTrackingResponse(BaseModel):
    id: int
    order_code: str
    order_date: str
    full_order_key: str
    total_products: int
    received_products: int
    assigned_cell_id: Optional[int]
    status: str
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]
    shipped_at: Optional[datetime]
    
    class Config:
        from_attributes = True

# Cell History Schemas
class CellHistoryResponse(BaseModel):
    id: int
    action_type: str
    description: str
    order_code: Optional[str]
    order_date: Optional[str]
    old_data: Optional[str]
    new_data: Optional[str]
    products_data: Optional[str]
    product_count: Optional[int]
    performed_by: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

# Cell Detail with History and Products
class CellDetailResponse(BaseModel):
    id: int
    position_x: int
    position_y: int
    cell_name: str
    current_order_code: Optional[str]
    current_order_date: Optional[str]
    current_full_order_key: Optional[str]
    current_product_count: int
    target_product_count: Optional[int]
    status: str
    note: Optional[str]
    created_at: datetime
    updated_at: datetime
    filled_at: Optional[datetime]
    cleared_at: Optional[datetime]
    products: List[ProductResponse] = []
    histories: List[CellHistoryResponse] = []
    
    class Config:
        from_attributes = True

# API Response Schemas
class ProductAssignmentResponse(BaseModel):
    success: bool
    message: str
    grid_id: Optional[int] = None
    grid_name: Optional[str] = None
    cell_id: Optional[int] = None
    cell_name: Optional[str] = None
    cell_position: Optional[str] = None
    order_code: Optional[str] = None
    current_count: Optional[int] = None
    target_count: Optional[int] = None
    cell_status: Optional[str] = None
    product_info: Optional[dict] = None
    duplicate: Optional[bool] = False

class GridStatusResponse(BaseModel):
    grid_id: int
    grid_name: str
    total_cells: int
    empty_cells: int
    filling_cells: int
    full_cells: int
    cells: List[GridCellResponse]

class ApiResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None

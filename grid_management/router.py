from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload
from typing import List
from core.core.database import get_db

from . import crud, schemas, models

router = APIRouter(
    prefix="/api",
    tags=["Grid Management - Public API"]
)

# Grid Management Endpoints

@router.post("/create", response_model=schemas.GridResponse)
def create_grid(
    grid: schemas.GridCreate,
    db: Session = Depends(get_db)
):
    """
    Tạo lưới mới với kích thước width x height
    Tự động tạo tất cả các ô trong lưới
    """
    try:
        db_grid = crud.create_grid(db=db, grid=grid)
        return db_grid
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create grid: {str(e)}"
        )

@router.get("/grids", response_model=schemas.PaginationResponse[schemas.GridResponse])
def get_grids(
    page: int = 1,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Lấy danh sách tất cả lưới"""
    data = crud.get_grids(db=db, skip=(page - 1) * limit, limit=limit)
    paginationData = schemas.PaginationResponse(
        page=page,
        limit=limit,
        total=len(data),
        data=data,  
    )
    print(paginationData)
    
    return paginationData

@router.get("/grid/{grid_id}", response_model=schemas.GridWithCellsResponse)
def get_grid_detail(
    grid_id: int,
    db: Session = Depends(get_db)
):
    """Lấy chi tiết lưới kèm tất cả ô và sản phẩm"""
    grid = db.query(models.Grid).options(
        selectinload(models.Grid.cells).selectinload(models.GridCell.products)
    ).filter(models.Grid.id == grid_id).first()
    
    if not grid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grid not found"
        )
    return grid

@router.put("/grid/{grid_id}", response_model=schemas.GridResponse)
def update_grid(
    grid_id: int,
    grid_update: schemas.GridUpdate,
    db: Session = Depends(get_db)
):
    """
    Cập nhật lưới (tên hoặc kích thước)
    
    **Tăng kích thước:**
    - Tự động tạo thêm các ô mới
    - VD: 5x4 → 10x10 sẽ tạo thêm 80 ô mới
    
    **Giảm kích thước:**
    - Chỉ cho phép nếu các ô bị xóa KHÔNG có sản phẩm
    - Nếu có sản phẩm → Trả về lỗi và danh sách ô có sản phẩm
    
    **Chỉ đổi tên:**
    - Không ảnh hưởng đến cells
    """
    result = crud.update_grid(db=db, grid_id=grid_id, grid_update=grid_update)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )
    
    return result["grid"]

# Product Assignment Endpoints

@router.post("/grid/assign-product", response_model=schemas.ProductAssignmentResponse)
def assign_product(
    product: schemas.ProductInput,
    db: Session = Depends(get_db)
):
    """
    Quét và phân bổ sản phẩm tự động
    - Chỉ cần truyền thông tin sản phẩm từ QR code
    - Hệ thống tự động tìm lưới active và ô phù hợp
    - Kiểm tra trùng lặp product_code
    - Tự động phân bổ vào ô cùng order hoặc ô trống
    - Trả về thông tin chi tiết về vị trí đã phân bổ
    """
    result = crud.assign_product_to_cell(db=db, product_input=product)
    
    if not result["success"]:
        if result.get("duplicate"):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=result["message"]
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )
    
    return result

@router.get("/grid/product/{product_code}/check")
def check_product_duplicate(
    product_code: str,
    db: Session = Depends(get_db)
):
    """Kiểm tra sản phẩm đã tồn tại chưa"""
    exists = crud.check_product_exists(db=db, product_code=product_code)
    return {
        "product_code": product_code,
        "exists": exists,
        "message": "Product already exists" if exists else "Product does not exist"
    }

# Cell Management Endpoints

@router.get("/grid/cells/ready-to-ship", response_model=List[schemas.GridCellResponse])
def get_cells_ready_to_ship(
    db: Session = Depends(get_db)
):
    """
    Lấy danh sách các ô sẵn sàng giao hàng (status = "full")
    
    **Dùng cho:**
    - Admin xem các ô đã đầy, cần lấy hàng đi giao
    - Sắp xếp theo thời gian đầy (filled_at) - ô nào đầy trước sẽ hiện trước
    """
    cells = db.query(models.GridCell).options(
        selectinload(models.GridCell.products)
    ).filter(
        models.GridCell.status == "full"
    ).order_by(
        models.GridCell.filled_at.asc()
    ).all()
    
    return cells

@router.get("/grid/cells/by-status/{status}", response_model=List[schemas.GridCellResponse])
def get_cells_by_status(
    status: str,
    db: Session = Depends(get_db)
):
    """
    Lấy danh sách ô theo trạng thái
    
    **Trạng thái:**
    - empty: Ô trống
    - filling: Đang nhận hàng
    - full: Đã đầy (sẵn sàng giao)
    """
    valid_statuses = ["empty", "filling", "full"]
    if status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Only accepts: {', '.join(valid_statuses)}"
        )
    
    cells = db.query(models.GridCell).options(
        selectinload(models.GridCell.products)
    ).filter(
        models.GridCell.status == status
    ).order_by(
        models.GridCell.updated_at.desc()
    ).all()
    
    return cells

@router.get("/grid/cell/{cell_id}/detail", response_model=schemas.CellDetailResponse)
def get_cell_detail(
    cell_id: int,
    db: Session = Depends(get_db)
):
    """
    Lấy chi tiết ô bao gồm:
    - Thông tin ô
    - Danh sách sản phẩm hiện tại (với timestamp created_at)
    - Lịch sử giao hàng của ô
    """
    cell = db.query(models.GridCell).options(
        selectinload(models.GridCell.products),
        selectinload(models.GridCell.histories)
    ).filter(models.GridCell.id == cell_id).first()
    
    if not cell:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cell not found"
        )
    return cell

@router.put("/grid/cell/{cell_id}/status")
def update_cell_status(
    cell_id: int,
    status_update: schemas.CellStatusUpdate,
    db: Session = Depends(get_db)
):
    """
    Cập nhật trạng thái của ô
    
    **QUAN TRỌNG:**
    - Nếu đổi sang "empty": Sẽ TỰ ĐỘNG tạo lịch sử, xóa sản phẩm, clear tất cả thông tin đơn hàng
    - Nếu đổi "filling"/"full": Chỉ update trạng thái, GIỮ NGUYÊN dữ liệu
    
    **Khuyến nghị:**
    - Dùng API này để đổi "filling" ↔ "full" (thủ công)
    - Dùng `/cell/{id}/clear` để giải phóng ô (tương đương đổi về "empty")
    """
    cell = db.query(models.GridCell).filter(models.GridCell.id == cell_id).first()
    if not cell:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cell not found"
        )
    
    # Validate status
    valid_statuses = ["empty", "filling", "full"]
    if status_update.status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Only accepts: {', '.join(valid_statuses)}"
        )
    
    # Nếu đổi sang "empty" → Phải clear hết data (giống clear_cell)
    if status_update.status == "empty":
        success = crud.clear_cell(db=db, cell_id=cell_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot clear cell (cell is empty or system error)"
            )
        
        return {
            "success": True,
            "message": f"Released cell {cell.cell_name} and switched to 'empty' status. History has been saved.",
            "cell_id": cell_id,
            "cell_name": cell.cell_name,
            "new_status": "empty",
            "history_created": True,
            "data_cleared": True
        }
    
    # Nếu đổi filling/full → Chỉ update status
    old_status = cell.status
    cell.status = status_update.status
    
    # Cập nhật filled_at nếu chuyển sang full
    if status_update.status == "full" and old_status != "full":
        from datetime import datetime
        cell.filled_at = datetime.utcnow()
    
    # Log: Đổi status thủ công
    crud.log_cell_history(
        db=db,
        cell_id=cell_id,
        action_type="status_changed",
        description=f"Cell {cell.cell_name} changed from '{old_status}' → '{status_update.status}' (manual)",
        order_code=cell.current_order_code,
        order_date=cell.current_order_date,
        old_data={"status": old_status},
        new_data={"status": status_update.status, "filled_at": cell.filled_at.isoformat() if cell.filled_at else None}
    )
    
    db.commit()
    db.refresh(cell)
    
    return {
        "success": True,
        "message": f"Updated cell {cell.cell_name} status from '{old_status}' to '{status_update.status}'",
        "cell_id": cell_id,
        "cell_name": cell.cell_name,
        "old_status": old_status,
        "new_status": status_update.status,
        "history_created": False,
        "data_cleared": False
    }

@router.put("/grid/cell/{cell_id}/note")
def update_cell_note(
    cell_id: int,
    note_update: schemas.CellNoteUpdate,
    db: Session = Depends(get_db)
):
    """Cập nhật ghi chú cho ô"""
    success = crud.update_cell_note(db=db, cell_id=cell_id, note=note_update.note)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cell not found"
        )
    
    return {
        "success": True,
        "message": "Updated cell note",
        "cell_id": cell_id,
        "note": note_update.note
    }

@router.post("/grid/cell/{cell_id}/clear")
def clear_cell(
    cell_id: int,
    db: Session = Depends(get_db)
):
    """
    Giải phóng ô - giao hàng
    - Chuyển tất cả sản phẩm vào lịch sử
    - Reset ô về trạng thái empty
    - Xóa ghi chú
    - Cập nhật order tracking thành shipped
    """
    success = crud.clear_cell(db=db, cell_id=cell_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot release cell (cell is empty or system error)"
        )
    
    return {
        "success": True,
        "message": "Successfully released cell and shipped products",
        "cell_id": cell_id
    }

@router.get("/grid/cell/{cell_id}/history", response_model=schemas.PaginationResponse[schemas.CellHistoryResponse])
def get_cell_history(
    cell_id: int,
    page: int = 1,
    limit: int = 10,
    action_type: str = None,
    order_code: str = None,
    order_date: str = None,
    db: Session = Depends(get_db)
):
    """Lấy lịch sử của ô"""
    histories = crud.get_cell_histories(db=db, cell_id=cell_id, skip=(page - 1) * limit, limit=limit, action_type=action_type, order_code=order_code, order_date=order_date)
    paginationData = schemas.PaginationResponse(
        page=page,
        limit=limit,
        total=len(histories),
        data=histories,
    )
    return paginationData

# Order Tracking Endpoints

@router.get("/grid/order/{full_order_key}", response_model=schemas.OrderTrackingResponse)
def get_order_status(
    full_order_key: str,
    db: Session = Depends(get_db)
):
    """
    Lấy trạng thái đơn hàng theo full_order_key
    VD: VA-M-000126-101725 (order_code-order_date)
    """
    order = db.query(models.OrderTracking).filter(
        models.OrderTracking.full_order_key == full_order_key
    ).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    return order

@router.get("/grid/orders", response_model=schemas.PaginationResponse[schemas.OrderTrackingResponse])
def get_all_orders(
    status_filter: str = None,
    page: int = 1,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    Lấy danh sách đơn hàng
    status_filter: pending, filling, completed, shipped
    """
    query = db.query(models.OrderTracking)
    
    if status_filter:
        query = query.filter(models.OrderTracking.status == status_filter)
    
    orders = query.order_by(models.OrderTracking.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
    paginationData = schemas.PaginationResponse(
        page=page,
        limit=limit,
        total=len(orders),
        data=orders,
    )
    return paginationData

# Statistics Endpoints

@router.get("/grid/status/summary")
def get_system_summary(db: Session = Depends(get_db)):
    """Lấy thống kê tổng quan hệ thống"""
    
    # Thống kê lưới
    total_grids = db.query(models.Grid).filter(models.Grid.is_active == True).count()
    total_cells = db.query(models.GridCell).count()
    
    # Thống kê ô
    empty_cells = db.query(models.GridCell).filter(models.GridCell.status == "empty").count()
    filling_cells = db.query(models.GridCell).filter(models.GridCell.status == "filling").count()
    full_cells = db.query(models.GridCell).filter(models.GridCell.status == "full").count()
    
    # Thống kê sản phẩm
    total_products = db.query(models.Product).count()
    
    # Thống kê đơn hàng
    total_orders = db.query(models.OrderTracking).count()
    pending_orders = db.query(models.OrderTracking).filter(models.OrderTracking.status == "pending").count()
    filling_orders = db.query(models.OrderTracking).filter(models.OrderTracking.status == "filling").count()
    completed_orders = db.query(models.OrderTracking).filter(models.OrderTracking.status == "completed").count()
    shipped_orders = db.query(models.OrderTracking).filter(models.OrderTracking.status == "shipped").count()
    
    return {
        "grids": {
            "total": total_grids,
            "total_cells": total_cells
        },
        "cells": {
            "empty": empty_cells,
            "filling": filling_cells,
            "full": full_cells,
            "utilization_rate": round((filling_cells + full_cells) / total_cells * 100, 2) if total_cells > 0 else 0
        },
        "products": {
            "total": total_products
        },
        "orders": {
            "total": total_orders,
            "pending": pending_orders,
            "filling": filling_orders,
            "completed": completed_orders,
            "shipped": shipped_orders
        }
    }

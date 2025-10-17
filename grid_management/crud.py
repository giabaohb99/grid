from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import Optional, List
import json
from datetime import datetime

from . import models, schemas

def parse_product_code(product_code: str) -> dict:
    """
    Phân tích product_code: VA-M-000126-2
    """
    parts = product_code.split('-')
    if len(parts) != 4:
        raise ValueError("Invalid product code format")
    
    return {
        "production_area": parts[0],  # VA
        "size_code": parts[1],        # M
        "order_number": parts[2],     # 000126
        "product_number": int(parts[3])  # 2
    }

def parse_qr_data(qr_data: str) -> dict:
    """
    Phân tích qr_data: 101725-VA-M-000126-2
    """
    parts = qr_data.split('-', 1)
    if len(parts) != 2:
        raise ValueError("Invalid QR data format")
    
    return {
        "order_date": parts[0],  # 101725
        "product_code": parts[1]  # VA-M-000126-2
    }

def extract_order_code(product_code: str) -> str:
    """
    Trích xuất order code từ product_code: VA-M-000126-2 -> VA-M-000126
    """
    parts = product_code.split('-')
    return f"{parts[0]}-{parts[1]}-{parts[2]}"

def create_full_order_key(order_code: str, order_date: str) -> str:
    """
    Tạo key đầy đủ cho đơn hàng: order_code + order_date
    VD: VA-M-000126 + 101725 -> VA-M-000126-101725
    """
    return f"{order_code}-{order_date}"

def log_cell_history(
    db: Session,
    cell_id: int,
    action_type: str,
    description: str,
    order_code: str = None,
    order_date: str = None,
    old_data: dict = None,
    new_data: dict = None,
    products_data: str = None,
    product_count: int = None,
    performed_by: str = "system"
):
    """
    Ghi lại MỌI hoạt động vào cell_histories
    
    action_type:
    - product_added: Thêm sản phẩm
    - status_changed: Đổi trạng thái
    - note_updated: Cập nhật ghi chú
    - cell_cleared: Giải phóng ô (giao hàng)
    """
    history = models.CellHistory(
        cell_id=cell_id,
        action_type=action_type,
        description=description,
        order_code=order_code,
        order_date=order_date,
        old_data=json.dumps(old_data, ensure_ascii=False) if old_data else None,
        new_data=json.dumps(new_data, ensure_ascii=False) if new_data else None,
        products_data=products_data,
        product_count=product_count,
        performed_by=performed_by
    )
    db.add(history)
    # Không commit ở đây - transaction chính sẽ commit

# Grid CRUD
def create_grid(db: Session, grid: schemas.GridCreate) -> models.Grid:
    """Tạo lưới mới và tự động tạo các ô"""
    db_grid = models.Grid(
        name=grid.name,
        width=grid.width,
        height=grid.height,
        total_cells=grid.width * grid.height
    )
    db.add(db_grid)
    db.flush()  # Để có grid.id
    
    # Tạo các ô tự động
    cells = []
    for y in range(grid.height):
        for x in range(grid.width):
            cell_name = f"{chr(65 + y)}{x + 1}"  # A1, A2, B1, B2...
            cell = models.GridCell(
                grid_id=db_grid.id,
                position_x=x,
                position_y=y,
                cell_name=cell_name,
                current_product_count=0,
                status="empty"
            )
            cells.append(cell)
    
    db.add_all(cells)
    db.commit()
    db.refresh(db_grid)
    return db_grid

def get_grid(db: Session, grid_id: int) -> Optional[models.Grid]:
    """Lấy thông tin lưới theo ID"""
    return db.query(models.Grid).filter(models.Grid.id == grid_id).first()

def get_grids(db: Session, skip: int = 0, limit: int = 100) -> List[models.Grid]:
    """Lấy danh sách lưới"""
    return db.query(models.Grid).filter(models.Grid.is_active == True).offset(skip).limit(limit).all()

def get_grid_with_cells(db: Session, grid_id: int) -> Optional[models.Grid]:
    """Lấy lưới kèm tất cả ô và sản phẩm"""
    return db.query(models.Grid).filter(models.Grid.id == grid_id).first()

def update_grid(db: Session, grid_id: int, grid_update: schemas.GridUpdate) -> dict:
    """
    Cập nhật grid (tên hoặc kích thước)
    - Nếu thay đổi kích thước: tạo thêm cells mới hoặc xóa cells (nếu không có sản phẩm)
    """
    grid = db.query(models.Grid).filter(models.Grid.id == grid_id).first()
    if not grid:
        return {"success": False, "message": "Không tìm thấy lưới"}
    
    # Cập nhật tên nếu có
    if grid_update.name is not None:
        grid.name = grid_update.name
    
    # Cập nhật kích thước nếu có
    if grid_update.width is not None or grid_update.height is not None:
        new_width = grid_update.width if grid_update.width is not None else grid.width
        new_height = grid_update.height if grid_update.height is not None else grid.height
        old_width = grid.width
        old_height = grid.height
        
        # Kiểm tra nếu giảm kích thước
        if new_width < old_width or new_height < old_height:
            # Lấy các cells sẽ bị xóa
            cells_to_delete = db.query(models.GridCell).filter(
                and_(
                    models.GridCell.grid_id == grid_id,
                    (models.GridCell.position_x >= new_width) | (models.GridCell.position_y >= new_height)
                )
            ).all()
            
            # Kiểm tra cells có sản phẩm không
            cells_with_products = [cell for cell in cells_to_delete if cell.current_product_count > 0]
            if cells_with_products:
                cell_names = ", ".join([cell.cell_name for cell in cells_with_products])
                return {
                    "success": False,
                    "message": f"Không thể giảm kích thước. Các ô sau đây đang có sản phẩm: {cell_names}",
                    "cells_with_products": [cell.cell_name for cell in cells_with_products]
                }
            
            # Xóa các cells không có sản phẩm
            for cell in cells_to_delete:
                db.delete(cell)
        
        # Nếu tăng kích thước - tạo thêm cells mới
        if new_width > old_width or new_height > old_height:
            existing_cells = {(cell.position_x, cell.position_y) for cell in grid.cells}
            new_cells = []
            
            for y in range(new_height):
                for x in range(new_width):
                    if (x, y) not in existing_cells:
                        cell_name = f"{chr(65 + y)}{x + 1}"  # A1, A2, B1, B2...
                        cell = models.GridCell(
                            grid_id=grid_id,
                            position_x=x,
                            position_y=y,
                            cell_name=cell_name,
                            current_product_count=0,
                            status="empty"
                        )
                        new_cells.append(cell)
            
            if new_cells:
                db.add_all(new_cells)
        
        # Cập nhật thông tin grid
        grid.width = new_width
        grid.height = new_height
        grid.total_cells = new_width * new_height
    
    grid.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(grid)
    
    return {
        "success": True,
        "message": "Đã cập nhật lưới thành công",
        "grid": grid
    }

# Product CRUD
def check_product_exists(db: Session, product_code: str) -> bool:
    """Kiểm tra sản phẩm đã tồn tại chưa"""
    return db.query(models.Product).filter(models.Product.product_code == product_code).first() is not None

def assign_product_to_cell(db: Session, product_input: schemas.ProductInput) -> dict:
    """
    Phân bổ sản phẩm vào ô
    Logic: Tự động tìm grid active, tìm ô đang filling cùng order_code, nếu không có thì tìm ô empty
    """
    try:
        # Kiểm tra trùng lặp
        if check_product_exists(db, product_input.productCode):
            return {
                "success": False,
                "message": f"Sản phẩm {product_input.productCode} đã tồn tại trong hệ thống",
                "duplicate": True
            }
        
        # Phân tích dữ liệu
        product_info = parse_product_code(product_input.productCode)
        qr_info = parse_qr_data(product_input.qrData)
        order_code = extract_order_code(product_input.productCode)
        order_date = qr_info["order_date"]
        full_order_key = create_full_order_key(order_code, order_date)
        
        # Tìm grid active đầu tiên (hoặc có thể có logic chọn grid khác)
        active_grid = db.query(models.Grid).filter(models.Grid.is_active == True).first()
        if not active_grid:
            return {
                "success": False,
                "message": "Không có lưới nào đang hoạt động trong hệ thống"
            }
        
        # Tìm ô đang filling cùng full_order_key (order_code + order_date) trong tất cả grid active
        existing_cell = db.query(models.GridCell).join(models.Grid).filter(
            and_(
                models.Grid.is_active == True,
                models.GridCell.current_full_order_key == full_order_key,
                models.GridCell.status == "filling"
            )
        ).first()
        
        if existing_cell:
            target_cell = existing_cell
            target_grid = existing_cell.grid
        else:
            # Tìm ô trống đầu tiên trong grid active
            target_cell = db.query(models.GridCell).join(models.Grid).filter(
                and_(
                    models.Grid.is_active == True,
                    models.GridCell.status == "empty"
                )
            ).first()
            
            if not target_cell:
                return {
                    "success": False,
                    "message": "Không có ô trống trong tất cả lưới để phân bổ sản phẩm"
                }
            
            target_grid = target_cell.grid
        
        # Tạo sản phẩm mới
        new_product = models.Product(
            cell_id=target_cell.id,
            product_code=product_input.productCode,
            size=product_input.size,
            color=product_input.color,
            qr_data=product_input.qrData,
            number=int(product_input.number),
            total=int(product_input.total),
            production_area=product_info["production_area"],
            size_code=product_info["size_code"],
            order_number=product_info["order_number"],
            product_number=product_info["product_number"],
            order_date=qr_info["order_date"]
        )
        
        db.add(new_product)
        
        # Lưu status cũ để log
        old_status = target_cell.status
        old_count = target_cell.current_product_count or 0
        
        # Cập nhật thông tin ô
        target_cell.current_order_code = order_code
        target_cell.current_order_date = order_date
        target_cell.current_full_order_key = full_order_key
        target_cell.current_product_count = (target_cell.current_product_count or 0) + 1
        target_cell.target_product_count = int(product_input.total)
        target_cell.updated_at = datetime.utcnow()
        
        # Cập nhật trạng thái ô
        if target_cell.current_product_count >= target_cell.target_product_count:
            target_cell.status = "full"
            target_cell.filled_at = datetime.utcnow()
        else:
            target_cell.status = "filling"
        
        # Log: Thêm sản phẩm
        log_cell_history(
            db=db,
            cell_id=target_cell.id,
            action_type="product_added",
            description=f"Thêm sản phẩm {product_input.productCode} ({product_input.size}/{product_input.color}) vào ô {target_cell.cell_name}",
            order_code=order_code,
            order_date=order_date,
            new_data={
                "product_code": product_input.productCode,
                "size": product_input.size,
                "color": product_input.color,
                "current_count": target_cell.current_product_count,
                "target_count": target_cell.target_product_count
            }
        )
        
        # Log: Đổi status (nếu thay đổi)
        if old_status != target_cell.status:
            log_cell_history(
                db=db,
                cell_id=target_cell.id,
                action_type="status_changed",
                description=f"Ô {target_cell.cell_name} đổi từ '{old_status}' → '{target_cell.status}' (tự động)",
                order_code=order_code,
                order_date=order_date,
                old_data={"status": old_status, "count": old_count},
                new_data={"status": target_cell.status, "count": target_cell.current_product_count, "filled_at": target_cell.filled_at.isoformat() if target_cell.filled_at else None}
            )
        
        # Cập nhật/tạo order tracking
        order_tracking = db.query(models.OrderTracking).filter(
            models.OrderTracking.full_order_key == full_order_key
        ).first()
        
        if not order_tracking:
            order_tracking = models.OrderTracking(
                order_code=order_code,
                order_date=order_date,
                full_order_key=full_order_key,
                total_products=int(product_input.total),
                received_products=0,
                assigned_cell_id=target_cell.id,
                status="pending"
            )
            db.add(order_tracking)
        
        order_tracking.received_products = (order_tracking.received_products or 0) + 1
        if order_tracking.received_products >= order_tracking.total_products:
            order_tracking.status = "completed"
            order_tracking.completed_at = datetime.utcnow()
        else:
            order_tracking.status = "filling"
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Đã phân bổ sản phẩm vào ô {target_cell.cell_name} trong lưới {target_grid.name}",
            "grid_id": target_grid.id,
            "grid_name": target_grid.name,
            "cell_id": target_cell.id,
            "cell_name": target_cell.cell_name,
            "cell_position": f"({target_cell.position_x}, {target_cell.position_y})",
            "order_code": order_code,
            "current_count": target_cell.current_product_count,
            "target_count": target_cell.target_product_count,
            "cell_status": target_cell.status,
            "product_info": {
                "production_area": product_info["production_area"],
                "size_code": product_info["size_code"],
                "order_number": product_info["order_number"],
                "product_number": product_info["product_number"],
                "order_date": qr_info["order_date"]
            }
        }
        
    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "message": f"Lỗi khi phân bổ sản phẩm: {str(e)}"
        }

# Cell CRUD
def update_cell_note(db: Session, cell_id: int, note: Optional[str]) -> bool:
    """Cập nhật ghi chú cho ô"""
    cell = db.query(models.GridCell).filter(models.GridCell.id == cell_id).first()
    if not cell:
        return False
    
    old_note = cell.note
    cell.note = note
    cell.updated_at = datetime.utcnow()
    
    # Log: Update note
    log_cell_history(
        db=db,
        cell_id=cell_id,
        action_type="note_updated",
        description=f"Cập nhật ghi chú cho ô {cell.cell_name}",
        order_code=cell.current_order_code,
        order_date=cell.current_order_date,
        old_data={"note": old_note},
        new_data={"note": note}
    )
    
    db.commit()
    return True

def clear_cell(db: Session, cell_id: int) -> bool:
    """
    Giải phóng ô - chuyển sản phẩm vào lịch sử và reset ô
    """
    try:
        cell = db.query(models.GridCell).filter(models.GridCell.id == cell_id).first()
        if not cell or cell.status == "empty":
            return False
        
        # Lấy tất cả sản phẩm trong ô
        products = db.query(models.Product).filter(models.Product.cell_id == cell_id).all()
        
        if products:
            # Tạo lịch sử
            products_data = []
            for product in products:
                products_data.append({
                    "product_code": product.product_code,
                    "size": product.size,
                    "color": product.color,
                    "qr_data": product.qr_data,
                    "number": product.number,
                    "total": product.total,
                    "created_at": product.created_at.isoformat()
                })
            
            # Log: Clear cell (giao hàng)
            log_cell_history(
                db=db,
                cell_id=cell_id,
                action_type="cell_cleared",
                description=f"Giải phóng ô {cell.cell_name} - Giao đơn hàng {cell.current_order_code}",
                order_code=cell.current_order_code,
                order_date=cell.current_order_date,
                old_data={
                    "status": cell.status,
                    "order_code": cell.current_order_code,
                    "product_count": cell.current_product_count,
                    "note": cell.note
                },
                new_data={
                    "status": "empty",
                    "order_code": None,
                    "product_count": 0
                },
                products_data=json.dumps(products_data, ensure_ascii=False),
                product_count=cell.current_product_count or len(products)
            )
            
            # Xóa tất cả sản phẩm
            for product in products:
                db.delete(product)
        
        # Cập nhật order tracking
        if cell.current_full_order_key:
            order_tracking = db.query(models.OrderTracking).filter(
                models.OrderTracking.full_order_key == cell.current_full_order_key
            ).first()
            if order_tracking:
                order_tracking.status = "shipped"
                order_tracking.shipped_at = datetime.utcnow()
        
        # Reset ô
        cell.current_order_code = None
        cell.current_order_date = None
        cell.current_full_order_key = None
        cell.current_product_count = 0
        cell.target_product_count = None
        cell.status = "empty"
        cell.note = None
        cell.filled_at = None
        cell.cleared_at = datetime.utcnow()
        cell.updated_at = datetime.utcnow()
        
        db.commit()
        return True
        
    except Exception as e:
        db.rollback()
        return False

def get_grid_status(db: Session, grid_id: int) -> Optional[dict]:
    """Lấy trạng thái tổng quan của lưới"""
    grid = get_grid_with_cells(db, grid_id)
    if not grid:
        return None
    
    empty_count = sum(1 for cell in grid.cells if cell.status == "empty")
    filling_count = sum(1 for cell in grid.cells if cell.status == "filling")
    full_count = sum(1 for cell in grid.cells if cell.status == "full")
    
    return {
        "grid_id": grid.id,
        "grid_name": grid.name,
        "total_cells": grid.total_cells,
        "empty_cells": empty_count,
        "filling_cells": filling_count,
        "full_cells": full_count,
        "cells": grid.cells
    }

def get_cell_histories(db: Session, cell_id: int) -> List[models.CellHistory]:
    """Lấy lịch sử của ô"""
    return db.query(models.CellHistory).filter(
        models.CellHistory.cell_id == cell_id
    ).order_by(models.CellHistory.cleared_at.desc()).all()

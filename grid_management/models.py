from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from core.core.database import Base

class Grid(Base):
    """
    Bảng quản lý lưới (grid) - lưu thông tin về kích thước và cấu hình lưới
    """
    __tablename__ = "grids"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment="Tên lưới")
    width = Column(Integer, nullable=False, comment="Chiều rộng lưới")
    height = Column(Integer, nullable=False, comment="Chiều cao lưới")
    total_cells = Column(Integer, nullable=False, comment="Tổng số ô (width * height)")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True, comment="Trạng thái hoạt động")
    
    # Relationship
    cells = relationship("GridCell", back_populates="grid", cascade="all, delete-orphan")

class GridCell(Base):
    """
    Bảng quản lý từng ô trong lưới
    """
    __tablename__ = "grid_cells"
    
    id = Column(Integer, primary_key=True, index=True)
    grid_id = Column(Integer, ForeignKey("grids.id"), nullable=False)
    position_x = Column(Integer, nullable=False, comment="Vị trí X trong lưới (0-based)")
    position_y = Column(Integer, nullable=False, comment="Vị trí Y trong lưới (0-based)")
    cell_name = Column(String(50), nullable=False, comment="Tên ô (ví dụ: A1, B2)")
    
    # Thông tin đơn hàng hiện tại
    current_order_code = Column(String(100), nullable=True, comment="Mã đơn hàng hiện tại (VA-M-000126)")
    current_order_date = Column(String(10), nullable=True, comment="Ngày đơn hàng hiện tại (101725)")
    current_full_order_key = Column(String(120), nullable=True, comment="Key đầy đủ: order_code-order_date")
    current_product_count = Column(Integer, default=0, comment="Số sản phẩm hiện tại trong ô")
    target_product_count = Column(Integer, nullable=True, comment="Tổng số sản phẩm cần có trong đơn hàng")
    
    # Trạng thái ô
    status = Column(String(20), default="empty", comment="Trạng thái: empty, filling, full")
    note = Column(Text, nullable=True, comment="Ghi chú cho ô")
    
    # Thời gian
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    filled_at = Column(DateTime, nullable=True, comment="Thời gian ô được đầy")
    cleared_at = Column(DateTime, nullable=True, comment="Thời gian ô được giải phóng")
    
    # Unique constraint cho vị trí trong grid
    __table_args__ = (UniqueConstraint('grid_id', 'position_x', 'position_y', name='unique_cell_position'),)
    
    # Relationships
    grid = relationship("Grid", back_populates="cells")
    products = relationship("Product", back_populates="cell", cascade="all, delete-orphan")
    histories = relationship("CellHistory", back_populates="cell", cascade="all, delete-orphan")
    order_tracking = relationship("OrderTracking", back_populates="assigned_cell")

class Product(Base):
    """
    Bảng lưu thông tin chi tiết từng sản phẩm trong ô
    """
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    cell_id = Column(Integer, ForeignKey("grid_cells.id"), nullable=False)
    
    # Thông tin sản phẩm từ FE
    product_code = Column(String(100), nullable=False, unique=True, comment="Mã sản phẩm: VA-M-000126-2 (UNIQUE)")
    size = Column(String(10), nullable=False, comment="Kích thước: S, M, L, XL")
    color = Column(String(50), nullable=False, comment="Màu sắc")
    qr_data = Column(String(200), nullable=False, comment="Dữ liệu QR: 101725-VA-M-000126-2")
    number = Column(Integer, nullable=False, comment="Số thứ tự sản phẩm trong đơn hàng")
    total = Column(Integer, nullable=False, comment="Tổng số sản phẩm trong đơn hàng")
    
    # Thông tin phân tích từ product_code
    production_area = Column(String(10), nullable=False, comment="Khu sản xuất: VA")
    size_code = Column(String(5), nullable=False, comment="Mã size: M")
    order_number = Column(String(20), nullable=False, comment="Mã đơn hàng: 000126")
    product_number = Column(Integer, nullable=False, comment="Số sản phẩm: 2")
    
    # Thông tin thời gian từ qr_data
    order_date = Column(String(10), nullable=False, comment="Ngày đơn hàng: 101725")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    cell = relationship("GridCell", back_populates="products")

class CellHistory(Base):
    """
    Bảng lưu lịch sử của từng ô - mỗi lần ô được đầy và giải phóng
    """
    __tablename__ = "cell_histories"
    
    id = Column(Integer, primary_key=True, index=True)
    cell_id = Column(Integer, ForeignKey("grid_cells.id"), nullable=False)
    
    # Thông tin đơn hàng đã hoàn thành
    order_code = Column(String(100), nullable=False, comment="Mã đơn hàng đã hoàn thành")
    product_count = Column(Integer, nullable=False, comment="Số sản phẩm đã hoàn thành")
    products_data = Column(Text, nullable=False, comment="JSON data của tất cả sản phẩm")
    
    # Thông tin thời gian
    started_at = Column(DateTime, nullable=False, comment="Thời gian bắt đầu nhận đơn hàng")
    completed_at = Column(DateTime, nullable=False, comment="Thời gian hoàn thành đơn hàng")
    cleared_at = Column(DateTime, default=datetime.utcnow, comment="Thời gian giải phóng ô")
    
    # Ghi chú tại thời điểm hoàn thành
    note_at_completion = Column(Text, nullable=True, comment="Ghi chú khi hoàn thành")
    
    # Relationships
    cell = relationship("GridCell", back_populates="histories")

class OrderTracking(Base):
    """
    Bảng theo dõi trạng thái đơn hàng
    """
    __tablename__ = "order_tracking"
    
    id = Column(Integer, primary_key=True, index=True)
    order_code = Column(String(100), nullable=False, comment="Mã đơn hàng: VA-M-000126")
    order_date = Column(String(10), nullable=False, comment="Ngày đơn hàng: 101725")
    full_order_key = Column(String(120), nullable=False, unique=True, comment="Key đầy đủ: order_code-order_date")
    total_products = Column(Integer, nullable=False, comment="Tổng số sản phẩm trong đơn hàng")
    received_products = Column(Integer, default=0, comment="Số sản phẩm đã nhận")
    assigned_cell_id = Column(Integer, ForeignKey("grid_cells.id"), nullable=True, comment="Ô được phân bổ")
    
    status = Column(String(20), default="pending", comment="Trạng thái: pending, filling, completed, shipped")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True, comment="Thời gian hoàn thành đơn hàng")
    shipped_at = Column(DateTime, nullable=True, comment="Thời gian giao hàng")
    
    # Relationships
    assigned_cell = relationship("GridCell", back_populates="order_tracking")

class CellActivityLog(Base):
    """
    Bảng ghi lại TẤT CẢ hoạt động trên ô
    - Thêm sản phẩm
    - Đổi trạng thái
    - Update ghi chú
    - Giải phóng ô
    """
    __tablename__ = "cell_activity_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    cell_id = Column(Integer, ForeignKey("grid_cells.id"), nullable=False)
    
    action = Column(String(50), nullable=False, comment="Hành động: product_added, status_changed, note_updated, cell_cleared")
    description = Column(Text, nullable=False, comment="Mô tả chi tiết hành động")
    
    # Thông tin trước và sau
    old_value = Column(Text, nullable=True, comment="Giá trị cũ (JSON)")
    new_value = Column(Text, nullable=True, comment="Giá trị mới (JSON)")
    
    # Thông tin người thực hiện (nếu có auth)
    performed_by = Column(String(100), nullable=True, comment="Người thực hiện (user_id hoặc 'system')")
    
    created_at = Column(DateTime, default=datetime.utcnow, comment="Thời gian thực hiện")
    
    # Relationships
    cell = relationship("GridCell", backref="activity_logs")

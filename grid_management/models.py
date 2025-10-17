from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from core.core.database import Base

class Grid(Base):
    """
    Grid management table - stores grid size and configuration
    """
    __tablename__ = "grids"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment="Grid name")
    width = Column(Integer, nullable=False, comment="Grid width")
    height = Column(Integer, nullable=False, comment="Grid height")
    total_cells = Column(Integer, nullable=False, comment="Total cells (width * height)")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True, comment="Active status")
    
    # Relationship
    cells = relationship("GridCell", back_populates="grid", cascade="all, delete-orphan")

class GridCell(Base):
    """
    Cell management table - each cell in the grid
    """
    __tablename__ = "grid_cells"
    
    id = Column(Integer, primary_key=True, index=True)
    grid_id = Column(Integer, ForeignKey("grids.id"), nullable=False)
    position_x = Column(Integer, nullable=False, comment="X position in grid (0-based)")
    position_y = Column(Integer, nullable=False, comment="Y position in grid (0-based)")
    cell_name = Column(String(50), nullable=False, comment="Cell name (e.g: A1, B2)")
    
    # Current order information
    current_order_code = Column(String(100), nullable=True, comment="Current order code (VA-M-000126)")
    current_order_date = Column(String(10), nullable=True, comment="Current order date (101725)")
    current_full_order_key = Column(String(120), nullable=True, comment="Full key: order_code-order_date")
    current_product_count = Column(Integer, default=0, comment="Current product count in cell")
    target_product_count = Column(Integer, nullable=True, comment="Total products needed for order")
    
    # Cell status
    status = Column(String(20), default="empty", comment="Status: empty, filling, full")
    note = Column(Text, nullable=True, comment="Cell note")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    filled_at = Column(DateTime, nullable=True, comment="Time when cell was filled")
    cleared_at = Column(DateTime, nullable=True, comment="Time when cell was cleared")
    
    # Unique constraint cho vị trí trong grid
    __table_args__ = (UniqueConstraint('grid_id', 'position_x', 'position_y', name='unique_cell_position'),)
    
    # Relationships
    grid = relationship("Grid", back_populates="cells")
    products = relationship("Product", back_populates="cell", cascade="all, delete-orphan")
    histories = relationship("CellHistory", back_populates="cell", cascade="all, delete-orphan")
    order_tracking = relationship("OrderTracking", back_populates="assigned_cell")

class Product(Base):
    """
    Product details table - each product in a cell
    """
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    cell_id = Column(Integer, ForeignKey("grid_cells.id"), nullable=False)
    
    # Product information from FE
    product_code = Column(String(100), nullable=False, unique=True, comment="Product code: VA-M-000126-2 (UNIQUE)")
    size = Column(String(10), nullable=False, comment="Size: S, M, L, XL")
    color = Column(String(50), nullable=False, comment="Color")
    qr_data = Column(String(200), nullable=False, comment="QR data: 101725-VA-M-000126-2")
    number = Column(Integer, nullable=False, comment="Product sequence number in order")
    total = Column(Integer, nullable=False, comment="Total products in order")
    
    # Parsed information from product_code
    production_area = Column(String(10), nullable=False, comment="Production area: VA")
    size_code = Column(String(5), nullable=False, comment="Size code: M")
    order_number = Column(String(20), nullable=False, comment="Order number: 000126")
    product_number = Column(Integer, nullable=False, comment="Product number: 2")
    
    # Time information from qr_data
    order_date = Column(String(10), nullable=False, comment="Order date: 101725")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    cell = relationship("GridCell", back_populates="products")

class CellHistory(Base):
    """
    Cell history table - ALL cell activities
    - Product added
    - Status changed
    - Note updated
    - Cell cleared
    """
    __tablename__ = "cell_histories"
    
    id = Column(Integer, primary_key=True, index=True)
    cell_id = Column(Integer, ForeignKey("grid_cells.id"), nullable=False)
    
    # Action type
    action_type = Column(String(50), nullable=False, comment="Type: product_added, status_changed, note_updated, cell_cleared")
    description = Column(Text, nullable=False, comment="Detailed description")
    
    # Order information (if any)
    order_code = Column(String(100), nullable=True, comment="Related order code")
    order_date = Column(String(10), nullable=True, comment="Order date")
    
    # Old and new data (JSON)
    old_data = Column(Text, nullable=True, comment="Data before change (JSON)")
    new_data = Column(Text, nullable=True, comment="Data after change (JSON)")
    
    # Additional info for cell_cleared action
    products_data = Column(Text, nullable=True, comment="Product JSON data when cleared")
    product_count = Column(Integer, nullable=True, comment="Product count when cleared")
    
    # Performer
    performed_by = Column(String(100), default="system", comment="Performed by")
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, comment="Action timestamp")
    
    # Relationships
    cell = relationship("GridCell", back_populates="histories")

class OrderTracking(Base):
    """
    Order tracking table - order status tracking
    """
    __tablename__ = "order_tracking"
    
    id = Column(Integer, primary_key=True, index=True)
    order_code = Column(String(100), nullable=False, comment="Order code: VA-M-000126")
    order_date = Column(String(10), nullable=False, comment="Order date: 101725")
    full_order_key = Column(String(120), nullable=False, unique=True, comment="Full key: order_code-order_date")
    total_products = Column(Integer, nullable=False, comment="Total products in order")
    received_products = Column(Integer, default=0, comment="Received products count")
    assigned_cell_id = Column(Integer, ForeignKey("grid_cells.id"), nullable=True, comment="Assigned cell")
    
    status = Column(String(20), default="pending", comment="Status: pending, filling, completed, shipped")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True, comment="Order completion time")
    shipped_at = Column(DateTime, nullable=True, comment="Shipping time")
    
    # Relationships
    assigned_cell = relationship("GridCell", back_populates="order_tracking")

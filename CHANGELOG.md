# 🔄 Changelog - Grid Management API

## ✅ Đã cập nhật

### 1. **Schema ProductInput - Format đúng**

**Cũ (SAI):**
```json
{
  "qr_data": "101725-VA-M-000126-2",
  "size": "M",
  "color": "Đỏ",
  "number": 2,
  "total": 5
}
```

**Mới (ĐÚNG):**
```json
{
  "productCode": "VA-M-000126-2",
  "qrData": "101725-VA-M-000126-2",
  "size": "M",
  "color": "Đỏ",
  "number": "2",
  "total": "5"
}
```

**Lưu ý:**
- ✅ `productCode` (camelCase) - bắt buộc
- ✅ `qrData` (camelCase) - bắt buộc  
- ✅ `number` và `total` phải là **string**, không phải integer

---

### 2. **API Mới - Cell Detail**

**Endpoint:** `GET /v1/api/grid/cell/{cell_id}/detail`

Lấy thông tin chi tiết ô bao gồm:
- ✅ Thông tin ô (id, name, status, position...)
- ✅ **Danh sách sản phẩm hiện tại** (với timestamp `created_at`)
- ✅ **Lịch sử giao hàng** của ô (histories)

**Example:**
```bash
curl -X GET "http://localhost:8000/v1/api/grid/cell/1/detail"
```

**Response:**
```json
{
  "id": 1,
  "cell_name": "A1",
  "status": "full",
  "products": [
    {
      "id": 1,
      "product_code": "VA-M-000126-1",
      "created_at": "2024-01-15T10:30:00",
      ...
    }
  ],
  "histories": [
    {
      "id": 1,
      "order_code": "VA-M-000100",
      "cleared_at": "2024-01-14T14:00:00",
      ...
    }
  ]
}
```

---

### 3. **API Mới - Update Cell Status**

**Endpoint:** `PUT /v1/api/grid/cell/{cell_id}/status`

Cập nhật trạng thái ô (empty/filling/full)

**Example:**
```bash
curl -X PUT "http://localhost:8000/v1/api/grid/cell/1/status" \
  -H "Content-Type: application/json" \
  -d '{"status": "full"}'
```

**Các trạng thái hợp lệ:**
- `empty`: Ô trống
- `filling`: Đang nhận hàng
- `full`: Đã đầy

---

### 4. **API Đã Xóa**

❌ `GET /v1/api/grid/{grid_id}/status` - Đã xóa

**Lý do:** Thông tin này đã có trong endpoint `GET /v1/api/grid/{grid_id}` (grid detail)

---

### 5. **API Mới - Update Grid Size**

**Endpoint:** `PUT /v1/api/grid/{grid_id}`

Cập nhật lưới (tên hoặc kích thước)

**Example - Tăng size từ 5x4 → 10x10:**
```bash
curl -X PUT "http://localhost:8000/v1/api/grid/1" \
  -H "Content-Type: application/json" \
  -d '{"width": 10, "height": 10}'
```

**Logic:**
- ✅ **Tăng kích thước**: Tự động tạo thêm cells mới
- ⚠️ **Giảm kích thước**: Chỉ cho phép nếu cells bị xóa KHÔNG có sản phẩm
- ✅ **Đổi tên**: Không ảnh hưởng cells

---

## 📝 Tóm tắt

| Thay đổi | Loại | Mô tả |
|----------|------|-------|
| ProductInput Schema | **FIX** | Sử dụng camelCase, number/total là string |
| `/cell/{id}/detail` | **NEW** | Lấy chi tiết ô + products + histories |
| `/cell/{id}/status` | **NEW** | Cập nhật trạng thái ô |
| `/grid/{id}` (PUT) | **NEW** | Update grid (tên/kích thước) |
| `/grid/{id}/status` | **REMOVED** | Đã xóa, dùng grid detail thay thế |

---

## 🚀 Migration Guide

### Nếu đang dùng assign-product API:

**Trước:**
```python
data = {
    "qr_data": "...",
    "number": 2,
    "total": 5
}
```

**Sau:**
```python
data = {
    "productCode": "VA-M-000126-2",
    "qrData": "...",
    "number": "2",     # String
    "total": "5"       # String
}
```

### Nếu đang dùng grid status API:

**Trước:**
```python
response = requests.get(f"/v1/api/grid/{grid_id}/status")
```

**Sau:**
```python
# Option 1: Dùng grid detail (có đầy đủ cells)
response = requests.get(f"/v1/api/grid/{grid_id}")

# Option 2: Dùng stats summary (nếu chỉ cần số liệu tổng quan)
response = requests.get("/v1/api/grid/stats/summary")
```

---

**Ngày cập nhật:** 2024-10-17


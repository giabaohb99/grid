# 📘 Hướng Dẫn Test API - Grid Management System

## 🚀 Khởi động API

### Với Docker:
```bash
docker-compose up -d
```

### Không dùng Docker:
```bash
# Cài đặt dependencies
pip install -r requirements.txt

# Chạy server
python main.py
# hoặc
uvicorn main:app --reload
```

API sẽ chạy tại: **http://localhost:8000**

## 📚 API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 🧪 Test API Endpoints

### 1️⃣ Grid Management (Quản lý lưới)

#### 1.1. Tạo lưới mới
Tạo một lưới 5x4 (5 cột x 4 hàng = 20 ô)

```bash
curl -X POST "http://localhost:8000/v1/api/grid/create" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Kho A - Lưới 1",
    "width": 5,
    "height": 4
  }'
```

**Python:**
```python
import requests

url = "http://localhost:8000/v1/api/grid/create"
data = {
    "name": "Kho A - Lưới 1",
    "width": 5,
    "height": 4
}
response = requests.post(url, json=data)
print(response.json())
```

**Response:**
```json
{
  "id": 1,
  "name": "Kho A - Lưới 1",
  "width": 5,
  "height": 4,
  "total_cells": 20,
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T10:30:00",
  "is_active": true
}
```

---

#### 1.2. Lấy danh sách tất cả lưới

```bash
curl -X GET "http://localhost:8000/v1/api/grid/list?skip=0&limit=10"
```

**Python:**
```python
url = "http://localhost:8000/v1/api/grid/list"
params = {"skip": 0, "limit": 10}
response = requests.get(url, params=params)
print(response.json())
```

---

#### 1.3. Xem chi tiết lưới (kèm tất cả các ô)

```bash
curl -X GET "http://localhost:8000/v1/api/grid/1"
```

**Python:**
```python
grid_id = 1
url = f"http://localhost:8000/v1/api/grid/{grid_id}"
response = requests.get(url)
print(response.json())
```

**Response:**
```json
{
  "id": 1,
  "name": "Kho A - Lưới 1",
  "width": 5,
  "height": 4,
  "total_cells": 20,
  "cells": [
    {
      "id": 1,
      "cell_name": "A1",
      "position_x": 0,
      "position_y": 0,
      "status": "empty",
      "current_product_count": 0,
      "current_order_code": null,
      "note": null
    }
    // ... 19 ô khác
  ]
}
```

---

#### 1.4. Cập nhật lưới (tên hoặc kích thước)

**API mới**: Update grid - Thay đổi tên hoặc kích thước lưới

```bash
# Chỉ đổi tên
curl -X PUT "http://localhost:8000/v1/api/grid/1" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Kho A - Lưới Mới"
  }'

# Tăng kích thước từ 5x4 lên 10x10
curl -X PUT "http://localhost:8000/v1/api/grid/1" \
  -H "Content-Type: application/json" \
  -d '{
    "width": 10,
    "height": 10
  }'

# Đổi cả tên và kích thước
curl -X PUT "http://localhost:8000/v1/api/grid/1" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Kho B",
    "width": 8,
    "height": 6
  }'
```

**Python:**
```python
grid_id = 1
url = f"http://localhost:8000/v1/api/grid/{grid_id}"

# Tăng kích thước từ 5x4 → 10x10
data = {
    "width": 10,
    "height": 10
}
response = requests.put(url, json=data)
print(response.json())
```

**Response Success:**
```json
{
  "id": 1,
  "name": "Kho A - Lưới 1",
  "width": 10,
  "height": 10,
  "total_cells": 100,
  "created_at": "2024-01-15T10:00:00",
  "is_active": true
}
```

**Response Error (nếu giảm size mà có ô đang chứa sản phẩm):**
```json
{
  "detail": "Không thể giảm kích thước. Các ô sau đây đang có sản phẩm: E5, F1, F2"
}
```

**Logic xử lý:**

**Tăng kích thước (5x4 → 10x10):**
- ✅ Tự động tạo thêm 80 ô mới (từ 20 ô → 100 ô)
- ✅ Các ô cũ giữ nguyên (kể cả sản phẩm đang có)
- ✅ Cell naming: A1-A10, B1-B10, ..., J1-J10

**Giảm kích thước (10x10 → 5x4):**
- ⚠️ Kiểm tra các ô sẽ bị xóa
- ❌ Nếu có ô đang chứa sản phẩm → **Báo lỗi**, không cho phép
- ✅ Nếu tất cả ô trống → Xóa và giảm kích thước

**Chỉ đổi tên:**
- ✅ Không ảnh hưởng đến cells

---

### 2️⃣ Product Assignment (Quét & phân bổ sản phẩm)

#### 2.1. Quét QR và phân bổ sản phẩm tự động

**Kịch bản**: Quét QR code sản phẩm `101725-VA-M-000126-2`

**⚠️ LưU Ý**: Các field phải đúng format camelCase và number/total là **string**

```bash
curl -X POST "http://localhost:8000/v1/api/grid/assign-product" \
  -H "Content-Type: application/json" \
  -d '{
    "productCode": "VA-M-000126-2",
    "qrData": "101725-VA-M-000126-2",
    "size": "M",
    "color": "Đỏ",
    "number": "2",
    "total": "5"
  }'
```

**Python:**
```python
url = "http://localhost:8000/v1/api/grid/assign-product"
product_data = {
    "productCode": "VA-M-000126-2",      # Mã sản phẩm
    "qrData": "101725-VA-M-000126-2",    # Dữ liệu QR (order_date-product_code)
    "size": "M",                          # Kích thước
    "color": "Đỏ",                        # Màu sắc
    "number": "2",                        # Sản phẩm thứ 2 (STRING)
    "total": "5"                          # Tổng 5 sản phẩm (STRING)
}
response = requests.post(url, json=product_data)
print(response.json())
```

**Response Success:**
```json
{
  "success": true,
  "message": "Đã phân bổ sản phẩm vào ô A1",
  "product": {
    "id": 1,
    "product_code": "VA-M-000126-2",
    "qr_data": "101725-VA-M-000126-2",
    "size": "M",
    "color": "Đỏ",
    "number": 2,
    "total": 5,
    "production_area": "VA",
    "order_number": "000126",
    "order_date": "101725"
  },
  "assigned_cell": {
    "id": 1,
    "cell_name": "A1",
    "position_x": 0,
    "position_y": 0,
    "status": "filling",
    "current_product_count": 1,
    "target_product_count": 5,
    "current_order_code": "VA-M-000126",
    "current_full_order_key": "VA-M-000126-101725"
  },
  "order_tracking": {
    "order_code": "VA-M-000126",
    "order_date": "101725",
    "full_order_key": "VA-M-000126-101725",
    "total_products": 5,
    "received_products": 1,
    "status": "filling"
  }
}
```

**Response Error - Duplicate:**
```json
{
  "detail": "Sản phẩm VA-M-000126-2 đã tồn tại trong hệ thống"
}
```

---

#### 2.2. Quét nhiều sản phẩm cùng đơn hàng

```bash
# Sản phẩm 1
curl -X POST "http://localhost:8000/v1/api/grid/assign-product" \
  -H "Content-Type: application/json" \
  -d '{"productCode":"VA-M-000126-1","qrData":"101725-VA-M-000126-1","size":"M","color":"Đỏ","number":"1","total":"5"}'

# Sản phẩm 2
curl -X POST "http://localhost:8000/v1/api/grid/assign-product" \
  -H "Content-Type: application/json" \
  -d '{"productCode":"VA-M-000126-2","qrData":"101725-VA-M-000126-2","size":"M","color":"Đỏ","number":"2","total":"5"}'

# Sản phẩm 3
curl -X POST "http://localhost:8000/v1/api/grid/assign-product" \
  -H "Content-Type: application/json" \
  -d '{"productCode":"VA-M-000126-3","qrData":"101725-VA-M-000126-3","size":"L","color":"Xanh","number":"3","total":"5"}'

# Sản phẩm 4
curl -X POST "http://localhost:8000/v1/api/grid/assign-product" \
  -H "Content-Type: application/json" \
  -d '{"productCode":"VA-M-000126-4","qrData":"101725-VA-M-000126-4","size":"M","color":"Đỏ","number":"4","total":"5"}'

# Sản phẩm 5 (Ô sẽ chuyển sang status="full")
curl -X POST "http://localhost:8000/v1/api/grid/assign-product" \
  -H "Content-Type: application/json" \
  -d '{"productCode":"VA-M-000126-5","qrData":"101725-VA-M-000126-5","size":"S","color":"Vàng","number":"5","total":"5"}'
```

**Python - Loop:**
```python
products = [
    {"productCode":"VA-M-000126-1","qrData":"101725-VA-M-000126-1","size":"M","color":"Đỏ","number":"1","total":"5"},
    {"productCode":"VA-M-000126-2","qrData":"101725-VA-M-000126-2","size":"M","color":"Đỏ","number":"2","total":"5"},
    {"productCode":"VA-M-000126-3","qrData":"101725-VA-M-000126-3","size":"L","color":"Xanh","number":"3","total":"5"},
    {"productCode":"VA-M-000126-4","qrData":"101725-VA-M-000126-4","size":"M","color":"Đỏ","number":"4","total":"5"},
    {"productCode":"VA-M-000126-5","qrData":"101725-VA-M-000126-5","size":"S","color":"Vàng","number":"5","total":"5"},
]

url = "http://localhost:8000/v1/api/grid/assign-product"
for product in products:
    response = requests.post(url, json=product)
    print(f"Sản phẩm {product['number']}: {response.json()}")
```

---

#### 2.3. Kiểm tra sản phẩm đã tồn tại chưa

```bash
curl -X GET "http://localhost:8000/v1/api/grid/product/VA-M-000126-2/check"
```

**Python:**
```python
product_code = "VA-M-000126-2"
url = f"http://localhost:8000/v1/api/grid/product/{product_code}/check"
response = requests.get(url)
print(response.json())
```

**Response:**
```json
{
  "product_code": "VA-M-000126-2",
  "exists": true,
  "message": "Sản phẩm đã tồn tại"
}
```

---

### 3️⃣ Cell Management (Quản lý ô)

#### 3.1. Lấy chi tiết ô (kèm products & history)

**API mới**: Lấy chi tiết đầy đủ của 1 ô, bao gồm:
- Thông tin ô
- Danh sách sản phẩm hiện tại (có timestamp `created_at`)
- Lịch sử giao hàng của ô

```bash
curl -X GET "http://localhost:8000/v1/api/grid/cell/1/detail"
```

**Python:**
```python
cell_id = 1
url = f"http://localhost:8000/v1/api/grid/cell/{cell_id}/detail"
response = requests.get(url)
print(response.json())
```

**Response:**
```json
{
  "id": 1,
  "cell_name": "A1",
  "position_x": 0,
  "position_y": 0,
  "status": "full",
  "current_order_code": "VA-M-000126",
  "current_order_date": "101725",
  "current_full_order_key": "VA-M-000126-101725",
  "current_product_count": 5,
  "target_product_count": 5,
  "note": "Ưu tiên giao hàng trước 3PM",
  "created_at": "2024-01-15T10:00:00",
  "updated_at": "2024-01-15T11:00:00",
  "filled_at": "2024-01-15T11:00:00",
  "cleared_at": null,
  "products": [
    {
      "id": 1,
      "product_code": "VA-M-000126-1",
      "size": "M",
      "color": "Đỏ",
      "qr_data": "101725-VA-M-000126-1",
      "number": 1,
      "total": 5,
      "created_at": "2024-01-15T10:30:00",
      "production_area": "VA",
      "order_number": "000126",
      "order_date": "101725"
    },
    {
      "id": 2,
      "product_code": "VA-M-000126-2",
      "created_at": "2024-01-15T10:32:00",
      ...
    }
    // ... 3 sản phẩm khác
  ],
  "histories": [
    {
      "id": 1,
      "order_code": "VA-M-000100",
      "product_count": 3,
      "started_at": "2024-01-14T09:00:00",
      "completed_at": "2024-01-14T10:00:00",
      "cleared_at": "2024-01-14T14:00:00",
      "note_at_completion": "Giao rồi",
      "products_data": "[{...}, {...}, {...}]"
    }
  ]
}
```

---

#### 3.2. Cập nhật trạng thái ô

**API mới**: Cập nhật trạng thái ô (empty/filling/full)

```bash
curl -X PUT "http://localhost:8000/v1/api/grid/cell/1/status" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "full"
  }'
```

**Python:**
```python
cell_id = 1
url = f"http://localhost:8000/v1/api/grid/cell/{cell_id}/status"
data = {"status": "full"}  # empty, filling, hoặc full
response = requests.put(url, json=data)
print(response.json())
```

**Response:**
```json
{
  "success": true,
  "message": "Đã cập nhật trạng thái ô A1 thành 'full'",
  "cell_id": 1,
  "cell_name": "A1",
  "new_status": "full"
}
```

**Các trạng thái hợp lệ:**
- `empty`: Ô trống
- `filling`: Đang nhận hàng
- `full`: Đã đầy

---

#### 3.3. Cập nhật ghi chú cho ô

```bash
curl -X PUT "http://localhost:8000/v1/api/grid/cell/1/note" \
  -H "Content-Type: application/json" \
  -d '{
    "note": "Ưu tiên giao hàng trước 3PM"
  }'
```

**Python:**
```python
cell_id = 1
url = f"http://localhost:8000/v1/api/grid/cell/{cell_id}/note"
data = {"note": "Ưu tiên giao hàng trước 3PM"}
response = requests.put(url, json=data)
print(response.json())
```

**Response:**
```json
{
  "success": true,
  "message": "Đã cập nhật ghi chú cho ô",
  "cell_id": 1,
  "note": "Ưu tiên giao hàng trước 3PM"
}
```

---

#### 3.4. Giải phóng ô - Giao hàng (Clear Cell)

```bash
curl -X POST "http://localhost:8000/v1/api/grid/cell/1/clear"
```

**Python:**
```python
cell_id = 1
url = f"http://localhost:8000/v1/api/grid/cell/{cell_id}/clear"
response = requests.post(url)
print(response.json())
```

**Response:**
```json
{
  "success": true,
  "message": "Đã giải phóng ô và giao hàng thành công",
  "cell_id": 1
}
```

**Sau khi clear:**
- Tất cả sản phẩm được chuyển vào `cell_histories`
- Ô reset về `status="empty"`, `current_product_count=0`
- Order tracking chuyển sang `status="shipped"`

---

#### 3.5. Xem lịch sử của ô (deprecated - dùng cell detail thay thế)

```bash
curl -X GET "http://localhost:8000/v1/api/grid/cell/1/history"
```

**Python:**
```python
cell_id = 1
url = f"http://localhost:8000/v1/api/grid/cell/{cell_id}/history"
response = requests.get(url)
print(response.json())
```

**Response:**
```json
[
  {
    "id": 1,
    "cell_id": 1,
    "order_code": "VA-M-000126",
    "product_count": 5,
    "started_at": "2024-01-15T10:30:00",
    "completed_at": "2024-01-15T11:00:00",
    "cleared_at": "2024-01-15T11:05:00",
    "note_at_completion": "Ưu tiên giao hàng trước 3PM",
    "products_data": "[{...}, {...}]"  // JSON string
  }
]
```

---

### 4️⃣ Order Tracking (Theo dõi đơn hàng)

#### 4.1. Lấy trạng thái đơn hàng

```bash
curl -X GET "http://localhost:8000/v1/api/grid/order/VA-M-000126-101725"
```

**Python:**
```python
full_order_key = "VA-M-000126-101725"
url = f"http://localhost:8000/v1/api/grid/order/{full_order_key}"
response = requests.get(url)
print(response.json())
```

**Response:**
```json
{
  "id": 1,
  "order_code": "VA-M-000126",
  "order_date": "101725",
  "full_order_key": "VA-M-000126-101725",
  "total_products": 5,
  "received_products": 5,
  "assigned_cell_id": 1,
  "status": "completed",
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T11:00:00",
  "completed_at": "2024-01-15T11:00:00",
  "shipped_at": null
}
```

**Các trạng thái đơn hàng:**
- `pending`: Mới tạo, chưa nhận sản phẩm nào
- `filling`: Đang nhận sản phẩm
- `completed`: Đã nhận đủ sản phẩm
- `shipped`: Đã giao hàng

---

#### 4.2. Lấy danh sách đơn hàng

```bash
# Tất cả đơn hàng
curl -X GET "http://localhost:8000/v1/api/grid/orders/list?skip=0&limit=10"

# Lọc theo trạng thái
curl -X GET "http://localhost:8000/v1/api/grid/orders/list?status_filter=filling&skip=0&limit=10"
```

**Python:**
```python
# Tất cả đơn hàng
url = "http://localhost:8000/v1/api/grid/orders/list"
params = {"skip": 0, "limit": 10}
response = requests.get(url, params=params)
print(response.json())

# Lọc đơn hàng đang filling
params = {"status_filter": "filling", "skip": 0, "limit": 10}
response = requests.get(url, params=params)
print(response.json())
```

---

### 5️⃣ Statistics (Thống kê)

#### 5.1. Thống kê tổng quan hệ thống

```bash
curl -X GET "http://localhost:8000/v1/api/grid/stats/summary"
```

**Python:**
```python
url = "http://localhost:8000/v1/api/grid/stats/summary"
response = requests.get(url)
print(response.json())
```

**Response:**
```json
{
  "grids": {
    "total": 2,
    "total_cells": 40
  },
  "cells": {
    "empty": 30,
    "filling": 5,
    "full": 5,
    "utilization_rate": 25.0
  },
  "products": {
    "total": 25
  },
  "orders": {
    "total": 10,
    "pending": 2,
    "filling": 3,
    "completed": 3,
    "shipped": 2
  }
}
```

---

## 🎯 Kịch bản Test Hoàn Chỉnh

### Kịch bản: Nhập kho và giao hàng

```python
import requests
import time

BASE_URL = "http://localhost:8000/v1"

# 1. Tạo lưới
print("1. Tạo lưới 5x4...")
grid = requests.post(f"{BASE_URL}/api/grid/create", json={
    "name": "Kho A - Test",
    "width": 5,
    "height": 4
}).json()
print(f"✅ Đã tạo lưới ID: {grid['id']}")

# 2. Quét 5 sản phẩm cùng đơn hàng
print("\n2. Quét 5 sản phẩm đơn hàng VA-M-000126...")
products = [
    {"productCode":"VA-M-000126-1","qrData":"101725-VA-M-000126-1","size":"M","color":"Đỏ","number":"1","total":"5"},
    {"productCode":"VA-M-000126-2","qrData":"101725-VA-M-000126-2","size":"M","color":"Đỏ","number":"2","total":"5"},
    {"productCode":"VA-M-000126-3","qrData":"101725-VA-M-000126-3","size":"L","color":"Xanh","number":"3","total":"5"},
    {"productCode":"VA-M-000126-4","qrData":"101725-VA-M-000126-4","size":"M","color":"Đỏ","number":"4","total":"5"},
    {"productCode":"VA-M-000126-5","qrData":"101725-VA-M-000126-5","size":"S","color":"Vàng","number":"5","total":"5"},
]

for product in products:
    result = requests.post(f"{BASE_URL}/api/grid/assign-product", json=product).json()
    cell_name = result['assigned_cell']['cell_name']
    status = result['assigned_cell']['status']
    count = result['assigned_cell']['current_product_count']
    print(f"✅ Sản phẩm {product['number']}/5 → Ô {cell_name} ({status}) - Đã có {count}/5 sản phẩm")
    time.sleep(0.5)

# 3. Kiểm tra trạng thái đơn hàng
print("\n3. Kiểm tra trạng thái đơn hàng...")
order = requests.get(f"{BASE_URL}/api/grid/order/VA-M-000126-101725").json()
print(f"✅ Đơn hàng {order['order_code']}: {order['status']}")
print(f"   Đã nhận: {order['received_products']}/{order['total_products']} sản phẩm")

# 4. Xem chi tiết lưới
print("\n4. Xem chi tiết lưới...")
grid_detail = requests.get(f"{BASE_URL}/api/grid/{grid['id']}").json()
used_cells = [c for c in grid_detail['cells'] if c['status'] != 'empty']
print(f"✅ Có {len(used_cells)} ô đang được sử dụng")

# 5. Xem chi tiết ô (kèm products & history)
print("\n5. Xem chi tiết ô...")
cell_id = used_cells[0]['id']
cell_detail = requests.get(f"{BASE_URL}/api/grid/cell/{cell_id}/detail").json()
print(f"✅ Ô {cell_detail['cell_name']}:")
print(f"   - Status: {cell_detail['status']}")
print(f"   - Sản phẩm hiện tại: {len(cell_detail['products'])}")
print(f"   - Lịch sử: {len(cell_detail['histories'])} lần giao hàng")

# 6. Cập nhật trạng thái ô
print("\n6. Cập nhật trạng thái ô...")
status_result = requests.put(f"{BASE_URL}/api/grid/cell/{cell_id}/status", json={
    "status": "full"
}).json()
print(f"✅ {status_result['message']}")

# 7. Thêm ghi chú cho ô
print("\n7. Thêm ghi chú cho ô...")
requests.put(f"{BASE_URL}/api/grid/cell/{cell_id}/note", json={
    "note": "Ưu tiên giao hàng trước 3PM"
})
print(f"✅ Đã thêm ghi chú cho ô {used_cells[0]['cell_name']}")

# 8. Giải phóng ô - Giao hàng
print("\n8. Giải phóng ô - Giao hàng...")
clear_result = requests.post(f"{BASE_URL}/api/grid/cell/{cell_id}/clear").json()
print(f"✅ {clear_result['message']}")

# 9. Thống kê tổng quan
print("\n9. Thống kê tổng quan...")
stats = requests.get(f"{BASE_URL}/api/grid/stats/summary").json()
print(f"✅ Tổng số lưới: {stats['grids']['total']}")
print(f"✅ Tổng số ô: {stats['grids']['total_cells']}")
print(f"✅ Tỷ lệ sử dụng: {stats['cells']['utilization_rate']}%")
print(f"✅ Tổng sản phẩm: {stats['products']['total']}")
print(f"✅ Tổng đơn hàng: {stats['orders']['total']}")

print("\n🎉 Test hoàn tất!")
```

---

## 🔧 Troubleshooting

### Lỗi kết nối database:
```bash
# Kiểm tra PostgreSQL đang chạy
docker-compose ps

# Xem logs
docker-compose logs db
docker-compose logs app
```

### Lỗi 422 Validation Error:
- Kiểm tra format JSON
- Đảm bảo tất cả required fields đều có

### Lỗi 409 Conflict (Duplicate):
- Sản phẩm đã tồn tại trong hệ thống
- Kiểm tra bằng endpoint `/product/{product_code}/check`

### Reset database:
```bash
# Xóa volume và tạo lại
docker-compose down -v
docker-compose up -d
```

---

## 📊 Postman Collection

Import file này vào Postman để test nhanh: (Tạo collection và export)

---

## 🎓 Tips

1. **Sử dụng Swagger UI** (http://localhost:8000/docs) để test trực quan
2. **QR Format**: `{order_date}-{product_code}` (VD: `101725-VA-M-000126-2`)
3. **Product Code Format**: `{area}-{size}-{order_number}-{product_number}` (VD: `VA-M-000126-2`)
4. **Tự động phân bổ**: Hệ thống tự tìm ô cùng order hoặc ô trống
5. **Status flow**: empty → filling → full → (clear) → empty

---

Chúc bạn test API thành công! 🚀


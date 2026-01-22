# 后端接口文档

## 基础信息

- **Base URL**: `http://localhost:8000`
- **API前缀**: `/api`
- **数据格式**: JSON

---

## 接口列表

### 1. 上传图片

上传图片并创建推理任务。

**请求**
```
POST /api/upload
Content-Type: multipart/form-data
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | File | 是 | 图片文件 (jpg/jpeg/png/bmp/webp) |

**响应**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "任务已创建，正在处理中"
}
```

**错误码**
| 状态码 | 说明 |
|--------|------|
| 400 | 文件格式不支持或文件过大 |
| 503 | 任务队列已满 |

**示例**
```bash
curl -X POST "http://localhost:8000/api/upload" \
  -F "file=@test.jpg"
```

---

### 2. 查询任务状态

查询指定任务的处理状态。

**请求**
```
GET /api/task/{task_id}/status
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| task_id | string | 是 | 任务ID (路径参数) |

**响应**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "created_at": "2026-01-21T13:30:00",
  "completed_at": "2026-01-21T13:30:05",
  "inference_time": 0.523,
  "error_message": null
}
```

**任务状态**
| 状态 | 说明 |
|------|------|
| pending | 等待处理 |
| processing | 处理中 |
| completed | 已完成 |
| failed | 失败 |

**示例**
```bash
curl "http://localhost:8000/api/task/550e8400-e29b-41d4-a716-446655440000/status"
```

---

### 3. 获取任务结果

获取任务的完整推理结果。

**请求**
```
GET /api/task/{task_id}/result
```

**响应**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "result": {
    "detections": [
      {
        "class": "car",
        "class_id": 2,
        "confidence": 0.8734,
        "bbox": {
          "x_min": 100.5,
          "y_min": 200.3,
          "x_max": 300.8,
          "y_max": 400.2
        }
      },
      {
        "class": "person",
        "class_id": 0,
        "confidence": 0.9156,
        "bbox": {
          "x_min": 450.0,
          "y_min": 120.5,
          "x_max": 520.3,
          "y_max": 380.8
        }
      }
    ],
    "detection_count": 2,
    "inference_time": 0.523,
    "image_size": {
      "width": 1920,
      "height": 1080
    }
  },
  "result_image_url": "/api/task/550e8400-e29b-41d4-a716-446655440000/result-image",
  "error_message": null,
  "created_at": "2026-01-21T13:30:00",
  "completed_at": "2026-01-21T13:30:05"
}
```

**示例**
```bash
curl "http://localhost:8000/api/task/550e8400-e29b-41d4-a716-446655440000/result"
```

---

### 4. 获取结果图片

获取带标注框的结果图片。

**请求**
```
GET /api/task/{task_id}/result-image
```

**响应**
- Content-Type: image/jpeg
- 返回带检测框标注的图片

**示例**
```bash
curl -o result.jpg "http://localhost:8000/api/task/550e8400-e29b-41d4-a716-446655440000/result-image"
```

---

### 5. 获取任务列表

分页获取任务列表。

**请求**
```
GET /api/tasks
```

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| page | int | 否 | 1 | 页码 |
| page_size | int | 否 | 10 | 每页数量 (1-100) |
| status | string | 否 | - | 状态过滤 |

**响应**
```json
{
  "total": 25,
  "tasks": [
    {
      "task_id": "550e8400-e29b-41d4-a716-446655440000",
      "original_filename": "test.jpg",
      "status": "completed",
      "created_at": "2026-01-21T13:30:00",
      "updated_at": "2026-01-21T13:30:05"
    }
  ],
  "page": 1,
  "page_size": 10
}
```

**示例**
```bash
curl "http://localhost:8000/api/tasks?page=1&page_size=10&status=completed"
```

---

### 6. 系统状态

获取系统运行状态。

**请求**
```
GET /api/system/status
```

**响应**
```json
{
  "status": "running",
  "model_loaded": true,
  "device": "cuda",
  "queue_size": 3,
  "queue_running": true
}
```

---

### 7. 健康检查

服务健康检查接口。

**请求**
```
GET /api/health
```

**响应**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-21T13:30:00.000000"
}
```

---

## 错误响应格式

```json
{
  "detail": "错误描述信息"
}
```

## 常见错误码

| 状态码 | 说明 |
|--------|------|
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |
| 503 | 服务暂时不可用 |

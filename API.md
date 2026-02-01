# 后端接口文档

## 基础信息

- **Base URL**: `http://localhost:8001`
- **API前缀**: `/api`
- **数据格式**: JSON

---

## 接口列表

### 1. 提交推理任务

提交一个推理任务，传入序号参数。

**请求**
```
POST /api/inference?index={序号}
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| index | int | 是 | 序号参数（>=1），作为Query参数 |

**响应**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "index": 1,
  "message": "任务已创建，正在处理中"
}
```

**示例**
```bash
curl -X POST "http://localhost:8001/api/inference?index=1"
```

```javascript
// JavaScript
const response = await fetch('http://localhost:8001/api/inference?index=1', {
  method: 'POST'
});
const data = await response.json();
console.log(data.task_id);
```

---

### 2. 查询任务状态

查询指定任务的处理状态。

**请求**
```
GET /api/task/{task_id}/status
```

**响应**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "index": 1,
  "status": "completed",
  "created_at": "2026-01-22T13:30:00",
  "completed_at": "2026-01-22T13:30:35",
  "inference_time": 32.5,
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
curl "http://localhost:8001/api/task/550e8400-e29b-41d4-a716-446655440000/status"
```

---

### 3. 获取任务结果

获取任务的推理结果，包含结果文件列表。

**请求**
```
GET /api/task/{task_id}/result
```

**响应（成功）**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "index": 1,
  "status": "completed",
  "inference_time": 32.5,
  "created_at": "2026-01-22T13:30:00",
  "completed_at": "2026-01-22T13:30:35",
  "files": [
    {
      "filename": "result_001.jpg",
      "type": "image",
      "url": "/api/task/550e8400-e29b-41d4-a716-446655440000/file/result_001.jpg"
    },
    {
      "filename": "output.mp4",
      "type": "video",
      "url": "/api/task/550e8400-e29b-41d4-a716-446655440000/file/output.mp4"
    }
  ]
}
```

**响应（未完成）**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "message": "任务尚未完成",
  "error_message": null
}
```

---

### 4. 获取结果文件

获取指定的结果文件（图片或视频）。

**请求**
```
GET /api/task/{task_id}/file/{filename}
```

**响应**
- 返回图片或视频文件
- Content-Type: image/jpeg, image/png, video/mp4 等

**示例**
```html
<!-- 在HTML中显示图片 -->
<img src="http://localhost:8001/api/task/{task_id}/file/result.jpg" />

<!-- 在HTML中播放视频 -->
<video src="http://localhost:8001/api/task/{task_id}/file/output.mp4" controls></video>
```

---

### 5. 获取任务列表

分页获取任务列表。

**请求**
```
GET /api/tasks?page=1&page_size=10&status=completed
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
  "page": 1,
  "page_size": 10,
  "tasks": [
    {
      "task_id": "550e8400-e29b-41d4-a716-446655440000",
      "index": 1,
      "status": "completed",
      "created_at": "2026-01-22T13:30:00",
      "completed_at": "2026-01-22T13:30:35"
    }
  ]
}
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
  "ssh_connected": true,
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
  "timestamp": "2026-01-22T13:30:00.000000"
}
```

---

## 前端调用流程

```
1. POST /api/inference?index=序号  →  获取 task_id
2. 轮询 GET /api/task/{task_id}/status  →  直到 status === "completed"
3. GET /api/task/{task_id}/result  →  获取结果文件列表
4. 使用 files[].url 展示图片或视频
```

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
| 503 | 服务暂时不可用（队列已满） |

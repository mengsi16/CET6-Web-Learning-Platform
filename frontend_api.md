# Frontend Data Interface Specification (v1.0)

本文档定义了前端（Web 端）与后端交互所需的数据接口规范。主要用于支持真题内容展示、单词查询与生词本同步等核心功能。

## 1. 基础说明 (General)
- **Base URL**: `/api/v1` (示例)
- **Content-Type**: `application/json`
- **Authentication**: 建议使用 Bearer Token (Header: `Authorization: Bearer <token>`)

---

## 2. 试卷文档接口 (Documents)
用于获取主视图（DocumentViewer）中展示的试卷内容（模拟 PDF 文本层）。

### 2.0 获取试卷列表
用于前端侧边栏或主页展示可选的试卷列表。

- **Endpoint**: `GET /documents/list`
- **Response Example**:
```json
{
  "code": 200,
  "data": [
    {
      "year": "2023",
      "month": "06",
      "papers": [
        {
          "id": "2023_06_set1",
          "title": "2023年6月CET6真题(第一套)",
          "filename": "2023年06月CET6真题(第一套).pdf"
        },
        {
          "id": "2023_06_set2",
          "title": "2023年6月CET6真题(第二套)",
          "filename": "2023年06月CET6真题(第二套).docx"
        }
      ]
    }
  ]
}
```

### 2.1 获取试卷内容详情
前端根据试卷 ID 或路径获取用于渲染的文本行数据。

- **Endpoint**: `GET /documents/content`
- **Query Params**:
  - `doc_id` (string): 试卷唯一标识 (e.g., "2023-june-set1")

- **Response Example**:
```json
{
  "code": 200,
  "data": {
    "docId": "2023-june-set1",
    "title": "2023年6月CET6真题(第一套)",
    "lines": [
      "College English Test Band 6 (CET-6)",
      "Part I Writing (30 minutes)",
      "Directions: For this part, you are allowed 30 minutes to write an essay...",
      "Innovation is the primary driving force for development..."
    ],
    "meta": {
      "totalPages": 12,
      "pageDimensions": { "width": 800, "height": 1131 }
    }
  }
}
```
*前端 `dummyContent` 将由 `data.lines` 替换。*

### 2.2 试卷标注 (Annotations)
用于持久化画布上的高亮、笔迹等。

- **获取标注**: `GET /user/annotations?doc_id=...`
- **保存标注**: `POST /user/annotations`
  - **Body**: `{ "docId": "...", "strokes": [...] }`

### 2.3 写作/笔记 (Essays)
用于持久化该文档关联的 Markdown 笔记。

- **获取笔记**: `GET /user/essay?doc_id=...`
- **保存笔记**: `POST /user/essay`
  - **Body**: `{ "docId": "...", "content": "# Markdown Content" }`

---

## 3. 词典与翻译接口 (Dictionary)
用于前端鼠标悬停、划词翻译时的数据获取。

### 3.1 单词查询
- **Endpoint**: `GET /dictionary/lookup`
- **Query Params**:
  - `word` (string): 需要查询的单词 (e.g., "innovation")

- **Response Example**:
```json
{
  "code": 200,
  "data": {
    "word": "Innovation",
    "phonetic": "ˌɪnəˈveɪʃn",
    "meaning": "n. 创新, 革新; 新事物",
    "audioUrl": "https://api.dictionary.com/audio/innovation.mp3",
    "examples": [
      "Technological innovation is changing the world."
    ]
  }
}
```
*前端 `translationPopup` 组件将展示此数据。*

---

## 4. 生词本接口 (Vocabulary / Word Book)
用于管理用户的生词本（WordBook 组件）。

### 4.1 获取生词列表
- **Endpoint**: `GET /user/vocabulary`
- **Query Params**:
  - `page` (int): 页码
  - `limit` (int): 每页数量

- **Response Example**:
```json
{
  "code": 200,
  "data": {
    "total": 105,
    "items": [
      {
        "id": "wd_1001",
        "text": "Innovation",
        "phonetic": "ˌɪnəˈveɪʃn",
        "meaning": "n. 创新, 革新",
        "addedAt": 1678892231000
      },
      {
        "id": "wd_1002",
        "text": "Significant",
        "phonetic": "sɪɡˈnɪfɪkənt",
        "meaning": "adj. 重大的; 有效的",
        "addedAt": 1678892100000
      }
    ]
  }
}
```
*前端 `markedWords` 数组将从此处加载，不再仅依赖 localStorage。*

### 4.2 添加生词
当用户使用高亮笔标记单词或在弹窗点击收藏时调用。

- **Endpoint**: `POST /user/vocabulary`
- **Request Body**:
```json
{
  "word": "innovation" 
  // 后端应自行负责查找词典完善 phonetic 和 meaning，或由前端根据 Dictionary 接口缓存的数据一并传入（取决于架构设计，建议仅传 word）
}
```

- **Response Example**:
```json
{
  "code": 200,
  "message": "Added successfully",
  "data": {
    "id": "wd_1001",
    "text": "Innovation",
    "phonetic": "ˌɪnəˈveɪʃn",
    "meaning": "n. 创新, 革新",
    "addedAt": 1678892231000
  }
}
```

### 4.3 移除生词
在 WordBook 列表点击删除时调用。

- **Endpoint**: `DELETE /user/vocabulary/{id}`
- **Path Params**:
  - `id`: 生词记录 IDs

- **Response Example**:
```json
{ "code": 200, "message": "Deleted successfully" }
```

---

## 5. 写作/笔记接口 (Essay / Notes) - Obsolete (Merged into 2.3)
This section is preserved for reference but functionally replaced by the general essay interface in section 2.3.
  "docId": "2023-june-set1",
  "content": "# My Essay\n\nInnovation is crucial..."
}
```

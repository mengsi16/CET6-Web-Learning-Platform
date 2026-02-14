# Backend API Documentation

Base URL: `http://localhost:8000`

## Documents

### Get Documents List
Retrieves a hierarchical list of available CET6 documents grouped by year and month.

- **URL**: `/api/v1/documents/list`
- **Method**: `GET`
- **Response**:
  ```json
  {
    "code": 200,
    "data": [
      {
        "year": "2023",
        "month": "06",
        "papers": [
          {
            "id": "2023年06月CET6真题/Title.pdf",
            "title": "Title",
            "filename": "Title.pdf"
          }
        ]
      }
    ]
  }
  ```

### Get Document Content
Retrieves the text content of a specific document.

- **URL**: `/api/v1/documents/content`
- **Method**: `GET`
- **Query Parameters**:
  - `doc_id` (string, required): The relative path of the document (obtained from the list endpoint).
- **Response**:
  ```json
  {
    "code": 200,
    "data": {
      "docId": "path/to/doc.pdf",
      "title": "doc.pdf",
      "lines": [
        "Line 1 text...",
        "Line 2 text..."
      ],
      "meta": {
        "totalPages": 0
      }
    }
  }
  ```
- **Errors**:
  - `403 Access denied`: If path traversal is attempted.
  - `404 File not found`: If the document does not exist.

## User Data

### Get Annotations
Retrieves the saved drawing/annotations for a document.

- **URL**: `/api/v1/user/annotations`
- **Method**: `GET`
- **Query Parameters**:
  - `doc_id` (string, required): The relative path of the document.
- **Response**:
  ```json
  {
    "code": 200,
    "data": [
      {
        "type": "highlight",
        "color": "#ffff00",
        "points": [{"x": 10, "y": 10}, {"x": 20, "y": 20}]
      }
    ]
  }
  ```

### Save Annotations
Saves the drawing/annotations for a document.

- **URL**: `/api/v1/user/annotations`
- **Method**: `POST`
- **Body**:
  ```json
  {
    "docId": "path/to/doc.pdf",
    "strokes": []
  }
  ```
- **Response**:
  ```json
  {
    "code": 200,
    "message": "Saved successfully"
  }
  ```

### Get Essay
Retrieves the saved essay/notes for a document.

- **URL**: `/api/v1/user/essay`
- **Method**: `GET`
- **Query Parameters**:
  - `doc_id` (string, required): The relative path of the document.
- **Response**:
  ```json
  {
    "code": 200,
    "data": {
      "content": "# My Essay\n..."
    }
  }
  ```

### Save Essay
Saves the essay/notes for a document.

- **URL**: `/api/v1/user/essay`
- **Method**: `POST`
- **Body**:
  ```json
  {
    "docId": "path/to/doc.pdf",
    "content": "# My Essay\n..."
  }
  ```
- **Response**:
  ```json
  {
    "code": 200,
    "message": "Saved successfully"
  }
  ```

## Vocabulary (User Word Book)

### Get Vocabulary List
Retrieves the user's saved vocabulary list with pagination.

- **URL**: `/api/v1/user/vocabulary`
- **Method**: `GET`
- **Query Parameters**:
  - `page` (integer, optional): Page number (default: 1).
  - `limit` (integer, optional): Items per page (default: 100).
- **Response**:
  ```json
  {
    "code": 200,
    "data": {
      "total": 15,
      "items": [
        {
          "id": "wd_123456789",
          "text": "example",
          "phonetic": "[ɪgˈzɑːmpl]",
          "meaning": "n. 例子；榜样",
          "addedAt": 1678888888000
        }
      ]
    }
  }
  ```

### Add Vocabulary
Adds a new word to the vocabulary list. The backend attempts to fetch meaning and phonetic info.

- **URL**: `/api/v1/user/vocabulary`
- **Method**: `POST`
- **Body**:
  ```json
  {
    "word": "example"
  }
  ```
- **Response**:
  ```json
  {
    "code": 200,
    "message": "Added successfully",
    "data": {
      "id": "wd_123456789",
      "text": "example",
      "phonetic": "...",
      "meaning": "...",
      "addedAt": 1678888888000
    }
  }
  ```

### Delete Vocabulary
Removes a word from the vocabulary list.

- **URL**: `/api/v1/user/vocabulary/{id}`
- **Method**: `DELETE`
- **Path Parameters**:
  - `id` (string, required): The ID of the vocabulary item to delete.
- **Response**:
  ```json
  {
    "code": 200,
    "message": "Deleted successfully"
  }
  ```

## Dictionary

### Lookup Word
Look up a word's definition and phonetic symbol.

- **URL**: `/api/v1/dictionary/lookup`
- **Method**: `GET`
- **Query Parameters**:
  - `word` (string, required): The word to look up.
- **Response**:
  ```json
  {
    "code": 200,
    "data": {
      "word": "hello",
      "phonetic": "...",
      "meaning": "...",
      "examples": []
    }
  }
  ```

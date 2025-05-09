# Marketplace API Documentation

This document provides information about the REST API endpoints available in the marketplace system.

## Authentication

All API endpoints require authentication. Use session authentication for web browsers or basic authentication for API clients.

## Endpoints

### Products API

#### List Products
- **URL**: `/api/products/`
- **Method**: GET
- **Description**: Get a list of all available products
- **Query Parameters**:
  - `category`: Filter products by category
- **Response**: List of products with details

#### Get Product Details
- **URL**: `/api/products/{id}/`
- **Method**: GET
- **Description**: Get detailed information about a specific product
- **Response**: Product details

#### Purchase Product
- **URL**: `/api/products/{id}/purchase/`
- **Method**: POST
- **Description**: Purchase a product
- **Response**: 
  - Success: `{"message": "Purchase successful"}`
  - Error: `{"error": "Error message"}`

### Transactions API

#### List Transactions
- **URL**: `/api/transactions/`
- **Method**: GET
- **Description**: Get a list of user's transactions
- **Response**: List of transactions

#### Get Transaction Summary
- **URL**: `/api/transactions/summary/`
- **Method**: GET
- **Description**: Get summary of user's transactions
- **Response**: 
  ```json
  {
    "total_spent": 0.00,
    "total_earned": 0.00,
    "net_balance": 0.00
  }
  ```

### User Account API

#### Get Account Details
- **URL**: `/api/accounts/`
- **Method**: GET
- **Description**: Get user's account details
- **Response**: Account information

#### Deposit Money
- **URL**: `/api/accounts/{id}/deposit/`
- **Method**: POST
- **Description**: Deposit money into user's account
- **Request Body**:
  ```json
  {
    "amount": 100.00
  }
  ```
- **Response**:
  - Success: `{"message": "Deposit successful"}`
  - Error: `{"error": "Error message"}`

## Error Handling

All API endpoints return appropriate HTTP status codes:
- 200: Success
- 400: Bad Request
- 401: Unauthorized
- 403: Forbidden
- 404: Not Found
- 500: Internal Server Error

Error responses include a message explaining the error:
```json
{
  "error": "Error message"
}
```

## Rate Limiting

API requests are limited to 100 requests per hour per user to prevent abuse.

## Versioning

The current API version is v1. Future versions will be available at `/api/v2/`, etc. 
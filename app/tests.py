import time

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.app import app

client = TestClient(app)


def test_get_products():
    response = client.get("/api/products")
    assert response.status_code == 200


def test_delete_all_products():
    # get all products
    response = client.get("/api/products")
    assert response.status_code == 200

    # delete all products
    for product in response.json():
        response = client.delete(f"/api/products/{product['id']}")
        assert response.status_code == 200
        assert response.json()["id"] == product["id"]

    # get all products
    response = client.get("/api/products")
    assert response.status_code == 200
    assert len(response.json()) == 0


async def test_add_product():
    response = client.post(
        "/api/products",
        json={
            "title": "Apple",
            "description": "An apple a day keeps the doctor away",
            "price": 1.99,
        },
    )
    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "title": "Apple",
        "description": "An apple a day keeps the doctor away",
        "price": 1.99,
    }


#
#
# def test_get_product():
#     response = client.get("/api/products/1")
#     assert response.status_code == 200
#     assert response.json() == {
#         "id": 1,
#         "title": "Apple",
#         "description": "An apple a day keeps the doctor away",
#         "price": 1.99,
#     }
#
#
# def test_get_basket():
#     # should get error if not authorized
#     response = client.get("/api/basket")
#     assert response.status_code == 401
#
#
# def test_register():
#     client.post(
#         "/api/auth/register",
#         json={
#             "email": "test@example.com",
#             "password": "test",
#         },
#     )
#
#
# def test_login():
#     response = client.post(
#         "/api/auth/jwt/login",
#         data={
#             "username": "test@example.com",
#             "password": "test",
#         },
#     )
#     assert response.status_code == 200
#     assert response.json()["access_token"]
#     assert response.json()["token_type"] == "bearer"
#
#     # save token for future requests
#     global token
#     token = response.json()["access_token"]
#
#
# def test_get_basket_authorized():
#     response = client.get("/api/basket", headers={"Authorization": f"Bearer {token}"})
#     assert response.status_code == 200
#     assert response.json() == {
#         "id": 1,
#         "items": [],
#     }
#
#
# def test_add_to_basket():
#     response = client.post(
#         "/api/basket/1/1",
#         headers={"Authorization": f"Bearer {token}"},
#     )
#     assert response.status_code == 200
#     assert response.json() == {
#         "id": 1,
#         "product_id": 1,
#     }
#
#
# def test_remove_from_basket():
#     response = client.delete(
#         "/api/basket/1/1",
#         headers={"Authorization": f"Bearer {token}"},
#     )
#     assert response.status_code == 200
#     assert response.json() == {
#         "id": 1,
#         "product_id": 1,
#     }
#
#
# def test_get_basket_empty():
#     response = client.get("/api/basket", headers={"Authorization": f"Bearer {token}"})
#     assert response.status_code == 200
#     assert response.json() == {
#         "id": 1,
#         "items": [],
#     }

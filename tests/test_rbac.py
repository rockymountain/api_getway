import pytest

def test_rbac_permission_denied(client, jwt_token_without_permission):
    headers = {"Authorization": f"Bearer {jwt_token_without_permission}"}
    response = client.get("/api/v1/protected-endpoint", headers=headers)
    assert response.status_code == 403
    data = response.json()
    assert "error_code" in data and data["error_code"] == 403
    assert "message" in data
    assert "request_id" in data
    assert "timestamp" in data

def test_rbac_permission_granted(client, jwt_token_with_permission):
    headers = {"Authorization": f"Bearer {jwt_token_with_permission}"}
    response = client.get("/api/v1/protected-endpoint", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)  # Tuỳ cấu trúc response thực tế

def test_rbac_no_token(client):
    response = client.get("/api/v1/protected-endpoint")
    assert response.status_code == 401
    data = response.json()
    assert data["error_code"] == 401
    assert "message" in data
    assert "request_id" in data
    assert "timestamp" in data

"""
Gợi ý để hoàn thiện thêm (khi API Gateway phát triển):

1. Định nghĩa và Cấu hình Endpoint Bảo vệ:
    Đảm bảo /api/v1/protected-endpoint (hoặc các endpoint thực tế bạn dùng để test) được định nghĩa trong API Gateway và được cấu hình với các yêu cầu quyền cụ thể để các kịch bản test RBAC có thể hoạt động chính xác.
2. Thiết lập Dữ liệu RBAC cho Môi trường Test:
    - Trong conftest.py hoặc thông qua các cơ chế setup/teardown khác, bạn cần đảm bảo rằng:
        - User tương ứng với jwt_token_without_permission (ví dụ: user_id_456) không có quyền truy cập /api/v1/protected-endpoint.
        - User tương ứng với jwt_token_with_permission (ví dụ: user_id_123) có quyền truy cập /api/v1/protected-endpoint.
    - Điều này có thể liên quan đến việc seed dữ liệu vào database test hoặc mock các service RBAC.
3. Mở rộng Assertions cho test_rbac_permission_granted:
    Khi endpoint /api/v1/protected-endpoint có response body cụ thể, hãy thêm các assertions để kiểm tra nội dung đó.
4. Thực hiện TODO về Test Cache RBAC:
    Đây vẫn là một phần quan trọng cần được triển khai để đảm bảo tính hiệu quả và đúng đắn của cơ chế cache (theo ADR-002 và ADR-017).
5. Test các Kịch bản RBAC Phức tạp hơn:
    - Nhiều role, nhiều permission.
    - Kế thừa role (nếu có).
    - Permission dựa trên resource (ví dụ: user A chỉ được sửa thông tin của chính mình, không được sửa của user B).
"""
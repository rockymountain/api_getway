import schemathesis
from app.main import app  # Đảm bảo đường dẫn đúng

schema = schemathesis.from_asgi("/openapi.json", app=app)

@schema.parametrize()
def test_api_compliance(case):
    \"\"\"Test schema-based bằng schemathesis (ADR-018).\"\"\"
    response = case.call_asgi()
    case.validate_response(response)
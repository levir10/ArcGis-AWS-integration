import os
from dotenv import load_dotenv

# Always load .env from script directory
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"), override=True)

class Config:
    APPSYNC_API_URL = os.environ.get("APPSYNC_API_URL")
    AWS_REGION = os.environ.get("AWS_REGION")
    AWS_PROFILE = os.environ.get("AWS_PROFILE", "default")
    BUCKET_NAME_SITES = os.environ.get("BUCKET_NAME_SITES", "exodb-sites-files")
    BUCKET_NAME_USER_LAYERS = os.environ.get("BUCKET_NAME_USER_LAYERS", "exodigo-sites-user-layers")
    LAMBDA_FUNCTION_NAME = os.environ.get("LAMBDA_FUNCTION_NAME", "InvokeClashesCalculationMock")
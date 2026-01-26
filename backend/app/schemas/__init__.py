"""
Pydantic schemas package - API request/response models
"""

from app.schemas.user import (
    UserCreate,
    UserLogin,
    UserUpdate,
    UserResponse,
    AuthResponse,
    TokenRefreshRequest,
    TokenRefreshResponse,
    PasswordChange,
    PasswordReset,
    PasswordResetConfirm,
    GoogleAuthRequest,
    MessageResponse
)

from app.schemas.dataset import (
    CategoryResponse,
    DatasetFieldResponse,
    DatasetCreate,
    DatasetUpdate,
    DatasetListResponse,
    DatasetDetailResponse,
    DatasetAdminResponse,
    DatasetFilters,
    PaginatedDatasetResponse
)

from app.schemas.purchase import (
    PurchaseCreate,
    PurchaseResponse,
    PurchaseDetailResponse,
    PurchaseCreateResponse,
    PurchaseAlreadyOwned,
    RefundRequest,
    DownloadResponse,
    DownloadLogResponse,
    PaginatedPurchaseResponse,
    PaginatedPurchaseDetailResponse
)

from app.schemas.admin import (
    AdminLogin,
    AdminCreate,
    AdminResponse,
    AdminAuthResponse,
    DashboardStats,
    DashboardResponse,
    AuditLogResponse,
    PaginatedAuditLogResponse,
    UserAdminResponse,
    PaginatedUserResponse,
    UserStatusUpdate
)

from app.schemas.company import (
    CompanyResponse,
    CompanyDetailResponse,
    CompanyListResponse,
    CompanyAdminListResponse,
    ImportBatchResponse,
    ImportBatchListResponse,
    ImportProgressResponse,
    BulkVerificationResponse,
    VerificationStatsResponse,
    WorkerStatusResponse
)

__all__ = [
    # User
    "UserCreate",
    "UserLogin",
    "UserUpdate",
    "UserResponse",
    "AuthResponse",
    "TokenRefreshRequest",
    "TokenRefreshResponse",
    "PasswordChange",
    "PasswordReset",
    "PasswordResetConfirm",
    "GoogleAuthRequest",
    "MessageResponse",
    
    # Dataset
    "CategoryResponse",
    "DatasetFieldResponse",
    "DatasetCreate",
    "DatasetUpdate",
    "DatasetListResponse",
    "DatasetDetailResponse",
    "DatasetAdminResponse",
    "DatasetFilters",
    "PaginatedDatasetResponse",
    
    # Purchase
    "PurchaseCreate",
    "PurchaseResponse",
    "PurchaseDetailResponse",
    "PurchaseCreateResponse",
    "PurchaseAlreadyOwned",
    "RefundRequest",
    "DownloadResponse",
    "DownloadLogResponse",
    "PaginatedPurchaseResponse",
    "PaginatedPurchaseDetailResponse",
    
    # Admin
    "AdminLogin",
    "AdminCreate",
    "AdminResponse",
    "AdminAuthResponse",
    "DashboardStats",
    "DashboardResponse",
    "AuditLogResponse",
    "PaginatedAuditLogResponse",
    "UserAdminResponse",
    "PaginatedUserResponse",
    "UserStatusUpdate",

    # Company
    "CompanyResponse",
    "CompanyDetailResponse",
    "CompanyListResponse",
    "CompanyAdminListResponse",
    "ImportBatchResponse",
    "ImportBatchListResponse",
    "ImportProgressResponse",
    "BulkVerificationResponse",
    "VerificationStatsResponse",
    "WorkerStatusResponse"
]

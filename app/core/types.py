"""
Mami AI - Shared Type Definitions
==================================

Bu modül, circular import sorunlarını çözmek için merkezi tip tanımları içerir.
TYPE_CHECKING bloklarında kullanılmak üzere Protocol ve TypedDict tanımları.

Kullanım:
    from typing import TYPE_CHECKING
    
    if TYPE_CHECKING:
        from app.core.types import UserLike, SettingsLike
    
    def process_user(user: UserLike) -> dict[str, Any]:
        return {"id": user.id, "name": user.username}
"""

from typing import Any, Optional, Protocol

from typing_extensions import TypedDict

# ============================================================================
# USER PROTOCOLS
# ============================================================================

class UserLike(Protocol):
    """User model interface for type checking.
    
    Duck typing interface that matches app.core.models.User
    """
    id: Optional[int]
    username: str
    email: Optional[str]
    role: str  # "admin" or "user"
    is_admin: bool
    is_active: bool
    is_banned: bool
    active_persona: Optional[str]


class UserPreferenceLike(Protocol):
    """UserPreference model interface."""
    user_id: int
    key: str
    value: str
    category: str
    is_active: bool


# ============================================================================
# SETTINGS PROTOCOLS
# ============================================================================

class SettingsLike(Protocol):
    """Settings interface for type checking.
    
    Duck typing interface that matches app.config.Settings
    """
    APP_NAME: str
    DEBUG: bool
    SECRET_KEY: str
    
    # Database
    DATABASE_URL: Optional[str]
    CHROMA_PERSIST_DIR: str
    
    # Groq API
    GROQ_API_KEY: str
    GROQ_DECIDER_MODEL: str
    GROQ_ANSWER_MODEL: str
    GROQ_FAST_MODEL: str
    
    # Methods
    def get_cors_origins_list(self) -> list[str]: ...
    def get_groq_api_keys(self) -> list[str]: ...


# ============================================================================
# MESSAGE & CONVERSATION PROTOCOLS
# ============================================================================

class MessageLike(Protocol):
    """Message model interface."""
    id: Optional[int]
    conversation_id: str
    role: str
    content: str


class ConversationLike(Protocol):
    """Conversation model interface."""
    id: str
    user_id: int
    title: Optional[str]
    created_at: Any  # datetime
    updated_at: Any  # datetime


# ============================================================================
# SEMANTIC ANALYSIS TYPES
# ============================================================================

class SemanticAnalysisDict(TypedDict, total=False):
    """Semantic analysis result dictionary."""
    intent_type: str
    domain: str
    should_use_internet: bool
    risk_level: str
    requires_search: bool
    query_type: Optional[str]
    entities: list[str]


class SemanticAnalysisLike(Protocol):
    """Semantic analysis result interface."""
    intent_type: str
    domain: str
    should_use_internet: bool
    risk_level: str
    requires_search: bool
    query_type: Optional[str]
    entities: list[str]


# ============================================================================
# ROUTING & DECISION TYPES
# ============================================================================

class RoutingDecisionDict(TypedDict, total=False):
    """Routing decision dictionary."""
    target: str
    tool_intent: Optional[str]
    reason: str
    use_local: bool
    force_groq: bool
    persona_override: bool


# ============================================================================
# MEMORY TYPES
# ============================================================================

class MemoryRecordDict(TypedDict, total=False):
    """Memory record dictionary."""
    id: str
    user_id: int
    text: str
    type: str
    importance: float
    topic: str
    source: str
    is_active: bool
    created_at: str
    last_accessed: str
    score: Optional[float]
    vector_similarity: Optional[float]
    metadata: dict[str, Any]


# ============================================================================
# CONTEXT TYPES
# ============================================================================

class UserContextDict(TypedDict, total=False):
    """User context dictionary."""
    recent_context: Optional[str]
    conversation_summary: Optional[str]
    relevant_memories: list[Any]
    relevant_documents: list[Any]
    user_preferences: dict[str, str]
    style_profile: dict[str, Any]


# ============================================================================
# IMAGE GENERATION TYPES
# ============================================================================

class ImageJobSpecDict(TypedDict, total=False):
    """Image job specification dictionary."""
    prompt: str
    checkpoint: str
    variant: str
    is_nsfw: bool
    user_tier: str


# ============================================================================
# HELPER TYPE ALIASES
# ============================================================================

# Common dictionary types
JSONDict = dict[str, Any]
MetadataDict = dict[str, Any]
ConfigDict = dict[str, Any]

# Message history type
MessageHistory = list[dict[str, str]]

# Search result type
SearchResult = dict[str, Any]
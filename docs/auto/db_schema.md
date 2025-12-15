# Database Schema

## Models
### SystemConfig
| Column | Type |
|---|---|
| id | `Optional[int]` |
| key | `str` |
| value | `str` |
| value_type | `str` |
| category | `str` |
| description | `Optional[str]` |
| is_secret | `bool` |
| is_editable | `bool` |
| default_value | `Optional[str]` |
| created_at | `datetime` |
| updated_at | `datetime` |
| updated_by | `Optional[str]` |

### ModelConfig
| Column | Type |
|---|---|
| id | `Optional[int]` |
| name | `str` |
| display_name | `str` |
| provider | `str` |
| model_id | `str` |
| purpose | `str` |
| is_active | `bool` |
| is_default | `bool` |
| priority | `int` |
| parameters | `Dict[str, Any]` |
| capabilities | `Dict[str, bool]` |
| description | `Optional[str]` |
| created_at | `datetime` |
| updated_at | `datetime` |

### APIConfig
| Column | Type |
|---|---|
| id | `Optional[int]` |
| name | `str` |
| display_name | `str` |
| base_url | `str` |
| is_active | `bool` |
| timeout | `int` |
| rate_limit | `int` |
| retry_count | `int` |
| settings | `Dict[str, Any]` |
| description | `Optional[str]` |
| created_at | `datetime` |
| updated_at | `datetime` |

### ThemeConfig
| Column | Type |
|---|---|
| id | `Optional[int]` |
| name | `str` |
| display_name | `str` |
| is_active | `bool` |
| is_default | `bool` |
| sort_order | `int` |
| colors | `Dict[str, str]` |
| fonts | `Dict[str, str]` |
| custom_css | `Optional[str]` |
| created_at | `datetime` |
| updated_at | `datetime` |

### PersonaConfig
| Column | Type |
|---|---|
| id | `Optional[int]` |
| name | `str` |
| display_name | `str` |
| mode_type | `str` |
| description | `Optional[str]` |
| icon | `Optional[str]` |
| is_active | `bool` |
| is_default | `bool` |
| sort_order | `int` |
| system_prompt | `str` |
| personality_traits | `Dict[str, Any]` |
| behavior_rules | `Dict[str, Any]` |
| allowed_providers | `List[str]` |
| requires_uncensored | `bool` |
| preferred_model_purpose | `Optional[str]` |
| preference_override_mode | `str` |
| example_dialogues | `List[Dict[str, str]]` |
| created_at | `datetime` |
| updated_at | `datetime` |

### ImageGenConfig
| Column | Type |
|---|---|
| id | `Optional[int]` |
| name | `str` |
| display_name | `str` |
| is_active | `bool` |
| is_default | `bool` |
| checkpoint | `str` |
| vae | `Optional[str]` |
| loras | `List[Dict[str, Any]]` |
| default_params | `Dict[str, Any]` |
| negative_prompt_template | `str` |
| description | `Optional[str]` |
| created_at | `datetime` |
| updated_at | `datetime` |

### UITextConfig
| Column | Type |
|---|---|
| id | `Optional[int]` |
| key | `str` |
| value | `str` |
| locale | `str` |
| category | `str` |
| description | `Optional[str]` |
| updated_at | `datetime` |

### User
| Column | Type |
|---|---|
| id | `Optional[int]` |
| username | `str` |
| password_hash | `str` |
| role | `str` |
| is_banned | `bool` |
| selected_model | `str` |
| bela_unlocked | `bool` |
| active_persona | `str` |
| limits | `Dict[str, Any]` |
| permissions | `Dict[str, Any]` |
| created_at | `datetime` |
| preferences | `List["UserPreference"]` |
| conversations | `List["Conversation"]` |
| sessions | `List["Session"]` |
| presets | `List["ModelPreset"]` |

### UserPreference
| Column | Type |
|---|---|
| id | `Optional[int]` |
| user_id | `int` |
| key | `str` |
| value | `str` |
| category | `str` |
| source | `str` |
| is_active | `bool` |
| updated_at | `datetime` |
| user | `Optional[User]` |

### ModelPreset
| Column | Type |
|---|---|
| id | `Optional[int]` |
| name | `str` |
| description | `Optional[str]` |
| system_prompt_template | `str` |
| temperature | `float` |
| max_tokens | `Optional[int]` |
| model_name | `Optional[str]` |
| is_global | `bool` |
| owner_id | `Optional[int]` |
| owner | `Optional[User]` |
| conversations | `List["Conversation"]` |

### Conversation
| Column | Type |
|---|---|
| id | `str` |
| user_id | `int` |
| title | `Optional[str]` |
| preset_id | `Optional[int]` |
| created_at | `datetime` |
| updated_at | `datetime` |
| user | `Optional[User]` |
| preset | `Optional[ModelPreset]` |
| messages | `List["Message"]` |
| summary | `Optional["ConversationSummary"]` |

### Message
| Column | Type |
|---|---|
| id | `Optional[int]` |
| conversation_id | `str` |
| role | `str` |
| content | `str` |
| extra_metadata | `Dict[str, Any]` |
| created_at | `datetime` |
| conversation | `Optional[Conversation]` |

### ConversationSummary
| Column | Type |
|---|---|
| conversation_id | `str` |
| summary | `str` |
| updated_at | `datetime` |
| message_count_at_update | `int` |
| last_message_id | `Optional[int]` |
| conversation | `Optional["Conversation"]` |

### AnswerCache
| Column | Type |
|---|---|
| id | `Optional[int]` |
| user_id | `int` |
| cache_key | `str` |
| question | `str` |
| answer | `str` |
| engine | `str` |
| created_at | `datetime` |
| expires_at | `Optional[datetime]` |
| user | `Optional["User"]` |

### UsageCounter
| Column | Type |
|---|---|
| id | `Optional[int]` |
| user_id | `int` |
| usage_date | `date` |
| groq_count | `int` |
| local_count | `int` |
| total_chat_count | `int` |
| user | `Optional["User"]` |

### Session
| Column | Type |
|---|---|
| id | `str` |
| user_id | `int` |
| type | `str` |
| expires_at | `datetime` |
| user_agent | `Optional[str]` |
| created_at | `datetime` |
| user | `Optional[User]` |

### Invite
| Column | Type |
|---|---|
| code | `str` |
| created_by | `str` |
| is_used | `bool` |
| used_by | `Optional[str]` |
| used_at | `Optional[datetime]` |
| created_at | `datetime` |

### Feedback
| Column | Type |
|---|---|
| id | `Optional[int]` |
| user_id | `int` |
| conversation_id | `Optional[str]` |
| message_content | `str` |
| feedback_type | `str` |
| created_at | `datetime` |
| user | `Optional["User"]` |
| conversation | `Optional["Conversation"]` |

### AIIdentityConfig
| Column | Type |
|---|---|
| id | `int` |
| display_name | `str` |
| developer_name | `str` |
| product_family | `str` |
| short_intro | `str` |
| forbid_provider_mention | `bool` |
| updated_at | `datetime` |

### ConversationSummarySettings
| Column | Type |
|---|---|
| id | `int` |
| summary_enabled | `bool` |
| summary_first_threshold | `int` |
| summary_update_step | `int` |
| summary_max_messages | `int` |
| updated_at | `datetime` |


## Migrations
- 20251207_1933_8ff1f9138cea_add_active_persona_to_users.py

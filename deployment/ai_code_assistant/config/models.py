# Available GigaChat models and their API names
GIGACHAT_MODELS = {
    # Base models (Freemium tier)
    'base': 'GigaChat',      # Base model (likely what's referred to as 'Lite' in documentation)
    'gpt': 'GigaChat',       # Alias for base model
    'lite': 'GigaChat',       # Alias for base model (documentation mentions GigaChat Lite)
    
    # Pro models (limited tokens in Freemium)
    'pro': 'GigaChat-Pro',
    'pro2': 'GigaChat-2-Pro',
    
    # Max models (limited tokens in Freemium)
    'max': 'GigaChat-Max',
    'max2': 'GigaChat-2-Max',
    
    # Preview models
    'preview': 'GigaChat-preview',
    'preview2': 'GigaChat-2-preview',
    'preview-pro': 'GigaChat-Pro-preview',
    'preview2-pro': 'GigaChat-2-Pro-preview',
    'preview-max': 'GigaChat-Max-preview',
    'preview2-max': 'GigaChat-2-Max-preview',
    
    # Embedding models
    'embeddings': 'Embeddings',
    'embeddings2': 'Embeddings-2',
    'embeddings-gigar': 'EmbeddingsGigaR'
}

# Default model to use (using base model which is likely the 'Lite' version in documentation)
DEFAULT_MODEL = 'base'

# Model categories for reference
MODEL_CATEGORIES = {
    'freemium': ['base', 'pro', 'max'],  # Models available in freemium tier
    'paid': ['preview', 'preview2', 'preview-pro', 'preview2-pro', 'preview-max', 'preview2-max'],
    'embeddings': ['embeddings', 'embeddings2', 'embeddings-gigar']
}
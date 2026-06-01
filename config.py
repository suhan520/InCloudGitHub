"""
配置文件 - InCloud GitHub 云上扫描器
"""
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# GitHub配置
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', '')

# 扫描配置
SCAN_INTERVAL_HOURS = int(os.getenv('SCAN_INTERVAL_HOURS', 24))
OUTPUT_DIR = os.getenv('OUTPUT_DIR', './scan_reports')

# AI相关的敏感信息模式
SENSITIVE_PATTERNS = [
    # OpenAI API密钥格式
    r'sk-[a-zA-Z0-9]{32,}',
    r'sk-proj-[a-zA-Z0-9_-]{32,}',
    
    # Anthropic API密钥格式
    r'sk-ant-[a-zA-Z0-9_-]{32,}',
    
    # Google AI (Gemini) API密钥格式
    r'AIza[a-zA-Z0-9_-]{35}',
    
    # ===== 常见环境变量名模式 (snake_case) =====
    # AI API Keys
    r'AI_API_KEY[\s]*=[\s]*["\']?([a-zA-Z0-9_-]{20,})["\']?',
    r'ai_api_key[\s]*=[\s]*["\']?([a-zA-Z0-9_-]{20,})["\']?',
    
    # OpenAI
    r'OPENAI_API_KEY[\s]*=[\s]*["\']?([a-zA-Z0-9_-]{20,})["\']?',
    r'openai_api_key[\s]*=[\s]*["\']?([a-zA-Z0-9_-]{20,})["\']?',
    r'OPENAI_KEY[\s]*=[\s]*["\']?([a-zA-Z0-9_-]{20,})["\']?',
    
    # Anthropic
    r'ANTHROPIC_AUTH_TOKEN[\s]*=[\s]*["\']?([a-zA-Z0-9_-]{20,})["\']?',
    r'ANTHROPIC_API_KEY[\s]*=[\s]*["\']?([a-zA-Z0-9_-]{20,})["\']?',
    r'anthropic_api_key[\s]*=[\s]*["\']?([a-zA-Z0-9_-]{20,})["\']?',
    
    # Claude
    r'CLAUDE_API_KEY[\s]*=[\s]*["\']?([a-zA-Z0-9_-]{20,})["\']?',
    r'claude_api_key[\s]*=[\s]*["\']?([a-zA-Z0-9_-]{20,})["\']?',
    
    # 通用 API Key
    r'API_KEY[\s]*=[\s]*["\']?([a-zA-Z0-9_-]{20,})["\']?',
    r'api_key[\s]*=[\s]*["\']?([a-zA-Z0-9_-]{20,})["\']?',
    
    # Chat API Key
    r'CHAT_API_KEY[\s]*=[\s]*["\']?([a-zA-Z0-9_-]{20,})["\']?',
    r'chat_api_key[\s]*=[\s]*["\']?([a-zA-Z0-9_-]{20,})["\']?',
    
    # ===== camelCase 和 PascalCase 模式 =====
    # 对象属性赋值: apiKey: "value"
    r'apiKey[\s]*:[\s]*["\']([a-zA-Z0-9_-]{20,})["\']',
    r'ApiKey[\s]*:[\s]*["\']([a-zA-Z0-9_-]{20,})["\']',
    
    # 变量赋值: apiKey = "value"
    r'apiKey[\s]*=[\s]*["\']([a-zA-Z0-9_-]{20,})["\']',
    r'ApiKey[\s]*=[\s]*["\']([a-zA-Z0-9_-]{20,})["\']',
    
    # chatApiKey 模式
    r'chatApiKey[\s]*[:=][\s]*["\']([a-zA-Z0-9_-]{20,})["\']',
    r'ChatApiKey[\s]*[:=][\s]*["\']([a-zA-Z0-9_-]{20,})["\']',
    
    # openaiApiKey 模式
    r'openaiApiKey[\s]*[:=][\s]*["\']([a-zA-Z0-9_-]{20,})["\']',
    r'OpenaiApiKey[\s]*[:=][\s]*["\']([a-zA-Z0-9_-]{20,})["\']',
    r'openAIKey[\s]*[:=][\s]*["\']([a-zA-Z0-9_-]{20,})["\']',
    
    # anthropicApiKey 模式
    r'anthropicApiKey[\s]*[:=][\s]*["\']([a-zA-Z0-9_-]{20,})["\']',
    r'AnthropicApiKey[\s]*[:=][\s]*["\']([a-zA-Z0-9_-]{20,})["\']',
    
    # ===== 其他 AI 服务 =====
    # Google AI / Gemini
    r'GOOGLE_API_KEY[\s]*=[\s]*["\']?([a-zA-Z0-9_-]{20,})["\']?',
    r'GEMINI_API_KEY[\s]*=[\s]*["\']?([a-zA-Z0-9_-]{20,})["\']?',
    
    # Hugging Face
    r'HUGGINGFACE_API_KEY[\s]*=[\s]*["\']?([a-zA-Z0-9_-]{20,})["\']?',
    r'HF_TOKEN[\s]*=[\s]*["\']?([a-zA-Z0-9_-]{20,})["\']?',
    
    # Cohere
    r'COHERE_API_KEY[\s]*=[\s]*["\']?([a-zA-Z0-9_-]{20,})["\']?',
    
    # Azure OpenAI
    r'AZURE_OPENAI_KEY[\s]*=[\s]*["\']?([a-zA-Z0-9_-]{20,})["\']?',
    r'AZURE_OPENAI_API_KEY[\s]*=[\s]*["\']?([a-zA-Z0-9_-]{20,})["\']?',
]

# GitHub搜索关键词
AI_SEARCH_KEYWORDS = [
    'openai api',
    'anthropic claude',
    'gpt api',
    'AI_API_KEY',
    'ANTHROPIC_AUTH_TOKEN',
    'chat_api_key',
    'apiKey',
    'sk-ant-',
    'sk-proj-',
    'OPENAI_API_KEY',
    'chatApiKey',
]

# 要排除的文件扩展名
EXCLUDED_EXTENSIONS = [
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg',
    '.mp4', '.avi', '.mov', '.wmv',
    '.zip', '.tar', '.gz', '.rar',
    '.exe', '.dll', '.so', '.dylib',
    '.pdf', '.doc', '.docx',
]

# 要排除的目录
EXCLUDED_DIRS = [
    'node_modules',
    '.git',
    'dist',
    'build',
    '__pycache__',
    'venv',
    'env',
]

# GitHub API速率限制
MAX_REPOS_PER_SEARCH = 100
SEARCH_DELAY_SECONDS = 2

# 仓库更新时间过滤
# 只搜索最近指定天数内有更新的仓库（忽略长时间不维护的库）
MIN_DAYS_SINCE_UPDATE = int(os.getenv('MIN_DAYS_SINCE_UPDATE', 665))

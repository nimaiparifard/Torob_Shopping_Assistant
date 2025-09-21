# Router System Testing Guide

این راهنما نحوه تست کامل سیستم Router را شرح می‌دهد.

## انواع تست‌ها

### 1. تست سریع (Quick Test)
برای بررسی سریع عملکرد پایه سیستم:

```bash
python router/run_tests.py --type quick
```

### 2. تست‌های واحد (Unit Tests)
برای تست اجزای مجزا:

```bash
python router/run_tests.py --type unit
```

### 3. تست‌های جامع (Comprehensive Tests)
برای تست کامل تمام قابلیت‌ها:

```bash
python router/run_tests.py --type comprehensive
```

### 4. تست پیکربندی (Config Test)
برای بررسی تنظیمات:

```bash
python router/run_tests.py --type config
```

### 5. همه تست‌ها
برای اجرای تمام تست‌ها:

```bash
python router/run_tests.py --type all
```

## تست‌های اجزای مختلف

### Hard Signal Detection
تست تشخیص الگوهای مشخص:

```python
from router import HardSignalDetector, RouterState

detector = HardSignalDetector()
state = RouterState(user_query="کابینت کد D14")
result = detector.detect(state)
print(f"Agent: {result.agent}, Confidence: {result.confidence}")
```

### Semantic Routing
تست مسیریابی معنایی:

```python
from router import SemanticRouter, get_router_config_from_env

config = get_router_config_from_env()
router = SemanticRouter(config)
await router.initialize()

state = RouterState(user_query="یه لپ تاپ خوب میخوام")
decision = await router.route_by_similarity(state)
```

### Embedding Service
تست سرویس embedding:

```python
from router import EmbeddingService, get_router_config_from_env

config = get_router_config_from_env()
service = EmbeddingService(config)

# تست تک متن
embedding = await service.get_embedding("سلام چطورید؟")

# تست دسته‌ای
texts = ["متن 1", "متن 2", "متن 3"]
embeddings = await service.get_embeddings_batch(texts)

# تست تشابه
similarity = service.cosine_similarity(embeddings[0], embeddings[1])
```

### Intent Parsing
تست تحلیل قصد:

```python
from router import IntentParser, get_router_config_from_env

config = get_router_config_from_env()
parser = IntentParser(config)

state = RouterState(user_query="قیمت گوشی سامسونگ چقدره؟")
intent = await parser.parse_intent(state)
print(f"Intent: {intent.intent}, Confidence: {intent.confidence}")
```

### Main Router Integration
تست router اصلی:

```python
from router import MainRouter, get_router_config_from_env, RouterState

config = get_router_config_from_env()
router = MainRouter(config)
await router.initialize()

state = RouterState(user_query="مقایسه آیفون با سامسونگ")
decision = await router.route(state)

# تحلیل دقیق
explanation = await router.get_routing_explanation("مقایسه آیفون با سامسونگ")
```

## مثال‌های تست

### تست عملکرد (Performance Test)

```python
import time
import asyncio

async def performance_test():
    config = get_router_config_from_env()
    router = MainRouter(config)
    await router.initialize()
    
    queries = ["سلام", "قیمت گوشی چقدره؟"] * 50
    
    start_time = time.time()
    for query in queries:
        state = RouterState(user_query=query)
        await router.route(state)
    
    total_time = time.time() - start_time
    avg_time = total_time / len(queries)
    
    print(f"Total time: {total_time:.2f}s")
    print(f"Average per query: {avg_time:.3f}s")
    print(f"Queries per second: {len(queries)/total_time:.1f}")
```

### تست دقت (Accuracy Test)

```python
test_cases = [
    ("کابینت کد D14", AgentType.SPECIFIC_PRODUCT),
    ("قیمت گوشی چقدره؟", AgentType.PRODUCT_FEATURE),
    ("مقایسه آیفون با سامسونگ", AgentType.COMPARISON),
    ("چطور خرید کنم؟", AgentType.GENERAL),
    ("یه لپ تاپ خوب میخوام", AgentType.EXPLORATION),
    ("فروشندگان کدومن؟", AgentType.SELLER_INFO)
]

correct = 0
total = len(test_cases)

for query, expected_agent in test_cases:
    state = RouterState(user_query=query)
    decision = await router.route(state)
    
    if decision.agent == expected_agent:
        correct += 1
        print(f"✅ {query} -> {decision.agent.name}")
    else:
        print(f"❌ {query} -> {decision.agent.name} (expected: {expected_agent.name})")

accuracy = correct / total
print(f"Accuracy: {accuracy:.2%}")
```

### تست Session Management

```python
from router import SessionManager

manager = SessionManager(max_turns=5)
session = manager.create_session("test-user")

# شبیه‌سازی مکالمه
conversation = [
    "سلام، یه گوشی میخوام",
    "بودجم 10 میلیونه",
    "کدوم برند بهتره؟",
    "سامسونگ یا شیائومی؟",
    "نظر نهایی شما چیه؟"
]

for query in conversation:
    state = RouterState(
        user_query=query,
        session_context=session.get_context_for_routing(),
        turn_count=session.turn_count
    )
    
    decision = await router.route(state)
    session.add_turn(query, decision, f"[Response from {decision.agent.name}]")
    
    print(f"Turn {session.turn_count}: {decision.agent.name}")
    
    if session.should_force_conclusion:
        print("⚠️ Should force conclusion!")
    
    if session.is_at_turn_limit:
        print("🛑 At turn limit!")
        break
```

## تست با داده‌های مختلف

### تست با متن‌های فارسی

```python
persian_queries = [
    "سلام، چطور می‌تونم خرید کنم؟",
    "قیمت گوشی سامسونگ گلکسی A54 چقدره؟",
    "یه لپ تاپ گیمینگ خوب تا 20 میلیون تومان میخوام",
    "مقایسه آیفون 15 پرو مکس با سامسونگ S24 اولترا",
    "فروشندگان معتبر لوازم خانگی در ترب کدومن؟"
]
```

### تست با متن‌های مختلط

```python
mixed_queries = [
    "گوشی iPhone 15 Pro Max قیمتش چقدره؟",
    "لپ تاپ ASUS ROG Strix G15 مدل 2024",
    "Samsung Galaxy S24 Ultra vs iPhone 15 Pro Max",
    "کد محصول SKU-12345 رو پیدا کن"
]
```

## اجرای تست‌ها

### پیش‌نیازها

1. فایل `.env` با تنظیمات صحیح
2. نصب dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### اجرای تست ساده

```bash
python test_router_system.py
```

### اجرای تست‌های کامل

```bash
python router/run_tests.py --type all
```

### تست بدون فایل .env

```python
# در فایل تست، config را مستقیم تنظیم کنید:
config = RouterConfig(
    openai_api_key="your-api-key",
    openai_base_url="https://turbo.torob.com/v1"
)
```

## نکات مهم

1. **API Key**: مطمئن شوید API key معتبر است
2. **Network**: اتصال اینترنت برای OpenAI API لازم است  
3. **Memory**: تست‌های جامع حافظه زیادی مصرف می‌کنند
4. **Time**: تست‌های کامل ممکن است چند دقیقه طول بکشند

## عیب‌یابی

### خطاهای رایج

1. **"Configuration validation failed"**
   - فایل `.env` را بررسی کنید
   - API key را تایید کنید

2. **"OpenAI API Error"**
   - اتصال اینترنت را بررسی کنید
   - API key و base URL را تایید کنید

3. **"Import Error"**
   - dependencies را نصب کنید
   - Python path را بررسی کنید

### لاگ‌ها

برای دیدن لاگ‌های بیشتر:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## گزارش تست

تست‌ها گزارش کاملی از عملکرد ایجاد می‌کنند شامل:

- دقت هر جزء
- زمان پاسخ
- نرخ موفقیت
- خطاهای رخ داده
- آمار cache و memory

این گزارش‌ها برای بهینه‌سازی و بهبود سیستم استفاده می‌شوند.

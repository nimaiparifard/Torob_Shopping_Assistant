# Router Module - دستیار خرید هوشمند

این ماژول مسئول مسیریابی درخواست‌های کاربران به عامل‌های مناسب در سیستم دستیار خرید هوشمند است.

## معماری Router

Router از سه استراتژی مکمل برای تصمیم‌گیری استفاده می‌کند:

### 1. تشخیص سیگنال‌های سخت (Hard Signals)
- **سرعت**: بسیار سریع (regex-based)
- **دقت**: بسیار بالا برای الگوهای مشخص
- **موارد استفاده**:
  - کدهای محصول (SKU, مدل)
  - شناسه‌های base
  - کلمات کلیدی مشخص (مقایسه، فروشنده، قیمت)

### 2. تحلیل Intent با LLM
- **سرعت**: متوسط
- **دقت**: بالا برای درک معنایی
- **موارد استفاده**:
  - استخراج موجودیت‌ها
  - تشخیص قصد پیچیده
  - درک زمینه مکالمه

### 3. تشابه معنایی (Semantic Similarity)
- **سرعت**: سریع (با کش)
- **دقت**: خوب برای موارد عمومی
- **موارد استفاده**:
  - مقایسه با نمونه‌های از پیش تعریف شده
  - تشخیص الگوهای مشابه
  - fallback برای موارد نامشخص

## عامل‌های سیستم

### Agent 0: عامل عمومی
- پاسخ به سوالات روزمره
- راهنمای خرید
- قوانین و مقررات

### Agent 1: یافتن محصول خاص
- جستجوی محصول با کد یا مدل دقیق
- دسترسی مستقیم به محصول

### Agent 2: ویژگی‌های محصول
- قیمت محصولات
- مشخصات فنی
- اطلاعات تکمیلی محصول

### Agent 3: اطلاعات فروشندگان
- لیست فروشندگان یک محصول
- اطلاعات فروشگاه‌ها

### Agent 4: کاوش و تعامل
- کمک به کاربر برای یافتن محصول مناسب
- پرسش و پاسخ تعاملی
- حداکثر 5 دور مکالمه

### Agent 5: مقایسه محصولات
- مقایسه دو یا چند محصول
- ارائه پیشنهاد بهترین گزینه

## نحوه استفاده

### راه‌اندازی اولیه

```python
from router import RouterConfig, MainRouter, RouterState

# پیکربندی
config = RouterConfig(
    openai_api_key="your-api-key",
    embedding_model="text-embedding-3-small",
    llm_model="gpt-4o-mini",
    max_turns=5
)

# ایجاد router
router = MainRouter(config)
await router.initialize()
```

### مسیریابی یک درخواست

```python
# ایجاد state
state = RouterState(
    user_query="قیمت گوشی سامسونگ A54 چقدره؟",
    turn_count=0
)

# مسیریابی
decision = await router.route(state)

print(f"عامل: {decision.agent}")
print(f"اطمینان: {decision.confidence}")
print(f"دلیل: {decision.reasoning}")
```

### مدیریت جلسه

```python
from router import SessionManager

# ایجاد مدیر جلسه
session_manager = SessionManager(max_turns=5)

# ایجاد یا دریافت جلسه
session = session_manager.get_or_create_session("user-123")

# افزودن دور مکالمه
session.add_turn(query, decision, response)

# بررسی محدودیت دورها
if session.is_at_turn_limit:
    print("به حد مجاز رسیدیم!")
```

## جزئیات پیاده‌سازی

### فرآیند مسیریابی

1. **Hard Signal Detection**
   - بررسی regex patterns
   - استخراج کدها و شناسه‌ها
   - تصمیم‌گیری سریع با اطمینان بالا

2. **Intent Parsing** (در صورت نیاز)
   - ارسال به LLM
   - استخراج ساختاریافته
   - تحلیل موجودیت‌ها

3. **Semantic Routing** (در صورت نیاز)
   - محاسبه embedding
   - مقایسه با نمونه‌ها
   - انتخاب بر اساس تشابه

4. **Decision Combination**
   - ترکیب وزن‌دار نتایج
   - اعمال قوانین کسب‌وکار
   - تصمیم نهایی

### بهینه‌سازی‌ها

- **Caching**: ذخیره embeddings برای کاهش محاسبات
- **Batch Processing**: پردازش دسته‌ای embeddings
- **Early Exit**: خروج سریع با hard signals
- **Turn Budget**: مدیریت هوشمند دورهای مکالمه

## مثال‌های کاربردی

### مثال 1: تشخیص محصول با کد

```
ورودی: "لطفا کابینت چهار کشو کد D14 رو برام پیدا کن"
خروجی: Agent 1 (محصول خاص) - اطمینان: 0.95
```

### مثال 2: سوال درباره قیمت

```
ورودی: "قیمت پارچه لیکرا حلقوی نوریس 1/30 طلایی چقدره؟"
خروجی: Agent 2 (ویژگی محصول) - اطمینان: 0.90
```

### مثال 3: درخواست مقایسه

```
ورودی: "مقایسه آیفون 15 با سامسونگ S24 اولترا"
خروجی: Agent 5 (مقایسه) - اطمینان: 0.85
```

### مثال 4: جستجوی کلی

```
ورودی: "یه لپ تاپ خوب برای برنامه نویسی میخوام"
خروجی: Agent 4 (کاوش) - اطمینان: 0.75
```

## تنظیمات و پیکربندی

### آستانه‌های تشابه

```python
config = RouterConfig(
    similarity_threshold_low=0.3,   # زیر این مقدار → کاوش
    similarity_threshold_high=0.7,  # بالای این مقدار → اطمینان بالا
)
```

### مدیریت دورها

```python
config = RouterConfig(
    max_turns=5,              # حداکثر دورهای مکالمه
    force_conclusion_turn=4,  # اجبار به نتیجه‌گیری
)
```

### انتخاب مدل

```python
config = RouterConfig(
    embedding_model="text-embedding-3-small",  # سریع و ارزان
    # یا
    embedding_model="text-embedding-3-large",  # دقیق‌تر
    
    llm_model="gpt-4o-mini",  # سریع برای intent
    # یا
    llm_model="gpt-4",        # دقیق‌تر
)
```

## نکات عملکرد

1. **برای سرعت بیشتر**:
   - از `text-embedding-3-small` استفاده کنید
   - hard signals را اولویت دهید
   - cache را فعال نگه دارید

2. **برای دقت بیشتر**:
   - از `text-embedding-3-large` استفاده کنید
   - آستانه‌ها را افزایش دهید
   - نمونه‌های بیشتری اضافه کنید

3. **برای مقیاس‌پذیری**:
   - از Qdrant برای ذخیره embeddings استفاده کنید
   - session cleanup را فعال کنید
   - batch processing را بهینه کنید

## توسعه و گسترش

### اضافه کردن عامل جدید

1. AgentType را در `base.py` گسترش دهید
2. نمونه‌های جدید در `exemplars.py` اضافه کنید
3. قوانین hard signal در `hard_signals.py` بروز کنید
4. intent mapping را در `intent_parser.py` اضافه کنید

### اضافه کردن زبان جدید

1. نمونه‌های چندزبانه در exemplars اضافه کنید
2. regex patterns را برای زبان جدید بروز کنید
3. از embedding model چندزبانه استفاده کنید

## Troubleshooting

### مشکل: Router همیشه به کاوش می‌رود
- آستانه similarity را کاهش دهید
- نمونه‌های بیشتری اضافه کنید
- hard signals را بررسی کنید

### مشکل: تصمیمات نادرست
- logs را بررسی کنید
- از `get_routing_explanation` استفاده کنید
- نمونه‌های اشتباه را اصلاح کنید

### مشکل: کندی عملکرد
- cache را بررسی کنید
- از مدل سبک‌تر استفاده کنید
- batch size را بهینه کنید

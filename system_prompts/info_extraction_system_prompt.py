info_extraction_system_prompt = (
    "تو یک استخراج‌کننده حرفه‌ای اطلاعات محصولات هستی. "
    "ورودی همیشه یک پرسش کاربر است که ممکن است شامل اطلاعات مختلفی درباره محصول مورد نظر باشد. "
    "وظیفه‌ی تو این است که تمام اطلاعات موجود در متن را استخراج کرده و در قالب JSON معتبر (UTF-8) ارائه دهی. "
    "هیچ متن اضافه، توضیح یا نشانه‌گذاری دیگری مجاز نیست. "
    "خروجی باید دقیقاً به این ساختار باشد: "
    '{"product_name": "...", "city_name": "...", "brand_name": "...", "category_name": "...", "features": {...}, "lowest_price": ..., "highest_price": ..., "has_warranty": ..., "shop_name": "...", "score": ...}. '

    "قوانین بسیار مهم و غیرقابل تخطی: "
    "۱. نام محصول را کامل و دقیق استخراج کن (شامل همه جزئیات مثل مدل، کد، رنگ، طرح، سایز). "
    "۲. نام شهر را فقط از نام‌های شهرهای ایران استخراج کن. "
    "۳. نام برند را از متن استخراج کن. "
    "۴. دسته‌بندی محصول را بر اساس نام محصول تشخیص بده. "
    "۵. ویژگی‌ها را به صورت دیکشنری با کلید فارسی و مقدار استخراج کن. "
    "۶. قیمت‌ها را به صورت عدد صحیح (بدون کاما یا نقطه) استخراج کن. "
    "۷. اگر اطلاعاتی موجود نبود، مقدار null قرار بده. "
    "۸. امتیاز فروشگاه را بین ۰ تا ۵ استخراج کن. "
    "۹. گارانتی را true/false/null تشخیص بده. "

    "نمونه‌ی کلیدی: "
    "پرسش: 'سلام! من دنبال یه لوستر سقفی هستم که برای اتاق نشیمن مناسب باشه.' "
    "خروجی درست: "
    '{"product_name": "لوستر سقفی مناسب اتاق نشیمن", "city_name": null, "brand_name": null, "category_name": "لوستر", "features": null, "lowest_price": null, "highest_price": null, "has_warranty": null, "shop_name": null, "score": null}. '
)

info_extraction_samples = [
    {
        "input": "سلام! من دنبال یه لوستر سقفی هستم که برای اتاق نشیمن مناسب باشه. می‌خواستم بدونم آیا می‌تونید به من کمک کنید تا یه فروشنده خوب پیدا کنم? ممنون می‌شم اگه راهنمایی کنید.",
        "product_name": "لوستر سقفی مناسب اتاق نشیمن",
        "city_name": None,
        "brand_name": None,
        "category_name": "لوستر",
        "features": None,
        "lowest_price": None,
        "highest_price": None,
        "has_warranty": None,
        "shop_name": None,
        "score": None
    },
    {
        "input": "من به دنبال لوستری هستم که نصب سقفی داشته باشه و از جنس پلاستیک باشه. همچنین، قیمتش حدود ۱,۱۵۰,۰۰۰ تومان باشه. آیا می‌تونید فروشنده‌ای با این مشخصات پیدا کنید؟ ممنون می‌شم اگه راهنمایی کنید.",
        "product_name": "لوستر سقفی نصب سقفی",
        "city_name": None,
        "brand_name": None,
        "category_name": "لوستر",
        "features": {"جنس": "پلاستیک"},
        "lowest_price": 1150000,
        "highest_price": None,
        "has_warranty": None,
        "shop_name": None,
        "score": None
    },
    {
        "input": "سلام! من دنبال یه گیاه بونسای هستم که خیلی خاص و زیبا باشه. می‌خوام برای هدیه دادن استفاده کنم و بهتره که ارسال گل رایگان هم داشته باشه. قیمتش هم حدوداً بین ۳,۷۰۰,۰۰۰ تا ۴,۱۰۰,۰۰۰ تومان باشه. می‌تونید کمکم کنید؟",
        "product_name": "گیاه بونسای",
        "city_name": None,
        "brand_name": None,
        "category_name": "گیاه",
        "features": {"ارسال": "رایگان"},
        "lowest_price": 3700000,
        "highest_price": 4100000,
        "has_warranty": None,
        "shop_name": None,
        "score": None
    },
    {
        "input": "محصولی که به دنبالش هستم، \"ملحفه کشدار تشک خوشخواب دو نفره هتلی کرم بژ\" است. آیا می‌تونید فروشنده‌ای با امتیاز ۵.۰ در کرج پیدا کنید که این محصول رو داشته باشه؟",
        "product_name": "ملحفه کشدار تشک خوشخواب دو نفره هتلی کرم بژ",
        "city_name": "کرج",
        "brand_name": None,
        "category_name": "ملحفه",
        "features": None,
        "lowest_price": None,
        "highest_price": None,
        "has_warranty": None,
        "shop_name": None,
        "score": 5.0
    },
    {
        "input": "من دنبال یه تلویزیون سامسونگ ۵۵ اینچ ۴K هستم که قیمتش زیر ۱۵ میلیون تومان باشه و گارانتی داشته باشه. می‌تونید در تهران پیدا کنید؟",
        "product_name": "تلویزیون سامسونگ ۵۵ اینچ ۴K",
        "city_name": "تهران",
        "brand_name": "سامسونگ",
        "category_name": "تلویزیون",
        "features": {"سایز": "۵۵ اینچ", "وضوح": "۴K"},
        "lowest_price": None,
        "highest_price": 15000000,
        "has_warranty": True,
        "shop_name": None,
        "score": None
    },
    {
        "input": "آیا می‌تونید یه ماشین لباسشویی بوش ۷ کیلویی با گارانتی ۲۴ ماهه در اصفهان پیدا کنید؟",
        "product_name": "ماشین لباسشویی بوش ۷ کیلویی",
        "city_name": "اصفهان",
        "brand_name": "بوش",
        "category_name": "ماشین لباسشویی",
        "features": {"ظرفیت": "۷ کیلو"},
        "lowest_price": None,
        "highest_price": None,
        "has_warranty": True,
        "shop_name": None,
        "score": None
    },
    {
        "input": "من دنبال یه کفش ورزشی نایکی هستم که سایز ۴۲ باشه و رنگ مشکی داشته باشه. قیمتش هم بین ۲ تا ۳ میلیون تومان باشه.",
        "product_name": "کفش ورزشی نایکی سایز ۴۲",
        "city_name": None,
        "brand_name": "نایکی",
        "category_name": "کفش",
        "features": {"سایز": "۴۲", "رنگ": "مشکی"},
        "lowest_price": 2000000,
        "highest_price": 3000000,
        "has_warranty": None,
        "shop_name": None,
        "score": None
    },
    {
        "input": "آیا می‌تونید یه فروشگاه با امتیاز بالای ۴ در مشهد پیدا کنید که یخچال ال جی داشته باشه؟",
        "product_name": "یخچال ال جی",
        "city_name": "مشهد",
        "brand_name": "ال جی",
        "category_name": "یخچال",
        "features": None,
        "lowest_price": None,
        "highest_price": None,
        "has_warranty": None,
        "shop_name": None,
        "score": 4.0
    }
]
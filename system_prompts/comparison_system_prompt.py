route_task_comparison_system_prompt = (
    "تو یک مسیریاب هوشمند برای تشخیص نوع مقایسه محصولات هستی. "
    "ورودی همیشه یک پرسش کاربر است که شامل مقایسه دو محصول می‌باشد. "
    "خروجی باید فقط و فقط در قالب JSON معتبر (UTF-8) و دقیقا با این ساختار باشد: "
    '{"comparison_type": "...", "product_name_1": "...", "product_random_key_1": "...", "product_name_2": "...", "product_random_key_2": "..."}. '

    "انواع مقایسه قابل تشخیص: "
    "۱. 'feature_level' - مقایسه ویژگی‌های فنی و مشخصات محصولات "
    "۲. 'shop_level' - مقایسه از نظر تعداد فروشگاه‌ها و در دسترس بودن "
    "۳. 'warranty_level' - مقایسه از نظر ضمانت و گارانتی در شهرهای مختلف "
    "۴. 'city_level' - مقایسه از نظر موجودی در شهرهای مختلف"
    "5. 'general' - اگر نوع مقایسه مشخص نبود یا مبهم بود"

    "قوانین بسیار مهم: "
    "۱. نام محصولات را کامل و دقیق استخراج کن (شامل همه جزئیات مثل مدل، کد، رنگ، طرح، سایز). "
    "۲. اگر شناسه محصول (random_key) در متن ذکر شده، آن را در فیلد مربوطه قرار بده، در غیر این صورت null. "
    "۳. اگر نام محصول مشخص نبود مقدار product_name را 'نامشخص' قرار بده. "
    "۴. خروجی هیچ متن، توضیح، نشانه‌گذاری اضافه، یا فرمت دیگری نباید داشته باشد. "
    "۵. بسیار دقت کن که comparison_type دقیقا مطابق با درخواست کاربر باشد. "
    "۶. اگر درخواست مبهم بود، comparison_type را 'general' قرار بده. "
    "۷. برای تشخیص نوع مقایسه به کلمات کلیدی توجه کن: "
    "   - feature_level: ویژگی، مشخصات، کیفیت، عملکرد، مصرف انرژی، وضوح، اصالت، تعداد تکه‌ها "
    "   - shop_level: فروشگاه، موجود، خرید، در دسترس "
    "   - warranty_level: گارانتی، ضمانت، خدمات پس از فروش "
    "   - city_level: شهر، شهرها، مکان‌های مختلف "
    "اگر نوع مقایسه مبهم باشد یا نتوانی تشخیص دهی، مقدار comparison_type را 'general' قرار بده. "
    "برای مثال از این دسته می توان به این مثال دقت کرد کدام یک از یخچال فریزر کمبی جی‌ پلاس مدل M5320 یا یخچال فریزر جی پلاس مدل GRF-P5325 برای خانواده‌های پرجمعیت مناسب‌تر است؟ "

    "مثال کلیدی: "
    "پرسش: 'کدامیک از محصولات دراور فایل کمدی پلاستیکی طرح کودک با شناسه ebolgl و دراور هوم کت ۴ طبقه بزرگ طرح دار از پلاستیک با شناسه nihvhq در فروشگاه‌های بیشتری موجود است؟' "
    "خروجی درست: "
    '{"comparison_type": "shop_level", "product_name_1": "دراور فایل کمدی پلاستیکی طرح کودک", "product_random_key_1": "ebolgl", "product_name_2": "دراور هوم کت ۴ طبقه بزرگ طرح دار از پلاستیک", "product_random_key_2": "nihvhq"}. '
)

route_task_comparison_samples = [
    # نمونه‌های مقایسه ویژگی‌ها
    {
        "input": "از بین یخچال فریزر هیمالیا مدل FIVE MODE ظرفیت ۲۲ فوت هومباردار با شناسه \"faddzl\" و یخچال فریزر هیمالیا مدل کمبی 530 هوم بار با شناسه \"nkepsf\"، کدام رنگ‌های موجود بیشتری جهت انطباق با سبک‌های مختلف آشپزخانه دارد؟",
        "comparison_type": "feature_level",
        "product_name_1": "یخچال فریزر هیمالیا مدل FIVE MODE ظرفیت ۲۲ فوت هومباردار",
        "product_random_key_1": "faddzl",
        "product_name_2": "یخچال فریزر هیمالیا مدل کمبی 530 هوم بار",
        "product_random_key_2": "nkepsf"
    },
    {
      "input": "کدام یک از یخچال فریزر کمبی جی‌ پلاس مدل M5320 یا یخچال فریزر جی پلاس مدل GRF-P5325 برای خانواده‌های پرجمعیت مناسب‌تر است؟ ",
        "comparison_type": "general",
        "product_name_1": "یخچال فریزر کمبی جی‌ پلاس مدل M5320",
        "product_random_key_1": None,
        "product_name_2": "یخچال فریزر جی پلاس مدل GRF-P5325",
        "product_random_key_2": None
    },
    {
        "input": "کدام یک از این تلویزیون‌ها برای تماشای محتوای با وضوح بالا مناسب‌تر است؟ تلویزیون جی پلاس مدل PH514N سایز ۵۰ اینچ یا تلویزیون جی پلاس GTV-50RU766S سایز ۵۰ اینچ",
        "comparison_type": "feature_level",
        "product_name_1": "تلویزیون جی پلاس مدل PH514N سایز ۵۰ اینچ",
        "product_random_key_1": None,
        "product_name_2": "تلویزیون جی پلاس GTV-50RU766S سایز ۵۰ اینچ",
        "product_random_key_2": None
    },
    {
        "input": "برای مقایسه، کدام یک از محصولات جا ادویه شیشه ای با درب چوبی و استند نردبانی با شناسه gouchy و جا ادویه مک کارتی استند چوبی با شناسه uhqmhb از نظر تعداد تکه‌ها بیشتر است؟",
        "comparison_type": "feature_level",
        "product_name_1": "جا ادویه شیشه ای با درب چوبی و استند نردبانی",
        "product_random_key_1": "gouchy",
        "product_name_2": "جا ادویه مک کارتی استند چوبی",
        "product_random_key_2": "uhqmhb"
    },
    {
        "input": "سلام، می‌خواستم بدانم بین یخچال فریزر ۴ کشویی ظرفیت ۲۹۴۶ با شناسه kdihkn و یخچال ایستکول ظرفیت ۵ فوت با شناسه bmonga کدام یک مصرف انرژی بهتری دارند؟",
        "comparison_type": "feature_level",
        "product_name_1": "یخچال فریزر ۴ کشویی ظرفیت ۲۹۴۶",
        "product_random_key_1": "kdihkn",
        "product_name_2": "یخچال ایستکول ظرفیت ۵ فوت",
        "product_random_key_2": "bmonga"
    },
    {
        "input": "این دو تلویزیون ال جی NANO75 سایز ۵۰ اینچ Ultra HD 4K LED و تلویزیون ال جی مدل UT80006 سایز ۵۰ اینچ Ultra HD 4K LED با شناسه dmsmlc از لحاظ اصالت محصول چگونه با یکدیگر مقایسه می‌شوند؟",
        "comparison_type": "feature_level",
        "product_name_1": "تلویزیون ال جی NANO75 سایز ۵۰ اینچ Ultra HD 4K LED",
        "product_random_key_1": None,
        "product_name_2": "تلویزیون ال جی مدل UT80006 سایز ۵۰ اینچ Ultra HD 4K LED",
        "product_random_key_2": "dmsmlc"
    },
    {
        "input" : "می‌خواستم بدونم برای دیدن فیلم‌های 4K، بین تلویزیون جی‌پلاس مدل PH514N و مدل GTV-50RU766S هر دو در سایز ۵۰ اینچ، کدوم کیفیت بهتری ارائه می‌دهند؟",
        "comparison_type": "feature_level",
        "product_name_1": "تلویزیون جی‌پلاس مدل PH514N سایز ۵۰ اینچ",
        "product_random_key_1": None,
        "product_name_2": "تلویزیون جی‌پلاس مدل GTV-50RU766S سایز ۵۰ اینچ",
        "product_random_key_2": None
    },
    {
        "input": "سلام، از نظر مصرف انرژی، یخچال چهارکشو با ظرفیت ۲۹۴۶ لیتر (شناسه kdihkn) بهینه‌تره یا یخچال ایستکول ۵ فوتی (شناسه bmonga)؟",
        "comparison_type": "feature_level",
        "product_name_1": "یخچال چهارکشو با ظرفیت ۲۹۴۶ لیتر",
        "product_random_key_1": "kdihkn",
        "product_name_2": "یخچال ایستکول ۵ فوتی",
        "product_random_key_2": "bmonga"
    },
    {
      "input": "اگر بخوام برای تماشای محتوای با وضوح بالا یک تلویزیون انتخاب کنم، خرید جی‌پلاس ۵۰ اینچ PH514N بهتره یا مدل GTV-50RU766S؟",
        "comparison_type": "feature_level",
        "product_name_1": "تلویزیون جی‌پلاس ۵۰ اینچ PH514N",
        "product_random_key_1": None,
        "product_name_2": "تلویزیون جی‌پلاس مدل GTV-50RU766S سایز ۵۰ اینچ",
        "product_random_key_2": None
    },
    {
        "input": "بین یخچال فریزر چهار کشویی با ظرفیت ۲۹۴۶ لیتر (شناسه kdihkn) و یخچال ایستکول ۵ فوت (شناسه bmonga)، کدوم یکی از نظر مصرف انرژی بهینه‌تره؟",
        "comparison_type": "feature_level",
        "product_name_1": "یخچال فریزر چهار کشویی با ظرفیت ۲۹۴۶ لیتر",
        "product_random_key_1": "kdihkn",
        "product_name_2": "یخچال ایستکول ۵ فوت",
        "product_random_key_2": "bmonga"
    },
    # نمونه‌های مقایسه فروشگاه‌ها
    {
        "input": "کدامیک از محصولات دراور فایل کمدی پلاستیکی طرح کودک با شناسه ebolgl و دراور هوم کت ۴ طبقه بزرگ طرح دار از پلاستیک با شناسه nihvhq در فروشگاه‌های بیشتری موجود است و آسان‌تر می‌توان آن را خرید؟",
        "comparison_type": "shop_level",
        "product_name_1": "دراور فایل کمدی پلاستیکی طرح کودک",
        "product_random_key_1": "ebolgl",
        "product_name_2": "دراور هوم کت ۴ طبقه بزرگ طرح دار از پلاستیک",
        "product_random_key_2": "nihvhq"
    },
    {
        "input": "کدام یک از این دو محصول در فروشگاه‌های بیشتری موجود است؟ گوشی سامسونگ گلکسی A54 یا آیفون 14",
        "comparison_type": "shop_level",
        "product_name_1": "گوشی سامسونگ گلکسی A54",
        "product_random_key_1": None,
        "product_name_2": "آیفون 14",
        "product_random_key_2": None
    },
    
    # نمونه‌های مقایسه گارانتی
    {
        "input": "کدام یک از این دو لپ‌تاپ با توجه به گارانتی و خدمات پس از فروش بهتر است؟ لپ‌تاپ لنوو مدل Ideapad 3 15ITL6 با گارانتی ۱۸ ماهه یا لپ‌تاپ ایسوس مدل VivoBook R565EA با گارانتی ۲۴ ماهه؟",
        "comparison_type": "warranty_level",
        "product_name_1": "لپ‌تاپ لنوو مدل Ideapad 3 15ITL6",
        "product_random_key_1": None,
        "product_name_2": "لپ‌تاپ ایسوس مدل VivoBook R565EA",
        "product_random_key_2": None
    },
    {
        "input": "کدام یک از این دو تلویزیون گارانتی بهتری دارد؟ تلویزیون سونی مدل KD-55X80K یا تلویزیون سامسونگ مدل UN55TU8000",
        "comparison_type": "warranty_level",
        "product_name_1": "تلویزیون سونی مدل KD-55X80K",
        "product_random_key_1": None,
        "product_name_2": "تلویزیون سامسونگ مدل UN55TU8000",
        "product_random_key_2": None
    },
    {
        "input": "اگر بخوایم از نظر در دسترس بودن توی فروشگاه‌ها مقایسه کنیم، دراور پلاستیکی کودک (ebolgI) بیشتر موجوده یا مدل ۴ طبقه هوم کت (nihvhq)؟",
        "comparison_type": "shop_level",
        "product_name_1": "دراور پلاستیکی کودک",
        "product_random_key_1": "ebolgI",
        "product_name_2": "دراور مدل ۴ طبقه هوم کت",
        "product_random_key_2": "nihvhq"
    },
    {
        "input": "بین گوشی سامسونگ گلکسی A54 و آیفون 14، کدوم یکی توی فروشگاه‌های بیشتری موجوده؟",
        "comparison_type": "shop_level",
        "product_name_1": "گوشی سامسونگ گلکسی A54",
        "product_random_key_1": None,
        "product_name_2": "آیفون 14",
        "product_random_key_2": None
    },
    {
        "input": "بین دو محصول دراور پلاستیکی طرح کودک (ebolgI) و دراور هوم کت ۴ طبقه (nihvhq)، کدوم رو راحت‌تر میشه توی فروشگاه‌های مختلف پیدا کرد؟",
        "comparison_type": "shop_level",
        "product_name_1": "دراور پلاستیکی طرح کودک",
        "product_random_key_1": "ebolgI",
        "product_name_2": "دراور هوم کت ۴ طبقه",
        "product_random_key_2": "nihvhq"
    },
    {
        "input": "بین دو محصول دراور پلاستیکی طرح کودک (ebolgI) و دراور هوم کت ۴ طبقه (nihvhq)،کدام یک میانگین قیمت کمتری دارد؟",
        "comparison_type": "shop_level",
        "product_name_1": "دراور پلاستیکی طرح کودک",
        "product_random_key_1": "ebolgI",
        "product_name_2": "دراور هوم کت ۴ طبقه",
        "product_random_key_2": "nihvhq"
    },
    {
        "input": "بین گوشی سامسونگ گلکسی A54 و آیفون 14، از نظر حداقل قیمت مقایسه کنید.",
        "comparison_type": "shop_level",
        "product_name_1": "گوشی سامسونگ گلکسی A54",
        "product_random_key_1": None,
        "product_name_2": "آیفون 14",
        "product_random_key_2": None
    },
    {
        "input": "از نظر بیش ترین قیمت مقایسه کن؟ تلویزیون سونی مدل KD-55X80K یا تلویزیون سامسونگ مدل UN55TU8000",
        "comparison_type": "shop_level",
        "product_name_1": "تلویزیون سونی مدل KD-55X80K",
        "product_random_key_1": None,
        "product_name_2": "تلویزیون سامسونگ مدل UN55TU8000",
        "product_random_key_2": None
    },


    # نمونه‌های مقایسه شهرها
    {
        "input": "کدام محصول بین گلدون کنار سالنی سه سایزی طرح راش با شناسه dzpdls و گلدان شیشه‌ای لب طلایی مدل گلوریا سایز ۷۰ سانتی در تعداد بیشتری از شهرها موجود است؟",
        "comparison_type": "city_level",
        "product_name_1": "گلدون کنار سالنی سه سایزی طرح راش",
        "product_random_key_1": "dzpdls",
        "product_name_2": "گلدان شیشه‌ای لب طلایی مدل گلوریا سایز ۷۰ سانتی",
        "product_random_key_2": None
    },
    {
        "input": "کدام یک از این دو محصول در شهرهای بیشتری موجود است؟ ماشین لباسشویی بوش مدل WAT28441 یا ماشین ظرفشویی بوش مدل SPS46MI00E",
        "comparison_type": "city_level",
        "product_name_1": "ماشین لباسشویی بوش مدل WAT28441",
        "product_random_key_1": None,
        "product_name_2": "ماشین ظرفشویی بوش مدل SPS46MI00E",
        "product_random_key_2": None
    },
    {
      "input": "می‌خوام بدونم کدوم محصول رو توی شهرهای کمتری میشه پیدا کرد: گلدون کنار سالنی سه سایزی طرح راش (شناسه dzpdls) یا گلدان شیشه‌ای لب طلایی مدل گلوریا سایز ۷۰ سانتی؟" ,
      "comparison_type": "city_level",
      "product_name_1": "گلدون کنار سالنی سه سایزی طرح راش",
      "product_random_key_1": "dzpdls",
      "product_name_2": "گلدان شیشه‌ای لب طلایی مدل گلوریا سایز ۷۰ سانتی",
        "product_random_key_2": None
    },
    {
        "input": "سلام، اگر بخوایم گستره‌ی عرضه در شهرهای مختلف رو مقایسه کنیم، گلدون سه سایزی طرح راش (dzpdls) بیشتر تو شهرها موجوده یا گلدان گلوریا ۷۰ سانتی لب‌طلایی؟",
        "comparison_type": "city_level",
        "product_name_1": "گلدون سه سایزی طرح راش",
        "product_random_key_1": "dzpdls",
        "product_name_2": "گلدان گلوریا ۷۰ سانتی لب‌طلایی",
        "product_random_key_2": None
    },
    {
      "input": "برای خرید، برام مهمه کدوم محصول در شهرهای بیشتری حضور داره. به نظرت گلدون کنار سالنی طرح راش (شناسه dzpdls) فراگیرتره یا گلدان شیشه‌ای گلوریا ۷۰ سانتی؟",
        "comparison_type": "city_level",
        "product_name_1": "گلدون کنار سالنی طرح راش",
        "product_random_key_1": "dzpdls",
        "product_name_2": "گلدان شیشه‌ای گلوریا ۷۰ سانتی",
        "product_random_key_2": None
    },
    {
        "input": "می‌خواستم مقایسه کنم از نظر تعداد شهرهایی که محصول توشون موجوده: گلدون سه‌تکه طرح راش (dzpdls) بیشتر توی شهرها پیدا میشه یا گلدان شیشه‌ای گلوریا ۷۰ سانتی؟",
        "comparison_type": "city_level",
        "product_name_1": "گلدون سه‌تکه طرح راش",
        "product_random_key_1": "dzpdls",
        "product_name_2": "گلدان شیشه‌ای گلوریا ۷۰ سانتی",
        "product_random_key_2": None
    },
    {
        "input": "از نظر پراکندگی در شهرهای مختلف، خرید کدوم راحت‌تره: گلدون طرح راش سه سایزی (شناسه dzpdls) یا گلدان گلوریا ۷۰ سانتی لب طلایی؟",
        "comparison_type": "city_level",
        "product_name_1": "گلدون طرح راش سه سایزی",
        "product_random_key_1": "dzpdls",
        "product_name_2": "گلدان گلوریا ۷۰ سانتی لب طلایی",
        "product_random_key_2": None
    },
    # نمونه‌های مقایسه ضمانت در شهرها
    {
        "input": "محصول لحاف کرسی دست دوز ترمه طرح نسترن رنگ زرشکی با شناسه iushix و لحاف کرسی دست دوز ترمه آبی طرح نسترن کد 119807 Lahaf از نظر در دسترس بودن گارانتی در شهرهای مختلف را مقایسه کنید. کدام یک گزینه بهتری است؟",
        "comparison_type": "warranty_level",
        "product_name_1": "لحاف کرسی دست دوز ترمه طرح نسترن رنگ زرشکی",
        "product_random_key_1": "iushix",
        "product_name_2": "لحاف کرسی دست دوز ترمه آبی طرح نسترن کد 119807",
        "product_random_key_2": "Lahaf"
    },

    {
        "input": "کدام یک از این دو محصول ضمانت بهتری در شهرهای مختلف دارد؟ یخچال سامسونگ مدل RT28K5070SL یا یخچال ال جی مدل GL-B201SLC",
        "comparison_type": "warranty_level",
        "product_name_1": "یخچال سامسونگ مدل RT28K5070SL",
        "product_random_key_1": None,
        "product_name_2": "یخچال ال جی مدل GL-B201SLC",
        "product_random_key_2": None
    },
    {
        "input": "می‌خواستم بدونم از نظر پوشش خدمات گارانتی در شهرهای مختلف، لحاف کرسی ترمه دست‌دوز طرح نسترن رنگ زرشکی (شناسه iushix) بهتره یا مدل آبی طرح نسترن کد 119807؟",
        "comparison_type": "warranty_level",
        "product_name_1": "لحاف کرسی ترمه دست‌دوز طرح نسترن رنگ زرشکی",
        "product_random_key_1": "iushix",
        "product_name_2": "لحاف کرسی ترمه آبی طرح نسترن کد 119807",
        "product_random_key_2": None
    },
    {
      "input":  "گر بخوایم گارانتی محصولات رو در سطح شهرهای مختلف بررسی کنیم، کدوم لحاف کرسی دست‌دوز ترمه پوشش بهتری داره: مدل زرشکی (iushix) یا مدل آبی کد 119807؟",
        "comparison_type": "warranty_level",
        "product_name_1": "لحاف کرسی دست‌دوز ترمه مدل زرشکی",
        "product_random_key_1": "iushix",
        "product_name_2": "لحاف کرسی دست‌دوز ترمه مدل آبی کد 119807",
        "product_random_key_2": None
    },
    {
        "input": "برای کسانی که نگران قبض برق آخر ماه هستند، کولر گازی گری 12000 بهتره یا ال‌جی 9000؟",
        "comparison_type": "general",
        "product_name_1": "کولر گازی گری 12000",
        "product_random_key_1": None,
        "product_name_2": "کولر گازی ال‌جی 9000",
        "product_random_key_2": None
    },
    {
        "input": "ین ماشین لباسشویی اسنوا 7 کیلویی و پاکشوما 8 کیلویی کدومش در طولانی‌مدت بیشتر رضایت می‌ده؟",
        "comparison_type": "general",
        "product_name_1": "ماشین لباسشویی اسنوا 7 کیلویی",
        "product_random_key_1": None,
        "product_name_2": "پاکشوما 8 کیلویی",
        "product_random_key_2": None
    },
    {
        "input": "برای خانواده‌ای که حوصله شست‌وشوی زیاد نداره، ماشین ظرفشویی بوش سری 6 بهتره یا سامسونگ 14 نفره؟",
        "comparison_type": "general",
        "product_name_1": "ماشین ظرفشویی بوش سری 6",
        "product_random_key_1": None,
        "product_name_2": "ماشین ظرفشویی سامسونگ 14 نفره",
        "product_random_key_2": None
    },
    {
        "input" : "گوشی شیائومی Redmi Note 11 یا سامسونگ A32 بیشتر به درد کسی می‌خوره که مدام توی اینستاگرام می‌چرخه؟",
        "comparison_type": "general",
        "product_name_1": "گوشی شیائومی Redmi Note 11",
        "product_random_key_1": None,
        "product_name_2": "گوشی سامسونگ A32",
        "product_random_key_2": None
    },
    {
        "input": "بین لپ‌تاپ ایسوس VivoBook و لنوو IdeaPad کدومش برای دانشجوها بهتره؟",
        "comparison_type": "general",
        "product_name_1": "لپ‌تاپ ایسوس VivoBook",
        "product_random_key_1": None,
        "product_name_2": "لپ‌تاپ لنوو IdeaPad",
        "product_random_key_2": None
    }
]

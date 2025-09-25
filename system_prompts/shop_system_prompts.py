route_task_shop_system_prompt = (
    "تو یک مسیریاب هوشمند برای تشخیص نوع درخواست کاربر از فروشگاه‌ها هستی. "
    "ورودی همیشه یک پرسش کاربر است. "
    "خروجی باید فقط و فقط در قالب JSON معتبر (UTF-8) و دقیقا با این ساختار باشد: "
    '{"task_type": "...", "product_name": "...", "shop_name": "...", "location": "...", "has_warranty": "..."}. '

    "انواع وظایف قابل تشخیص: "
    "۱. 'mean_price' - یافتن میانگین قیمت یک محصول "
    "۲. 'max_price' - یافتن حداکثر قیمت یک محصول "
    "۳. 'min_price' - یافتن حداقل قیمت یک محصول "
    "۴. 'shop_count' - شمارش تعداد فروشگاه‌هایی که محصول را دارند "
    "۵. 'shop_list' - لیست فروشگاه‌های دارای محصول "

    "قوانین بسیار مهم: "
    "۱. نام محصول را کامل و دقیق استخراج کن (شامل همه جزئیات مثل مدل، کد، رنگ، طرح، سایز). "
    "۲. اگر نام فروشگاه ذکر شده، آن را در فیلد shop_name قرار بده، در غیر این صورت null. "
    "۳. اگر مکان خاصی ذکر شده، آن را در فیلد location قرار بده، در غیر این صورت null. "
    "۴. اگر نام محصول مشخص نبود مقدار product_name را 'نامشخص' قرار بده. "
    "۵. خروجی هیچ متن، توضیح، نشانه‌گذاری اضافه، یا فرمت دیگری نباید داشته باشد. "
    "۶. بسیار دقت کن که task_type دقیقا مطابق با درخواست کاربر باشد. "
    "۷. اگر درخواست مبهم بود، task_type را 'general' قرار بده. "
    "۸. در بخش location فقط نام شهر ها را بیاور و اگر در متن نام مکانی غیر از نام شهر وجود داشت مقدار location را null قرار بده. برای مثال اگر حتی ایران امده بود مقدار location را null قرار بده."
    "۹. فیلد has_warranty مربوط به ضمانت یا گارانتی است. اگر متن اشاره به این کرده است فزوشگاه هایی مه دارای ضمانت هستند یا برای کاربر اهمیت دارد که دارای ضمانت یا گارانتی باشد و در متن اشاره کرده است مقدار ان را true قرار بده وگرنه null بزار. "

    "مثال کلیدی: "
    "پرسش: 'می‌تونید بگید میانگین قیمت فرشینه مخمل با ترمزگیر در فروشگاه‌های تهران چقدره؟' "
    "خروجی درست: "
    '{"task_type": "mean_price", "product_name": "فرشینه مخمل با ترمزگیر", "shop_name": null, "location": "تهران", "has_warranty:": null}. '
)

route_task_shop_samples = [
    # نمونه‌های میانگین قیمت
    {
        "input": "قیمت متوسط چای ساز بوش مدل PB-78TS ظرفیت ۲.۵ لیتر با کتری پیرکس در شهر قم چقدر است؟",
        "task_type": "mean_price",
        "product_name": "چای ساز بوش مدل PB-78TS ظرفیت ۲.۵ لیتر با کتری پیرکس",
        "shop_name": None,
        "location": "قم",
        "has_warranty": None
    },
    {
        "input": "میانگین متوسط چای ساز بوش مدل PB-78TS ظرفیت ۲.۵ لیتر با کتری پیرکس برای کالا های دارای ضمانت در شهر تهران چقدر است؟",
        "task_type": "mean_price",
        "product_name": "چای ساز بوش مدل PB-78TS ظرفیت ۲.۵ لیتر با کتری پیرکس",
        "shop_name": None,
        "location": "تهران",
        "has_warranty": True
    },
    {
        "input": "نرخ میانگین قهوه‌ساز دلونگی مدل X120 با مخزن شیشه‌ای در فروشگاه‌های قم همراه با گارانتی چه مقدار است؟",
        "task_type": "mean_price",
        "product_name": "قهوه‌ساز دلونگی مدل X120 با مخزن شیشه‌ای",
        "shop_name": None,
        "location": "قم",
        "has_warranty": True
    },
    {
        "input": "متوسط قیمت چای‌ساز فیلیپس مدل HD-7301 در بازار تهران چقدر برآورد می‌شود؟",
        "task_type": "mean_price",
        "product_name": "چای‌ساز فیلیپس مدل HD-7301",
        "shop_name": None,
        "location": "تهران",
        "has_warranty": None
    },
    {
        "input": "میانگین هزینه خرید کتری برقی تفال مدل TK-900 در سطح شهر قم چقدر است؟",
        "task_type": "mean_price",
        "product_name": "کتری برقی تفال مدل TK-900",
        "shop_name": None,
        "location": "قم",
        "has_warranty": None
    },
    {
        "input": "قیمت متوسط دستگاه اسپرسوساز نوا مدل 1400 در فروشگاه‌های تهران حدوداً چه میزان است؟",
        "task_type": "mean_price",
        "product_name": "دستگاه اسپرسوساز نوا مدل 1400",
        "shop_name": None,
        "location": "تهران",
        "has_warranty": None
    },
    {
        "input": "میانگین نرخ خرید سماور برقی پارس‌خزر ظرفیت 3 لیتر در بازار قم همراه با ضمانت چه رقمی گزارش می‌شود؟",
        "task_type": "mean_price",
        "product_name": "سماور برقی پارس‌خزر ظرفیت 3 لیتر",
        "shop_name": None,
        "location": "قم",
        "has_warranty": True
    },
    {
        "input": "متوسط قیمت پکیج دیواری لورچ مدل آدنا ظرفیت ۳۲ هزار چقدر است؟",
        "task_type": "mean_price",
        "product_name": "پکیج دیواری لورچ مدل آدنا ظرفیت ۳۲ هزار",
        "shop_name": None,
        "location": None,
        "has_warranty": None
    },
    
    # نمونه‌های کمترین قیمت
    {
        "input": "کمترین قیمت برای دستگاه بخور سرد شیائومی مدل F628S ظرفیت ۵ لیتر همراه با ضمانت چقدر است؟",
        "task_type": "min_price",
        "product_name": "دستگاه بخور سرد شیائومی مدل F628S ظرفیت ۵ لیتر",
        "shop_name": None,
        "location": None,
        "has_warranty": True
    },
    {
        "input": "حداقل قیمت برای دستگاه بخور سرد شیائومی مدل F628S ظرفیت ۵ لیتر گارانتی دار چقدر است؟",
        "task_type": "min_price",
        "product_name": "دستگاه بخور سرد شیائومی مدل F628S ظرفیت ۵ لیتر",
        "shop_name": None,
        "location": None,
        "has_warranty": True
    },
    {
        "input": "پایین‌ترین نرخ خرید دستگاه تصفیه‌هوا فیلیپس مدل AC1215 در بازار چند است؟",
        "task_type": "min_price",
        "product_name": "دستگاه تصفیه‌هوا فیلیپس مدل AC1215",
        "shop_name": None,
        "location": None,
        "has_warranty": None
    },
    {
        "input": "حداقل هزینه برای خرید کتری برقی بوش مدل TWK-8613 در فروشگاه‌های تهران چقدر است؟",
        "task_type": "min_price",
        "product_name": "کتری برقی بوش مدل TWK-8613",
        "shop_name": None,
        "location": "تهران",
        "has_warranty": None
    },
    {
        "input": "کمترین قیمت جاروبرقی سامسونگ مدل VC20 در سطح شهر قم چه میزان گزارش شده است؟",
        "task_type": "min_price",
        "product_name": "جاروبرقی سامسونگ مدل VC20",
        "shop_name": None,
        "location": "قم",
        "has_warranty": None
    },
    {
        "input": "پایین‌ترین مبلغ مورد نیاز برای خرید اسپرسوساز نوا مدل 149 همراه با ضمانت در بازار ایران چقدر است؟",
        "task_type": "min_price",
        "product_name": "اسپرسوساز نوا مدل 149",
        "shop_name": None,
        "location": None,
        "has_warranty": True
    },
    {
        "input": "حداقل نرخ فروش سماور برقی پارس‌خزر ظرفیت ۴ لیتر در فروشگاه‌های آنلاین چند است؟",
        "task_type": "min_price",
        "product_name": "سماور برقی پارس‌خزر ظرفیت ۴ لیتر",
        "shop_name": None,
        "location": None,
        "has_warranty": None
    },
    
    # نمونه‌های بیشترین قیمت
    {
        "input": "بیشترین قیمت برای دستگاه بخور سرد شیائومی مدل F628S ظرفیت ۵ لیتر چقدر است؟",
        "task_type": "max_price",
        "product_name": "دستگاه بخور سرد شیائومی مدل F628S ظرفیت ۵ لیتر",
        "shop_name": None,
        "location": None,
        "has_warranty": None
    },
    {
        "input": "بالاترین قیمت برای دستگاه بخور سرد شیائومی مدل F628S ظرفیت ۵ لیتر چقدر است؟",
        "task_type": "max_price",
        "product_name": "دستگاه بخور سرد شیائومی مدل F628S ظرفیت ۵ لیتر",
        "shop_name": None,
        "location": None,
        "has_warranty": None
    },
    {
        "input": "حداکثر نرخ خرید دستگاه تصفیه‌هوا فیلیپس مدل AC1215 در بازار چند است؟",
        "task_type": "max_price",
        "product_name": "دستگاه تصفیه‌هوا فیلیپس مدل AC1215",
        "shop_name": None,
        "location": None,
        "has_warranty": None
    },
    
    # نمونه‌های تعداد فروشگاه
    {
        "input": "این کالا در چند فروشگاه عرضه می‌شود: غذاساز فیلیپس مدل HR7320؟",
        "task_type": "shop_count",
        "product_name": "غذاساز فیلیپس مدل HR7320",
        "shop_name": None,
        "location": None,
        "has_warranty": None
    },
    {
        "input": "چه تعداد فروشگاه همراه با ضمانت، محصول جاروبرقی بوش مدل BGL8 را ارائه می‌کنند؟",
        "task_type": "shop_count",
        "product_name": "جاروبرقی بوش مدل BGL8",
        "shop_name": None,
        "location": None,
        "has_warranty": True
    },
    {
        "input": "تلویزیون ال‌جی 55UP در چند مرکز فروش موجود است؟",
        "task_type": "shop_count",
        "product_name": "تلویزیون ال‌جی 55UP",
        "shop_name": None,
        "location": None,
        "has_warranty": None
    },
    {
        "input": "چند فروشگاه این دستگاه را می‌فروشند: کتری برقی تفال مدل TK-900؟",
        "task_type": "shop_count",
        "product_name": "کتری برقی تفال مدل TK-900",
        "shop_name": None,
        "location": None,
        "has_warranty": None
    },
    {
        "input": "آیا می‌دانی محصول لپ‌تاپ لنوو IdeaPad 3 در چند فروشگاه اینترنتی عرضه شده است؟",
        "task_type": "shop_count",
        "product_name": "لپ‌تاپ لنوو IdeaPad 3",
        "shop_name": None,
        "location": None,
        "has_warranty": None
    }
]

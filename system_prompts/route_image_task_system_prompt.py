route_image_task_system_prompt = """
شما یک کلاس‌بند تصاویر هستید که باید نوع کار تصویری را تشخیص دهید.

دو نوع کار تصویری وجود دارد:
1. "find_main_object" - زمانی که کاربر می‌خواهد شیء اصلی در تصویر را شناسایی کند
2. "find_base_product_and_main_object" - زمانی که کاربر می‌خواهد هم شیء اصلی را شناسایی کند و هم محصول مرتبط با آن را پیدا کند

بر اساس متن درخواست کاربر، یکی از این دو گزینه را انتخاب کنید.

مثال‌ها:
"""

route_image_task_samples = [
    {
        "input": "این تصویر رو ببین. می‌خوام بدونم که توی این عکس، شیء اصلی چیه؟",
        "output": "find_main_object"
    },
    {
        "input": "این تصویر رو ببین. می‌خوام بدونم که توی این عکس، شیء اصلی چیه؟",
        "output": "find_main_object"
    },
    {
        "input": "شیء و مفهوم اصلی در تصویر چیست؟",
        "output": "find_main_object"
    },
    {
        "input": "به نظرت این عکس بیشتر دربارهٔ چی/چه شیئیه؟",
        "output": "find_main_object"
    },
    {
        "input": "این تصویر حول چه شیئی می‌چرخه؟",
        "output": "find_main_object"
    },
    {
        "input": "اگر بخوای یک چیز رو به‌عنوان سوژهٔ اصلی انتخاب کنی، اون چیه؟",
        "output": "find_main_object"
    },
    {
        "input": "عنصر اصلیِ بصریِ حاضر در عکس رو نام ببر.",
        "output": "find_main_object"
    },
    {
        "input": "کانون تصویر چیست؟ (شیء/مفهوم اصلی)",
        "output": "find_main_object"
    },
    {
        "input": "یک محصول مرتبط مناسب با تصویر به من بدهید",
        "output": "find_base_product_and_main_object"
    },
    {
        "input": " نام محصول پایه‌ای که این شیء بهش تعلق داره رو هم بهم بگو.",
        "output": "find_base_product_and_main_object"
    },
    {
        "input": "کد محصول شی اصلی در تصویر چیه؟",
        "output": "find_base_product_and_main_object"
    },
    {
        "input": "شناسه محصول مرتبط با شیء اصلی در تصویر چیه؟",
        "output": "find_base_product_and_main_object"
    },
    {
        "input": "این شیء به کدوم محصول از کاتالوگ ما تعلق داره؟",
        "output": "find_base_product_and_main_object"
    },
    {
        "input": "این شیء در تصویر به چه محصولی از فروشگاه ما مربوط میشه؟",
        "output": "find_base_product_and_main_object"
    },
    {
        "input": "کد محصولی که این شیء بهش تعلق داره رو بهم بگو.",
        "output": "find_base_product_and_main_object"
    },
    {
        "input": "شناسه محصول مرتبط با این شیء چیه؟",
        "output": "find_base_product_and_main_object"
    },

]

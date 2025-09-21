"""
Agent exemplars for semantic routing
Contains typical queries for each agent type
"""

from typing import Dict, List
from dataclasses import dataclass
from .base import AgentType


@dataclass
class Exemplar:
    """Single exemplar for an agent"""
    query: str
    description: str
    keywords: List[str]


class AgentExemplars:
    """Manages exemplar queries for each agent type"""
    
    def __init__(self):
        self._exemplars = self._initialize_exemplars()
    
    def _initialize_exemplars(self) -> Dict[AgentType, List[Exemplar]]:
        """Initialize exemplar queries for each agent in Persian"""
        return {
            AgentType.GENERAL: [
                # Policy and procedure questions
                Exemplar(
                    "سلام، چطور می‌تونم از سایت خرید کنم؟",
                    "سوال عمومی درباره نحوه خرید",
                    ["سلام", "خرید", "چطور", "راهنما"]
                ),
                Exemplar(
                    "ساعت کاری پشتیبانی چه زمانی است؟",
                    "سوال درباره ساعت کاری",
                    ["ساعت", "پشتیبانی", "زمان", "کاری"]
                ),
                Exemplar(
                    "آیا امکان مرجوع کردن کالا وجود دارد؟",
                    "سوال درباره قوانین مرجوعی",
                    ["مرجوع", "برگشت", "کالا", "قوانین"]
                ),
                Exemplar(
                    "نحوه پرداخت چگونه است؟",
                    "سوال درباره روش‌های پرداخت",
                    ["پرداخت", "نحوه", "روش", "قسطی"]
                ),
                Exemplar(
                    "آیا ضمانت اصالت کالا دارید؟",
                    "سوال درباره ضمانت و اصالت",
                    ["ضمانت", "اصالت", "کالا", "تضمین"]
                ),
                # General/unclear questions that should default here
                Exemplar(
                    "سلام خوبی؟",
                    "سلام و احوال‌پرسی کلی",
                    ["سلام", "خوبی", "احوال", "چطور"]
                ),
                Exemplar(
                    "کمک میخوام",
                    "درخواست کمک عمومی",
                    ["کمک", "نیاز", "راهنمایی"]
                ),
                Exemplar(
                    "نمیدونم چی بخرم",
                    "سردرگمی در انتخاب",
                    ["نمیدونم", "انتخاب", "سردرگم"]
                ),
                Exemplar(
                    "این سایت چیکار میکنه؟",
                    "سوال کلی درباره سرویس",
                    ["سایت", "چیکار", "خدمات", "توضیح"]
                ),
                Exemplar(
                    "یه چیزی میخوام",
                    "درخواست نامشخص",
                    ["چیزی", "میخوام", "نامشخص"]
                )
            ],
            
            AgentType.SPECIFIC_PRODUCT: [
                Exemplar(
                    "لطفا کابینت چهار کشو کد D14 رو برام پیدا کن",
                    "درخواست محصول با کد مشخص",
                    ["کابینت", "کد", "D14", "پیدا", "محصول"]
                ),
                Exemplar(
                    "محصول با شناسه SKU-12345 را نشان بده",
                    "درخواست محصول با SKU",
                    ["SKU", "شناسه", "محصول", "نشان"]
                ),
                Exemplar(
                    "دنبال لپ تاپ ASUS مدل X515EA هستم",
                    "درخواست محصول با مدل دقیق",
                    ["لپ تاپ", "ASUS", "مدل", "X515EA"]
                ),
                Exemplar(
                    "گوشی آیفون 15 پرو مکس 256 گیگ رو میخوام",
                    "درخواست محصول خاص با مشخصات",
                    ["گوشی", "آیفون", "15", "پرو مکس", "256"]
                ),
                Exemplar(
                    "یخچال ساید بای ساید سامسونگ مدل RS66 رو برام پیدا کن",
                    "درخواست لوازم خانگی با مدل",
                    ["یخچال", "سامسونگ", "RS66", "مدل"]
                )
            ],
            
            AgentType.PRODUCT_FEATURE: [
                Exemplar(
                    "قیمت پارچه لیکرا حلقوی نوریس 1/30 طلایی چقدره؟",
                    "سوال درباره قیمت محصول خاص",
                    ["قیمت", "پارچه", "لیکرا", "نوریس", "طلایی"]
                ),
                Exemplar(
                    "مشخصات فنی تلویزیون سونی X90J رو میخوام",
                    "درخواست مشخصات فنی",
                    ["مشخصات", "فنی", "تلویزیون", "سونی"]
                ),
                Exemplar(
                    "ابعاد و وزن ماشین لباسشویی بوش 8 کیلو چقدره؟",
                    "سوال درباره ابعاد و وزن",
                    ["ابعاد", "وزن", "ماشین لباسشویی", "بوش"]
                ),
                Exemplar(
                    "رنگ‌های موجود کفش نایک ایرمکس چیه؟",
                    "سوال درباره رنگ‌های موجود",
                    ["رنگ", "موجود", "کفش", "نایک"]
                ),
                Exemplar(
                    "گارانتی لپ تاپ دل اینسپایرون چند ساله؟",
                    "سوال درباره گارانتی",
                    ["گارانتی", "لپ تاپ", "دل", "چند"]
                )
            ],
            
            AgentType.SELLER_INFO: [
                Exemplar(
                    "فروشندگان گوشی سامسونگ A54 در ترب کدومن؟",
                    "لیست فروشندگان محصول خاص",
                    ["فروشندگان", "گوشی", "سامسونگ", "ترب"]
                ),
                Exemplar(
                    "کدوم فروشگاه‌ها تبلت آیپد دارن؟",
                    "فروشگاه‌های دارای محصول",
                    ["فروشگاه", "تبلت", "آیپد", "دارن"]
                ),
                Exemplar(
                    "بهترین فروشنده لوازم آشپزخانه کیه؟",
                    "بهترین فروشنده در دسته",
                    ["بهترین", "فروشنده", "لوازم", "آشپزخانه"]
                ),
                Exemplar(
                    "فروشگاه‌های معتبر برای خرید موبایل؟",
                    "فروشگاه‌های معتبر",
                    ["فروشگاه", "معتبر", "خرید", "موبایل"]
                ),
                Exemplar(
                    "آیا فروشنده دیجی‌کالا محصول X را دارد؟",
                    "محصول در فروشنده خاص",
                    ["فروشنده", "دیجی‌کالا", "محصول", "دارد"]
                )
            ],
            
            AgentType.EXPLORATION: [
                Exemplar(
                    "یه لپ تاپ خوب برای برنامه نویسی میخوام",
                    "درخواست کلی برای یافتن محصول",
                    ["لپ تاپ", "خوب", "برنامه نویسی"]
                ),
                Exemplar(
                    "دنبال یخچال مناسب برای خونه کوچیک هستم",
                    "جستجوی محصول با معیار کلی",
                    ["یخچال", "مناسب", "خونه", "کوچیک"]
                ),
                Exemplar(
                    "بهترین گوشی تا 10 میلیون تومان؟",
                    "جستجو با محدودیت قیمت",
                    ["بهترین", "گوشی", "میلیون", "تومان"]
                ),
                Exemplar(
                    "کفش ورزشی راحت برای دویدن میخوام",
                    "جستجوی محصول برای کاربرد خاص",
                    ["کفش", "ورزشی", "راحت", "دویدن"]
                ),
                Exemplar(
                    "هدفون بی‌سیم با کیفیت صدای عالی",
                    "جستجو با ویژگی کلی",
                    ["هدفون", "بی‌سیم", "کیفیت", "صدا"]
                )
            ],
            
            AgentType.COMPARISON: [
                Exemplar(
                    "مقایسه آیفون 15 با سامسونگ S24 اولترا",
                    "مقایسه دو محصول مشخص",
                    ["مقایسه", "آیفون", "سامسونگ", "با"]
                ),
                Exemplar(
                    "تفاوت بین ماشین لباسشویی ال جی و سامسونگ 8 کیلو",
                    "مقایسه محصولات مشابه",
                    ["تفاوت", "بین", "ماشین لباسشویی", "ال جی", "سامسونگ"]
                ),
                Exemplar(
                    "کدوم بهتره؟ لپ تاپ ایسوس ROG یا MSI Gaming",
                    "انتخاب بین دو گزینه",
                    ["کدوم", "بهتره", "لپ تاپ", "ایسوس", "MSI"]
                ),
                Exemplar(
                    "مقایسه قیمت و کیفیت تلویزیون سونی و ال جی 55 اینچ",
                    "مقایسه قیمت و کیفیت",
                    ["مقایسه", "قیمت", "کیفیت", "تلویزیون", "سونی", "ال جی"]
                ),
                Exemplar(
                    "بین این سه مدل یخچال کدوم رو پیشنهاد میدی؟",
                    "انتخاب از چند گزینه",
                    ["بین", "سه", "مدل", "یخچال", "پیشنهاد"]
                )
            ]
        }
    
    def get_exemplars(self, agent_type: AgentType) -> List[Exemplar]:
        """Get exemplars for a specific agent type"""
        return self._exemplars.get(agent_type, [])
    
    def get_all_exemplars(self) -> Dict[AgentType, List[Exemplar]]:
        """Get all exemplars"""
        return self._exemplars
    
    def get_exemplar_texts(self, agent_type: AgentType) -> List[str]:
        """Get only the query texts for an agent type"""
        return [ex.query for ex in self.get_exemplars(agent_type)]
    
    def get_exemplar_keywords(self, agent_type: AgentType) -> List[str]:
        """Get all keywords for an agent type"""
        keywords = []
        for ex in self.get_exemplars(agent_type):
            keywords.extend(ex.keywords)
        return list(set(keywords))  # Remove duplicates

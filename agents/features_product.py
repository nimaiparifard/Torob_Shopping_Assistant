"""
Agent 2: Product Features Agent - Torob AI Assistant

This agent extracts product features and specifications from the database.
It first finds the product by name, then retrieves and formats its features.

Usage:
    agent = FeaturesProductAgent(config)
    result = await agent.process_query("ویژگی‌های کمد چهار کشو را بگو")

Author: Torob AI Team
"""

import asyncio
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate

from db.base import DatabaseBaseLoader
from router.base import RouterConfig


@dataclass
class ProductFeaturesResult:
    """Result of product features extraction"""
    found: bool
    product_name: Optional[str] = None
    random_key: Optional[str] = None
    features: Optional[Dict[str, Any]] = None
    formatted_features: Optional[str] = None
    error: Optional[str] = None


class FeaturesProductAgent:
    """
    Agent 2: Extracts and formats product features from database
    """
    
    def __init__(self, config: RouterConfig):
        self.config = config
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.1,
            api_key=config.openai_api_key
        )
        self.db = None
        self._tools_created = False
        self.debug = True  # Enable debug logging
        
    def _ensure_db_connection(self):
        """Ensure database connection is available"""
        if not self.db:
            self.db = DatabaseBaseLoader()
    
    def _create_tools(self):
        """Create LangChain tools for this agent"""
        if self._tools_created:
            return
            
        @tool
        def extract_product_name(query: str) -> str:
            """
            Extract the main product name from user query in Persian.
            
            Args:
                query: User query in Persian asking about product features
                
            Returns:
                str: Extracted product name in Persian
            """
            # Use LLM to extract product name
            extraction_prompt = ChatPromptTemplate.from_messages([
                ("system", """تو یک استخراج‌کننده نام محصول هستی. وظیفه‌ات این است که از متن کاربر، نام کامل محصول را استخراج کنی.

قوانین مهم:
1. نام کامل محصول را با تمام جزئیات استخراج کن (شامل مدل، ویژگی‌ها، و مشخصات)
2. اگر کد محصول در پرانتز آمده (مثل کد D14)، آن را حذف کن
3. اگر عباراتی مثل "ویژگی‌های"، "مشخصات"، "بگو"، "را بگو" وجود دارد، آنها را حذف کن
4. تمام ویژگی‌های محصول مثل مدل، رنگ، سایز را حفظ کن
5. اگر نام محصول مشخص نیست، "نامشخص" برگردان

مثال‌ها:
- "ویژگی‌های کمد چهار کشو (کد D14) را بگو" → "کمد چهار کشو"
- "مشخصات گوشی سامسونگ گلکسی S24" → "گوشی سامسونگ گلکسی S24"
- "فرش 700شانه اُپال فیروزه ای چه ویژگی‌هایی دارد؟" → "فرش 700شانه اُپال فیروزه ای"
- "بگو کمد چهار درب ونوس طوسی چه مشخصاتی داره" → "کمد چهار درب ونوس طوسی"
"""),
                ("human", "{query}")
            ])
            
            try:
                response = self.llm.invoke(extraction_prompt.format_messages(query=query))
                extracted_name = response.content.strip()
                
                # Remove common prefixes/suffixes
                clean_phrases = [
                    "ویژگی‌های", "مشخصات", "بگو", "را بگو", "چه ویژگی‌هایی", "چه مشخصاتی",
                    "لطفا", "لطفاً", "برای من", "را پیدا کن", "پیدا کن", "پیدا کنید",
                    "را برای من", "این محصول را پیدا", "محصول", "برگردون", "کد",
                    "را برای من پیدا کنید", "می‌خواهم", "میخواهم", "داره", "دارد"
                ]
                
                cleaned_name = extracted_name
                for phrase in clean_phrases:
                    cleaned_name = cleaned_name.replace(phrase, "").strip()
                
                # Also try to extract everything between patterns
                import re
                patterns = [
                    r'ویژگی‌های\s+(.+?)\s+(?:را\s+)?بگو',
                    r'مشخصات\s+(.+?)(?:\s+را\s+بگو)?',
                    r'(.+?)\s+چه\s+ویژگی‌هایی',
                    r'(.+?)\s+چه\s+مشخصاتی',
                    r'بگو\s+(.+?)\s+چه\s+مشخصاتی',
                    r'(.+?)\s+ویژگی‌هایش',
                    r'(.+?)\s+مشخصاتش',
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, query)
                    if match:
                        potential_name = match.group(1).strip()
                        if self.debug:
                            print(f"📝 الگوی یافت شده: '{potential_name}'")
                        # Use the pattern match if it's longer/more complete
                        if len(potential_name) > len(cleaned_name):
                            cleaned_name = potential_name
                
                return cleaned_name if cleaned_name and cleaned_name != "نامشخص" else extracted_name
            except Exception as e:
                print(f"خطا در استخراج نام محصول: {e}")
                return ""
        
        @tool 
        def find_product_by_name(product_name: str) -> Dict[str, Any]:
            """
            Find product in database by Persian name and return basic info.
            
            Args:
                product_name: Persian name of the product
                
            Returns:
                dict: Product info with random_key if found
            """
            try:
                if not product_name:
                    return {"found": False, "error": "نام محصول خالی است"}
                
                self._ensure_db_connection()
                
                if not self.db:
                    return {"found": False, "error": "اتصال به پایگاه داده برقرار نیست"}
                
                # First try exact match
                if self.debug:
                    print(f"🔍 جستجوی دقیق برای: '{product_name}'")
                
                results = self.db.query(
                    "SELECT random_key, persian_name FROM base_products WHERE persian_name = ?", 
                    (product_name,)
                )
                
                if results:
                    if self.debug:
                        print(f"✅ تطابق دقیق یافت شد: {results[0]['persian_name']}")
                    return {
                        "found": True,
                        "random_key": results[0]['random_key'],
                        "product_name": results[0]['persian_name']
                    }
                
                # Try case-insensitive exact match
                results = self.db.query(
                    "SELECT random_key, persian_name FROM base_products WHERE LOWER(persian_name) = LOWER(?)", 
                    (product_name,)
                )
                
                if results:
                    return {
                        "found": True,
                        "random_key": results[0]['random_key'],
                        "product_name": results[0]['persian_name']
                    }
                
                # If no exact match, try partial match
                results = self.db.query(
                    "SELECT random_key, persian_name FROM base_products WHERE persian_name LIKE ?", 
                    (f'%{product_name}%',)
                )
                
                if results:
                    # Check if any result is actually an exact match
                    for result in results:
                        if result['persian_name'] == product_name:
                            return {
                                "found": True,
                                "random_key": result['random_key'],
                                "product_name": result['persian_name']
                            }
                    
                    # Return first result if no exact match found
                    return {
                        "found": True,
                        "random_key": results[0]['random_key'],
                        "product_name": results[0]['persian_name']
                    }
                
                return {"found": False, "error": "محصول یافت نشد"}
                
            except Exception as e:
                print(f"❌ خطا در جستجوی محصول: {e}")
                return {"found": False, "error": f"خطا در جستجو: {str(e)}"}
        
        @tool
        def get_product_features(random_key: str) -> Dict[str, Any]:
            """
            Get product features from database by random_key.
            
            Args:
                random_key: Product random key
                
            Returns:
                dict: Product features and additional info
            """
            try:
                if not random_key:
                    return {"found": False, "error": "کلید محصول خالی است"}
                
                self._ensure_db_connection()
                
                if not self.db:
                    return {"found": False, "error": "اتصال به پایگاه داده برقرار نیست"}
                
                # Get product details including features
                results = self.db.query(
                    """SELECT random_key, persian_name, english_name, extra_features, 
                              image_url, category_id, brand_id 
                       FROM base_products WHERE random_key = ?""", 
                    (random_key,)
                )
                
                if not results:
                    return {"found": False, "error": "محصول یافت نشد"}
                
                product = results[0]
                
                # Parse extra_features JSON
                features = {}
                if product['extra_features']:
                    try:
                        features = json.loads(product['extra_features'])
                    except json.JSONDecodeError as e:
                        print(f"خطا در تجزیه JSON ویژگی‌ها: {e}")
                        features = {}
                
                # Get category and brand names
                category_name = None
                brand_name = None
                
                if product['category_id']:
                    cat_results = self.db.query(
                        "SELECT title FROM categories WHERE id = ?", 
                        (product['category_id'],)
                    )
                    if cat_results:
                        category_name = cat_results[0]['title']
                
                if product['brand_id']:
                    brand_results = self.db.query(
                        "SELECT title FROM brands WHERE id = ?", 
                        (product['brand_id'],)
                    )
                    if brand_results:
                        brand_name = brand_results[0]['title']
                
                return {
                    "found": True,
                    "random_key": product['random_key'],
                    "persian_name": product['persian_name'],
                    "english_name": product['english_name'],
                    "features": features,
                    "category_name": category_name,
                    "brand_name": brand_name,
                    "image_url": product['image_url']
                }
                
            except Exception as e:
                print(f"❌ خطا در دریافت ویژگی‌های محصول: {e}")
                return {"found": False, "error": f"خطا در دریافت ویژگی‌ها: {str(e)}"}
        
        @tool
        def format_features_for_user(features_data: str) -> str:
            """
            Format product features in a user-friendly Persian format.
            
            Args:
                features_data: JSON string containing product features and info
                
            Returns:
                str: Formatted features in Persian
            """
            try:
                data = json.loads(features_data)
                
                if not data.get("found", False):
                    return f"❌ خطا: {data.get('error', 'اطلاعات محصول یافت نشد')}"
                
                product_name = data.get("persian_name", "نامشخص")
                features = data.get("features", {})
                category_name = data.get("category_name")
                brand_name = data.get("brand_name")
                english_name = data.get("english_name")
                
                # Start building the formatted response
                response_parts = [f"📋 ویژگی‌های محصول: {product_name}"]
                
                if english_name:
                    response_parts.append(f"🔤 نام انگلیسی: {english_name}")
                
                if brand_name:
                    response_parts.append(f"🏷️ برند: {brand_name}")
                
                if category_name:
                    response_parts.append(f"📂 دسته‌بندی: {category_name}")
                
                if features:
                    response_parts.append("\n🔧 مشخصات فنی:")
                    
                    # Feature mapping for better display
                    feature_mapping = {
                        "material": "جنس",
                        "originality": "اصالت",
                        "stock_status": "وضعیت موجودی",
                        "meterage": "متراژ",
                        "number_combs": "تعداد شانه",
                        "carpet_density": "تراکم فرش",
                        "background_color": "رنگ زمینه",
                        "size2": "سایز",
                        "piece_count": "تعداد قطعه",
                        "color": "رنگ",
                        "storage": "حافظه",
                        "screen_size": "اندازه صفحه",
                        "battery": "باتری",
                        "camera": "دوربین",
                        "ram": "رم",
                        "processor": "پردازنده",
                        "weight": "وزن",
                        "dimensions": "ابعاد",
                        "warranty": "گارانتی"
                    }
                    
                    for key, value in features.items():
                        if value and value != "" and value != "null":
                            persian_key = feature_mapping.get(key, key)
                            
                            # Handle different value types
                            if isinstance(value, list):
                                if value:  # Only show non-empty lists
                                    formatted_value = "، ".join(str(v) for v in value if v)
                                    response_parts.append(f"  • {persian_key}: {formatted_value}")
                            elif isinstance(value, str) and value.strip():
                                response_parts.append(f"  • {persian_key}: {value}")
                            elif isinstance(value, (int, float)):
                                response_parts.append(f"  • {persian_key}: {value}")
                else:
                    response_parts.append("\n⚠️ هیچ ویژگی خاصی برای این محصول ثبت نشده است.")
                
                return "\n".join(response_parts)
                
            except Exception as e:
                print(f"❌ خطا در فرمت‌بندی ویژگی‌ها: {e}")
                return f"❌ خطا در فرمت‌بندی ویژگی‌ها: {str(e)}"
        
        # Store tools as instance attributes
        self.extract_product_name_tool = extract_product_name
        self.find_product_tool = find_product_by_name
        self.get_features_tool = get_product_features
        self.format_features_tool = format_features_for_user
        self._tools_created = True
    
    async def process_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> ProductFeaturesResult:
        """
        Process user query to extract product features
        
        Args:
            query: User query in Persian asking about product features
            context: Optional context information
            
        Returns:
            ProductFeaturesResult: Result of product features extraction
        """
        try:
            # Ensure tools are created
            self._create_tools()
            
            # Step 1: Extract product name from query
            print(f"🔍 استخراج نام محصول از: {query}")
            extracted_name = self.extract_product_name_tool.invoke(query)
            
            if not extracted_name:
                return ProductFeaturesResult(
                    found=False,
                    error="نتوانستم نام محصول را از درخواست شما استخراج کنم"
                )
            
            print(f"📝 نام استخراج شده: {extracted_name}")
            
            # Step 2: Find product in database
            print(f"🔎 جستجو در پایگاه داده...")
            product_result = self.find_product_tool.invoke(extracted_name)
            
            if not product_result.get("found", False):
                return ProductFeaturesResult(
                    found=False,
                    error=product_result.get("error", "محصول یافت نشد")
                )
            
            random_key = product_result.get("random_key")
            product_name = product_result.get("product_name")
            
            print(f"✅ محصول یافت شد: {product_name} ({random_key})")
            
            # Step 3: Get product features
            print(f"🔧 دریافت ویژگی‌های محصول...")
            features_result = self.get_features_tool.invoke(random_key)
            
            if not features_result.get("found", False):
                return ProductFeaturesResult(
                    found=False,
                    error=features_result.get("error", "خطا در دریافت ویژگی‌ها")
                )
            
            # Step 4: Format features for user
            print(f"📝 فرمت‌بندی ویژگی‌ها...")
            formatted_features = self.format_features_tool.invoke(json.dumps(features_result))
            
            return ProductFeaturesResult(
                found=True,
                product_name=product_name,
                random_key=random_key,
                features=features_result.get("features", {}),
                formatted_features=formatted_features
            )
                
        except Exception as e:
            print(f"❌ خطا در پردازش درخواست: {e}")
            return ProductFeaturesResult(
                found=False,
                error=f"خطا در پردازش: {str(e)}"
            )
    
    def close(self):
        """Close database connection"""
        if self.db:
            self.db.close()
            self.db = None


# Example usage and testing
if __name__ == "__main__":
    async def test_agent():
        """Test the Features Product Agent"""
        from router.config import get_router_config_from_env
        
        # Create agent
        config = get_router_config_from_env()
        agent = FeaturesProductAgent(config)
        
        # Test queries
        test_queries = [
            "ویژگی‌های کمد چهار کشو (کد D14) را بگو",
            "مشخصات فرش 700شانه اُپال فیروزه ای",
            "گوشی سامسونگ گلکسی S24 چه ویژگی‌هایی دارد؟",
            "بگو کمد چهار درب ونوس طوسی چه مشخصاتی داره",
            "محصول ناموجود XYZ123 ویژگی‌هایش چیه"
        ]
        
        print("🧪 تست Agent 2 (Product Features)")
        print("=" * 50)
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n📋 تست {i}: {query}")
            print("-" * 40)
            
            result = await agent.process_query(query)
            
            if result.found:
                print(f"✅ نتیجه:")
                print(result.formatted_features)
            else:
                print(f"❌ خطا: {result.error}")
        
        # Clean up
        agent.close()
        print(f"\n🎯 تست Agent 2 تمام شد!")
    
    # Run test
    asyncio.run(test_agent())

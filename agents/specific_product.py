"""
Agent 1: Specific Product Finder - Torob AI Assistant

This agent finds specific products by name and returns their random_key.
It uses LangChain tools to extract product names and query the database.

Usage:
    agent = SpecificProductAgent(config)
    result = await agent.process_query("لطفا کمد چهار کشو (کد D14) را برای من پیدا کنید")

Author: Torob AI Team
"""

import asyncio
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
import json

from db.base import DatabaseBaseLoader
from router.base import RouterConfig


@dataclass
class ProductSearchResult:
    """Result of product search"""
    found: bool
    random_key: Optional[str] = None
    product_name: Optional[str] = None
    search_method: Optional[str] = None  # "exact" or "partial"
    error: Optional[str] = None


class SpecificProductAgent:
    """
    Agent 1: Finds specific products by name and returns random_key
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
                query: User query in Persian
                
            Returns:
                str: Extracted product name in Persian
            """
            # Use LLM to extract product name
            extraction_prompt = ChatPromptTemplate.from_messages([
                ("system", """تو یک استخراج‌کننده نام محصول هستی. وظیفه‌ات این است که از متن کاربر، نام کامل محصول را استخراج کنی.

قوانین مهم:
1. نام کامل محصول را با تمام جزئیات استخراج کن (شامل مدل، ویژگی‌ها، و مشخصات)
2. اگر کد محصول در پرانتز آمده (مثل کد D14)، آن را حذف کن
3. اگر عباراتی مثل "لطفا"، "برای من"، "پیدا کن" وجود دارد، آنها را حذف کن
4. تمام ویژگی‌های محصول مثل مدل، رنگ، سایز را حفظ کن
5. اگر نام محصول مشخص نیست، "نامشخص" برگردان

مثال‌ها:
- "لطفا کمد چهار کشو (کد D14) را برای من پیدا کنید" → "کمد چهار کشو"
- "کمد چهار طبقه بزرگ مدل C36 (72 عدد باتری 28 یا 42 آمپر)" → "کمد چهار طبقه بزرگ مدل C36 (72 عدد باتری 28 یا 42 آمپر)"
- "این محصول را پیدا رگال لباس با کمد چهار کشو و آینه کن" → "رگال لباس با کمد چهار کشو و آینه"
- "برای من محصول کمد چهار درب ونوس طوسی پیدا کن" → "کمد چهار درب ونوس طوسی"
"""),
                ("human", "{query}")
            ])
            
            try:
                response = self.llm.invoke(extraction_prompt.format_messages(query=query))
                extracted_name = response.content.strip()
                
                # Remove common prefixes/suffixes
                clean_phrases = [
                    "لطفا", "لطفاً", "برای من", "را پیدا کن", "پیدا کن", "پیدا کنید",
                    "را برای من", "این محصول را پیدا", "محصول", "برگردون", "کد",
                    "را برای من پیدا کنید", "می‌خواهم", "میخواهم"
                ]
                
                cleaned_name = extracted_name
                for phrase in clean_phrases:
                    cleaned_name = cleaned_name.replace(phrase, "").strip()
                
                # Also try to extract everything between "محصول" and "پیدا کن" or similar patterns
                import re
                patterns = [
                    r'محصول\s+(.+?)\s+(?:را\s+)?پیدا\s+کن',
                    r'(?:این\s+)?محصول\s+(?:را\s+)?پیدا\s+(.+?)\s+کن',
                    r'کد\s+(.+?)\s+(?:را\s+)?(?:برای\s+من\s+)?برگردون',
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
        def search_product_by_name(product_name: str) -> Dict[str, Any]:
            """
            Search for product in database by Persian name.
            
            Args:
                product_name: Persian name of the product
                
            Returns:
                dict: Search result with random_key if found
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
                        "product_name": results[0]['persian_name'],
                        "search_method": "exact"
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
                        "product_name": results[0]['persian_name'],
                        "search_method": "exact_case_insensitive"
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
                                "product_name": result['persian_name'],
                                "search_method": "exact"
                            }
                    
                    # Return first result if no exact match found
                    return {
                        "found": True,
                        "random_key": results[0]['random_key'],
                        "product_name": results[0]['persian_name'],
                        "search_method": "partial"
                    }
                
                return {"found": False, "error": "محصول یافت نشد"}
                
            except Exception as e:
                print(f"❌ خطا در جستجوی محصول: {e}")
                return {"found": False, "error": f"خطا در جستجو: {str(e)}"}
        
        # Store tools as instance attributes
        self.extract_product_name_tool = extract_product_name
        self.search_product_tool = search_product_by_name
        self._tools_created = True
    
    async def process_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> ProductSearchResult:
        """
        Process user query to find specific product
        
        Args:
            query: User query in Persian
            context: Optional context information
            
        Returns:
            ProductSearchResult: Result of product search
        """
        try:
            # Ensure tools are created
            self._create_tools()
            
            # Step 1: Extract product name from query
            print(f"🔍 استخراج نام محصول از: {query}")
            extracted_name = self.extract_product_name_tool.invoke(query)
            
            if not extracted_name:
                return ProductSearchResult(
                    found=False,
                    error="نتوانستم نام محصول را از درخواست شما استخراج کنم"
                )
            
            print(f"📝 نام استخراج شده: {extracted_name}")
            
            # Step 2: Search in database
            print(f"🔎 جستجو در پایگاه داده...")
            search_result = self.search_product_tool.invoke(extracted_name)
            
            # Check if search_result is None or not a dictionary
            if search_result is None:
                print(f"❌ خطا: نتیجه جستجو None است")
                return ProductSearchResult(
                    found=False,
                    error="خطا در جستجو - نتیجه None"
                )
            
            if not isinstance(search_result, dict):
                print(f"❌ خطا: نتیجه جستجو نوع نامعتبر است: {type(search_result)}")
                return ProductSearchResult(
                    found=False,
                    error="خطا در جستجو - نوع نتیجه نامعتبر"
                )
            
            if search_result.get("found", False):
                print(f"✅ محصول یافت شد: {search_result.get('random_key', 'نامشخص')}")
                return ProductSearchResult(
                    found=True,
                    random_key=search_result.get("random_key"),
                    product_name=search_result.get("product_name"),
                    search_method=search_result.get("search_method")
                )
            else:
                print(f"❌ محصول یافت نشد: {search_result.get('error', 'دلیل نامشخص')}")
                return ProductSearchResult(
                    found=False,
                    error=search_result.get("error", "محصول یافت نشد")
                )
                
        except Exception as e:
            print(f"❌ خطا در پردازش درخواست: {e}")
            return ProductSearchResult(
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
        """Test the Specific Product Agent"""
        from router.config import get_router_config_from_env
        
        # Create agent
        config = get_router_config_from_env()
        agent = SpecificProductAgent(config)
        
        # Test queries
        test_queries = [
            "لطفا کمد چهار کشو (کد D14) را برای من پیدا کنید",
            "گوشی سامسونگ گلکسی S24 می‌خواهم",
            "پارچه لایکرا دایره‌ای بافتنی نوریس 1/30 زرد طلایی قیمت چنده؟",
            "محصول ناموجود XYZ123"
        ]
        
        print("🧪 تست Agent 1 (Specific Product)")
        print("=" * 50)
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n📋 تست {i}: {query}")
            print("-" * 40)
            
            result = await agent.process_query(query)
            
            if result.found:
                print(f"✅ نتیجه: {result.random_key}")
                if result.search_method:
                    print(f"🔍 روش جستجو: {result.search_method}")
                if result.product_name:
                    print(f"📝 نام محصول: {result.product_name}")
            else:
                print(f"❌ خطا: {result.error}")
        
        # Clean up
        agent.close()
        print(f"\n🎯 تست Agent 1 تمام شد!")
    
    # Run test
    asyncio.run(test_agent())

"""
Hard signal detection using regex patterns and heuristics
Fast-path routing for clear patterns
"""

import re
from typing import List, Optional, Tuple, Set
from dataclasses import dataclass
from .base import AgentType, RouterState


@dataclass
class HardSignalResult:
    """Result of hard signal detection"""
    agent: Optional[AgentType] = None
    confidence: float = 0.0
    matched_patterns: List[str] = None
    extracted_data: dict = None
    
    def __post_init__(self):
        if self.matched_patterns is None:
            self.matched_patterns = []
        if self.extracted_data is None:
            self.extracted_data = {}


class HardSignalDetector:
    """Detects clear routing signals using regex patterns"""
    
    def __init__(self):
        # Compile regex patterns once for efficiency
        self.patterns = self._compile_patterns()
    
    def _compile_patterns(self) -> dict:
        """Compile all regex patterns"""
        return {
            # Product codes and SKUs
            'product_code': re.compile(
                r'\b(?:کد|code|sku|شناسه|مدل|model)\s*:?\s*([A-Za-z0-9\-_]+)\b',
                re.IGNORECASE | re.UNICODE
            ),
            
            # Exact SKU patterns
            'sku_pattern': re.compile(
                r'\b(?:SKU|sku)\s*:?\s*([A-Za-z0-9\-_]+)\b',
                re.IGNORECASE
            ),
            
            # Model patterns (e.g., "X515EA", "RS66", "A54", "15", "S24")
            'model_pattern': re.compile(
                r'\b([A-Z][A-Z0-9]{1,}(?:[-\s]?[A-Z0-9]+)*|\d{1,3}(?:\s+(?:پرو|pro|مکس|max|پلاس|plus))*|[A-Z]\d{1,3})\b',
                re.IGNORECASE | re.UNICODE
            ),
            
            # Price inquiry patterns
            'price_pattern': re.compile(
                r'(?:قیمت|چقدر|چند|هزینه|price|cost)',
                re.IGNORECASE | re.UNICODE
            ),
            
            # Comparison keywords
            'comparison_pattern': re.compile(
                r'(?:مقایسه|تفاوت|کدوم بهتره|بهتر|انتخاب بین|comparison|compare|versus|vs)',
                re.IGNORECASE | re.UNICODE
            ),
            
            # Seller/shop patterns
            'seller_pattern': re.compile(
                r'(?:فروشنده|فروشندگان|فروشگاه|فروشگاه‌ها|مغازه|مغازه‌ها|seller|sellers|shop|shops|store|stores)',
                re.IGNORECASE | re.UNICODE
            ),
            
            # Feature inquiry patterns
            'feature_pattern': re.compile(
                r'(?:مشخصات|ویژگی|ابعاد|وزن|رنگ|گارانتی|features|specs|specifications)',
                re.IGNORECASE | re.UNICODE
            ),
            
            # Base product patterns (for Torob bases)
            'base_pattern': re.compile(
                r'(?:base|پایه|محصول پایه)\s*:?\s*([A-Za-z0-9\-_]+)',
                re.IGNORECASE | re.UNICODE
            ),
            
            # Brand patterns
            'brand_pattern': re.compile(
                r'(?:' + '|'.join([
                    'سامسونگ', 'اپل', 'آیفون', 'شیائومی', 'هواوی', 'ال جی', 'سونی',
                    'ایسوس', 'لنوو', 'اچ پی', 'دل', 'نایک', 'آدیداس', 'پوما',
                    'Samsung', 'Apple', 'iPhone', 'Xiaomi', 'Huawei', 'LG', 'Sony',
                    'ASUS', 'Lenovo', 'HP', 'Dell', 'Nike', 'Adidas', 'Puma',
                    'بوش', 'Bosch', 'MSI', 'ROG'
                ]) + r')\b',
                re.IGNORECASE | re.UNICODE
            ),
            
            # Category patterns
            'category_pattern': re.compile(
                r'(?:' + '|'.join([
                    'گوشی', 'موبایل', 'موبیل', 'لپ تاپ', 'لپتاپ', 'تبلت', 'یخچال', 'ماشین لباسشویی',
                    'تلویزیون', 'کفش', 'لباس', 'کابینت', 'کمد', 'هدفون', 'پارچه', 'کفش',
                    'phone', 'mobile', 'laptop', 'tablet', 'refrigerator', 'washing machine',
                    'TV', 'television', 'shoes', 'clothes', 'cabinet', 'headphone', 'fabric'
                ]) + r')\b',
                re.IGNORECASE | re.UNICODE
            ),
            
            # General question patterns
            'general_pattern': re.compile(
                r'(?:چطور|چگونه|ساعت کاری|مرجوع|پرداخت|ضمانت اصالت|راهنما|how to|working hours|return|payment|warranty)',
                re.IGNORECASE | re.UNICODE
            ),
            
            # Specific product search patterns
            'find_product_pattern': re.compile(
                r'(?:پیدا کن|پیدا کنید|برای من پیدا|دنبال|می‌خواهم|میخواهم|می خواهم|'
                r'برگردون|برگردان|نشان بده|نشان دهید|جستجو کن|search|find|looking for)',
                re.IGNORECASE | re.UNICODE
            )
        }
    
    def detect(self, state: RouterState) -> HardSignalResult:
        """Detect hard signals in the query"""
        query = state.user_query.lower()
        result = HardSignalResult()
        
        # Check for multiple base matches (comparison)
        base_matches = self._extract_bases(query)
        if len(base_matches) >= 2:
            result.agent = AgentType.COMPARISON
            result.confidence = 0.95
            result.matched_patterns.append("multiple_bases")
            result.extracted_data['base_ids'] = base_matches
            return result
        
        # Check for explicit SKU/code patterns (highest priority for specific products)
        sku_match = self.patterns['sku_pattern'].search(query)
        code_match = self.patterns['product_code'].search(query)
        
        if sku_match or code_match:
            result.agent = AgentType.SPECIFIC_PRODUCT
            result.confidence = 0.95
            result.matched_patterns.append("explicit_code")
            if sku_match:
                result.extracted_data['sku'] = sku_match.group(1)
            if code_match:
                result.extracted_data['code'] = code_match.group(1)
            return result
        
        # Check for comparison patterns with brands/products
        if self.patterns['comparison_pattern'].search(query):
            brands = self._extract_brands(query)
            if len(brands) >= 2:
                result.agent = AgentType.COMPARISON
                result.confidence = 0.85
                result.matched_patterns.append("comparison_keywords")
                result.extracted_data['brands'] = brands
                return result
            # Single brand with comparison keywords might still be comparison
            elif brands and len(brands) == 1:
                result.agent = AgentType.COMPARISON
                result.confidence = 0.75
                result.matched_patterns.append("comparison_keywords")
                result.extracted_data['brands'] = brands
                return result
        
        # Check for seller/shop inquiries (check before product patterns)
        if self.patterns['seller_pattern'].search(query):
            result.agent = AgentType.SELLER_INFO
            result.confidence = 0.75
            result.matched_patterns.append("seller_keywords")
            brands = self._extract_brands(query)
            if brands:
                result.extracted_data['brands'] = brands
            return result
        
        # Check for specific model patterns with brand or detailed specs
        brands = self._extract_brands(query)
        models = self.patterns['model_pattern'].findall(query)
        categories = self.patterns['category_pattern'].findall(query)
        
        # Check if user is looking for a specific product
        has_find_pattern = bool(self.patterns['find_product_pattern'].search(query))
        
        # Enhanced specific product detection
        is_specific_product = False
        confidence = 0.0
        
        if brands and models:
            is_specific_product = True
            confidence = 0.8
            result.matched_patterns.append("brand_with_model")
            result.extracted_data['brand'] = brands[0]
            result.extracted_data['model'] = models[0]
        elif brands and categories and self._has_detailed_specs(query):
            # Detailed specs like "آیفون 15 پرو مکس 256 گیگ"
            is_specific_product = True
            confidence = 0.75
            result.matched_patterns.append("brand_with_specs")
            result.extracted_data['brand'] = brands[0]
            result.extracted_data['category'] = categories[0]
        elif brands and categories and has_find_pattern:
            # Brand + category + explicit search request (like "گوشی سامسونگ می‌خواهم")
            is_specific_product = True
            confidence = 0.85  # Increased confidence to override semantic routing
            result.matched_patterns.append("brand_category_find")
            result.extracted_data['brand'] = brands[0]
            result.extracted_data['category'] = categories[0]
        elif brands and has_find_pattern:
            # Brand + search request (like "سامسونگ پیدا کنید")
            is_specific_product = True
            confidence = 0.8  # Increased confidence
            result.matched_patterns.append("brand_find")
            result.extracted_data['brand'] = brands[0]
        elif brands and categories:
            # Brand + category without explicit find pattern (like "گوشی سامسونگ")
            is_specific_product = True
            confidence = 0.8  # Increased confidence
            result.matched_patterns.append("brand_category")
            result.extracted_data['brand'] = brands[0]
            result.extracted_data['category'] = categories[0]
        elif categories and has_find_pattern and len(query.split()) <= 8:
            # Category + find pattern for short queries (like "کمد چهار کشو پیدا کنید")
            # Length check to avoid general exploration queries
            is_specific_product = True
            confidence = 0.7  # Increased confidence
            result.matched_patterns.append("category_find")
            result.extracted_data['category'] = categories[0]
        elif categories and len(query.split()) <= 6:
            # Category only for very short queries (like "کمد چهار کشو")
            is_specific_product = True
            confidence = 0.6
            result.matched_patterns.append("category_only")
            result.extracted_data['category'] = categories[0]
        elif len(brands) >= 1 and self._has_detailed_specs(query):
            # Brand with detailed specifications
            is_specific_product = True
            confidence = 0.7
            result.matched_patterns.append("detailed_specs")
            result.extracted_data['brand'] = brands[0]
        
        if is_specific_product:
            result.agent = AgentType.SPECIFIC_PRODUCT
            result.confidence = confidence
            return result
        
        # Check for single base match
        if len(base_matches) == 1:
            # Check if asking about features/price
            if self.patterns['feature_pattern'].search(query) or self.patterns['price_pattern'].search(query):
                result.agent = AgentType.PRODUCT_FEATURE
                result.confidence = 0.9
                result.matched_patterns.append("base_with_feature")
            else:
                # Default to seller info for single base
                result.agent = AgentType.SELLER_INFO
                result.confidence = 0.85
                result.matched_patterns.append("single_base")
            result.extracted_data['base_id'] = base_matches[0]
            return result
        
        # Check for price inquiries (even without explicit base)
        if self.patterns['price_pattern'].search(query):
            # If has category or brand, likely asking about product features/price
            if categories or brands:
                result.agent = AgentType.PRODUCT_FEATURE
                result.confidence = 0.75
                result.matched_patterns.append("price_with_product")
                if brands:
                    result.extracted_data['brands'] = brands
                if categories:
                    result.extracted_data['categories'] = categories
                return result
        
        # Check for feature inquiries
        if self.patterns['feature_pattern'].search(query):
            if categories or brands:
                result.agent = AgentType.PRODUCT_FEATURE
                result.confidence = 0.7
                result.matched_patterns.append("feature_with_product")
                if brands:
                    result.extracted_data['brands'] = brands
                if categories:
                    result.extracted_data['categories'] = categories
                return result
        
        # Check for general questions
        if self.patterns['general_pattern'].search(query):
            result.agent = AgentType.GENERAL
            result.confidence = 0.8
            result.matched_patterns.append("general_keywords")
            return result
        
        # No clear hard signal detected
        return result
    
    def _extract_bases(self, query: str) -> List[str]:
        """Extract base IDs from query"""
        bases = []
        
        # Look for explicit base patterns
        base_matches = self.patterns['base_pattern'].findall(query)
        bases.extend(base_matches)
        
        # Look for patterns like "base-123" or "B123"
        implicit_base_pattern = re.compile(r'\b(?:base-|B)(\d+)\b', re.IGNORECASE)
        implicit_matches = implicit_base_pattern.findall(query)
        bases.extend(implicit_matches)
        
        return list(set(bases))  # Remove duplicates
    
    def _extract_brands(self, query: str) -> List[str]:
        """Extract brand names from query"""
        brands = self.patterns['brand_pattern'].findall(query)
        # Normalize brand names
        normalized = []
        for brand in brands:
            normalized_brand = brand.lower()
            # Map Persian to English for consistency
            brand_map = {
                'سامسونگ': 'samsung',
                'اپل': 'apple',
                'آیفون': 'iphone',
                'شیائومی': 'xiaomi',
                'هواوی': 'huawei',
                'ال جی': 'lg',
                'سونی': 'sony',
                'ایسوس': 'asus',
                'لنوو': 'lenovo',
                'اچ پی': 'hp',
                'دل': 'dell',
                'بوش': 'bosch'
            }
            if normalized_brand in brand_map:
                normalized_brand = brand_map[normalized_brand]
            normalized.append(normalized_brand)
        
        return list(set(normalized))  # Remove duplicates
    
    def _has_detailed_specs(self, query: str) -> bool:
        """Check if query contains detailed product specifications"""
        spec_patterns = [
            r'\d+\s*(?:گیگ|گیگابایت|gb|ترابایت|tb)',  # Storage: 256 گیگ, 1TB
            r'\d+\s*(?:اینچ|inch|")',  # Screen size: 6.5 اینچ, 15"
            r'\d+\s*(?:مگاپیکسل|mp|megapixel)',  # Camera: 48 مگاپیکسل
            r'(?:پرو|pro|مکس|max|plus|پلاس)',  # Product variants
            r'\d+\s*(?:رم|ram|حافظه)',  # RAM: 8 رم, 16GB RAM
            r'(?:dual|دوال)\s*(?:sim|سیم)',  # Dual SIM
            r'\d+\s*(?:هرتز|hz|khz|mhz)',  # Frequency
        ]
        
        for pattern in spec_patterns:
            if re.search(pattern, query, re.IGNORECASE | re.UNICODE):
                return True
        return False
    
    def extract_product_info(self, query: str) -> dict:
        """Extract all product-related information from query"""
        info = {
            'codes': [],
            'skus': [],
            'models': [],
            'brands': [],
            'categories': [],
            'bases': [],
            'has_price_inquiry': False,
            'has_feature_inquiry': False,
            'has_comparison': False
        }
        
        # Extract various patterns
        info['codes'] = self.patterns['product_code'].findall(query)
        info['skus'] = self.patterns['sku_pattern'].findall(query)
        info['models'] = self.patterns['model_pattern'].findall(query)
        info['brands'] = self._extract_brands(query)
        info['categories'] = self.patterns['category_pattern'].findall(query)
        info['bases'] = self._extract_bases(query)
        
        # Check for specific inquiries
        info['has_price_inquiry'] = bool(self.patterns['price_pattern'].search(query))
        info['has_feature_inquiry'] = bool(self.patterns['feature_pattern'].search(query))
        info['has_comparison'] = bool(self.patterns['comparison_pattern'].search(query))
        
        return info

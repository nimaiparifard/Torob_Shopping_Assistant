# System Prompts Module

The system prompts module contains carefully crafted prompts and examples for the AI agents in the Torob AI Assistant. These prompts enable the LLM to understand user queries, extract relevant information, and generate appropriate responses in Persian.

## 📁 Structure

```
system_prompts/
├── router_scenario_type.py                    # Query routing and scenario classification
├── comparison_system_prompt.py                # Product comparison logic
├── comparison_feature_level_system_prompt.py  # Feature-level comparison prompts
├── comparison_feature_system_prompt.py        # Feature extraction for comparison
├── comparison_final_decide_system_prompt.py   # Final comparison decision making
├── comparison_find_feature_general.py         # General feature finding
├── comparison_shop_system_prompt.py           # Shop-level comparison
├── product_features_system_prompts.py         # Product feature extraction
├── shop_system_prompts.py                     # Shop-related query handling
├── info_extraction_system_prompt.py           # General information extraction
├── extract_brand_from_image_system_prompt.py  # Brand extraction from images
├── extract_category_from_image_system_prompt.py # Category extraction from images
├── extract_final_dedicion_product_image_system_prompt.py # Final product decision from images
├── extract_name_system_prompt.py              # Product name extraction
├── extract_phrased_name_from_image_system_prompt.py # Phrased name extraction from images
├── find_important_part_system_prompt.py       # Important part identification
└── route_image_task_system_prompt.py          # Image task routing
```

## 🎯 Core Prompt Categories

### 1. Query Routing (`router_scenario_type.py`)

Routes user queries to appropriate agents based on intent analysis.

**Scenario Types:**
- `general`: General queries and random key extraction
- `exploration`: Product discovery with filtering
- `specific_product`: Specific product requests
- `feature_product`: Product feature queries
- `shop`: Shop-related queries (pricing, availability)
- `comparison`: Product comparison requests

**Key Features:**
- Persian language optimization
- Few-shot learning with extensive examples
- Context-aware classification
- Ambiguity handling
- Keyword-based detection

**Example Classification:**
```python
# Input: "سلام! من دنبال یه گیاه بونسای هستم که خیلی خاص و زیبا باشه"
# Output: {"scenario_type": "exploration"}

# Input: "وضوح تلویزیون ال جی مدل UT80006 سایز ۵۰ اینچ Ultra HD 4K LED به من بگو"
# Output: {"scenario_type": "feature_product"}
```

### 2. Product Comparison (`comparison_system_prompt.py`)

Handles multi-dimensional product comparisons.

**Comparison Types:**
- `feature_level`: Technical specifications comparison
- `shop_level`: Availability and pricing comparison
- `warranty_level`: Warranty coverage comparison
- `city_level`: Geographic availability comparison
- `general`: High-level product comparison

**Advanced Features:**
- Product name extraction with random keys
- Context-aware comparison type detection
- Persian language optimization
- Structured JSON output
- Error handling for ambiguous queries

**Example Usage:**
```python
# Input: "کدامیک از محصولات دراور فایل کمدی پلاستیکی طرح کودک با شناسه ebolgl و دراور هوم کت ۴ طبقه بزرگ طرح دار از پلاستیک با شناسه nihvhq در فروشگاه‌های بیشتری موجود است؟"
# Output: {
#   "comparison_type": "shop_level",
#   "product_name_1": "دراور فایل کمدی پلاستیکی طرح کودک",
#   "product_random_key_1": "ebolgl",
#   "product_name_2": "دراور هوم کت ۴ طبقه بزرگ طرح دار از پلاستیک",
#   "product_random_key_2": "nihvhq"
# }
```

### 3. Feature Extraction (`product_features_system_prompts.py`)

Extracts product names and desired features from user queries.

**Key Capabilities:**
- Complete product name extraction
- Feature identification from natural language
- Persian language understanding
- Context-aware feature mapping
- Structured output generation

**Example Extraction:**
```python
# Input: "می‌تونید بگید وزن فرشینه مخمل با ترمزگیر و عرض ۱ متر، طرح آشپزخانه با کد ۰۴ چقدره؟"
# Output: {
#   "product_name": "فرشینه مخمل با ترمزگیر و عرض ۱ متر، طرح آشپزخانه با کد ۰۴",
#   "features": ["وزن"]
# }
```

### 4. Shop Queries (`shop_system_prompts.py`)

Handles shop-related queries including pricing and availability.

**Query Types:**
- `mean_price`: Average price calculation
- `max_price`: Maximum price queries
- `min_price`: Minimum price queries
- `shop_count`: Shop availability counting
- `shop_list`: Shop listing with filters

**Advanced Features:**
- Location-based filtering
- Warranty status consideration
- Shop name extraction
- Price range analysis
- Persian language optimization

**Example Usage:**
```python
# Input: "قیمت متوسط چای ساز بوش مدل PB-78TS ظرفیت ۲.۵ لیتر با کتری پیرکس در شهر قم چقدر است؟"
# Output: {
#   "task_type": "mean_price",
#   "product_name": "چای ساز بوش مدل PB-78TS ظرفیت ۲.۵ لیتر با کتری پیرکس",
#   "shop_name": null,
#   "location": "قم",
#   "has_warranty": null
# }
```

### 5. Information Extraction (`info_extraction_system_prompt.py`)

Extracts comprehensive product information from user queries.

**Extracted Information:**
- Product name and description
- City and location
- Brand and category
- Features and specifications
- Price ranges
- Warranty status
- Shop information
- Rating scores

**Example Extraction:**
```python
# Input: "سلام! من دنبال یه لوستر سقفی هستم که برای اتاق نشیمن مناسب باشه"
# Output: {
#   "product_name": "لوستر سقفی مناسب اتاق نشیمن",
#   "city_name": null,
#   "brand_name": null,
#   "category_name": "لوستر",
#   "features": null,
#   "lowest_price": null,
#   "highest_price": null,
#   "has_warranty": null,
#   "shop_name": null,
#   "score": null
# }
```

### 6. Image Processing Prompts

#### Brand Extraction (`extract_brand_from_image_system_prompt.py`)
Extracts brand information from product images.

#### Category Extraction (`extract_category_from_image_system_prompt.py`)
Identifies product categories from images.

#### Product Name Extraction (`extract_name_system_prompt.py`)
Extracts product names from text descriptions.

#### Image Task Routing (`route_image_task_system_prompt.py`)
Routes image-based queries to appropriate handlers.

**Image Task Types:**
- `find_main_object`: Identify main object in image
- `find_base_product_and_main_object`: Identify object and find related product

## 🧠 Prompt Engineering Techniques

### Few-Shot Learning
All prompts include extensive examples to guide the LLM:
- **Positive Examples**: Correct classification/extraction examples
- **Negative Examples**: Common mistakes and edge cases
- **Context Examples**: Different scenarios and variations
- **Error Examples**: How to handle ambiguous inputs

### Persian Language Optimization
- **Natural Language Processing**: Understanding Persian grammar and syntax
- **Cultural Context**: Iranian e-commerce terminology
- **Regional Variations**: Different Persian dialects and expressions
- **Technical Terms**: Product-specific vocabulary

### Structured Output
- **JSON Format**: Consistent structured responses
- **Validation**: Input/output validation rules
- **Error Handling**: Graceful handling of invalid inputs
- **Type Safety**: Proper data type specification

## 🔧 Technical Implementation

### Prompt Template System
```python
# Example prompt structure
system_prompt = """
تو یک [ROLE] هستی.
ورودی همیشه یک [INPUT_TYPE] است.
خروجی باید فقط و فقط در قالب JSON معتبر (UTF-8) و دقیقا با این ساختار باشد:
{JSON_SCHEMA}

قوانین بسیار مهم:
{RULES}

مثال کلیدی:
{EXAMPLE}
"""

# Few-shot examples
examples = [
    {
        "input": "example input",
        "output": "expected output"
    }
]
```

### Validation Rules
- **Input Validation**: Check input format and content
- **Output Validation**: Ensure JSON structure compliance
- **Error Handling**: Graceful failure modes
- **Fallback Strategies**: Default responses for edge cases

### Performance Optimization
- **Prompt Length**: Optimized for token efficiency
- **Example Selection**: Most relevant examples chosen
- **Context Management**: Efficient context usage
- **Caching**: Prompt result caching

## 📊 Prompt Analytics

### Usage Tracking
- **Prompt Performance**: Success/failure rates
- **Response Quality**: Accuracy metrics
- **Token Usage**: Cost optimization
- **Error Analysis**: Common failure patterns

### A/B Testing
- **Prompt Variations**: Different prompt versions
- **Performance Comparison**: Effectiveness metrics
- **User Feedback**: Response quality assessment
- **Continuous Improvement**: Iterative optimization

## 🧪 Testing and Validation

### Test Coverage
- **Unit Tests**: Individual prompt testing
- **Integration Tests**: End-to-end functionality
- **Edge Case Tests**: Boundary condition handling
- **Performance Tests**: Response time and accuracy

### Validation Methods
- **Output Validation**: JSON structure compliance
- **Accuracy Testing**: Correct classification/extraction
- **Error Testing**: Failure scenario handling
- **Performance Testing**: Response time optimization

## 📈 Monitoring and Analytics

### Metrics Tracked
- **Classification Accuracy**: Correct scenario routing
- **Extraction Quality**: Information extraction accuracy
- **Response Time**: Prompt processing speed
- **Error Rates**: Failure frequency and types
- **User Satisfaction**: Response quality feedback

### Logging
- **Prompt Usage**: Which prompts are used most
- **Error Patterns**: Common failure scenarios
- **Performance Metrics**: Response time and accuracy
- **User Interactions**: Query patterns and preferences

## 🔄 Version History

- **v1.0.0**: Initial prompt implementation
- Persian language optimization
- Few-shot learning examples
- Structured output format
- Comprehensive error handling
- Performance optimization
- Analytics and monitoring

## 🎯 Best Practices

### Prompt Design
- **Clear Instructions**: Unambiguous task description
- **Consistent Format**: Standardized input/output structure
- **Comprehensive Examples**: Covering various scenarios
- **Error Handling**: Graceful failure modes

### Persian Language
- **Natural Expression**: Using natural Persian language
- **Cultural Context**: Understanding Iranian e-commerce
- **Technical Terms**: Product-specific vocabulary
- **Regional Variations**: Different Persian dialects

### Performance
- **Token Efficiency**: Optimized prompt length
- **Context Management**: Efficient context usage
- **Caching**: Result caching for repeated queries
- **Batch Processing**: Efficient bulk operations

import base64
import requests
import os
from openai import AsyncOpenAI
from typing import Dict, Any
import dotenv
from response_format import Response
dotenv.load_dotenv()


class ImageAgent:
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_URL"),
        )
    
    def get_base64_encoded_image(self, image_url: str) -> str:
        """
        Download image from URL and encode it to base64.
        """
        try:
            response = requests.get(image_url)
            response.raise_for_status()
            image_data = response.content
            base64_image = base64.b64encode(image_data).decode("utf-8")
            assert base64.b64decode(base64_image) == image_data
            return base64_image
        except Exception as e:
            print(f"Error downloading image: {e}")
            return None
    
    async def process_query(self, query: str, image_url: str) -> Response:
        """
        Process user query about an image.
        
        Args:
            query: User's question about the image
            image_url: URL of the image to analyze
            
        Returns:
            Answer about the image based on the query
        """
        try:
            # Download and encode image
            base64_image = self.get_base64_encoded_image(image_url)
            if not base64_image:
                return "متأسفم، نتوانستم تصویر را دانلود کنم. لطفاً URL تصویر را بررسی کنید."
            
            # Create the prompt for image analysis
            system_prompt = (
                "تو یک تحلیلگر تصویر هوشمند هستی. "
                "فقط یک عبارت کوتاه (2-4 کلمه) پاسخ بده که نشان‌دهنده شیء یا مفهوم اصلی در تصویر است. "
                "مثال: 'شمع با جاشمعی' یا 'تخته برش آشپزخانه' یا 'مبلمان اتاق نشیمن'. "
                "هیچ توضیح اضافی نده، فقط یک عبارت کوتاه."
            )
            
            # Call OpenAI Vision API
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",  # or gpt-4o for better vision capabilities
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": query
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1000,
                temperature=0.3
            )
            res = Response(message=response.choices[0].message.content, base_random_keys=[], member_random_keys=[])
            return res
            
        except Exception as e:
            print(f"Error in process_image_query: {e}")
            res = Response(message=f"متأسفم، خطایی در تحلیل تصویر رخ داد: {str(e)}", base_random_keys=[], member_random_keys=[])
            return res
    
    async def identify_main_object(self, image_url: str) -> Response:
        """
        Identify the main object or concept in the image.
        This is a specialized method for the specific query type.
        """
        query = "شیء و مفهوم اصلی در تصویر چیست؟"
        output =  await self.process_query(query, image_url)
        return output
    
    async def analyze_product_in_image(self, image_url: str) -> str:
        """
        Analyze if there's a product in the image and provide details.
        """
        query = "آیا در این تصویر محصولی وجود دارد؟ اگر بله، جزئیات آن را شرح بده."
        return await self.process_query(query, image_url)
    
    async def get_image_description(self, image_url: str) -> str:
        """
        Get a general description of the image.
        """
        query = "این تصویر را به طور کامل و دقیق توصیف کن."
        return await self.process_query(query, image_url)


# Test function
async def test_image_agent():
    """
    Test the ImageAgent with the provided example.
    """
    agent = ImageAgent()
    
    # Test with the provided example
    image_url = "https://image.torob.com/base/images/KE/w-/KEw-BMGHp0UcnUrP.jpg"
    query = "شیء و مفهوم اصلی در تصویر چیست؟"
    
    print("🖼️ Testing Image Agent")
    print("=" * 40)
    print(f"Query: {query}")
    print(f"Image URL: {image_url}")
    print("\nAnalyzing image...")
    
    try:
        response = await agent.process_query(query, image_url)
        print(f"\nResponse: {response}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test other methods
    print("\n" + "=" * 40)
    print("Testing other analysis methods...")
    
    try:
        main_object = await agent.identify_main_object(image_url)
        print(f"\nMain Object: {main_object}")
        
        product_analysis = await agent.analyze_product_in_image(image_url)
        print(f"\nProduct Analysis: {product_analysis}")
        
        description = await agent.get_image_description(image_url)
        print(f"\nGeneral Description: {description}")
        
    except Exception as e:
        print(f"Error in additional tests: {e}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_image_agent())

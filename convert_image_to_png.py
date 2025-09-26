import base64
import io
from PIL import Image
import os

def convert_base64_to_png(base64_data, output_filename="converted_image.png"):
    """
    Convert base64 image data to PNG format and save it.
    
    Args:
        base64_data (str): Base64 encoded image data
        output_filename (str): Output PNG filename
    """
    try:
        # Remove data URL prefix if present
        if base64_data.startswith('data:image/'):
            base64_data = base64_data.split(',')[1]
        
        # Decode base64 data
        image_data = base64.b64decode(base64_data)
        
        # Open image from bytes
        image = Image.open(io.BytesIO(image_data))
        
        # Convert to RGB if necessary (for PNG compatibility)
        if image.mode in ('RGBA', 'LA', 'P'):
            # Keep transparency for PNG
            pass
        elif image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Save as PNG
        image.save(output_filename, 'PNG')
        print(f"✅ Image successfully converted and saved as: {output_filename}")
        print(f"📏 Image size: {image.size[0]}x{image.size[1]} pixels")
        print(f"🎨 Image mode: {image.mode}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error converting image: {str(e)}")
        return False

def main():
    # Import the image data from image_examples.py
    try:
        from agents.image_examples import images
        
        if not images:
            print("❌ No images found in image_examples.py")
            return
        
        # Process the first image
        first_image = images[0]
        image_data = first_image["image"]
        
        print("🖼️ Converting base64 image to PNG...")
        print(f"📝 Query: {first_image['query']}")
        
        # Convert and save
        success = convert_base64_to_png(image_data, "converted_image.png")
        
        if success:
            print("\n🎉 Conversion completed successfully!")
        else:
            print("\n💥 Conversion failed!")
            
    except ImportError:
        print("❌ Could not import image_examples.py")
        print("Make sure the file exists and is in the correct location.")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    main()

import base64
import io
from PIL import Image
import argparse
import sys

def convert_base64_to_png(base64_data, output_filename="output.png", input_format="auto"):
    """
    Convert base64 image data to PNG format and save it.
    
    Args:
        base64_data (str): Base64 encoded image data
        output_filename (str): Output PNG filename
        input_format (str): Input format ('auto', 'jpeg', 'png', etc.)
    """
    try:
        # Remove data URL prefix if present
        if base64_data.startswith('data:image/'):
            # Extract format from data URL
            format_part = base64_data.split(';')[0].split('/')[-1]
            base64_data = base64_data.split(',')[1]
            if input_format == "auto":
                input_format = format_part
        
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
        print(f"📁 File size: {os.path.getsize(output_filename)} bytes")
        
        return True
        
    except Exception as e:
        print(f"❌ Error converting image: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Convert base64 image data to PNG format')
    parser.add_argument('--input', '-i', help='Input base64 string or file path')
    parser.add_argument('--output', '-o', default='output.png', help='Output PNG filename')
    parser.add_argument('--format', '-f', default='auto', help='Input image format (auto, jpeg, png, etc.)')
    parser.add_argument('--from-file', action='store_true', help='Read base64 data from file')
    
    args = parser.parse_args()
    
    if not args.input:
        print("❌ Please provide input data using --input or -i")
        print("Usage examples:")
        print("  python base64_to_png_converter.py --input 'data:image/jpeg;base64,/9j/4AAQ...'")
        print("  python base64_to_png_converter.py --input base64_data.txt --from-file")
        return
    
    # Get base64 data
    if args.from_file:
        try:
            with open(args.input, 'r') as f:
                base64_data = f.read().strip()
        except FileNotFoundError:
            print(f"❌ File not found: {args.input}")
            return
    else:
        base64_data = args.input
    
    # Convert and save
    success = convert_base64_to_png(base64_data, args.output, args.format)
    
    if success:
        print(f"\n🎉 Conversion completed successfully!")
        print(f"📁 Output file: {args.output}")
    else:
        print(f"\n💥 Conversion failed!")
        sys.exit(1)

if __name__ == "__main__":
    import os
    main()

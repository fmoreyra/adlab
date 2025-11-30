#!/usr/bin/env python3
"""
PDF to Markdown Documentation Converter
Extracts text, images, and diagrams from PDF files and converts them to structured markdown documentation.
"""

import io
import re
import sys
from pathlib import Path

import fitz  # PyMuPDF
from PIL import Image


class PDFToDocsConverter:
    def __init__(self, pdf_path, output_dir="docs"):
        self.pdf_path = Path(pdf_path).expanduser()
        self.output_dir = Path(output_dir)
        self.images_dir = self.output_dir / "images"
        self.sections_dir = self.output_dir / "sections"
        
        # Create output directories
        self.output_dir.mkdir(exist_ok=True)
        self.images_dir.mkdir(exist_ok=True)
        
    def extract_images_from_page(self, page, page_num):
        """Extract embedded images from a PDF page."""
        images = []
        image_list = page.get_images(full=True)
        
        for img_index, img_info in enumerate(image_list):
            xref = img_info[0]
            try:
                base_image = self.doc.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]
                
                # Save image
                image_filename = f"page_{page_num:03d}_img_{img_index:02d}.{image_ext}"
                image_path = self.images_dir / image_filename
                
                with open(image_path, "wb") as f:
                    f.write(image_bytes)
                
                images.append(image_filename)
                print(f"  Extracted image: {image_filename}")
            except Exception as e:
                print(f"  Warning: Could not extract image {img_index} from page {page_num}: {e}")
        
        return images
    
    def render_page_as_image(self, page, page_num):
        """Render a page as an image (useful for diagrams and complex layouts)."""
        try:
            # Render page at higher resolution for better quality
            mat = fitz.Matrix(2.0, 2.0)  # 2x zoom for better quality
            pix = page.get_pixmap(matrix=mat)
            
            # Convert to PIL Image
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            
            # Save as PNG
            image_filename = f"page_{page_num:03d}_full.png"
            image_path = self.images_dir / image_filename
            img.save(image_path, "PNG", optimize=True)
            
            print(f"  Rendered page {page_num} as image: {image_filename}")
            return image_filename
        except Exception as e:
            print(f"  Warning: Could not render page {page_num}: {e}")
            return None
    
    def extract_text_from_page(self, page):
        """Extract text from a page, preserving structure."""
        try:
            # Extract text with layout preservation
            text = page.get_text("text")
            return text
        except Exception as e:
            print(f"  Warning: Could not extract text: {e}")
            return ""
    
    def detect_heading(self, text):
        """Simple heading detection based on text patterns."""
        lines = text.strip().split('\n')
        if not lines:
            return None, text
        
        first_line = lines[0].strip()
        
        # Check if first line looks like a heading (short, possibly all caps, etc.)
        if first_line and len(first_line) < 100:
            # Common heading patterns
            if (first_line.isupper() or 
                re.match(r'^[\d\.]+\s+[A-Z]', first_line) or
                re.match(r'^[A-Z][a-zA-Z\s]+$', first_line)):
                return first_line, '\n'.join(lines[1:])
        
        return None, text
    
    def process_pdf(self):
        """Main processing function."""
        print(f"Opening PDF: {self.pdf_path}")
        
        if not self.pdf_path.exists():
            print(f"Error: PDF file not found at {self.pdf_path}")
            return False
        
        self.doc = fitz.open(self.pdf_path)
        total_pages = len(self.doc)
        
        print(f"Processing {total_pages} pages...")
        
        markdown_content = []
        markdown_content.append(f"# {self.pdf_path.stem}\n\n")
        markdown_content.append(f"*Converted from PDF - {total_pages} pages*\n\n")
        markdown_content.append("---\n\n")
        
        # Process each page
        for page_num in range(total_pages):
            page = self.doc[page_num]
            print(f"\nProcessing page {page_num + 1}/{total_pages}...")
            
            # Extract text
            text = self.extract_text_from_page(page)
            
            # Extract embedded images
            extracted_images = self.extract_images_from_page(page, page_num + 1)
            
            # Check if page has significant visual content (diagrams, charts, etc.)
            # We'll render pages that have images or very little text
            should_render = len(extracted_images) > 0 or len(text.strip()) < 100
            
            if should_render:
                rendered_image = self.render_page_as_image(page, page_num + 1)
            else:
                rendered_image = None
            
            # Add to markdown
            markdown_content.append(f"## Page {page_num + 1}\n\n")
            
            # Add text content if available
            if text.strip():
                # Detect if first line is a heading
                heading, body = self.detect_heading(text)
                if heading:
                    markdown_content.append(f"### {heading}\n\n")
                    if body.strip():
                        markdown_content.append(f"{body}\n\n")
                else:
                    markdown_content.append(f"{text}\n\n")
            
            # Add images
            if rendered_image:
                markdown_content.append(f"![Page {page_num + 1}](images/{rendered_image})\n\n")
            
            for img in extracted_images:
                markdown_content.append(f"![Image from page {page_num + 1}](images/{img})\n\n")
            
            markdown_content.append("---\n\n")
        
        # Write main README
        readme_path = self.output_dir / "README.md"
        with open(readme_path, "w", encoding="utf-8") as f:
            f.writelines(markdown_content)
        
        print("\n✓ Documentation created successfully!")
        print(f"  Main file: {readme_path}")
        print(f"  Images: {len(list(self.images_dir.glob('*')))} files in {self.images_dir}")
        
        self.doc.close()
        return True

def main():
    if len(sys.argv) < 2:
        print("Usage: python pdf_to_docs.py <pdf_file> [output_dir]")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "docs"
    
    converter = PDFToDocsConverter(pdf_path, output_dir)
    success = converter.process_pdf()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()


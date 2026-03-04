import zipfile
import re
import sys
import xml.etree.ElementTree as ET

def extract_text_from_pptx(pptx_path):
    out = []
    try:
        with zipfile.ZipFile(pptx_path, 'r') as z:
            slides = [f for f in z.namelist() if f.startswith('ppt/slides/slide') and f.endswith('.xml')]
            slides.sort(key=lambda x: int(re.search(r'slide(\d+)', x).group(1)))
            for filename in slides:
                xml_content = z.read(filename).decode('utf-8')
                matches = re.findall(r'<a:t[^>]*>(.*?)</a:t>', xml_content)
                if matches:
                    slide_num = re.search(r'slide(\d+)\.xml', filename).group(1)
                    out.append(f"\n--- Slide {slide_num} ---")
                    for match in matches:
                        text = match.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"')
                        if text.strip():
                            out.append(text)
    except Exception as e:
        return f"Error extracting PPTX: {e}"
    
    return '\n'.join(out)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python read_pptx.py <path_to_pptx>")
        sys.exit(1)
    print(extract_text_from_pptx(sys.argv[1]))

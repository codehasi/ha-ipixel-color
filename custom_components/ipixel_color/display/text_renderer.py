"""Text rendering for iPIXEL Color displays."""
from __future__ import annotations

import io
import logging
import os
from pathlib import Path
from typing import Any, Tuple

from PIL import Image, ImageDraw, ImageFont

_LOGGER = logging.getLogger(__name__)

# Minimum font size to try
MIN_FONT_SIZE = 4


def _get_font_path(font_name: str) -> str | None:
    """Get path to font file from fonts/ folder.
    
    Args:
        font_name: Font filename (with or without extension)
        
    Returns:
        Full path to font file if found, None otherwise
    """
    # Add common font extensions if not present
    if not any(font_name.lower().endswith(ext) for ext in ['.ttf', '.otf', '.woff', '.woff2']):
        font_name += '.ttf'
    
    # Look in fonts/ folder relative to this module
    fonts_dir = Path(__file__).parent.parent / 'fonts'
    font_path = fonts_dir / font_name
    
    if font_path.exists():
        return str(font_path)
    
    _LOGGER.warning("Font %s not found in %s", font_name, fonts_dir)
    return None


def render_text_to_png(text: str, width: int, height: int, antialias: bool = True, font_size: int | None = None, font: str | None = None) -> bytes:
    """Render text to PNG image data.
    
    Args:
        text: Text to render (supports multiline with \n)
        width: Display width in pixels
        height: Display height in pixels
        antialias: Enable antialiasing for smoother text (default: True)
        font_size: Fixed font size in pixels, or None for auto-sizing (default: None)
        font: Font name from fonts/ folder, or None for default (default: None)
        
    Returns:
        PNG image data as bytes
    """
    # Create image with device dimensions
    # Use 'L' mode (grayscale) for non-antialiased to get sharper pixels
    if not antialias:
        img = Image.new('1', (width, height), 0)  # 1-bit pixels, black background
    else:
        img = Image.new('RGB', (width, height), (0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Process multiline text
    lines = text.split('\n') if '\n' in text else [text]
    
    # Get font - either fixed size or auto-optimized
    if font_size is not None:
        font_obj = get_fixed_font(font_size, font)
    else:
        font_obj = get_optimal_font(draw, lines, width, height, font)
    
    # Calculate total text height for centering
    total_height = 0
    line_heights = []
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font_obj)
        line_height = bbox[3] - bbox[1]
        line_heights.append(line_height)
        total_height += line_height
    
    # Start position for vertical centering
    y_start = (height - total_height) // 2
    current_y = y_start
    
    # Draw each line centered
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font_obj)
        text_width = bbox[2] - bbox[0]
        
        # Center horizontally
        x = (width - text_width) // 2
        
        # Draw the line with appropriate fill color
        if not antialias:
            draw.text((x, current_y), line, font=font_obj, fill=1)  # 1 for white in 1-bit mode
        else:
            draw.text((x, current_y), line, font=font_obj, fill=(255, 255, 255))
        current_y += line_heights[i]
    
    # Convert to PNG bytes
    png_buffer = io.BytesIO()
    
    # Convert 1-bit image to RGB for PNG output if needed
    if not antialias:
        # Convert 1-bit to RGB: 0 -> black (0,0,0), 1 -> white (255,255,255)
        rgb_img = Image.new('RGB', (width, height), (0, 0, 0))
        rgb_img.paste(img.point(lambda x: 255 if x else 0), (0, 0))
        rgb_img.save(png_buffer, format='PNG')
    else:
        img.save(png_buffer, format='PNG')
        
    return png_buffer.getvalue()


def get_fixed_font(size: int, font_name: str | None = None) -> ImageFont.FreeTypeFont:
    """Get font with fixed size.
    
    Args:
        size: Font size in pixels
        font_name: Optional font name from fonts/ folder
        
    Returns:
        Font object with the specified size
    """
    try:
        # Try to load custom font from fonts/ folder first
        if font_name:
            font_path = _get_font_path(font_name)
            if font_path:
                try:
                    return ImageFont.truetype(font_path, size)
                except Exception as e:
                    _LOGGER.warning("Could not load custom font %s: %s", font_name, e)
        
        # Use default font if custom font failed or not specified
        return ImageFont.load_default()
    except Exception as e:
        _LOGGER.warning("Error loading font size %d: %s, using default", size, e)
        return ImageFont.load_default()


def get_optimal_font(draw: ImageDraw.Draw, lines: list[str], 
                     max_width: int, max_height: int, font_name: str | None = None) -> ImageFont.FreeTypeFont:
    """Find the largest font size that fits all text within dimensions.
    
    Args:
        draw: ImageDraw object for text measurement
        lines: List of text lines to render
        max_width: Maximum width in pixels
        max_height: Maximum height in pixels
        font_name: Optional font name from fonts/ folder
        
    Returns:
        Optimal font for the text
    """
    # Try different font sizes from large to small
    for size in range(min(max_height, max_width), MIN_FONT_SIZE, -1):
        try:
            # Try to load custom font first, then default
            font = None
            if font_name:
                font_path = _get_font_path(font_name)
                if font_path:
                    try:
                        font = ImageFont.truetype(font_path, size)
                    except Exception as e:
                        _LOGGER.debug("Custom font %s failed at size %d: %s", font_name, size, e)
            
            # Use default font if custom font failed or not specified
            if font is None:
                font = ImageFont.load_default()
            
            # Check if all lines fit within dimensions
            fits = True
            total_height = 0
            
            for line in lines:
                bbox = draw.textbbox((0, 0), line, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                
                # Check if line fits horizontally
                if text_width > max_width:
                    fits = False
                    break
                    
                total_height += text_height
            
            # Check if all lines fit vertically
            if total_height > max_height:
                fits = False
            
            if fits:
                _LOGGER.debug("Optimal font size: %d (total height: %d/%d)", 
                            size, total_height, max_height)
                return font
                
        except Exception as e:
            _LOGGER.debug("Font size %d failed: %s", size, e)
            continue
    
    # Fallback to minimum font size
    _LOGGER.warning("Using fallback font - text may not fit optimally")
    return ImageFont.load_default()
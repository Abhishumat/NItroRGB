import os
import subprocess
import configparser
import colorsys
import math
from colorthief import ColorThief
from PIL import Image, ImageEnhance

def get_wallpaper_path():

    """Attempts to find the current wallpaper path across different Linux DEs."""
    
    # 1. Try GNOME
    try:
        for uri_key in ['picture-uri-dark', 'picture-uri']:
            result = subprocess.run(
                ['gsettings', 'get', 'org.gnome.desktop.background', uri_key], 
                capture_output=True, text=True
            )
            if result.returncode == 0 and result.stdout.strip() != "''":
                path = result.stdout.strip().strip("'").replace('file://', '')
                if os.path.exists(path):
                    return path
    except Exception:
        pass

    # 2. Try KDE Plasma
    kde_config = os.path.expanduser("~/.config/plasma-org.kde.plasma.desktop-appletsrc")
    if os.path.exists(kde_config):
        try:
            config = configparser.ConfigParser()
            config.read(kde_config)
            for section in config.sections():
                if 'Wallpaper' in section and 'Image' in config[section]:
                    path = config[section]['Image'].replace('file://', '')
                    if os.path.exists(path):
                        return path
        except Exception:
            pass

    return None

def boost_for_led(r, g, b):
    """
    Transforms monitor RGB to hardware LED RGB.
    Preserves pure white, but clamps low-saturation colors to 
    vibrant levels so LEDs don't look washed out.
    """
    h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
    
    if s < 0.08:
        return f"#{r:02x}{g:02x}{b:02x}"

    s_boosted = min(1.0, max(s * 2.0, 0.75))
    v_boosted = min(1.0, max(v * 1.2, 0.85))
    
    r_new, g_new, b_new = colorsys.hsv_to_rgb(h, s_boosted, v_boosted)
    return f"#{int(r_new * 255):02x}{int(g_new * 255):02x}{int(b_new * 255):02x}"

def extract_gradient(image_path=None):
    """
    Extracts colors with ColorThief and runs an LED saturation post-pass.
    """
    if not image_path:
        image_path = get_wallpaper_path()
        
    fallback_palette = ["#89b4fa", "#b4befe", "#89dceb", "#74c7ec"]
        
    if not image_path or not os.path.exists(image_path):
        return fallback_palette

    try:
        ct = ColorThief(image_path)
        palette = ct.get_palette(color_count=8, quality=5)
        
        if not palette:
            return fallback_palette

        boosted_colors = []
        for r, g, b in palette:
            hex_code = boost_for_led(r, g, b)
            if hex_code not in boosted_colors:
                boosted_colors.append(hex_code)
            if len(boosted_colors) == 4:
                break
                
        while len(boosted_colors) < 4:
            boosted_colors.append(boosted_colors[-1])
            
        return boosted_colors[:4]

    except Exception as e:
        print(f"Error processing wallpaper with ColorThief: {e}")
        return fallback_palette
    """
    Extracts a gorgeous 4-color palette using Median-Cut quantization 
    via ColorThief, completely bypassing manual math garbage.
    """
    if not image_path:
        image_path = get_wallpaper_path()
        
    fallback_palette = ["#89b4fa", "#b4befe", "#89dceb", "#74c7ec"]
        
    if not image_path or not os.path.exists(image_path):
        return fallback_palette

    try:
        # ColorThief handles the heavy lifting of finding dominant color blocks
        ct = ColorThief(image_path)
        
        # Get a palette of up to 8 colors
        palette = ct.get_palette(color_count=8, quality=5)
        
        if not palette:
            return fallback_palette
            
        # Convert RGB tuples to Hex
        hex_colors = [f"#{r:02x}{g:02x}{b:02x}" for r, g, b in palette]
        
        # Take the first 4 unique colors to avoid duplicates
        unique_colors = []
        for hex_code in hex_colors:
            if hex_code not in unique_colors:
                unique_colors.append(hex_code)
            if len(unique_colors) == 4:
                break
                
        while len(unique_colors) < 4:
            unique_colors.append(unique_colors[-1])
            
        return unique_colors[:4]

    except Exception as e:
        print(f"Error processing wallpaper with ColorThief: {e}")
        return fallback_palette
    """
    Extracts 4 vibrant colors, enforces color variety (hue distance), 
    and uses logarithmic scoring to ensure small accent colors aren't ignored.
    """
    if not image_path:
        image_path = get_wallpaper_path()
        
    fallback_palette = ["#89b4fa", "#b4befe", "#89dceb", "#74c7ec"]
        
    if not image_path or not os.path.exists(image_path):
        return fallback_palette

    try:
        img = Image.open(image_path).convert("RGB")
        img = img.resize((150, 150)) 
        
        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(2.5) 
        
        # Increased to 32 to ensure we catch very tiny accent colors
        img_quant = img.convert("P", palette=Image.ADAPTIVE, colors=32)
        img_rgb = img_quant.convert("RGB")
        colors = img_rgb.getcolors(150 * 150)
        
        valid_colors = []
        
        for count, (r, g, b) in colors:
            h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)
            
            if s > 0.15 and v > 0.15: 
                s_boosted = min(1.0, s * 1.5 + 0.2) 
                v_boosted = min(1.0, v * 1.2 + 0.3) 
                
                r_new, g_new, b_new = colorsys.hsv_to_rgb(h, s_boosted, v_boosted)
                r_hex = int(r_new * 255)
                g_hex = int(g_new * 255)
                b_hex = int(b_new * 255)
                
                # The Magic Fix: math.log prevents massive color blocks from 
                # bullying small accent colors out of the palette.
                score = math.log(count + 1) * (s_boosted * v_boosted)
                
                valid_colors.append((score, h, (r_hex, g_hex, b_hex)))

        valid_colors.sort(key=lambda x: x[0], reverse=True)
        
        # --- NEW: HUE DISTANCE FILTER ---
        final_colors = []
        
        def hue_distance(h1, h2):
            # Calculates shortest distance on a circular color wheel (0.0 to 1.0)
            return min(abs(h1 - h2), 1.0 - abs(h1 - h2))

        for item in valid_colors:
            # Only accept the color if its hue is at least ~8% different from already picked colors
            if all(hue_distance(item[1], picked[1]) > 0.08 for picked in final_colors):
                final_colors.append(item)
            if len(final_colors) == 4:
                break
                
        # Failsafe: If the image is truly just one color (e.g. pure blue), 
        # the filter above will only find 1 or 2 colors. Fill the rest with the next best scores.
        if len(final_colors) < 4:
            for item in valid_colors:
                if item not in final_colors:
                    final_colors.append(item)
                if len(final_colors) == 4:
                    break

        if not final_colors:
            return fallback_palette
            
        final_colors.sort(key=lambda x: x[1])
        
        hex_colors = [f"#{r:02x}{g:02x}{b:02x}" for _, _, (r, g, b) in final_colors]
        
        while len(hex_colors) < 4:
            hex_colors.append(hex_colors[-1])
            
        return hex_colors[:4]
        
    except Exception as e:
        print(f"Error processing wallpaper: {e}")
        return fallback_palette
    """
    Extracts 4 vibrant colors from an image, discarding muddy/dark backgrounds,
    boosts their LED visibility, and sorts them by hue for a smooth gradient.
    """
    if not image_path:
        image_path = get_wallpaper_path()
        
    # Your preferred cool-toned pastel sky gradient as a rock-solid fallback
    fallback_palette = ["#89b4fa", "#b4befe", "#89dceb", "#74c7ec"]
        
    if not image_path or not os.path.exists(image_path):
        return fallback_palette

    try:
        img = Image.open(image_path).convert("RGB")
        img = img.resize((150, 150)) 
        
        # 1. Crank up the saturation massively before quantization
        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(2.5) # Boost saturation by 250%
        
        # 2. Extract a larger pool of colors to choose from (24 instead of 4)
        # This prevents backgrounds from dominating the entire palette
        img_quant = img.convert("P", palette=Image.ADAPTIVE, colors=24)
        img_rgb = img_quant.convert("RGB")
        colors = img_rgb.getcolors(150 * 150)
        
        valid_colors = []
        
        for count, (r, g, b) in colors:
            h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)
            
            # 3. Filter out dull colors (blacks, whites, and grays)
            if s > 0.15 and v > 0.15: 
                # 4. Mathematically force the colors to be brighter and more saturated for LEDs
                s_boosted = min(1.0, s * 1.5 + 0.2) 
                v_boosted = min(1.0, v * 1.2 + 0.3) 
                
                # Convert back to RGB for final hex output
                r_new, g_new, b_new = colorsys.hsv_to_rgb(h, s_boosted, v_boosted)
                r_hex = int(r_new * 255)
                g_hex = int(g_new * 255)
                b_hex = int(b_new * 255)
                
                # 5. Score color based on dominance *and* how vibrant it is
                # This ensures a bright neon accent beats a slightly tinted gray background
                score = count * (s_boosted * v_boosted)
                
                valid_colors.append((score, h, (r_hex, g_hex, b_hex)))

        # 6. Sort by our custom score to get the best 4 vibrant colors
        valid_colors.sort(key=lambda x: x[0], reverse=True)
        top_4 = valid_colors[:4]
        
        # Failsafe: if the image was literally just monochrome gray/black
        if not top_4:
            return fallback_palette
            
        # 7. Sort the winning 4 by Hue to create that smooth left-to-right visual sweep
        top_4.sort(key=lambda x: x[1])
        
        hex_colors = [f"#{r:02x}{g:02x}{b:02x}" for _, _, (r, g, b) in top_4]
        
        # Ensure exactly 4 colors are returned (duplicate last color if needed)
        while len(hex_colors) < 4:
            hex_colors.append(hex_colors[-1])
            
        return hex_colors[:4]
        
    except Exception as e:
        print(f"Error processing wallpaper: {e}")
        return fallback_palette
    """
    Extracts 4 dominant colors from an image and sorts them by hue 
    to create a smooth left-to-right gradient.
    """
    if not image_path:
        image_path = get_wallpaper_path()
        
    # If we still can't find a wallpaper, return a default cool-toned pastel sky gradient
    if not image_path or not os.path.exists(image_path):
        return ["#89b4fa", "#b4befe", "#89dceb", "#74c7ec"]

    try:
        img = Image.open(image_path)
        # Downsize massively for performance; we only need rough color clusters, not details
        img = img.resize((150, 150)) 
        
        # Quantize the image down to exactly 4 colors
        img_quant = img.convert("P", palette=Image.ADAPTIVE, colors=4)
        img_rgb = img_quant.convert("RGB")
        
        # Extract the colors
        colors = img_rgb.getcolors(150 * 150)
        
        # Get the RGB values of the top 4 colors
        dom_colors = [c[1] for c in sorted(colors, key=lambda x: x[0], reverse=True)[:4]]
        
        # Mathematical sorting: Convert to HSV and sort by Hue for a gradient effect
        def get_hue(rgb):
            # rgb values must be 0.0 to 1.0 for colorsys
            return colorsys.rgb_to_hsv(rgb[0]/255, rgb[1]/255, rgb[2]/255)[0]
            
        dom_colors.sort(key=get_hue)
        
        # Format back to Hex strings
        hex_colors = [f"#{r:02x}{g:02x}{b:02x}" for r, g, b in dom_colors]
        
        # Failsafe: Ensure exactly 4 colors are returned
        while len(hex_colors) < 4:
            hex_colors.append(hex_colors[-1])
            
        return hex_colors[:4]
        
    except Exception as e:
        print(f"Error processing wallpaper: {e}")
        return ["#89b4fa", "#b4befe", "#89dceb", "#74c7ec"]
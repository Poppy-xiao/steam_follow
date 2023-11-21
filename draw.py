from PIL import Image, ImageDraw, ImageFont
import os
# 全局字体路径
fonts_path = os.path.join(os.path.dirname(__file__), 'fonts')
default_font = os.path.join(fonts_path, 'MSYH.TTC')

def concatenate_images_vertically(images):
    total_height = sum(img.height for img in images)
    max_width = max(img.width for img in images)
    combined_img = Image.new('RGBA', (max_width, total_height))

    y_offset = 0
    for img in images:
        combined_img.paste(img, (0, y_offset))
        y_offset += img.height

    return combined_img

# 全局绘制渐变线函数
def draw_gradient_line(draw, width, start, end, color_start, color_end):
    for i in range(start, end):
        r = color_start[0] + (color_end[0] - color_start[0]) * i // (end - start)
        g = color_start[1] + (color_end[1] - color_start[1]) * i // (end - start)
        b = color_start[2] + (color_end[2] - color_start[2]) * i // (end - start)
        draw.line([(0, i), (width, i)], fill=(r, g, b), width=1)

def draw_text(draw, text, x, y, font, font_color):
    draw.text((x, y), text, font=font, fill=font_color)

# 绘制包含图像和文本的矩形
def draw_rectangle_with_image_and_text(image_path, name, game, status, play_time=None, font_size=24):
    height = 150
    width = height * 4
    background_color = "#0e141bcc"
    img = Image.new('RGBA', (width, height), color=background_color)
    draw = ImageDraw.Draw(img)

    # 绘制渐变背景
    color_start, color_end = (28, 32, 40, 0), (14, 20, 27, 0)
    draw_gradient_line(draw, width, 0, height, color_start, color_end)

    # 贴图
    avatar = Image.open(image_path).resize((int(height * 0.63), int(height * 0.63)))
    x = int(0.035 * width)
    y = (height - avatar.height) // 2
    img.paste(avatar, (x, y))

    # 添加绿线和蓝线
    line_width = int(width * 0.082 / 5.5)  # 线的宽度
    green_color = '#7da84e'  # 绿色
    blue_color = '#4c91ac'   # 蓝色

    # 确定使用哪种颜色
    line_color = green_color if status == "is now playing" else blue_color

    # 绘制线
    draw = ImageDraw.Draw(img)
    line_x = x + avatar.width + int(avatar.width * 0.05)
    draw.line([(line_x, y), (line_x, y + avatar.height)], fill=line_color, width=line_width)


    # 设置文本位置
    text_start_x = avatar.width + int(width * 0.1)
    # 创建字体对象
    main_font = ImageFont.truetype(default_font, font_size)
    name_font = ImageFont.truetype(default_font, int(font_size*1.2))
    play_time_font = ImageFont.truetype(default_font, 15)

    # 设置文本颜色
    name_color = '#c7e1ad' if status == "is now playing" else '#7d7e80' if game == "Offline" else '#64bce0'
    status_color = '#7d7e80'
    game_color = '#7da84e' if status == "is now playing" else '#7d7e80' if game == "Offline" else '#4c91ac'

    # 绘制文本
    name_y = height * 1 // 4 - font_size // 2
    status_y = height * 1 // 2 - font_size // 2
    game_y = (height * 11 // 16) - font_size // 2
    draw_text(draw, name, text_start_x, name_y, name_font, name_color)
    draw_text(draw, status, text_start_x, status_y, main_font, status_color)
    draw_text(draw, game, text_start_x, game_y, main_font, game_color)

    if play_time is None:
        return img

    # 绘制游戏时长
    hours, remainder = divmod(play_time, 3600)  # 3600秒等于1小时
    minutes, seconds = divmod(remainder, 60)

    # 打印结果
    # 打印结果
    if hours > 0:
        play_time_text = f"共玩了{hours}小时 {minutes}分钟 {seconds}秒"
    elif minutes > 0:
        play_time_text = f"共玩了{minutes}分钟 {seconds}秒"
    else:
        play_time_text = f"共玩了{seconds}秒"
    text_width, text_height = draw.textsize(play_time_text, font=play_time_font)
    bottom_bar_height = text_height + 15
    bottom_bar = Image.new('RGBA', (img.width, bottom_bar_height), color="#000000")
    bottom_bar_draw = ImageDraw.Draw(bottom_bar)
    bottom_bar_draw.text(((img.width - text_width) / 2, (bottom_bar_height - text_height) / 2), play_time_text, fill="#808080", font=play_time_font)
    
    combined_img = Image.new('RGBA', (img.width, img.height + bottom_bar.height))
    combined_img.paste(img, (0, 0))
    combined_img.paste(bottom_bar, (0, img.height))
    
    return combined_img

# 绘制只包含文本的矩形
def draw_rectangle_with_text(text, font_size=15):
    width, height = 600, 50
    background_color = "#000000"
    img = Image.new('RGBA', (width, height), color=background_color)
    draw = ImageDraw.Draw(img)
    
    # 绘制渐变背景
    start_color, end_color = (14, 15, 18), (0, 0, 0)
    draw_gradient_line(draw, width, 0, height, start_color, end_color)
    
    # 设置文本
    font = ImageFont.truetype(default_font, font_size)
    text_width, text_height = draw.textsize(text, font=font)
    draw.text(((width - text_width) // 2, (height - text_height) // 2), text, font=font, fill="#808080")
    
    return img

# 测试函数
def test():
    img1 = draw_rectangle_with_image_and_text('test.png', 'personaname', 'Genshin Impact', 'is now playing')
    img1.show()
if __name__ == '__main__':
    test()
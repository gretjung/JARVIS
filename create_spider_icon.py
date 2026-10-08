from PIL import Image, ImageDraw

SIZE = 1024
img = Image.new("RGBA", (SIZE, SIZE), (5, 5, 10, 255))
draw = ImageDraw.Draw(img)

cx = SIZE // 2
cy = SIZE // 2

# HUD rings
for r, width in [(470, 18), (430, 8), (365, 5)]:
    draw.ellipse(
        (cx-r, cy-r, cx+r, cy+r),
        outline=(20, 180, 255, 230),
        width=width
    )

# Spider body
draw.ellipse(
    (cx-95, cy-155, cx+95, cy+155),
    fill=(12, 12, 18, 255),
    outline=(220, 30, 45, 255),
    width=14
)

# Spider head
draw.ellipse(
    (cx-105, cy-245, cx+105, cy-55),
    fill=(12, 12, 18, 255),
    outline=(220, 30, 45, 255),
    width=14
)

# Eyes
draw.polygon([
    (cx-72, cy-215),
    (cx-20, cy-200),
    (cx-35, cy-140),
    (cx-82, cy-160),
], fill=(20, 190, 255, 255))

draw.polygon([
    (cx+72, cy-215),
    (cx+20, cy-200),
    (cx+35, cy-140),
    (cx+82, cy-160),
], fill=(20, 190, 255, 255))

# Spider legs
legs = [
    ((cx-65, cy-100), (cx-260, cy-210), (cx-385, cy-170)),
    ((cx-75, cy-30),  (cx-280, cy-80),  (cx-410, cy-20)),
    ((cx-80, cy+45),  (cx-290, cy+40),  (cx-420, cy+120)),
    ((cx-65, cy+105), (cx-245, cy+190), (cx-365, cy+290)),
    ((cx+65, cy-100), (cx+260, cy-210), (cx+385, cy-170)),
    ((cx+75, cy-30),  (cx+280, cy-80),  (cx+410, cy-20)),
    ((cx+80, cy+45),  (cx+290, cy+40), (cx+420, cy+120)),
    ((cx+65, cy+105), (cx+245, cy+190), (cx+365, cy+290)),
]

for p1, p2, p3 in legs:
    draw.line(
        [p1, p2, p3],
        fill=(220, 30, 45, 255),
        width=28,
        joint="curve"
    )

# Center HUD
draw.ellipse(
    (cx-18, cy-18, cx+18, cy+18),
    fill=(20, 190, 255, 255)
)

img.save(r"C:\JARVIS\jarvis_spider.png")

sizes = [
    (16,16),
    (24,24),
    (32,32),
    (48,48),
    (64,64),
    (128,128),
    (256,256),
]

img.save(
    r"C:\JARVIS\jarvis.ico",
    format="ICO",
    sizes=sizes
)

print("SPIDER ICON CREATED")

import re

with open('script.js', 'r', encoding='utf-8') as f:
    content = f.read()

# Scale agent sizes for 32px cells (was 48px)
content = content.replace(', 22, 0, Math.PI', ', 15, 0, Math.PI')
content = content.replace(', 25, 0, Math.PI', ', 18, 0, Math.PI')
content = content.replace(', 17, 0, Math.PI', ', 12, 0, Math.PI')
content = content.replace('size === "large" ? 25 : 22', 'size === "large" ? 18 : 15')

# Reduce font sizes
content = re.sub(r'font = [\'"]bold 22px monospace[\'"]', 'font = "bold 16px monospace"', content)
content = re.sub(r'font = [\'"]bold 20px monospace[\'"]', 'font = "bold 15px monospace"', content)
content = re.sub(r'font = [\'"]bold 17px monospace[\'"]', 'font = "bold 13px monospace"', content)
content = re.sub(r'font = [\'"]19px monospace[\'"]', 'font = "14px monospace"', content)
content = re.sub(r'font = [\'"]bold 15px monospace[\'"]', 'font = "bold 12px monospace"', content)

with open('script.js', 'w', encoding='utf-8') as f:
    f.write(content)

print('✓ Scaled for 32px cells')

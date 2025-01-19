import re

a = """
# test

<div style="text-align:center">
    <img src="/image/test1.webp" height="300" width="400" />
</div><div style="text-align:center">
    <img src="/image/test2.webp" height="300" width="400" />
</div>

<div style="text-align:center">
    <img src="/image/test3.webp" height="300" width="400" />
</div>


"""

pattern = '<img src="/image/.*/>'
img_files = []
for i in re.compile(pattern).findall(a):
    f:str = len('<img src="/image/')
    e:str = '.webp"'
    i:str = i[f:]
    i:str = i[:i.find(e)]
    img_files.append(i)
print(img_files)



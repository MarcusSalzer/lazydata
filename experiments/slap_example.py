from lazydata.slap import SLAP

slap = SLAP(["2", "balls", "-v", "3"])

x = slap.oneP.string  # "balls" [str]
x = slap.oneP.optional.int  # 2 [int|None]
print(x)

c = slap.one(str)  # "balls" [str]
print(c)
# c = slap.one_optional(str)  # "balls" [str|None]
c = slap.set(str)

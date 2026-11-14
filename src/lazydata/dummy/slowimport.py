from time import perf_counter, sleep

print("slow import...")
_t0 = perf_counter()
sleep(1)
print(f"slow_import OK ({perf_counter() - _t0:.3f} s)")

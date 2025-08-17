import time

# ⏱ Utility to benchmark the runtime of any function
def benchmark_function(func, *args, **kwargs):
    """
    Measures execution time of any function and returns result + duration.
    """
    start = time.time()                         # 🕒 Start timer
    result = func(*args, **kwargs)              # ⚙️ Execute the function
    end = time.time()                           # 🕒 Stop timer

    duration = round(end - start, 6)            # ⏱ Time in seconds (to microseconds)
    return {
        "result": result,                       # ✅ Output from the actual function
        "execution_time_sec": duration          # ⏱ How long it took
    }

